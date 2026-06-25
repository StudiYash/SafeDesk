"""About placeholder screen."""

import customtkinter as ctk

from safedesk.app.application import RuntimeContext


class AboutScreen(ctk.CTkFrame):
    def __init__(self, master, context: RuntimeContext):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text="About SafeDesk", font=ctk.CTkFont(size=24, weight="bold")).grid(
            row=0,
            column=0,
            sticky="w",
            padx=6,
            pady=(0, 12),
        )
        text = (
            f"{context.settings.app_name} {context.settings.version}\n\n"
            "SafeDesk is an owner-controlled, local-first Windows security project.\n\n"
            "Developer: Yash Shukla\n"
            "GitHub: StudiYash\n"
            "License: CC BY-NC-SA 4.0"
        )
        ctk.CTkLabel(self, text=text, justify="left", wraplength=780).grid(
            row=1,
            column=0,
            sticky="w",
            padx=6,
            pady=6,
        )
