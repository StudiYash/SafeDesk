"""Manual intruder detection and local evidence capture demo screen."""

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
from safedesk.intruders.intruder_capture import save_intruder_evidence_frame
from safedesk.intruders.intruder_manifest import build_intruder_capture_status
from safedesk.logging.event_logger import build_logger_from_config
from safedesk.storage.paths import project_root
from safedesk.vision.camera_manager import CameraManager
from safedesk.vision.owner_manifest import build_registration_status
from safedesk.vision.owner_recognition import verify_owner_against_samples


class IntruderDetectionDemoScreen(ctk.CTkFrame):
    """Manual owner-vs-unknown detection foundation.

    Camera and analysis start only through explicit owner button clicks.
    """

    def __init__(self, master, context: RuntimeContext):
        super().__init__(master, fg_color=ds.CONTENT_BG)
        self.context = context
        self.config = context.load_result.config
        self.intruder_config = self.config.get("intruder_detection", {})
        self.registration_config = self.config.get("owner_face_registration", {})
        self.event_logger = build_logger_from_config(self.config)
        self.camera = CameraManager(int(self.intruder_config.get("camera_index", 0)))
        self.current_frame = None
        self.preview_image = None
        self.preview_after_id = None
        self.preview_size = (500, 281)
        self.is_processing = False
        self._operation_queue: queue.Queue[tuple[Any, Exception | None]] = queue.Queue()
        self._operation_poll_after_id = None
        self._active_completion: Callable[[Any], None] | None = None
        self._is_destroyed = False

        self.intruder_images_dir = self._resolve_path(self.intruder_config.get("intruder_images_dir", "data/intruders"))
        self.intruder_manifest_path = self._resolve_path(
            self.intruder_config.get("manifest_path", "data/config/intruder_capture_manifest.json")
        )
        self.owner_samples_dir = self._resolve_path(self.registration_config.get("samples_dir", "data/owner/samples"))
        self.owner_manifest_path = self._resolve_path(
            self.registration_config.get("manifest_path", "data/config/owner_registration_manifest.json")
        )
        self.required_owner_samples = int(self.intruder_config.get("minimum_owner_samples_required", 5))

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        page = ScrollablePage(self)
        page.grid(row=0, column=0, sticky="nsew")

        PageHeader(
            page,
            "Intruder Detection Demo",
            "Manually compare a current camera frame against local owner samples and optionally save local evidence.",
        ).grid(row=0, column=0, sticky="ew", padx=4, pady=(0, 10))

        InfoBanner(
            page,
            "Manual foundation only. No protected mode, threat escalation, automatic email, alarm, lockdown, or shutdown runs here. "
            "Unknown/unverified evidence images are local-only and ignored by Git.",
            kind="warning",
            compact=True,
        ).grid(row=1, column=0, sticky="ew", padx=4, pady=(0, 12))

        workspace = ctk.CTkFrame(page, fg_color="transparent")
        workspace.grid(row=2, column=0, sticky="nsew", padx=4, pady=0)
        workspace.grid_columnconfigure(0, weight=1, uniform="intruder")
        workspace.grid_columnconfigure(1, weight=1, uniform="intruder")

        left_panel = ctk.CTkFrame(workspace, **ds.card_kwargs())
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        left_panel.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            left_panel,
            text="Detection Status",
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

        button_row = ctk.CTkFrame(left_panel, fg_color="transparent")
        button_row.grid(row=3, column=0, sticky="ew", padx=ds.SPACE_LG, pady=(0, ds.SPACE_SM))
        for column in (0, 1):
            button_row.grid_columnconfigure(column, weight=1)

        self.start_camera_button = ctk.CTkButton(button_row, text="Start Camera", command=self.start_camera, **ds.primary_button_kwargs())
        self.start_camera_button.grid(row=0, column=0, sticky="ew", padx=(0, 6), pady=(0, 8))
        self.analyze_button = ctk.CTkButton(
            button_row,
            text="Analyze & Capture If Unknown",
            command=self.analyze_current_frame,
            **ds.primary_button_kwargs(),
        )
        self.analyze_button.grid(row=0, column=1, sticky="ew", padx=(6, 0), pady=(0, 8))
        self.stop_camera_button = ctk.CTkButton(button_row, text="Stop Camera", command=self.stop_camera, **ds.secondary_button_kwargs())
        self.stop_camera_button.grid(row=1, column=0, sticky="ew", padx=(0, 6))
        self.refresh_status_button = ctk.CTkButton(button_row, text="Refresh Status", command=self.refresh_status, **ds.secondary_button_kwargs())
        self.refresh_status_button.grid(row=1, column=1, sticky="ew", padx=(6, 0))

        self.message_banner = InfoBanner(
            left_panel,
            "Camera and analysis start only by button click.",
            kind="neutral",
            compact=True,
            wraplength=360,
        )
        self.message_banner.grid(row=4, column=0, sticky="ew", padx=ds.SPACE_LG, pady=(0, ds.SPACE_SM))

        self.result_panel = ctk.CTkFrame(left_panel, **ds.panel_kwargs())
        self.result_panel.grid(row=5, column=0, sticky="ew", padx=ds.SPACE_LG, pady=(0, ds.SPACE_LG))
        self.result_panel.grid_columnconfigure(0, weight=1)
        self.result_label = ctk.CTkLabel(
            self.result_panel,
            text="Last intruder detection result: not run yet",
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
            text="Camera Preview",
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

    def refresh_status(self) -> None:
        registration_status = build_registration_status(
            self.owner_samples_dir,
            self.owner_manifest_path,
            self.required_owner_samples,
        )
        capture_status = build_intruder_capture_status(
            self.intruder_images_dir,
            self.intruder_manifest_path,
            enabled=self.intruder_config.get("enabled", True),
            demo_only=self.intruder_config.get("demo_only", True),
        )
        self.status_label.configure(
            text=(
                f"Intruder detection: {'enabled' if capture_status.enabled else 'disabled'}\n"
                f"Mode: {'demo only' if capture_status.demo_only else 'review required'}\n"
                f"Owner samples: {registration_status.sample_count} saved / {self.required_owner_samples} required\n"
                f"Evidence captures: {capture_status.image_count} saved locally\n"
                f"Camera: {'open' if self.camera.is_opened else 'stopped'}"
            )
        )

    def start_camera(self) -> None:
        if self.is_processing:
            self.message_banner.set_message("Wait for the current intruder detection operation to finish before starting the camera.")
            return
        status = self.camera.open()
        self.message_banner.set_message(status.message)
        if status.success and self.preview_after_id is None:
            self._schedule_preview()
        self.refresh_status()

    def analyze_current_frame(self) -> None:
        if self.is_processing:
            self.message_banner.set_message("Intruder detection work is already running. Please wait for it to finish.")
            return
        if not self.intruder_config.get("enabled", True):
            self.message_banner.set_message("Intruder Detection Demo is disabled in configuration.")
            self.result_label.configure(text="Last intruder detection result: disabled\nReason: intruder_detection.enabled is false.")
            self._log_intruder_check("skipped", "disabled", image_saved=False)
            return
        if not self.camera.is_opened or self.current_frame is None:
            self.message_banner.set_message("Start the camera and wait for a preview frame before analyzing.")
            self.result_label.configure(text="Last intruder detection result: camera/frame not ready")
            self._log_intruder_check("blocked", "camera_not_ready", image_saved=False)
            return

        registration_status = build_registration_status(
            self.owner_samples_dir,
            self.owner_manifest_path,
            self.required_owner_samples,
        )
        if registration_status.sample_count < self.required_owner_samples:
            self.message_banner.set_message("Not ready: owner samples are required before intruder detection testing.")
            self.result_label.configure(
                text=(
                    "Last intruder detection result: not ready\n"
                    f"Owner samples: {registration_status.sample_count} saved / {self.required_owner_samples} required"
                )
            )
            self._log_intruder_check("skipped", "not_ready", image_saved=False, sample_count=registration_status.sample_count)
            return

        frame_snapshot = self.current_frame.copy() if hasattr(self.current_frame, "copy") else self.current_frame

        def worker():
            recognition = verify_owner_against_samples(frame_snapshot, self.config)
            capture = None
            should_capture = recognition.success and recognition.ready and not recognition.recognized
            if should_capture:
                capture = save_intruder_evidence_frame(
                    frame_snapshot,
                    self.intruder_images_dir,
                    self.intruder_manifest_path,
                    image_format=str(self.intruder_config.get("image_format", "jpg")),
                    image_quality=int(self.intruder_config.get("image_quality", 90)),
                )
            return recognition, capture

        def on_complete(result) -> None:
            recognition, capture = result
            self._handle_analysis_result(recognition, capture)

        self.message_banner.set_message("Analyzing current frame manually. This may take a while on CPU.")
        self._run_background_operation(worker, on_complete)

    def _handle_analysis_result(self, recognition, capture) -> None:
        if not recognition.ready:
            self.message_banner.set_message("Intruder detection check skipped safely because prerequisites were not ready.")
            self.result_label.configure(text=f"Last intruder detection result: not ready\nReason: {recognition.message}")
            self._log_intruder_check(
                "skipped",
                "not_ready",
                image_saved=False,
                samples_checked=recognition.samples_checked,
            )
            self.refresh_status()
            return

        if recognition.recognized:
            self.message_banner.set_message("Manual check complete: owner appears recognized. No evidence image saved.")
            self.result_label.configure(
                text=(
                    "Last intruder detection result: owner recognized\n"
                    "Evidence saved: no\n"
                    f"Samples checked: {recognition.samples_checked}"
                )
            )
            self._log_intruder_check(
                "success",
                "owner_recognized",
                image_saved=False,
                samples_checked=recognition.samples_checked,
            )
            self.refresh_status()
            return

        result_status = "uncertain" if recognition.uncertain else "unknown_detected"
        if capture is None:
            self.message_banner.set_message("Manual check complete: unknown/unverified result. Evidence capture was not attempted.")
            self.result_label.configure(
                text=(
                    f"Last intruder detection result: {result_status}\n"
                    "Evidence saved: no"
                )
            )
            self._log_intruder_check("failed", result_status, image_saved=False, samples_checked=recognition.samples_checked)
            self.refresh_status()
            return

        if capture.success:
            self.message_banner.set_message("Unknown/unverified result captured as local evidence.")
            self.result_label.configure(
                text=(
                    f"Last intruder detection result: {result_status}\n"
                    "Evidence saved: yes\n"
                    f"Capture ID: {capture.capture_id}\n"
                    f"Local evidence count: {capture.image_count}"
                )
            )
            self._log_intruder_check(
                "success",
                result_status,
                image_saved=True,
                capture_id=capture.capture_id,
                image_count=capture.image_count,
                samples_checked=recognition.samples_checked,
            )
            self._log_intruder_capture(capture.capture_id, capture.image_count)
        else:
            self.message_banner.set_message("Unknown/unverified result found, but local evidence capture failed safely.")
            self.result_label.configure(
                text=(
                    f"Last intruder detection result: {result_status}\n"
                    "Evidence saved: no\n"
                    f"Capture status: {capture.status}"
                )
            )
            self._log_intruder_check(
                "failed",
                "capture_failed",
                image_saved=False,
                samples_checked=recognition.samples_checked,
            )
        self.refresh_status()

    def _run_background_operation(self, worker, on_complete) -> None:
        if self.is_processing:
            self.message_banner.set_message("Intruder detection work is already running. Please wait for it to finish.")
            return
        self._set_processing(True, "analyzing current frame...")
        self._active_completion = on_complete

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
                self.message_banner.set_message("Intruder detection operation failed safely.")
                self.result_label.configure(text="Last intruder detection result: failed safely")
                self._log_intruder_check("failed", "operation_failed", image_saved=False)
            elif self._active_completion is not None:
                self._active_completion(result)
        finally:
            self._active_completion = None
            self._set_processing(False, "idle")

    def _set_processing(self, processing: bool, operation: str) -> None:
        self.is_processing = processing
        self.operation_label.configure(text=f"Operation: {operation}")
        state = "disabled" if processing else "normal"
        for button in (self.start_camera_button, self.analyze_button, self.refresh_status_button):
            button.configure(state=state)
        self.stop_camera_button.configure(state="normal")

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

    def stop_camera(self) -> None:
        self.release_resources()
        self._clear_preview("Camera preview is stopped.")
        self.message_banner.set_message("Camera stopped.")
        self.refresh_status()

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
    def build_intruder_check_log_message(result_status: str) -> str:
        if result_status == "camera_not_ready":
            return "Manual intruder check was blocked because camera/frame was not ready."
        if result_status == "not_ready":
            return "Manual intruder check was skipped because prerequisites were not ready."
        if result_status in {"owner_recognized", "unknown_detected", "uncertain", "capture_failed", "disabled", "operation_failed"}:
            return f"Manual intruder check completed with status: {result_status}."
        return "Manual intruder check completed."

    @staticmethod
    def intruder_check_log_severity(status: str, result_status: str, image_saved: bool) -> str:
        warning_results = {"camera_not_ready", "unknown_detected", "uncertain", "capture_failed", "operation_failed"}
        if image_saved or result_status in warning_results:
            return "WARNING"
        if status in {"failed", "blocked"}:
            return "WARNING"
        return "INFO"

    def _log_intruder_check(
        self,
        status: str,
        result_status: str,
        image_saved: bool,
        capture_id: str = "",
        image_count: int = 0,
        sample_count: int | None = None,
        samples_checked: int = 0,
    ) -> None:
        try:
            metadata = {
                "result_status": result_status,
                "image_saved": image_saved,
                "sample_count": self._owner_sample_count() if sample_count is None else sample_count,
                "samples_checked": samples_checked,
                "demo_only": True,
            }
            if capture_id:
                metadata["capture_id"] = capture_id
            if image_count:
                metadata["image_count"] = image_count
            self.event_logger.log_event(
                category="intruder_detection",
                action="manual_intruder_check",
                status=status,
                severity=self.intruder_check_log_severity(status, result_status, image_saved),
                message=self.build_intruder_check_log_message(result_status),
                metadata=metadata,
            )
        except Exception:
            pass

    def _log_intruder_capture(self, capture_id: str, image_count: int) -> None:
        try:
            self.event_logger.log_event(
                category="intruder_detection",
                action="intruder_image_captured",
                status="success",
                severity="WARNING",
                message="Intruder evidence image captured locally.",
                metadata={
                    "result_status": "evidence_captured",
                    "image_saved": True,
                    "capture_id": capture_id,
                    "image_count": image_count,
                    "demo_only": True,
                },
            )
        except Exception:
            pass

    def _owner_sample_count(self) -> int:
        status = build_registration_status(self.owner_samples_dir, self.owner_manifest_path, self.required_owner_samples)
        return status.sample_count

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
