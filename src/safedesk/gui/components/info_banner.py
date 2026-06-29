"""Read-only SafeDesk information banner."""

import customtkinter as ctk

from safedesk.gui import design_system as ds


class InfoBanner(ctk.CTkFrame):
    """Compact branded banner for guidance and status messages."""

    def __init__(self, master, message: str, kind: str = "neutral", compact: bool = False, wraplength: int = 760, **kwargs):
        colors = ds.banner_colors(kind)
        super().__init__(
            master,
            fg_color=colors["fg_color"],
            corner_radius=ds.RADIUS_MD,
            border_width=1,
            border_color=colors["border_color"],
            **kwargs,
        )
        self.grid_columnconfigure(1, weight=1)
        vertical_pad = ds.SPACE_XS if compact else ds.SPACE_SM
        horizontal_pad = ds.SPACE_SM if compact else ds.SPACE_MD
        self.accent = ctk.CTkFrame(self, width=4, corner_radius=ds.RADIUS_SM, fg_color=colors["accent"])
        self.accent.grid(row=0, column=0, sticky="nsw", padx=(ds.SPACE_SM, 0), pady=vertical_pad)
        self.label = ctk.CTkLabel(
            self,
            text=message,
            justify="left",
            anchor="w",
            wraplength=wraplength,
            text_color=colors["text"],
            font=ctk.CTkFont(size=ds.FONT_SMALL if compact else ds.FONT_BODY),
        )
        self.label.grid(row=0, column=1, padx=horizontal_pad, pady=vertical_pad, sticky="ew")

    def set_message(self, message: str) -> None:
        self.label.configure(text=message)
