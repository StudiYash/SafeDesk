"""Theme helpers for the SafeDesk GUI shell."""

from typing import Any

VALID_THEMES = {"dark", "light", "system"}


def apply_theme(ui_config: dict[str, Any]) -> None:
    """Apply CustomTkinter appearance settings from safe UI config."""

    import customtkinter as ctk

    theme = str(ui_config.get("theme", "dark")).lower()
    if theme not in VALID_THEMES:
        theme = "dark"

    ctk.set_appearance_mode(theme)
    ctk.set_default_color_theme("dark-blue")
