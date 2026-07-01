"""Face recognition demo screen."""

from pathlib import Path
import queue
import threading
from typing import Any, Callable

import customtkinter as ctk

from safedesk.app.application import RuntimeContext
from safedesk.gui import design_system as ds
from safedesk.gui.components.info_banner import InfoBanner
from safedesk.gui.components.page_header import PageHeader
from safedesk.gui.components.scrollable_page import ScrollablePage
from safedesk.logging.event_logger import build_logger_from_config
from safedesk.storage.paths import project_root
from safedesk.vision.camera_manager import CameraManager
from safedesk.vision.compute_device import ComputeDeviceStatus, detect_compute_device
from safedesk.vision.deepface_adapter import check_deepface_dependency, compute_face_representation
from safedesk.vision.owner_recognition import discover_owner_sample_paths, verify_owner_against_samples


class FaceRecognitionDemoScreen(ctk.CTkFrame):
    """Manual local recognition demo screen.

    Recognition runs only when the owner clicks Verify Current Frame.
    """

    def __init__(self, master, context: RuntimeContext):
        super().__init__(master, fg_color=ds.CONTENT_BG)
        self.context = context
        self.recognition_config = context.load_result.config.get("owner_recognition", {})
        self.registration_config = context.load_result.config.get("owner_face_registration", {})
        self.event_logger = build_logger_from_config(context.load_result.config)
        self.camera = CameraManager(int(self.registration_config.get("camera_index", 0)))
        self.current_frame = None
        self.preview_image = None
        self.preview_after_id = None
        self.preview_size = (500, 281)
        self.is_processing = False
        self.compute_device_status: ComputeDeviceStatus | None = None
        self._operation_queue: queue.Queue[tuple[Any, Exception | None]] = queue.Queue()
        self._operation_poll_after_id = None
        self._active_completion: Callable[[Any], None] | None = None
        self._is_destroyed = False

        self.samples_dir = self._resolve_path(self.registration_config.get("samples_dir", "data/owner/samples"))
        self.required_samples = int(self.recognition_config.get("minimum_samples_required", 5))

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        page = ScrollablePage(self)
        page.grid(row=0, column=0, sticky="nsew")

        PageHeader(
            page,
            "Face Recognition Demo",
            "Compare the current camera frame against local owner samples without unlocking or activating protected mode.",
        ).grid(row=0, column=0, sticky="ew", padx=4, pady=(0, 10))

        InfoBanner(
            page,
            "Demo only: this checks whether the current frame appears to match local owner samples. "
            "It does not unlock SafeDesk, enable protected mode, run liveness checks, capture intruders, or send data anywhere.",
            kind="warning",
            compact=True,
        ).grid(row=1, column=0, sticky="ew", padx=4, pady=(0, 12))

        workspace = ctk.CTkFrame(page, fg_color="transparent")
        workspace.grid(row=2, column=0, sticky="nsew", padx=4, pady=0)
        workspace.grid_columnconfigure(0, weight=1, uniform="recognition")
        workspace.grid_columnconfigure(1, weight=1, uniform="recognition")

        left_panel = ctk.CTkFrame(workspace, **ds.card_kwargs())
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        left_panel.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            left_panel,
            text="Recognition Status",
            font=ctk.CTkFont(size=ds.FONT_H3, weight="bold"),
            text_color=ds.TEXT_PRIMARY,
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=ds.SPACE_LG, pady=(ds.SPACE_LG, ds.SPACE_SM))

        self.status_label = ctk.CTkLabel(
            left_panel,
            text="",
            justify="left",
            anchor="w",
            text_color=ds.TEXT_SECONDARY,
            wraplength=390,
            font=ctk.CTkFont(size=ds.FONT_SMALL),
        )
        self.status_label.grid(row=1, column=0, sticky="ew", padx=ds.SPACE_LG, pady=(0, ds.SPACE_SM))

        self.operation_label = ctk.CTkLabel(
            left_panel,
            text="Operation: idle",
            justify="left",
            anchor="w",
            text_color=ds.SAFEDESK_ALERT,
            font=ctk.CTkFont(size=ds.FONT_BODY, weight="bold"),
        )
        self.operation_label.grid(row=2, column=0, sticky="ew", padx=ds.SPACE_LG, pady=(0, ds.SPACE_SM))

        readiness_row = ctk.CTkFrame(left_panel, fg_color="transparent")
        readiness_row.grid(row=3, column=0, sticky="ew", padx=ds.SPACE_LG, pady=(0, ds.SPACE_SM))
        for column in (0, 1):
            readiness_row.grid_columnconfigure(column, weight=1)
        self.check_readiness_button = ctk.CTkButton(readiness_row, text="Check Readiness", command=self.check_readiness, **ds.secondary_button_kwargs())
        self.check_readiness_button.grid(row=0, column=0, sticky="ew", padx=(0, 6), pady=(0, 8))
        self.prepare_model_button = ctk.CTkButton(readiness_row, text="Prepare Model", command=self.prepare_model, **ds.secondary_button_kwargs())
        self.prepare_model_button.grid(row=0, column=1, sticky="ew", padx=(6, 0), pady=(0, 8))
        self.refresh_status_button = ctk.CTkButton(readiness_row, text="Refresh Status", command=self.refresh_status, **ds.secondary_button_kwargs())
        self.refresh_status_button.grid(row=1, column=0, columnspan=2, sticky="ew")

        camera_row = ctk.CTkFrame(left_panel, fg_color="transparent")
        camera_row.grid(row=4, column=0, sticky="ew", padx=ds.SPACE_LG, pady=(0, ds.SPACE_SM))
        for column in (0, 1):
            camera_row.grid_columnconfigure(column, weight=1)
        self.start_camera_button = ctk.CTkButton(camera_row, text="Start Camera", command=self.start_camera, **ds.primary_button_kwargs())
        self.start_camera_button.grid(row=0, column=0, sticky="ew", padx=(0, 6), pady=(0, 8))
        self.verify_frame_button = ctk.CTkButton(camera_row, text="Verify Frame", command=self.verify_current_frame, **ds.primary_button_kwargs())
        self.verify_frame_button.grid(row=0, column=1, sticky="ew", padx=(6, 0), pady=(0, 8))
        self.stop_camera_button = ctk.CTkButton(camera_row, text="Stop Camera", command=self.stop_camera, **ds.secondary_button_kwargs())
        self.stop_camera_button.grid(row=1, column=0, columnspan=2, sticky="ew")

        self.message_banner = InfoBanner(
            left_panel,
            "Recognition has not run. Camera and recognition start only by button click.",
            kind="neutral",
            compact=True,
            wraplength=360,
        )
        self.message_banner.grid(row=5, column=0, sticky="ew", padx=ds.SPACE_LG, pady=(0, ds.SPACE_SM))

        self.result_panel = ctk.CTkFrame(left_panel, **ds.panel_kwargs())
        self.result_panel.grid(row=6, column=0, sticky="ew", padx=ds.SPACE_LG, pady=(0, ds.SPACE_LG))
        self.result_panel.grid_columnconfigure(0, weight=1)
        self.result_label = ctk.CTkLabel(
            self.result_panel,
            text="Last recognition result: not run yet",
            justify="left",
            anchor="w",
            wraplength=370,
            text_color=ds.TEXT_PRIMARY,
            font=ctk.CTkFont(size=ds.FONT_SMALL),
        )
        self.result_label.grid(row=0, column=0, sticky="ew", padx=ds.SPACE_MD, pady=ds.SPACE_SM)

        preview_panel = ctk.CTkFrame(workspace, **ds.card_kwargs())
        preview_panel.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        preview_panel.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            preview_panel,
            text="Live Camera Preview",
            font=ctk.CTkFont(size=ds.FONT_H3, weight="bold"),
            text_color=ds.TEXT_PRIMARY,
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=ds.SPACE_LG, pady=(ds.SPACE_LG, ds.SPACE_SM))

        self.preview_frame = ctk.CTkFrame(preview_panel, width=self.preview_size[0], height=self.preview_size[1], **ds.panel_kwargs())
        self.preview_frame.grid(row=1, column=0, sticky="n", padx=ds.SPACE_LG, pady=(0, ds.SPACE_MD))
        self.preview_frame.grid_propagate(False)
        self.preview_frame.grid_columnconfigure(0, weight=1)
        self.preview_frame.grid_rowconfigure(0, weight=1)

        self._create_preview_label("Camera preview is stopped.")
        self.refresh_status()

    def _resolve_path(self, value: str) -> Path:
        path = Path(value)
        return path if path.is_absolute() else project_root() / path

    def _sample_count(self) -> int:
        return len(discover_owner_sample_paths(self.samples_dir))

    def _recognition_engine_text(self) -> str:
        if self.compute_device_status is None:
            return "Recognition engine: not checked"
        if self.compute_device_status.device_type == "gpu":
            return "Recognition engine: GPU available"
        if self.compute_device_status.device_type == "cpu":
            return "Recognition engine: CPU mode"
        return "Recognition engine: unknown"

    def _compute_runtime_note(self) -> str:
        if self.compute_device_status is None:
            return "Recognition may take a while on CPU if GPU acceleration is not available."
        if self.compute_device_status.device_type == "gpu":
            return "GPU detected. Running TensorFlow-backed recognition with available acceleration."
        if self.compute_device_status.device_type == "cpu":
            return "Recognition is running in CPU mode. This may take several seconds."
        return self.compute_device_status.message

    def _set_result_display(self, text: str) -> None:
        self.result_label.configure(text=text)

    def refresh_status(self) -> None:
        sample_count = self._sample_count()
        ready_by_samples = sample_count >= self.required_samples
        self.status_label.configure(
            text=(
                f"Model / detector: {self.recognition_config.get('model_name', 'ArcFace')} / "
                f"{self.recognition_config.get('detector_backend', 'retinaface')}\n"
                f"{self._recognition_engine_text()}\n"
                f"Samples: {sample_count} saved / {self.required_samples} required\n"
                f"Demo readiness: {'ready by samples' if ready_by_samples else 'not ready by samples'}"
            )
        )

    def _set_processing_buttons(self, processing: bool) -> None:
        state = "disabled" if processing else "normal"
        for button in (
            self.check_readiness_button,
            self.prepare_model_button,
            self.refresh_status_button,
            self.start_camera_button,
            self.verify_frame_button,
        ):
            button.configure(state=state)
        self.stop_camera_button.configure(state="normal")

    def _run_background_operation(
        self,
        operation_label: str,
        message: str,
        worker: Callable[[], Any],
        on_complete: Callable[[Any], None],
    ) -> None:
        if self.is_processing:
            self.message_banner.set_message("Recognition work is already running. Please wait for it to finish.")
            return

        self.is_processing = True
        self._active_completion = on_complete
        self.operation_label.configure(text=f"Operation: {operation_label}")
        self.message_banner.set_message(message)
        self._set_processing_buttons(True)

        def run_worker() -> None:
            try:
                self._operation_queue.put((worker(), None))
            except Exception as exc:
                self._operation_queue.put((None, exc))

        threading.Thread(target=run_worker, daemon=True).start()
        self._schedule_operation_poll()

    def _schedule_operation_poll(self) -> None:
        if self._is_destroyed:
            return
        if self._operation_poll_after_id is None:
            self._operation_poll_after_id = self.after(100, self._poll_operation_queue)

    def _poll_operation_queue(self) -> None:
        self._operation_poll_after_id = None
        if self._is_destroyed:
            return

        try:
            result, error = self._operation_queue.get_nowait()
        except queue.Empty:
            if self.is_processing:
                self._schedule_operation_poll()
            return

        try:
            if error is not None:
                self.message_banner.set_message(f"Recognition operation failed safely: {error}")
            elif self._active_completion is not None:
                self._active_completion(result)
        finally:
            self.is_processing = False
            self._active_completion = None
            self.operation_label.configure(text="Operation: idle")
            self._set_processing_buttons(False)
            self.refresh_status()

    def check_readiness(self) -> None:
        def worker() -> dict[str, Any]:
            return {
                "dependency": check_deepface_dependency(),
                "compute": detect_compute_device(),
                "sample_count": self._sample_count(),
            }

        def on_complete(result: dict[str, Any]) -> None:
            dependency = result["dependency"]
            compute_status = result["compute"]
            sample_count = result["sample_count"]
            self.compute_device_status = compute_status
            if not dependency.available:
                self.message_banner.set_message(f"Not ready: DeepFace dependency issue: {dependency.message} {compute_status.message}")
            elif sample_count < self.required_samples:
                self.message_banner.set_message(
                    f"Not ready: {sample_count} owner samples available, {self.required_samples} required. "
                    f"{compute_status.message}"
                )
            else:
                self.message_banner.set_message(f"Ready by samples. DeepFace importable. {compute_status.message}")

        self._run_background_operation(
            "checking readiness...",
            "Checking recognition readiness and TensorFlow compute device...",
            worker,
            on_complete,
        )

    def prepare_model(self) -> None:
        samples = discover_owner_sample_paths(self.samples_dir)
        if not samples:
            self.message_banner.set_message("Not ready: owner samples are required before model warm-up.")
            return

        def worker():
            return compute_face_representation(samples[0], self.recognition_config)

        def on_complete(result) -> None:
            self.message_banner.set_message(result.message)

        self._run_background_operation(
            "preparing model...",
            f"Preparing recognition model. First run may need internet and may take a while on CPU... {self._compute_runtime_note()}",
            worker,
            on_complete,
        )

    def start_camera(self) -> None:
        if self.is_processing:
            self.message_banner.set_message("Wait for the current recognition operation to finish before starting the camera.")
            return
        status = self.camera.open()
        self.message_banner.set_message(status.message)
        if status.success and self.preview_after_id is None:
            self._schedule_preview()

    def _schedule_preview(self) -> None:
        self._refresh_preview()
        if self.camera.is_opened:
            self.preview_after_id = self.after(120, self._schedule_preview)
        else:
            self.preview_after_id = None

    def _refresh_preview(self) -> None:
        result = self.camera.read_frame()
        if not result.success:
            self._clear_preview(result.message)
            return

        self.current_frame = result.frame
        try:
            import cv2
            from PIL import Image

            rgb_frame = cv2.cvtColor(result.frame, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(rgb_frame)
            image.thumbnail(self.preview_size)
            self.preview_image = ctk.CTkImage(light_image=image, dark_image=image, size=image.size)
            self.preview_label.configure(text="", image=self.preview_image)
        except Exception as exc:
            self._clear_preview(f"Preview unavailable: {exc}")

    def verify_current_frame(self) -> None:
        if not self.camera.is_opened or self.current_frame is None:
            self.message_banner.set_message("Start the camera and wait for a preview frame before running recognition.")
            self._set_result_display(
                "Last recognition result: Not ready\nReason: start the camera and wait for a preview frame before running recognition."
            )
            self._log_recognition_event(
                "blocked",
                {"result_status": "camera_not_ready"},
            )
            return

        frame_snapshot = self.current_frame.copy() if hasattr(self.current_frame, "copy") else self.current_frame

        def worker():
            return verify_owner_against_samples(frame_snapshot, self.context.load_result.config)

        def on_complete(result) -> None:
            if result.best_distance is None:
                self._set_result_display(f"Last recognition result: Not ready\nReason: {result.message}")
                self.message_banner.set_message("Recognition failed safely.")
                self._log_recognition_event(
                    "skipped" if not result.ready else "failed",
                    {
                        "result_status": "not_ready" if not result.ready else "failed",
                        "samples_checked": result.samples_checked,
                    },
                )
            else:
                result_lines = [
                    f"Last recognition result: {result.message}",
                    f"Best distance: {result.best_distance:.4f}",
                    f"Samples checked: {result.samples_checked}",
                ]
                if result.matched_sample:
                    result_lines.insert(2, f"Matched sample: {result.matched_sample}")
                self._set_result_display("\n".join(result_lines))
                self.message_banner.set_message(
                    f"Recognition finished: {result.message.lower()}."
                )
                event_status = "success" if result.recognized else "blocked" if result.uncertain else "failed"
                self._log_recognition_event(
                    event_status,
                    {
                        "result_status": "recognized" if result.recognized else "uncertain" if result.uncertain else "not_recognized",
                        "samples_checked": result.samples_checked,
                    },
                )

        self._set_result_display("Last recognition result: verification running...")
        self._run_background_operation(
            "verifying current frame...",
            f"Verifying current frame. This may take a while on CPU... {self._compute_runtime_note()}",
            worker,
            on_complete,
        )

    def stop_camera(self) -> None:
        self.release_resources()
        self._clear_preview("Camera preview is stopped.")
        self.message_banner.set_message("Camera stopped.")

    def release_resources(self) -> None:
        if self.preview_after_id is not None:
            try:
                self.after_cancel(self.preview_after_id)
            except Exception:
                pass
            self.preview_after_id = None
        self.current_frame = None
        self.camera.release()

    def _clear_preview(self, message: str = "Camera preview is stopped.") -> None:
        self.preview_image = None
        self.current_frame = None
        try:
            self.preview_label.destroy()
        except Exception:
            pass
        self._create_preview_label(message)

    def _create_preview_label(self, message: str = "Camera preview is stopped.") -> None:
        self.preview_label = ctk.CTkLabel(self.preview_frame, text=message, text_color=ds.TEXT_SECONDARY, wraplength=420)
        self.preview_label.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

    @staticmethod
    def build_recognition_log_message(result_status: str) -> str:
        if result_status == "camera_not_ready":
            return "Recognition demo check was blocked because camera/frame was not ready."
        if result_status == "not_ready":
            return "Recognition demo check was skipped because prerequisites were not ready."
        if result_status in {"recognized", "not_recognized", "uncertain", "failed"}:
            return f"Recognition demo check completed with status: {result_status}."
        return "Recognition demo check completed with status: unknown."

    def _log_recognition_event(self, status: str, metadata: dict | None = None) -> None:
        try:
            safe_metadata = {
                "sample_count": self._sample_count(),
                "demo_only": True,
            }
            if metadata:
                safe_metadata.update(metadata)
            result_status = str(safe_metadata.get("result_status", "unknown"))
            self.event_logger.log_event(
                category="recognition_demo",
                action="manual_recognition_check",
                status=status,
                severity="WARNING" if status in {"failed", "blocked"} else "INFO",
                message=self.build_recognition_log_message(result_status),
                metadata=safe_metadata,
            )
        except Exception:
            pass

    def destroy(self) -> None:
        self._is_destroyed = True
        if self._operation_poll_after_id is not None:
            try:
                self.after_cancel(self._operation_poll_after_id)
            except Exception:
                pass
            self._operation_poll_after_id = None
        self.release_resources()
        super().destroy()
