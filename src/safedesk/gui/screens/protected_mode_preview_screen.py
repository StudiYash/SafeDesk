"""Protected mode preview placeholder screen."""

import customtkinter as ctk

from safedesk.app.application import RuntimeContext


class ProtectedModePreviewScreen(ctk.CTkFrame):
    def __init__(self, master, context: RuntimeContext):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text="Protected Mode Preview", font=ctk.CTkFont(size=24, weight="bold")).grid(
            row=0,
            column=0,
            sticky="w",
            padx=6,
            pady=(0, 12),
        )
        message = (
            "This is a preview only. No real protected mode is active. "
            "No lockdown, fullscreen enforcement, camera access, or shutdown behavior is enabled. "
            "Phase 14 will handle protected mode planning later."
        )
        ctk.CTkLabel(self, text=message, wraplength=780, justify="left").grid(
            row=1,
            column=0,
            sticky="w",
            padx=6,
            pady=6,
        )
