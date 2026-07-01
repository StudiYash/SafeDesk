"""Owner face registration sample capture screen."""

from pathlib import Path

import customtkinter as ctk

from safedesk.app.application import RuntimeContext
from safedesk.gui import design_system as ds
from safedesk.gui.components.info_banner import InfoBanner
from safedesk.gui.components.page_header import PageHeader
from safedesk.gui.components.scrollable_page import ScrollablePage
from safedesk.logging.event_logger import build_logger_from_config
from safedesk.storage.paths import project_root
from safedesk.vision.camera_manager import CameraManager
from safedesk.vision.owner_manifest import build_registration_status
from safedesk.vision.owner_registration import save_owner_sample


class OwnerFaceRegistrationScreen(ctk.CTkFrame):
    """Manual owner sample capture screen.

    The camera starts only when the owner clicks Start Camera.
    """

    def __init__(self, master, context: RuntimeContext):
        super().__init__(master, fg_color=ds.CONTENT_BG)
        self.context = context
        self.registration_config = context.load_result.config.get("owner_face_registration", {})
        self.event_logger = build_logger_from_config(context.load_result.config)
        self.camera = CameraManager(int(self.registration_config.get("camera_index", 0)))
        self.current_frame = None
        self.preview_image = None
        self.preview_after_id = None
        self.preview_size = (500, 281)

        self.samples_dir = self._resolve_path(self.registration_config.get("samples_dir", "data/owner/samples"))
        self.manifest_path = self._resolve_path(
            self.registration_config.get("manifest_path", "data/config/owner_registration_manifest.json")
        )
        self.required_samples = int(self.registration_config.get("required_samples", 5))

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        page = ScrollablePage(self)
        page.grid(row=0, column=0, sticky="nsew")

        PageHeader(
            page,
            "Owner Face Registration",
            "Capture local owner face samples for later recognition phases.",
        ).grid(row=0, column=0, sticky="ew", padx=4, pady=(0, 10))

        InfoBanner(
            page,
            "Owner samples are sensitive local biometric data. They are saved only under ignored local runtime folders. "
            "This phase does not perform recognition, matching, liveness checks, unlock, intruder detection, lockdown, or shutdown.",
            kind="warning",
            compact=True,
        ).grid(row=1, column=0, sticky="ew", padx=4, pady=(0, 12))

        workspace = ctk.CTkFrame(page, fg_color="transparent")
        workspace.grid(row=2, column=0, sticky="nsew", padx=4, pady=0)
        workspace.grid_columnconfigure(0, weight=1, uniform="registration")
        workspace.grid_columnconfigure(1, weight=1, uniform="registration")

        left_panel = ctk.CTkFrame(workspace, **ds.card_kwargs())
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        left_panel.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            left_panel,
            text="Registration Status",
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
            wraplength=380,
        )
        self.status_label.grid(row=1, column=0, sticky="ew", padx=ds.SPACE_LG, pady=(0, ds.SPACE_MD))

        button_row = ctk.CTkFrame(left_panel, fg_color="transparent")
        button_row.grid(row=2, column=0, sticky="ew", padx=ds.SPACE_LG, pady=(0, ds.SPACE_MD))
        for column in (0, 1):
            button_row.grid_columnconfigure(column, weight=1)
        ctk.CTkButton(button_row, text="Start Camera", command=self.start_camera, **ds.primary_button_kwargs()).grid(
            row=0,
            column=0,
            sticky="ew",
            padx=(0, 6),
            pady=(0, 8),
        )
        ctk.CTkButton(button_row, text="Capture Sample", command=self.capture_sample, **ds.primary_button_kwargs()).grid(
            row=0,
            column=1,
            sticky="ew",
            padx=(6, 0),
            pady=(0, 8),
        )
        ctk.CTkButton(button_row, text="Stop Camera", command=self.stop_camera, **ds.secondary_button_kwargs()).grid(
            row=1,
            column=0,
            sticky="ew",
            padx=(0, 6),
        )
        ctk.CTkButton(button_row, text="Refresh Status", command=self.refresh_status, **ds.secondary_button_kwargs()).grid(
            row=1,
            column=1,
            sticky="ew",
            padx=(6, 0),
        )

        self.message_banner = InfoBanner(
            left_panel,
            "Camera is not started. Click Start Camera only when ready.",
            kind="neutral",
            compact=True,
            wraplength=360,
        )
        self.message_banner.grid(row=3, column=0, sticky="ew", padx=ds.SPACE_LG, pady=(0, ds.SPACE_LG))

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
        self.preview_frame.grid(row=1, column=0, sticky="n", padx=ds.SPACE_LG, pady=(0, ds.SPACE_LG))
        self.preview_frame.grid_propagate(False)
        self.preview_frame.grid_columnconfigure(0, weight=1)
        self.preview_frame.grid_rowconfigure(0, weight=1)

        self._create_preview_label("Camera preview is stopped.")
        self.refresh_status()

    def _resolve_path(self, value: str) -> Path:
        path = Path(value)
        return path if path.is_absolute() else project_root() / path

    def refresh_status(self) -> None:
        status = build_registration_status(self.samples_dir, self.manifest_path, self.required_samples)
        state = "completed" if status.registration_complete else "pending"
        self.status_label.configure(
            text=(
                f"Owner face registration: {state}\n"
                f"Owner face samples: {status.sample_count} saved / {status.required_sample_count} required\n"
                f"Samples folder present: {'yes' if status.samples_dir_exists else 'no'}\n"
                f"Manifest present: {'yes' if status.manifest_exists else 'no'}"
            )
        )

    def start_camera(self) -> None:
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

    def capture_sample(self) -> None:
        if not self.camera.is_opened or self.current_frame is None:
            message = "Start the camera and wait for a preview frame before capturing a sample."
            self.message_banner.set_message(message)
            self._log_owner_registration_event("blocked")
            return

        result = save_owner_sample(
            self.current_frame,
            self.samples_dir,
            self.manifest_path,
            self.required_samples,
            image_format=str(self.registration_config.get("image_format", "jpg")),
            image_quality=int(self.registration_config.get("image_quality", 90)),
        )
        self.message_banner.set_message(result.message)
        self.refresh_status()
        self._log_owner_registration_event("success" if result.success else "failed", result=result)

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
    def build_owner_registration_log_message(status: str) -> str:
        if status == "blocked":
            return "Owner sample capture was blocked because camera/frame was not ready."
        return f"Owner sample capture completed with status: {status}."

    def _log_owner_registration_event(self, status: str, result=None) -> None:
        try:
            registration_status = build_registration_status(self.samples_dir, self.manifest_path, self.required_samples)
            sample_count = int(getattr(result, "sample_count", 0) or registration_status.sample_count)
            registration_complete = bool(
                getattr(result, "registration_complete", False) or registration_status.registration_complete
            )
            self.event_logger.log_event(
                category="owner_registration",
                action="sample_capture",
                status=status,
                severity="WARNING" if status in {"failed", "blocked"} else "INFO",
                message=self.build_owner_registration_log_message(status),
                metadata={
                    "sample_count": sample_count,
                    "required_sample_count": self.required_samples,
                    "registration_complete": registration_complete,
                    "camera_open": self.camera.is_opened,
                },
            )
        except Exception:
            pass

    def destroy(self) -> None:
        self.release_resources()
        super().destroy()
