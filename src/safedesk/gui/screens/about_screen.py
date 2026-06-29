"""About placeholder screen."""

import customtkinter as ctk

from safedesk.app.application import RuntimeContext
from safedesk.gui import design_system as ds
from safedesk.gui.components.scrollable_page import ScrollablePage
from safedesk.gui.components.status_card import StatusCard
from safedesk.storage.paths import project_root


class AboutScreen(ctk.CTkFrame):
    def __init__(self, master, context: RuntimeContext):
        super().__init__(master, fg_color=ds.CONTENT_BG)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.logo_image = None

        page = ScrollablePage(self)
        page.grid(row=0, column=0, sticky="nsew")
        self._add_logo(page)

        StatusCard(
            page,
            f"{context.settings.app_name} {context.settings.version}",
            [
                ("Project", "Windows-focused local security system"),
                ("Developer", "Yash Shukla"),
                ("GitHub", "StudiYash"),
                ("License", "CC BY-NC-SA 4.0"),
                ("Data posture", "local-first"),
            ],
            accent=ds.SAFEDESK_RED,
        ).grid(row=1, column=0, sticky="ew", padx=4, pady=6)

    def _add_logo(self, parent) -> None:
        logo_path = project_root() / "SafeDesk Logo.png"
        if not logo_path.exists():
            ctk.CTkLabel(
                parent,
                text="SafeDesk logo not found.",
                text_color=ds.TEXT_SECONDARY,
                anchor="center",
            ).grid(row=0, column=0, sticky="ew", padx=ds.SPACE_LG, pady=(0, ds.SPACE_LG))
            return

        try:
            from PIL import Image

            image = Image.open(logo_path)
            max_width = 1000
            if image.width > max_width:
                ratio = max_width / image.width
                image = image.resize((max_width, max(1, int(image.height * ratio))))
            self.logo_image = ctk.CTkImage(light_image=image, dark_image=image, size=image.size)
            ctk.CTkLabel(parent, text="", image=self.logo_image).grid(
                row=0,
                column=0,
                sticky="n",
                padx=4,
                pady=(0, ds.SPACE_LG),
            )
        except Exception:
            ctk.CTkLabel(
                parent,
                text="SafeDesk logo could not be loaded.",
                text_color=ds.TEXT_SECONDARY,
                anchor="center",
            ).grid(row=0, column=0, sticky="ew", padx=ds.SPACE_LG, pady=(0, ds.SPACE_LG))
