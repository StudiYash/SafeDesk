"""Manual password and panic-code authentication setup screen."""

import customtkinter as ctk

from safedesk.app.application import RuntimeContext
from safedesk.auth.authentication_service import AuthenticationService
from safedesk.gui import design_system as ds
from safedesk.gui.components.form_field import FormField
from safedesk.gui.components.info_banner import InfoBanner
from safedesk.gui.components.page_header import PageHeader
from safedesk.gui.components.scrollable_page import ScrollablePage


class AuthenticationSetupScreen(ctk.CTkFrame):
    """Manual foundation screen for local hashed password and panic-code setup."""

    def __init__(self, master, context: RuntimeContext):
        super().__init__(master, fg_color=ds.CONTENT_BG)
        self.context = context
        self.service = AuthenticationService(context.load_result.config)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        page = ScrollablePage(self)
        page.grid(row=0, column=0, sticky="nsew")
        for column in (0, 1):
            page.grid_columnconfigure(column, weight=1, uniform="auth_setup")

        PageHeader(
            page,
            "Authentication Setup",
            "Set and test local password and panic-code foundations without unlocking SafeDesk.",
        ).grid(row=0, column=0, columnspan=2, sticky="ew", padx=4, pady=(0, 10))

        InfoBanner(
            page,
            "Foundation/demo only: saved values are local hashes. This screen does not unlock SafeDesk, start protected mode, "
            "trigger lockdown, or trigger shutdown.",
            kind="warning",
            compact=True,
        ).grid(row=1, column=0, columnspan=2, sticky="ew", padx=4, pady=(0, 12))

        status_panel = ctk.CTkFrame(page, **ds.card_kwargs())
        status_panel.grid(row=2, column=0, sticky="nsew", padx=(4, 8), pady=6)
        status_panel.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            status_panel,
            text="Authentication Status",
            font=ctk.CTkFont(size=ds.FONT_H3, weight="bold"),
            text_color=ds.TEXT_PRIMARY,
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=ds.SPACE_LG, pady=(ds.SPACE_LG, ds.SPACE_SM))
        self.status_label = ctk.CTkLabel(
            status_panel,
            text="",
            justify="left",
            anchor="w",
            text_color=ds.TEXT_SECONDARY,
            wraplength=380,
            font=ctk.CTkFont(size=ds.FONT_BODY),
        )
        self.status_label.grid(row=1, column=0, sticky="ew", padx=ds.SPACE_LG, pady=(0, ds.SPACE_LG))

        message_panel = ctk.CTkFrame(page, **ds.card_kwargs())
        message_panel.grid(row=2, column=1, sticky="nsew", padx=(8, 4), pady=6)
        message_panel.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            message_panel,
            text="Result",
            font=ctk.CTkFont(size=ds.FONT_H3, weight="bold"),
            text_color=ds.TEXT_PRIMARY,
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=ds.SPACE_LG, pady=(ds.SPACE_LG, ds.SPACE_SM))
        self.result_banner = InfoBanner(
            message_panel,
            "No authentication action has run yet.",
            kind="neutral",
            compact=True,
            wraplength=360,
        )
        self.result_banner.grid(row=1, column=0, sticky="ew", padx=ds.SPACE_LG, pady=(0, ds.SPACE_SM))
        ctk.CTkButton(
            message_panel,
            text="Refresh Status",
            command=self.refresh_status,
            **ds.secondary_button_kwargs(),
        ).grid(row=2, column=0, sticky="ew", padx=ds.SPACE_LG, pady=(0, ds.SPACE_SM))
        ctk.CTkButton(
            message_panel,
            text="Clear Inputs",
            command=self.clear_inputs,
            **ds.secondary_button_kwargs(),
        ).grid(row=3, column=0, sticky="ew", padx=ds.SPACE_LG, pady=(0, ds.SPACE_LG))

        password_panel = ctk.CTkFrame(page, **ds.card_kwargs())
        password_panel.grid(row=3, column=0, sticky="nsew", padx=(4, 8), pady=6)
        password_panel.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            password_panel,
            text="Set Master Password",
            font=ctk.CTkFont(size=ds.FONT_H3, weight="bold"),
            text_color=ds.TEXT_PRIMARY,
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=ds.SPACE_LG, pady=(ds.SPACE_LG, ds.SPACE_SM))
        self.master_password = FormField(password_panel, "Master password", "Enter master password", show="*")
        self.master_password.grid(row=1, column=0, sticky="ew", padx=ds.SPACE_LG, pady=6)
        self.confirm_master_password = FormField(password_panel, "Confirm master password", "Re-enter master password", show="*")
        self.confirm_master_password.grid(row=2, column=0, sticky="ew", padx=ds.SPACE_LG, pady=6)
        ctk.CTkButton(
            password_panel,
            text="Save Master Password",
            command=self.save_master_password,
            **ds.primary_button_kwargs(),
        ).grid(row=3, column=0, sticky="ew", padx=ds.SPACE_LG, pady=(8, ds.SPACE_LG))

        panic_panel = ctk.CTkFrame(page, **ds.card_kwargs())
        panic_panel.grid(row=3, column=1, sticky="nsew", padx=(8, 4), pady=6)
        panic_panel.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            panic_panel,
            text="Set Panic / Recovery Code",
            font=ctk.CTkFont(size=ds.FONT_H3, weight="bold"),
            text_color=ds.TEXT_PRIMARY,
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=ds.SPACE_LG, pady=(ds.SPACE_LG, ds.SPACE_SM))
        self.panic_code = FormField(panic_panel, "Panic / recovery code", "Enter recovery code", show="*")
        self.panic_code.grid(row=1, column=0, sticky="ew", padx=ds.SPACE_LG, pady=6)
        self.confirm_panic_code = FormField(panic_panel, "Confirm panic / recovery code", "Re-enter recovery code", show="*")
        self.confirm_panic_code.grid(row=2, column=0, sticky="ew", padx=ds.SPACE_LG, pady=6)
        ctk.CTkButton(
            panic_panel,
            text="Save Panic Code",
            command=self.save_panic_code,
            **ds.primary_button_kwargs(),
        ).grid(row=3, column=0, sticky="ew", padx=ds.SPACE_LG, pady=(8, ds.SPACE_LG))

        verify_panel = ctk.CTkFrame(page, **ds.card_kwargs())
        verify_panel.grid(row=4, column=0, columnspan=2, sticky="ew", padx=4, pady=6)
        for column in (0, 1):
            verify_panel.grid_columnconfigure(column, weight=1, uniform="verify")
        ctk.CTkLabel(
            verify_panel,
            text="Manual Verification",
            font=ctk.CTkFont(size=ds.FONT_H3, weight="bold"),
            text_color=ds.TEXT_PRIMARY,
            anchor="w",
        ).grid(row=0, column=0, columnspan=2, sticky="ew", padx=ds.SPACE_LG, pady=(ds.SPACE_LG, ds.SPACE_SM))

        self.verify_password_input = FormField(verify_panel, "Verify password input", "Enter password to test", show="*")
        self.verify_password_input.grid(row=1, column=0, sticky="ew", padx=(ds.SPACE_LG, ds.SPACE_SM), pady=6)
        self.verify_panic_input = FormField(verify_panel, "Verify panic code input", "Enter panic code to test", show="*")
        self.verify_panic_input.grid(row=1, column=1, sticky="ew", padx=(ds.SPACE_SM, ds.SPACE_LG), pady=6)
        ctk.CTkButton(
            verify_panel,
            text="Verify Password",
            command=self.verify_master_password,
            **ds.secondary_button_kwargs(),
        ).grid(row=2, column=0, sticky="ew", padx=(ds.SPACE_LG, ds.SPACE_SM), pady=(8, ds.SPACE_LG))
        ctk.CTkButton(
            verify_panel,
            text="Verify Panic Code",
            command=self.verify_panic_code,
            **ds.secondary_button_kwargs(),
        ).grid(row=2, column=1, sticky="ew", padx=(ds.SPACE_SM, ds.SPACE_LG), pady=(8, ds.SPACE_LG))

        self.refresh_status()

    def refresh_status(self) -> None:
        status = self.service.build_status()
        store_state = "present" if status.store_present else "missing"
        if status.store_present and not status.store_readable:
            store_state = "unreadable"
        self.status_label.configure(
            text=(
                f"Master password: {'configured' if status.master_password_configured else 'not configured'}\n"
                f"Panic code: {'configured' if status.panic_code_configured else 'not configured'}\n"
                f"Secret store: {store_state}\n"
                f"Mode: {'foundation only' if status.demo_only else 'review required'}\n"
                f"Foundation: {'enabled' if status.foundation_enabled else 'disabled'}"
            )
        )

    def save_master_password(self) -> None:
        try:
            result = self.service.set_master_password(self.master_password.get(), self.confirm_master_password.get())
        except Exception:
            self.result_banner.set_message("Master password could not be saved due to a local storage error.")
            return
        if result.success:
            self.master_password.clear()
            self.confirm_master_password.clear()
        self.result_banner.set_message(result.message)
        self.refresh_status()

    def save_panic_code(self) -> None:
        try:
            result = self.service.set_panic_code(self.panic_code.get(), self.confirm_panic_code.get())
        except Exception:
            self.result_banner.set_message("Panic/recovery code could not be saved due to a local storage error.")
            return
        if result.success:
            self.panic_code.clear()
            self.confirm_panic_code.clear()
        self.result_banner.set_message(result.message)
        self.refresh_status()

    def verify_master_password(self) -> None:
        result = self.service.verify_master_password(self.verify_password_input.get())
        self.result_banner.set_message(
            self._verification_message("Master Password", result.status, result.message, result.remaining_attempts)
        )
        self.refresh_status()

    def verify_panic_code(self) -> None:
        result = self.service.verify_panic_code(self.verify_panic_input.get())
        self.result_banner.set_message(self._verification_message("Panic code", result.status, result.message, result.remaining_attempts))
        self.refresh_status()

    def clear_inputs(self) -> None:
        for field in (
            self.master_password,
            self.confirm_master_password,
            self.panic_code,
            self.confirm_panic_code,
            self.verify_password_input,
            self.verify_panic_input,
        ):
            field.clear()
        self.result_banner.set_message("Secret input fields cleared.")

    @staticmethod
    def _verification_message(label: str, status: str, message: str, remaining_attempts: int) -> str:
        if status == "locked_out":
            return f"{label}: locked temporarily. {message}"
        if status == "success":
            return f"{label}: verified. {message}"
        if status == "failed":
            return f"{label}: not verified. Attempts remaining: {remaining_attempts}."
        return f"{label}: {message}"
