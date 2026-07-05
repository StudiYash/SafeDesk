"""SafeDesk application mode transition manager."""

from __future__ import annotations

from safedesk.app_modes.mode_models import AppModeTransitionResult, SafeDeskMode, parse_app_mode

ALLOWED_MODE_TRANSITIONS: dict[SafeDeskMode, tuple[SafeDeskMode, ...]] = {
    SafeDeskMode.LAUNCH: (
        SafeDeskMode.LAUNCH,
        SafeDeskMode.ADMIN_CONSOLE,
        SafeDeskMode.PUBLIC_LOCK,
    ),
    SafeDeskMode.ADMIN_CONSOLE: (
        SafeDeskMode.LAUNCH,
        SafeDeskMode.ADMIN_CONSOLE,
        SafeDeskMode.PUBLIC_LOCK,
    ),
    SafeDeskMode.PUBLIC_LOCK: (
        SafeDeskMode.LAUNCH,
        SafeDeskMode.ADMIN_CONSOLE,
        SafeDeskMode.PUBLIC_LOCK,
    ),
    SafeDeskMode.BACKGROUND_AGENT: (
        SafeDeskMode.LAUNCH,
        SafeDeskMode.BACKGROUND_AGENT,
    ),
}


class AppModeManager:
    """Small state manager for SafeDesk's top-level application mode."""

    def __init__(self, initial_mode: SafeDeskMode | str | None = SafeDeskMode.LAUNCH):
        self.current_mode = parse_app_mode(initial_mode) or SafeDeskMode.LAUNCH

    def can_transition(self, target_mode: SafeDeskMode | str | None) -> bool:
        """Return True when the requested transition is allowed."""

        parsed = parse_app_mode(target_mode)
        if parsed is None:
            return False
        return parsed in ALLOWED_MODE_TRANSITIONS.get(self.current_mode, ())

    def transition_to(self, target_mode: SafeDeskMode | str | None) -> AppModeTransitionResult:
        """Transition modes when the requested route is allowed."""

        previous = self.current_mode
        parsed = parse_app_mode(target_mode)
        if parsed is None:
            return AppModeTransitionResult(
                success=False,
                previous_mode=previous,
                new_mode=previous,
                status="invalid_mode",
                message="Requested SafeDesk mode is not supported.",
            )

        if parsed == previous:
            return AppModeTransitionResult(
                success=True,
                previous_mode=previous,
                new_mode=previous,
                status="unchanged",
                message="SafeDesk is already in the requested mode.",
            )

        if not self.can_transition(parsed):
            return AppModeTransitionResult(
                success=False,
                previous_mode=previous,
                new_mode=previous,
                status="blocked",
                message="Requested SafeDesk mode transition is not allowed.",
            )

        self.current_mode = parsed
        return AppModeTransitionResult(
            success=True,
            previous_mode=previous,
            new_mode=parsed,
            status="updated",
            message="SafeDesk mode updated.",
        )

    def reset_to_launch(self) -> AppModeTransitionResult:
        """Return to the safe launch router."""

        return self.transition_to(SafeDeskMode.LAUNCH)
