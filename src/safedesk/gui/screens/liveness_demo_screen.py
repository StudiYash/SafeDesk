"""Basic liveness movement challenge demo screen."""

import customtkinter as ctk

from safedesk.app.application import RuntimeContext
from safedesk.gui import design_system as ds
from safedesk.gui.components.info_banner import InfoBanner
from safedesk.gui.components.page_header import PageHeader
from safedesk.gui.components.scrollable_page import ScrollablePage
from safedesk.logging.event_logger import build_logger_from_config
from safedesk.vision.camera_manager import CameraManager
from safedesk.vision.liveness_challenge import LivenessChallenge, challenge_instruction, create_liveness_challenge
from safedesk.vision.liveness_detector import LivenessDetectionResult, LivenessDetectionState, update_liveness_state


def is_liveness_demo_enabled(liveness_config: dict) -> bool:
    """Return whether the demo challenge may run for the current config."""
    return liveness_config.get("enabled", True) is True


class LivenessDemoScreen(ctk.CTkFrame):
    """Manual demo-only liveness movement challenge screen."""

    def __init__(self, master, context: RuntimeContext):
        super().__init__(master, fg_color=ds.CONTENT_BG)
        self.context = context
        self.liveness_config = context.load_result.config.get("liveness", {})
        self.event_logger = build_logger_from_config(context.load_result.config)
        self.camera = CameraManager(int(self.liveness_config.get("camera_index", 0)))
        self.current_frame = None
        self.preview_image = None
        self.preview_after_id = None
        self.preview_size = (500, 281)
        self.challenge: LivenessChallenge | None = None
        self.liveness_state = LivenessDetectionState()
        self.liveness_active = False

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        page = ScrollablePage(self)
        page.grid(row=0, column=0, sticky="nsew")

        PageHeader(
            page,
            "Liveness Demo",
            "A basic local movement challenge foundation for later protected-mode planning.",
        ).grid(row=0, column=0, sticky="ew", padx=4, pady=(0, 10))

        InfoBanner(
            page,
            "Demo only: this checks simple face-position movement. It does not unlock SafeDesk, start protected mode, "
            "capture intruders, send alerts, or shut down the laptop.",
            kind="warning",
            compact=True,
        ).grid(row=1, column=0, sticky="ew", padx=4, pady=(0, 12))

        workspace = ctk.CTkFrame(page, fg_color="transparent")
        workspace.grid(row=2, column=0, sticky="nsew", padx=4, pady=0)
        workspace.grid_columnconfigure(0, weight=1, uniform="liveness")
        workspace.grid_columnconfigure(1, weight=1, uniform="liveness")

        left_panel = ctk.CTkFrame(workspace, **ds.card_kwargs())
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        left_panel.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            left_panel,
            text="Liveness Status",
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

        self.instruction_label = ctk.CTkLabel(
            left_panel,
            text="Challenge instruction: not started",
            justify="left",
            anchor="w",
            text_color=ds.TEXT_PRIMARY,
            wraplength=390,
            font=ctk.CTkFont(size=ds.FONT_BODY, weight="bold"),
        )
        self.instruction_label.grid(row=2, column=0, sticky="ew", padx=ds.SPACE_LG, pady=(0, ds.SPACE_SM))

        self.operation_label = ctk.CTkLabel(
            left_panel,
            text="Operation: idle",
            justify="left",
            anchor="w",
            text_color=ds.SAFEDESK_ALERT,
            font=ctk.CTkFont(size=ds.FONT_BODY, weight="bold"),
        )
        self.operation_label.grid(row=3, column=0, sticky="ew", padx=ds.SPACE_LG, pady=(0, ds.SPACE_SM))

        button_row = ctk.CTkFrame(left_panel, fg_color="transparent")
        button_row.grid(row=4, column=0, sticky="ew", padx=ds.SPACE_LG, pady=(0, ds.SPACE_SM))
        for column in (0, 1):
            button_row.grid_columnconfigure(column, weight=1)

        ctk.CTkButton(button_row, text="Start Camera", command=self.start_camera, **ds.primary_button_kwargs()).grid(
            row=0,
            column=0,
            sticky="ew",
            padx=(0, 6),
            pady=(0, 8),
        )
        ctk.CTkButton(button_row, text="Start Liveness Check", command=self.start_liveness_check, **ds.primary_button_kwargs()).grid(
            row=0,
            column=1,
            sticky="ew",
            padx=(6, 0),
            pady=(0, 8),
        )
        ctk.CTkButton(button_row, text="Reset Check", command=self.reset_check, **ds.secondary_button_kwargs()).grid(
            row=1,
            column=0,
            sticky="ew",
            padx=(0, 6),
            pady=(0, 8),
        )
        ctk.CTkButton(button_row, text="Stop Camera", command=self.stop_camera, **ds.secondary_button_kwargs()).grid(
            row=1,
            column=1,
            sticky="ew",
            padx=(6, 0),
            pady=(0, 8),
        )
        ctk.CTkButton(button_row, text="Refresh Status", command=self.refresh_status, **ds.secondary_button_kwargs()).grid(
            row=2,
            column=0,
            columnspan=2,
            sticky="ew",
        )

        self.message_banner = InfoBanner(
            left_panel,
            "Camera and liveness check start only by button click.",
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
            text="Last liveness result: not run yet",
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

    def refresh_status(self) -> None:
        self.status_label.configure(
            text=(
                f"Liveness demo: {'enabled' if self.liveness_config.get('enabled', True) else 'disabled'}\n"
                f"Mode: {'demo only' if self.liveness_config.get('demo_only', True) else 'not demo safe'}\n"
                f"Duration: {self.liveness_config.get('challenge_duration_seconds', 8)} seconds\n"
                f"Movement threshold: {self.liveness_config.get('movement_threshold_ratio', 0.08)} of frame width\n"
                f"Required movement frames: {self.liveness_config.get('minimum_detection_frames', 3)}\n"
                f"Camera: {'open' if self.camera.is_opened else 'stopped'}"
            )
        )

    def start_camera(self) -> None:
        status = self.camera.open()
        self.message_banner.set_message(status.message)
        if status.success and self.preview_after_id is None:
            self._schedule_preview()
        self.refresh_status()

    def start_liveness_check(self) -> None:
        if not is_liveness_demo_enabled(self.liveness_config):
            self.challenge = None
            self.liveness_state = LivenessDetectionState()
            self.liveness_active = False
            self.operation_label.configure(text="Operation: idle")
            self.message_banner.set_message(
                "Liveness demo is disabled in configuration. Enable liveness.enabled to run the demo."
            )
            self.result_label.configure(
                text="Last liveness result: disabled\nReason: liveness.enabled is false in configuration."
            )
            return

        if not self.camera.is_opened:
            self.message_banner.set_message("Start the camera before starting the liveness check.")
            self.result_label.configure(text="Last liveness result: not ready\nReason: camera is not open.")
            return

        self.challenge = create_liveness_challenge()
        self.liveness_state = LivenessDetectionState()
        self.liveness_active = True
        self.instruction_label.configure(text=f"Challenge instruction: {challenge_instruction(self.challenge)}")
        self.operation_label.configure(text="Operation: liveness challenge running")
        self.result_label.configure(text="Last liveness result: challenge running...")
        self.message_banner.set_message("Liveness challenge started. This is a basic movement demo only.")
        self.refresh_status()

    def reset_check(self) -> None:
        self.challenge = None
        self.liveness_state = LivenessDetectionState()
        self.liveness_active = False
        self.instruction_label.configure(text="Challenge instruction: not started")
        self.operation_label.configure(text="Operation: idle")
        self.result_label.configure(text="Last liveness result: not run yet")
        self.message_banner.set_message("Liveness check reset.")
        self.refresh_status()

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
        if self.liveness_active and self.challenge is not None:
            detection = update_liveness_state(result.frame, self.liveness_state, self.challenge, self.liveness_config)
            self._apply_liveness_result(detection)

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

    def _apply_liveness_result(self, result: LivenessDetectionResult) -> None:
        self.liveness_state = result.state
        self.message_banner.set_message(result.message)
        self.result_label.configure(
            text=(
                f"Last liveness result: {result.status}\n"
                f"Message: {result.message}\n"
                f"Movement frames: {result.state.successful_detection_frames} / "
                f"{self.liveness_config.get('minimum_detection_frames', 3)}"
            )
        )
        if result.state.completed:
            self.liveness_active = False
            self.operation_label.configure(text="Operation: idle")
            self._log_liveness_event(
                "liveness_check_completed",
                "success" if result.passed else "failed",
                {
                    "result_status": result.status,
                    "passed": result.passed,
                    "timed_out": result.timed_out,
                },
            )
        else:
            self.operation_label.configure(text="Operation: liveness challenge running")

    def stop_camera(self) -> None:
        self.release_resources()
        self._clear_preview("Camera preview is stopped.")
        self.liveness_active = False
        self.operation_label.configure(text="Operation: idle")
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
    def build_liveness_log_message(action: str, result_status: str, passed: bool | None = None) -> str:
        if action == "liveness_check_completed":
            final_status = "passed" if passed else "failed"
            return f"Liveness challenge completed with status: {final_status}."
        return "Liveness demo event completed."

    def _log_liveness_event(self, action: str, status: str, metadata: dict | None = None) -> None:
        try:
            safe_metadata = {
                "demo_only": True,
            }
            if metadata:
                safe_metadata.update(metadata)
            result_status = str(safe_metadata.get("result_status", "unknown"))
            passed = safe_metadata.get("passed")
            self.event_logger.log_event(
                category="liveness_demo",
                action=action,
                status=status,
                severity="WARNING" if status in {"failed", "blocked"} else "INFO",
                message=self.build_liveness_log_message(action, result_status, passed if isinstance(passed, bool) else None),
                metadata=safe_metadata,
            )
        except Exception:
            pass

    def destroy(self) -> None:
        self.release_resources()
        super().destroy()
