"""Owner/Admin Console gate screen."""

from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk

from safedesk.admin_gate import AdminGateManager
from safedesk.app.application import RuntimeContext
from safedesk.gui import design_system as ds
from safedesk.logging.event_logger import build_logger_from_config


class AdminGateScreen(ctk.CTkFrame):
    """Owner-facing gate before exposing the sidebar Admin Console."""

    def __init__(
        self,
        master,
        context: RuntimeContext,
        manager: AdminGateManager,
        on_gate_success: Callable[[], None],
        on_continue_setup: Callable[[], None],
        on_back_to_launch: Callable[[], None],
    ):
        super().__init__(master, fg_color=ds.CONTENT_BG)
        self.context = context
        self.manager = manager
        self.event_logger = build_logger_from_config(context.load_result.config)
        self.on_gate_success = on_gate_success
        self.on_continue_setup = on_continue_setup
        self.on_back_to_launch = on_back_to_launch
        self.password_entry: ctk.CTkEntry | None = None
        self.unlock_button: ctk.CTkButton | None = None
        self.message_label: ctk.CTkLabel | None = None
        self.status_label: ctk.CTkLabel | None = None
        self.recovery_code_entry: ctk.CTkEntry | None = None
        self.new_password_entry: ctk.CTkEntry | None = None
        self.confirm_new_password_entry: ctk.CTkEntry | None = None
        self.mode = "password"

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._build_layout()

    def _build_layout(self) -> None:
        for child in self.winfo_children():
            child.destroy()

        panel = ctk.CTkFrame(
            self,
            fg_color=ds.CARD_BG,
            corner_radius=ds.RADIUS_LG,
            border_width=1,
            border_color=ds.BORDER_MUTED,
        )
        panel.grid(row=0, column=0, padx=42, pady=42, sticky="")
        panel.grid_columnconfigure(0, weight=1)

        status = self.manager.build_status()
        if self.mode == "recovery":
            subtitle = "Reset owner password using a recovery code."
        else:
            subtitle = "Owner verification required to continue." if status.password_configured else "Owner password setup is required."

        ctk.CTkLabel(
            panel,
            text="Owner/Admin Console",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=ds.TEXT_PRIMARY,
        ).grid(row=0, column=0, padx=36, pady=(34, 6), sticky="ew")
        ctk.CTkLabel(
            panel,
            text=subtitle,
            font=ctk.CTkFont(size=ds.FONT_H3, weight="bold"),
            text_color=ds.TEXT_SECONDARY,
        ).grid(row=1, column=0, padx=36, pady=(0, 20), sticky="ew")

        self.status_label = ctk.CTkLabel(
            panel,
            text=self._status_summary(status),
            font=ctk.CTkFont(size=ds.FONT_SMALL),
            text_color=ds.TEXT_MUTED,
            anchor="center",
        )
        self.status_label.grid(row=2, column=0, padx=36, pady=(0, 12), sticky="ew")

        self.message_label = ctk.CTkLabel(
            panel,
            text=status.message,
            font=ctk.CTkFont(size=ds.FONT_BODY),
            text_color=ds.TEXT_SECONDARY,
            wraplength=420,
        )
        self.message_label.grid(row=3, column=0, padx=36, pady=(0, 18), sticky="ew")

        if self.mode == "recovery":
            self._build_recovery_controls(panel)
        elif status.password_configured:
            self._build_password_controls(panel, status)
        else:
            self._build_setup_controls(panel, status)

    def _build_password_controls(self, panel, status) -> None:
        self.password_entry = ctk.CTkEntry(
            panel,
            placeholder_text="Owner password",
            show="*",
            height=42,
            fg_color=ds.CARD_BG_ALT,
            border_color=ds.BORDER_MUTED,
            text_color=ds.TEXT_PRIMARY,
        )
        self.password_entry.grid(row=4, column=0, padx=36, pady=(0, 12), sticky="ew")
        self.password_entry.bind("<Return>", lambda _event: self._handle_unlock())

        locked = status.locked_out
        self.unlock_button = ctk.CTkButton(
            panel,
            text="Unlock Admin Console",
            command=self._handle_unlock,
            state="disabled" if locked else "normal",
            height=42,
            **ds.primary_button_kwargs(),
        )
        self.unlock_button.grid(row=5, column=0, padx=36, pady=(0, 10), sticky="ew")

        ctk.CTkButton(
            panel,
            text="Forgot Password?",
            command=self._show_recovery_mode,
            height=42,
            **ds.secondary_button_kwargs(),
        ).grid(row=6, column=0, padx=36, pady=(0, 10), sticky="ew")

        ctk.CTkButton(
            panel,
            text="Back to Launch",
            command=self._handle_back_to_launch,
            height=42,
            **ds.secondary_button_kwargs(),
        ).grid(row=7, column=0, padx=36, pady=(0, 34), sticky="ew")

        if self.password_entry is not None and not locked:
            self.password_entry.focus_set()

    def _build_setup_controls(self, panel, status) -> None:
        if status.development_continue_allowed:
            ctk.CTkButton(
                panel,
                text="Continue to Setup",
                command=self._handle_continue_setup,
                height=42,
                **ds.primary_button_kwargs(),
            ).grid(row=4, column=0, padx=36, pady=(0, 10), sticky="ew")

        ctk.CTkButton(
            panel,
            text="Back to Launch",
            command=self._handle_back_to_launch,
            height=42,
            **ds.secondary_button_kwargs(),
        ).grid(row=5, column=0, padx=36, pady=(0, 34), sticky="ew")

    def _build_recovery_controls(self, panel) -> None:
        auth_status = self.manager.auth_service.build_status()
        if not auth_status.recovery_codes_configured or auth_status.unused_recovery_code_count <= 0:
            self._set_message(
                "No recovery codes are configured. Use the local development reset process or set up recovery codes after regaining access."
            )
            ctk.CTkButton(
                panel,
                text="Back to Password Unlock",
                command=self._show_password_mode,
                height=42,
                **ds.secondary_button_kwargs(),
            ).grid(row=4, column=0, padx=36, pady=(0, 10), sticky="ew")
            ctk.CTkButton(
                panel,
                text="Back to Launch",
                command=self._handle_back_to_launch,
                height=42,
                **ds.secondary_button_kwargs(),
            ).grid(row=5, column=0, padx=36, pady=(0, 34), sticky="ew")
            return

        self.recovery_code_entry = ctk.CTkEntry(
            panel,
            placeholder_text="Recovery code",
            show="*",
            height=42,
            fg_color=ds.CARD_BG_ALT,
            border_color=ds.BORDER_MUTED,
            text_color=ds.TEXT_PRIMARY,
        )
        self.recovery_code_entry.grid(row=4, column=0, padx=36, pady=(0, 10), sticky="ew")
        self.new_password_entry = ctk.CTkEntry(
            panel,
            placeholder_text="New owner password",
            show="*",
            height=42,
            fg_color=ds.CARD_BG_ALT,
            border_color=ds.BORDER_MUTED,
            text_color=ds.TEXT_PRIMARY,
        )
        self.new_password_entry.grid(row=5, column=0, padx=36, pady=(0, 10), sticky="ew")
        self.confirm_new_password_entry = ctk.CTkEntry(
            panel,
            placeholder_text="Confirm new owner password",
            show="*",
            height=42,
            fg_color=ds.CARD_BG_ALT,
            border_color=ds.BORDER_MUTED,
            text_color=ds.TEXT_PRIMARY,
        )
        self.confirm_new_password_entry.grid(row=6, column=0, padx=36, pady=(0, 12), sticky="ew")

        for entry in (self.recovery_code_entry, self.new_password_entry, self.confirm_new_password_entry):
            entry.bind("<Return>", lambda _event: self._handle_recovery_reset())

        ctk.CTkButton(
            panel,
            text="Reset Password",
            command=self._handle_recovery_reset,
            height=42,
            **ds.primary_button_kwargs(),
        ).grid(row=7, column=0, padx=36, pady=(0, 10), sticky="ew")
        ctk.CTkButton(
            panel,
            text="Back to Password Unlock",
            command=self._show_password_mode,
            height=42,
            **ds.secondary_button_kwargs(),
        ).grid(row=8, column=0, padx=36, pady=(0, 10), sticky="ew")
        ctk.CTkButton(
            panel,
            text="Back to Launch",
            command=self._handle_back_to_launch,
            height=42,
            **ds.secondary_button_kwargs(),
        ).grid(row=9, column=0, padx=36, pady=(0, 34), sticky="ew")

        self.recovery_code_entry.focus_set()

    def _handle_unlock(self) -> None:
        if self.password_entry is None:
            return
        result = self.manager.verify_password(self.password_entry.get())
        self.password_entry.delete(0, "end")
        self._set_message(self._attempt_message(result.status, result.message, result.remaining_attempts))
        self._update_status_summary()
        self._log_password_result(result.status, result.remaining_attempts, result.lockout_remaining_seconds)
        if result.success:
            self.on_gate_success()
        elif result.status == "locked_out" and self.unlock_button is not None:
            self.unlock_button.configure(state="disabled")

    def _handle_continue_setup(self) -> None:
        result = self.manager.development_continue()
        self._set_message(result.message)
        self._log_gate_event(
            "admin_gate_continue_setup_requested",
            "Owner/Admin Gate setup continuation was requested.",
            status="success" if result.success else "blocked",
            metadata={"allowed": result.success, "result_status": result.status},
        )
        if result.success:
            self.on_continue_setup()

    def _show_recovery_mode(self) -> None:
        self.mode = "recovery"
        self._build_layout()
        self._set_message("Enter one unused recovery code and choose a new owner password.")
        self._log_gate_event(
            "admin_gate_recovery_view_opened",
            "Owner/Admin Gate recovery reset view opened.",
            metadata=self._recovery_count_metadata(),
        )

    def _show_password_mode(self) -> None:
        self.mode = "password"
        self._build_layout()

    def _handle_recovery_reset(self) -> None:
        if self.recovery_code_entry is None or self.new_password_entry is None or self.confirm_new_password_entry is None:
            return
        result = self.manager.reset_password_with_recovery_code(
            self.recovery_code_entry.get(),
            self.new_password_entry.get(),
            self.confirm_new_password_entry.get(),
        )
        self.recovery_code_entry.delete(0, "end")
        self.new_password_entry.delete(0, "end")
        self.confirm_new_password_entry.delete(0, "end")
        action = "admin_gate_recovery_password_reset_success" if result.success else "admin_gate_recovery_password_reset_failed"
        self._log_gate_event(
            action,
            "Owner/Admin Gate recovery reset result recorded.",
            status="success" if result.success else "failed",
            metadata={"result_status": result.status} | self._recovery_count_metadata(),
        )
        if result.success:
            self.mode = "password"
            self._build_layout()
            self._set_message("Owner password reset. Unlock the Admin Console with your new password.")
            return
        self._set_message(result.message)

    def _handle_back_to_launch(self) -> None:
        self._log_gate_event("admin_gate_back_to_launch", "Owner/Admin Gate returned to launch.")
        self.on_back_to_launch()

    def _set_message(self, message: str) -> None:
        if self.message_label is not None:
            self.message_label.configure(text=message)

    def _update_status_summary(self) -> None:
        if self.status_label is None:
            return
        self.status_label.configure(text=self._status_summary(self.manager.build_status()))

    @staticmethod
    def _attempt_message(status: str, message: str, remaining_attempts: int) -> str:
        if status == "failed":
            return f"Owner verification failed. Attempts remaining: {remaining_attempts}."
        if status == "locked_out":
            return message
        if status == "success":
            return "Owner verification succeeded."
        return message

    @staticmethod
    def _status_summary(status) -> str:
        if status.locked_out:
            return f"Temporarily locked. Try again in {status.lockout_remaining_seconds} seconds."
        if status.password_configured:
            return f"Attempts remaining: {status.remaining_attempts}"
        if status.setup_required and status.development_continue_allowed:
            return "Setup route available for local development."
        if status.setup_required:
            return "Setup route disabled by local configuration."
        return "Credential status unavailable."

    def _log_password_result(self, result_status: str, remaining_attempts: int, lockout_remaining_seconds: int) -> None:
        action = {
            "success": "admin_gate_password_success",
            "failed": "admin_gate_password_failed",
            "locked_out": "admin_gate_locked_out",
        }.get(result_status, "admin_gate_password_failed")
        event_status = "success" if result_status == "success" else "blocked" if result_status == "locked_out" else "failed"
        self._log_gate_event(
            action,
            "Owner/Admin Gate password verification result recorded.",
            status=event_status,
            metadata={
                "result_status": result_status,
                "remaining_attempts": remaining_attempts,
                "locked_out": result_status == "locked_out",
                "lockout_remaining_seconds": lockout_remaining_seconds,
            },
        )

    def _log_gate_event(
        self,
        action: str,
        message: str,
        status: str = "info",
        metadata: dict | None = None,
    ) -> None:
        try:
            gate_status = self.manager.build_status()
            safe_metadata = {
                "surface": "admin_gate",
                "password_configured": gate_status.password_configured,
                "development_continue_allowed": gate_status.development_continue_allowed,
                "locked_out": gate_status.locked_out,
            }
            if metadata:
                safe_metadata.update(metadata)
            self.event_logger.log_app_event(
                action=action,
                status=status,
                message=message,
                metadata=safe_metadata,
            )
        except Exception:
            pass

    def _recovery_count_metadata(self) -> dict:
        status = self.manager.auth_service.build_status()
        return {
            "recovery_codes_configured": status.recovery_codes_configured,
            "recovery_code_count": status.recovery_code_count,
            "unused_recovery_code_count": status.unused_recovery_code_count,
            "used_recovery_code_count": status.used_recovery_code_count,
        }
