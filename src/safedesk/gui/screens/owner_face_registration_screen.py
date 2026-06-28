"""Owner face registration sample capture screen."""

from pathlib import Path

import customtkinter as ctk

from safedesk.app.application import RuntimeContext
from safedesk.gui.components.info_banner import InfoBanner
from safedesk.storage.paths import project_root
from safedesk.vision.camera_manager import CameraManager
from safedesk.vision.owner_manifest import build_registration_status
from safedesk.vision.owner_registration import save_owner_sample


class OwnerFaceRegistrationScreen(ctk.CTkFrame):
    """Manual owner sample capture screen.

    The camera starts only when the owner clicks Start Camera.
    """

    def __init__(self, master, context: RuntimeContext):
        super().__init__(master)
        self.context = context
        self.registration_config = context.load_result.config.get("owner_face_registration", {})
        self.camera = CameraManager(int(self.registration_config.get("camera_index", 0)))
        self.current_frame = None
        self.preview_image = None
        self.preview_after_id = None
        self.preview_size = (560, 315)

        self.samples_dir = self._resolve_path(self.registration_config.get("samples_dir", "data/owner/samples"))
        self.manifest_path = self._resolve_path(
            self.registration_config.get("manifest_path", "data/config/owner_registration_manifest.json")
        )
        self.required_samples = int(self.registration_config.get("required_samples", 5))

        self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self, text="Owner Face Registration", font=ctk.CTkFont(size=22, weight="bold")).grid(
            row=0,
            column=0,
            sticky="w",
            padx=6,
            pady=(0, 6),
        )
        InfoBanner(
            self,
            "Owner samples are sensitive local biometric data. They are saved only under ignored local runtime folders. "
            "This phase does not perform recognition, matching, liveness checks, unlock, intruder detection, lockdown, or shutdown.",
        ).grid(row=1, column=0, sticky="ew", padx=6, pady=(0, 8))

        self.status_label = ctk.CTkLabel(self, text="", justify="left", anchor="w")
        self.status_label.grid(row=2, column=0, sticky="ew", padx=6, pady=(0, 6))

        button_row = ctk.CTkFrame(self, fg_color="transparent")
        button_row.grid(row=3, column=0, sticky="w", padx=6, pady=(0, 8))
        ctk.CTkButton(button_row, text="Start Camera", command=self.start_camera).grid(row=0, column=0, padx=(0, 8))
        ctk.CTkButton(button_row, text="Capture Sample", command=self.capture_sample).grid(row=0, column=1, padx=8)
        ctk.CTkButton(button_row, text="Stop Camera", command=self.stop_camera).grid(row=0, column=2, padx=8)
        ctk.CTkButton(button_row, text="Refresh Status", command=self.refresh_status).grid(row=0, column=3, padx=8)

        self.preview_frame = ctk.CTkFrame(self, width=self.preview_size[0], height=self.preview_size[1])
        self.preview_frame.grid(row=4, column=0, sticky="w", padx=6, pady=(0, 8))
        self.preview_frame.grid_propagate(False)
        self.preview_frame.grid_columnconfigure(0, weight=1)
        self.preview_frame.grid_rowconfigure(0, weight=1)

        self.preview_label = ctk.CTkLabel(self.preview_frame, text="Camera preview is stopped.")
        self.preview_label.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

        self.message_banner = InfoBanner(self, "Camera is not started. Click Start Camera only when ready.")
        self.message_banner.grid(row=5, column=0, sticky="ew", padx=6, pady=(0, 0))
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
            self.message_banner.set_message("Start the camera and wait for a preview frame before capturing a sample.")
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
        self.preview_label.configure(image=None)
        self.preview_label.configure(text=message)

    def destroy(self) -> None:
        self.release_resources()
        super().destroy()
