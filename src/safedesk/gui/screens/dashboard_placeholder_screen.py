"""Dashboard placeholder screen."""

import customtkinter as ctk

from safedesk.app.application import RuntimeContext


class DashboardPlaceholderScreen(ctk.CTkFrame):
    def __init__(self, master, context: RuntimeContext):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text="Dashboard", font=ctk.CTkFont(size=24, weight="bold")).grid(
            row=0,
            column=0,
            sticky="w",
            padx=6,
            pady=(0, 12),
        )
        ctk.CTkLabel(
            self,
            text="Placeholder for future intruder history and logs. No database is accessed and no records exist in this phase.",
            wraplength=780,
            justify="left",
        ).grid(row=1, column=0, sticky="w", padx=6, pady=6)
