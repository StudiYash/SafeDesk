"""Safe first-time setup wizard screen."""

import customtkinter as ctk

from safedesk.app.application import RuntimeContext
from safedesk.config.local_config_writer import LocalSetupPayload, save_local_setup_config
from safedesk.config.exceptions import SafeDeskConfigError
from safedesk.gui import design_system as ds
from safedesk.gui.components.form_field import FormField
from safedesk.gui.components.info_banner import InfoBanner
from safedesk.gui.components.page_header import PageHeader
from safedesk.gui.components.scrollable_page import ScrollablePage
from safedesk.utils.constants import SUPPORTED_SECURITY_MODES


class SetupWizardScreen(ctk.CTkFrame):
    """Collect safe, non-secret local setup values."""

    def __init__(self, master, context: RuntimeContext):
        super().__init__(master, fg_color=ds.CONTENT_BG)
        self.context = context
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        page = ScrollablePage(self)
        page.grid(row=0, column=0, sticky="nsew")

        PageHeader(
            page,
            "First-Time Setup Wizard",
            "Save non-secret local owner preferences for later phases.",
        ).grid(row=0, column=0, sticky="ew", padx=4, pady=(0, 10))

        InfoBanner(
            page,
            "This setup saves only non-secret local preferences. No password is created, no face image is captured, "
            "no email or OTP is configured, and no lockdown or shutdown is enabled in this phase.",
            kind="warning",
        ).grid(row=1, column=0, sticky="ew", padx=4, pady=(0, 12))

        form_panel = ctk.CTkFrame(page, **ds.card_kwargs())
        form_panel.grid(row=2, column=0, sticky="ew", padx=4, pady=6)
        form_panel.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            form_panel,
            text="Owner Profile",
            font=ctk.CTkFont(size=ds.FONT_H3, weight="bold"),
            text_color=ds.TEXT_PRIMARY,
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=ds.SPACE_LG, pady=(ds.SPACE_LG, ds.SPACE_SM))

        self.owner_name = FormField(form_panel, "Owner display name", "Example: Yash")
        self.owner_name.grid(row=1, column=0, sticky="ew", padx=ds.SPACE_LG, pady=6)
        self.owner_name.set(context.load_result.config.get("owner_profile", {}).get("owner_name", ""))

        self.owner_email = FormField(form_panel, "Owner email address (optional)", "owner@example.com")
        self.owner_email.grid(row=2, column=0, sticky="ew", padx=ds.SPACE_LG, pady=6)
        self.owner_email.set(context.load_result.config.get("owner_profile", {}).get("owner_email", ""))

        ctk.CTkLabel(
            form_panel,
            text="Preferred security mode",
            anchor="w",
            text_color=ds.TEXT_SECONDARY,
            font=ctk.CTkFont(size=ds.FONT_SMALL, weight="bold"),
        ).grid(row=3, column=0, sticky="ew", padx=ds.SPACE_LG, pady=(8, 0))
        self.security_mode = ctk.CTkOptionMenu(
            form_panel,
            values=list(SUPPORTED_SECURITY_MODES),
            fg_color=ds.CARD_BG_ALT,
            button_color=ds.SAFEDESK_RED,
            button_hover_color=ds.SAFEDESK_DEEP_RED,
            dropdown_fg_color=ds.CARD_BG_ALT,
            dropdown_hover_color=ds.BORDER_MUTED,
            dropdown_text_color=ds.TEXT_PRIMARY,
            text_color=ds.TEXT_PRIMARY,
        )
        self.security_mode.set(context.settings.security_mode if context.settings.security_mode in SUPPORTED_SECURITY_MODES else "demo_safe")
        self.security_mode.grid(row=4, column=0, sticky="w", padx=ds.SPACE_LG, pady=(4, 6))

        self.camera_index = FormField(form_panel, "Camera index placeholder", "0")
        self.camera_index.grid(row=5, column=0, sticky="ew", padx=ds.SPACE_LG, pady=(6, ds.SPACE_LG))
        self.camera_index.set("0")

        self.privacy_ack = ctk.BooleanVar(value=False)
        self.safe_mode_ack = ctk.BooleanVar(value=False)

        ack_panel = ctk.CTkFrame(page, **ds.panel_kwargs())
        ack_panel.grid(row=3, column=0, sticky="ew", padx=4, pady=6)
        ack_panel.grid_columnconfigure(0, weight=1)
        ctk.CTkCheckBox(
            ack_panel,
            text="I understand owner/intruder images, logs, and secrets must stay local and out of Git.",
            variable=self.privacy_ack,
            fg_color=ds.SAFEDESK_RED,
            hover_color=ds.SAFEDESK_DEEP_RED,
            border_color=ds.BORDER_MUTED,
            text_color=ds.TEXT_SECONDARY,
        ).grid(row=0, column=0, sticky="w", padx=ds.SPACE_LG, pady=(ds.SPACE_LG, 6))
        ctk.CTkCheckBox(
            ack_panel,
            text="I understand real email, lockdown, and shutdown remain disabled in this setup phase.",
            variable=self.safe_mode_ack,
            fg_color=ds.SAFEDESK_RED,
            hover_color=ds.SAFEDESK_DEEP_RED,
            border_color=ds.BORDER_MUTED,
            text_color=ds.TEXT_SECONDARY,
        ).grid(row=1, column=0, sticky="w", padx=ds.SPACE_LG, pady=(6, ds.SPACE_LG))

        self.status_banner = InfoBanner(page, "Ready to save safe local setup preferences.", kind="neutral")
        self.status_banner.grid(row=4, column=0, sticky="ew", padx=4, pady=(8, 8))

        ctk.CTkButton(page, text="Save Local Setup", command=self._save_setup, **ds.primary_button_kwargs()).grid(
            row=5,
            column=0,
            sticky="w",
            padx=4,
            pady=8,
        )

    def _save_setup(self) -> None:
        try:
            camera_index = int(self.camera_index.get().strip())
            payload = LocalSetupPayload(
                owner_name=self.owner_name.get(),
                owner_email=self.owner_email.get(),
                preferred_security_mode=self.security_mode.get(),
                demo_safe_mode=True,
                camera_index=camera_index,
                privacy_acknowledged=bool(self.privacy_ack.get()),
                safe_mode_acknowledged=bool(self.safe_mode_ack.get()),
            )
            save_local_setup_config(payload)
        except ValueError:
            self.status_banner.set_message("Camera index must be a whole number such as 0.")
            return
        except SafeDeskConfigError as exc:
            self.status_banner.set_message(f"Setup could not be saved: {exc}")
            return

        self.status_banner.set_message(
            "Local setup saved to config.local.json. Restart or re-open SafeDesk to reload local configuration."
        )
