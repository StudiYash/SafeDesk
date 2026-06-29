"""Manual OTP and email setup foundation screen."""

import customtkinter as ctk

from safedesk.alerts.email_sender import EmailSender, build_email_settings_status
from safedesk.app.application import RuntimeContext
from safedesk.auth.otp_manager import OtpManager
from safedesk.gui import design_system as ds
from safedesk.gui.components.form_field import FormField
from safedesk.gui.components.info_banner import InfoBanner
from safedesk.gui.components.page_header import PageHeader
from safedesk.gui.components.scrollable_page import ScrollablePage


class OtpEmailSetupScreen(ctk.CTkFrame):
    """Manual foundation screen for OTP generation, verification, and email testing."""

    def __init__(self, master, context: RuntimeContext):
        super().__init__(master, fg_color=ds.CONTENT_BG)
        self.context = context
        self.config = context.load_result.config
        self.otp_config = self.config.get("otp", {})
        self.otp_manager = OtpManager(self.config)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        page = ScrollablePage(self)
        page.grid(row=0, column=0, sticky="nsew")
        for column in (0, 1):
            page.grid_columnconfigure(column, weight=1, uniform="otp_email")

        PageHeader(
            page,
            "OTP & Email Setup",
            "Generate, send, and verify OTP codes in foundation mode.",
        ).grid(row=0, column=0, columnspan=2, sticky="ew", padx=4, pady=(0, 10))

        InfoBanner(
            page,
            "Foundation only: OTP checks do not unlock SafeDesk, start protected mode, trigger alerts, escalate threats, "
            "or send email unless explicitly configured and clicked.",
            kind="warning",
            compact=True,
        ).grid(row=1, column=0, columnspan=2, sticky="ew", padx=4, pady=(0, 12))

        email_panel = ctk.CTkFrame(page, **ds.card_kwargs())
        email_panel.grid(row=2, column=0, sticky="nsew", padx=(4, 8), pady=6)
        email_panel.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            email_panel,
            text="Email Settings Status",
            font=ctk.CTkFont(size=ds.FONT_H3, weight="bold"),
            text_color=ds.TEXT_PRIMARY,
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=ds.SPACE_LG, pady=(ds.SPACE_LG, ds.SPACE_SM))
        self.email_status_label = ctk.CTkLabel(
            email_panel,
            text="",
            justify="left",
            anchor="w",
            text_color=ds.TEXT_SECONDARY,
            wraplength=380,
            font=ctk.CTkFont(size=ds.FONT_BODY),
        )
        self.email_status_label.grid(row=1, column=0, sticky="ew", padx=ds.SPACE_LG, pady=(0, ds.SPACE_LG))

        otp_panel = ctk.CTkFrame(page, **ds.card_kwargs())
        otp_panel.grid(row=2, column=1, sticky="nsew", padx=(8, 4), pady=6)
        otp_panel.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            otp_panel,
            text="OTP Session Status",
            font=ctk.CTkFont(size=ds.FONT_H3, weight="bold"),
            text_color=ds.TEXT_PRIMARY,
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=ds.SPACE_LG, pady=(ds.SPACE_LG, ds.SPACE_SM))
        self.otp_status_label = ctk.CTkLabel(
            otp_panel,
            text="",
            justify="left",
            anchor="w",
            text_color=ds.TEXT_SECONDARY,
            wraplength=380,
            font=ctk.CTkFont(size=ds.FONT_BODY),
        )
        self.otp_status_label.grid(row=1, column=0, sticky="ew", padx=ds.SPACE_LG, pady=(0, ds.SPACE_SM))
        self.demo_otp_label = ctk.CTkLabel(
            otp_panel,
            text="Local demo OTP: not generated",
            justify="left",
            anchor="w",
            text_color=ds.SAFEDESK_ALERT,
            wraplength=380,
            font=ctk.CTkFont(size=ds.FONT_SMALL, weight="bold"),
        )
        self.demo_otp_label.grid(row=2, column=0, sticky="ew", padx=ds.SPACE_LG, pady=(0, ds.SPACE_LG))

        actions_panel = ctk.CTkFrame(page, **ds.card_kwargs())
        actions_panel.grid(row=3, column=0, sticky="nsew", padx=(4, 8), pady=6)
        for column in (0, 1):
            actions_panel.grid_columnconfigure(column, weight=1, uniform="otp_actions")
        ctk.CTkLabel(
            actions_panel,
            text="Manual OTP Actions",
            font=ctk.CTkFont(size=ds.FONT_H3, weight="bold"),
            text_color=ds.TEXT_PRIMARY,
            anchor="w",
        ).grid(row=0, column=0, columnspan=2, sticky="ew", padx=ds.SPACE_LG, pady=(ds.SPACE_LG, ds.SPACE_SM))

        ctk.CTkButton(
            actions_panel,
            text="Generate OTP",
            command=self.generate_otp,
            **ds.primary_button_kwargs(),
        ).grid(row=1, column=0, sticky="ew", padx=(ds.SPACE_LG, ds.SPACE_SM), pady=6)
        ctk.CTkButton(
            actions_panel,
            text="Send OTP Email",
            command=self.send_otp_email,
            **ds.secondary_button_kwargs(),
        ).grid(row=1, column=1, sticky="ew", padx=(ds.SPACE_SM, ds.SPACE_LG), pady=6)

        self.verify_otp_input = FormField(actions_panel, "Verify OTP input", "Enter OTP code", show="*")
        self.verify_otp_input.grid(row=2, column=0, columnspan=2, sticky="ew", padx=ds.SPACE_LG, pady=6)
        ctk.CTkButton(
            actions_panel,
            text="Verify OTP",
            command=self.verify_otp,
            **ds.secondary_button_kwargs(),
        ).grid(row=3, column=0, sticky="ew", padx=(ds.SPACE_LG, ds.SPACE_SM), pady=(6, ds.SPACE_LG))
        ctk.CTkButton(
            actions_panel,
            text="Reset OTP Session",
            command=self.reset_otp_session,
            **ds.secondary_button_kwargs(),
        ).grid(row=3, column=1, sticky="ew", padx=(ds.SPACE_SM, ds.SPACE_LG), pady=(6, ds.SPACE_LG))

        result_panel = ctk.CTkFrame(page, **ds.card_kwargs())
        result_panel.grid(row=3, column=1, sticky="nsew", padx=(8, 4), pady=6)
        result_panel.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            result_panel,
            text="Result / Email Test",
            font=ctk.CTkFont(size=ds.FONT_H3, weight="bold"),
            text_color=ds.TEXT_PRIMARY,
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=ds.SPACE_LG, pady=(ds.SPACE_LG, ds.SPACE_SM))
        self.message_banner = InfoBanner(
            result_panel,
            "No OTP or email action has run yet.",
            kind="neutral",
            compact=True,
            wraplength=360,
        )
        self.message_banner.grid(row=1, column=0, sticky="ew", padx=ds.SPACE_LG, pady=(0, ds.SPACE_SM))
        ctk.CTkButton(
            result_panel,
            text="Send Test Email",
            command=self.send_test_email,
            **ds.secondary_button_kwargs(),
        ).grid(row=2, column=0, sticky="ew", padx=ds.SPACE_LG, pady=(0, ds.SPACE_SM))
        ctk.CTkButton(
            result_panel,
            text="Refresh Status",
            command=self.refresh_status,
            **ds.secondary_button_kwargs(),
        ).grid(row=3, column=0, sticky="ew", padx=ds.SPACE_LG, pady=(0, ds.SPACE_LG))

        self.refresh_status()

    def refresh_status(self) -> None:
        email_status = build_email_settings_status(self.context.env, self.config, self.context.settings)
        self.email_status_label.configure(
            text=(
                f"Real email: {'enabled' if email_status.real_email_enabled else 'disabled'}\n"
                f"Sender address: {'configured' if email_status.sender_configured else 'missing'}\n"
                f"App password: {'present' if email_status.app_password_present else 'missing'}\n"
                f"OTP receiver: {'configured' if email_status.receiver_configured else 'missing'}\n"
                f"SMTP: {email_status.smtp_host}:{email_status.smtp_port}"
            )
        )

        status = self.otp_manager.session_status()
        self.otp_status_label.configure(
            text=(
                f"OTP generated: {'yes' if status.generated else 'no'}\n"
                f"Expired: {'yes' if status.expired else 'no'}\n"
                f"Attempts: {status.attempts_used} / {status.max_attempts}\n"
                f"Sends: {status.sends_used} / {status.resend_limit}\n"
                f"Cooldown: {status.cooldown_seconds_remaining} seconds\n"
                f"Mode: {'foundation only' if self.otp_config.get('demo_only', True) else 'review required'}"
            )
        )

        self.demo_otp_label.configure(
            text=self.build_demo_otp_display_text(status, email_status, self.otp_manager.session.code)
        )

    def generate_otp(self) -> None:
        if self.otp_config.get("otp_foundation_enabled", True) is not True:
            self.message_banner.set_message("OTP foundation is disabled in configuration.")
            return
        result = self.otp_manager.generate_otp()
        self.message_banner.set_message(f"{result.message} It expires in {result.expires_seconds} seconds.")
        self.refresh_status()

    def send_otp_email(self) -> None:
        eligibility = self.otp_manager.can_send_otp()
        if not eligibility.allowed:
            self.message_banner.set_message(eligibility.message)
            self.refresh_status()
            return

        sender = EmailSender(self.config, self.context.env, self.context.settings)
        result = sender.send_otp_email(self.otp_manager.session.code, self.otp_manager.session_status().expires_seconds_remaining)
        if result.success:
            self.otp_manager.record_send()
        self.message_banner.set_message(result.message)
        self.refresh_status()

    def verify_otp(self) -> None:
        result = self.otp_manager.verify_otp(self.verify_otp_input.get())
        self.message_banner.set_message(
            f"{result.message} Attempts remaining: {result.attempts_remaining}."
            if result.status in {"failed", "attempts_exceeded"}
            else result.message
        )
        self.refresh_status()

    def reset_otp_session(self) -> None:
        self.otp_manager.reset_session()
        self.verify_otp_input.clear()
        self.message_banner.set_message("OTP session reset. No OTP is active.")
        self.refresh_status()

    def send_test_email(self) -> None:
        sender = EmailSender(self.config, self.context.env, self.context.settings)
        result = sender.send_test_email()
        self.message_banner.set_message(result.message)
        self.refresh_status()

    @staticmethod
    def build_demo_otp_display_text(status, email_status, otp_code: str) -> str:
        """Return safe OTP display text for the manual foundation screen."""

        if not status.generated or status.expired:
            return "Local demo OTP: not generated"

        real_email_ready = (
            email_status.real_email_enabled
            and email_status.sender_configured
            and email_status.app_password_present
            and email_status.receiver_configured
        )
        if real_email_ready:
            return "OTP generated. Real email is configured, so use Send OTP Email and check the receiver inbox."

        return f"Local demo OTP (foundation testing only): {otp_code}"
