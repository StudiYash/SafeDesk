"""Template-based public lock screen foundation for SafeDesk."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import tkinter as tk

import customtkinter as ctk

from safedesk.app.application import RuntimeContext
from safedesk.gui import design_system as ds
from safedesk.logging.event_logger import build_logger_from_config
from safedesk.storage.paths import project_root

TEMPLATE_IMAGE_RELATIVE_PATH = Path("assets/images/safedesk_lockdown_template.png")
TEMPLATE_PADDING = 18

VERIFY_OWNER_BUTTON_RECT = {
    "x": 0.120,
    "y": 0.700,
    "w": 0.360,
    "h": 0.080,
}
RECOVERY_ACCESS_BUTTON_RECT = {
    "x": 0.505,
    "y": 0.700,
    "w": 0.325,
    "h": 0.080,
}
STATUS_MESSAGE_RECT = {
    "x": 0.165,
    "y": 0.857,
    "w": 0.670,
    "h": 0.040,
}
BUTTON_FONT_FAMILY = "Bahnschrift"
STATUS_FONT_FAMILY = "Bahnschrift"
BUTTON_TEXT_PRIMARY = "#E8DED1"
BUTTON_TEXT_SECONDARY = "#D1C4B6"
BUTTON_TEXT_HOVER = "#FFFFFF"
STATUS_TEXT_COLOR = "#9F938C"
BUTTON_HIT_VERTICAL_PADDING_RATIO = 0.025
INITIAL_STATUS_TEXT = "AWAITING OWNER VERIFICATION."
VERIFY_STATUS_TEXT = "OWNER VERIFICATION REQUEST RECEIVED."
RECOVERY_STATUS_TEXT = "RECOVERY ACCESS REQUEST RECEIVED."


class PublicLockScreen(ctk.CTkFrame):
    """Public-facing non-enforcing SafeDesk lock screen."""

    def __init__(self, master, context: RuntimeContext):
        super().__init__(master, fg_color=ds.SAFEDESK_BLACK)
        self.context = context
        self.event_logger = build_logger_from_config(context.load_result.config)
        self.template_source_image: Any | None = self._load_template_image()
        self.template_photo_image: Any | None = None
        self.template_canvas: tk.Canvas | None = None
        self.template_image_item: int | None = None
        self.verify_text_item: int | None = None
        self.recovery_text_item: int | None = None
        self.status_text_item: int | None = None
        self.fallback_status_message: ctk.CTkLabel | None = None
        self._last_display_size: tuple[int, int] | None = None
        self._verify_hit_rect: tuple[int, int, int, int] | None = None
        self._recovery_hit_rect: tuple[int, int, int, int] | None = None
        self._status_text = INITIAL_STATUS_TEXT
        self._hovered_action: str | None = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        if self.template_source_image is None:
            self._build_fallback_layout()
            return

        self._build_template_layout()
        self.bind("<Configure>", self._handle_resize)
        self.after(0, self._update_template_layout)
        self.after(50, self._update_template_layout)
        self.after(150, self._update_template_layout)

    def _load_template_image(self) -> Any | None:
        template_path = project_root() / TEMPLATE_IMAGE_RELATIVE_PATH
        if not template_path.exists():
            return None

        try:
            from PIL import Image

            with Image.open(template_path) as image:
                return image.convert("RGBA").copy()
        except Exception:
            return None

    def _build_template_layout(self) -> None:
        self.template_canvas = tk.Canvas(self, bd=0, highlightthickness=0, bg=ds.SAFEDESK_BLACK)
        self.template_canvas.place(x=0, y=0)
        self.template_image_item = self.template_canvas.create_image(0, 0, anchor="nw")
        self.verify_text_item = self.template_canvas.create_text(
            0,
            0,
            text="VERIFY OWNER",
            fill=BUTTON_TEXT_PRIMARY,
            anchor="center",
            justify="center",
        )
        self.recovery_text_item = self.template_canvas.create_text(
            0,
            0,
            text="RECOVERY ACCESS",
            fill=BUTTON_TEXT_SECONDARY,
            anchor="center",
            justify="center",
        )
        self.status_text_item = self.template_canvas.create_text(
            0,
            0,
            text=self._status_text,
            fill=STATUS_TEXT_COLOR,
            anchor="center",
            justify="center",
        )
        self.template_canvas.bind("<Button-1>", self._handle_canvas_click)
        self.template_canvas.bind("<Motion>", self._handle_canvas_motion)
        self.template_canvas.bind("<Leave>", self._handle_canvas_leave)

    def _build_fallback_layout(self) -> None:
        panel = ctk.CTkFrame(
            self,
            fg_color="#100E0E",
            corner_radius=ds.RADIUS_LG,
            border_width=2,
            border_color=ds.SAFEDESK_RED,
        )
        panel.grid(row=0, column=0, padx=42, pady=42, sticky="nsew")
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(0, weight=1)

        content = ctk.CTkFrame(panel, fg_color="transparent")
        content.grid(row=0, column=0, padx=34, pady=34, sticky="ew")
        content.grid_columnconfigure((0, 1), weight=1, uniform="fallback_actions")

        ctk.CTkLabel(
            content,
            text="SafeDesk Lockdown",
            font=ctk.CTkFont(size=34, weight="bold"),
            text_color=ds.TEXT_PRIMARY,
        ).grid(row=0, column=0, columnspan=2, pady=(0, 12), sticky="n")
        ctk.CTkLabel(
            content,
            text="Owner verification required.",
            font=ctk.CTkFont(size=ds.FONT_H3, weight="bold"),
            text_color=ds.TEXT_SECONDARY,
        ).grid(row=1, column=0, columnspan=2, pady=(0, 22), sticky="n")

        ctk.CTkButton(
            content,
            text="Verify Owner",
            command=self._handle_verify_owner,
            height=46,
            **ds.primary_button_kwargs(),
        ).grid(row=2, column=0, padx=(0, 8), pady=(0, 12), sticky="ew")
        ctk.CTkButton(
            content,
            text="Recovery Access",
            command=self._handle_recovery_access,
            height=46,
            **ds.secondary_button_kwargs(),
        ).grid(row=2, column=1, padx=(8, 0), pady=(0, 12), sticky="ew")

        self.fallback_status_message = ctk.CTkLabel(
            content,
            text=self._status_text,
            font=ctk.CTkFont(size=ds.FONT_SMALL),
            text_color=ds.TEXT_SECONDARY,
        )
        self.fallback_status_message.grid(row=3, column=0, columnspan=2, sticky="ew")

    def _handle_resize(self, _event) -> None:
        self._update_template_layout()

    def _update_template_layout(self) -> None:
        if self.template_source_image is None or self.template_canvas is None or self.template_image_item is None:
            return

        frame_width = max(1, self.winfo_width())
        frame_height = max(1, self.winfo_height())
        if frame_width < 50 or frame_height < 50:
            self.after(50, self._update_template_layout)
            return

        source_width, source_height = self.template_source_image.size
        available_width = max(1, frame_width - (TEMPLATE_PADDING * 2))
        available_height = max(1, frame_height - (TEMPLATE_PADDING * 2))
        scale = min(available_width / source_width, available_height / source_height)
        display_width = max(1, int(source_width * scale))
        display_height = max(1, int(source_height * scale))
        display_x = int((frame_width - display_width) / 2)
        display_y = int((frame_height - display_height) / 2)

        if self._last_display_size != (display_width, display_height):
            from PIL import Image, ImageTk

            resample = getattr(getattr(Image, "Resampling", Image), "LANCZOS", Image.BICUBIC)
            resized = self.template_source_image.resize((display_width, display_height), resample=resample)
            self.template_photo_image = ImageTk.PhotoImage(resized)
            self.template_canvas.itemconfigure(self.template_image_item, image=self.template_photo_image)
            self._last_display_size = (display_width, display_height)

        self.template_canvas.configure(width=display_width, height=display_height)
        self.template_canvas.place(x=display_x, y=display_y, width=display_width, height=display_height)
        self.template_canvas.coords(self.template_image_item, 0, 0)

        button_font_size = self._clamp(int(display_height * 0.024), 12, 22)
        status_font_size = self._clamp(int(display_height * 0.016), 9, 15)
        button_font = (BUTTON_FONT_FAMILY, button_font_size, "bold")
        status_font = (STATUS_FONT_FAMILY, status_font_size)

        verify_text_rect = self._place_text_item(
            self.verify_text_item,
            VERIFY_OWNER_BUTTON_RECT,
            display_width,
            display_height,
            button_font,
            BUTTON_TEXT_HOVER if self._hovered_action == "verify" else BUTTON_TEXT_PRIMARY,
        )
        recovery_text_rect = self._place_text_item(
            self.recovery_text_item,
            RECOVERY_ACCESS_BUTTON_RECT,
            display_width,
            display_height,
            button_font,
            BUTTON_TEXT_HOVER if self._hovered_action == "recovery" else BUTTON_TEXT_SECONDARY,
        )
        self._place_text_item(
            self.status_text_item,
            STATUS_MESSAGE_RECT,
            display_width,
            display_height,
            status_font,
            STATUS_TEXT_COLOR,
            text=self._status_text,
        )
        self._verify_hit_rect = self._expand_hit_rect(
            verify_text_rect,
            display_height,
            BUTTON_HIT_VERTICAL_PADDING_RATIO,
        )
        self._recovery_hit_rect = self._expand_hit_rect(
            recovery_text_rect,
            display_height,
            BUTTON_HIT_VERTICAL_PADDING_RATIO,
        )
        self._raise_canvas_text_items()

    def _place_text_item(
        self,
        item_id: int | None,
        rect: dict[str, float],
        image_width: int,
        image_height: int,
        font: tuple,
        fill: str,
        text: str | None = None,
    ) -> tuple[int, int, int, int] | None:
        if item_id is None or self.template_canvas is None:
            return None
        local_x = int(image_width * rect["x"])
        local_y = int(image_height * rect["y"])
        local_width = max(1, int(image_width * rect["w"]))
        local_height = max(1, int(image_height * rect["h"]))
        config: dict[str, Any] = {"font": font, "fill": fill, "width": local_width}
        if text is not None:
            config["text"] = text
        self.template_canvas.coords(item_id, local_x + (local_width / 2), local_y + (local_height / 2))
        self.template_canvas.itemconfigure(item_id, **config)
        return (local_x, local_y, local_width, local_height)

    def _raise_canvas_text_items(self) -> None:
        if self.template_canvas is None:
            return
        for item_id in (self.verify_text_item, self.recovery_text_item, self.status_text_item):
            if item_id is not None:
                try:
                    self.template_canvas.tag_raise(item_id)
                except Exception:
                    pass

    def _handle_canvas_click(self, event) -> None:
        if self._point_inside_rect(event.x, event.y, self._verify_hit_rect):
            self._handle_verify_owner()
            return
        if self._point_inside_rect(event.x, event.y, self._recovery_hit_rect):
            self._handle_recovery_access()

    def _handle_canvas_motion(self, event) -> None:
        hovered_action: str | None = None
        if self._point_inside_rect(event.x, event.y, self._verify_hit_rect):
            hovered_action = "verify"
        elif self._point_inside_rect(event.x, event.y, self._recovery_hit_rect):
            hovered_action = "recovery"

        if hovered_action == self._hovered_action:
            return

        self._hovered_action = hovered_action
        if self.template_canvas is not None:
            self.template_canvas.configure(cursor="hand2" if hovered_action else "")
        self._update_text_hover_colors()

    def _handle_canvas_leave(self, _event) -> None:
        self._hovered_action = None
        if self.template_canvas is not None:
            self.template_canvas.configure(cursor="")
        self._update_text_hover_colors()

    def _update_text_hover_colors(self) -> None:
        if self.template_canvas is None:
            return
        if self.verify_text_item is not None:
            self.template_canvas.itemconfigure(
                self.verify_text_item,
                fill=BUTTON_TEXT_HOVER if self._hovered_action == "verify" else BUTTON_TEXT_PRIMARY,
            )
        if self.recovery_text_item is not None:
            self.template_canvas.itemconfigure(
                self.recovery_text_item,
                fill=BUTTON_TEXT_HOVER if self._hovered_action == "recovery" else BUTTON_TEXT_SECONDARY,
            )

    @staticmethod
    def _point_inside_rect(x: int, y: int, rect: tuple[int, int, int, int] | None) -> bool:
        if rect is None:
            return False
        rect_x, rect_y, rect_width, rect_height = rect
        return rect_x <= x <= rect_x + rect_width and rect_y <= y <= rect_y + rect_height

    @staticmethod
    def _expand_hit_rect(
        rect: tuple[int, int, int, int] | None,
        image_height: int,
        vertical_padding_ratio: float,
    ) -> tuple[int, int, int, int] | None:
        if rect is None:
            return None
        rect_x, rect_y, rect_width, rect_height = rect
        vertical_padding = max(1, int(image_height * vertical_padding_ratio))
        expanded_y = max(0, rect_y - vertical_padding)
        expanded_bottom = min(image_height, rect_y + rect_height + vertical_padding)
        return (rect_x, expanded_y, rect_width, max(1, expanded_bottom - expanded_y))

    @staticmethod
    def _clamp(value: int, minimum: int, maximum: int) -> int:
        return max(minimum, min(maximum, value))

    def _handle_verify_owner(self) -> None:
        self._set_status_message(VERIFY_STATUS_TEXT)
        self._log_public_lock_action(
            "public_lock_verify_owner_requested",
            "Owner verification was requested from the public lock screen.",
        )

    def _handle_recovery_access(self) -> None:
        self._set_status_message(RECOVERY_STATUS_TEXT)
        self._log_public_lock_action(
            "public_lock_recovery_access_requested",
            "Recovery access was requested from the public lock screen.",
        )

    def _set_status_message(self, message: str) -> None:
        self._status_text = message
        if self.template_canvas is not None and self.status_text_item is not None:
            self.template_canvas.itemconfigure(self.status_text_item, text=message)
        if self.fallback_status_message is not None:
            self.fallback_status_message.configure(text=message)

    def _log_public_lock_action(self, action: str, message: str) -> None:
        try:
            self.event_logger.log_app_event(
                action=action,
                status="info",
                message=message,
                metadata={"surface": "public_lock"},
            )
        except Exception:
            pass
