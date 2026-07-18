from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def test_settings_screen_imports_without_opening_window():
    import pytest

    pytest.importorskip("customtkinter")
    from safedesk.gui.screens.settings_screen import SettingsScreen

    assert SettingsScreen is not None


def test_settings_screen_contains_only_explicit_managed_controls():
    source = (SRC / "safedesk" / "gui" / "screens" / "settings_screen.py").read_text(encoding="utf-8")

    for text in ("Save Settings", "Restore Safe Defaults", "Reload Startup Values", "Ctrl + Alt + L"):
        assert text in source
    for text in (
        "There is no separate Developer Mode switch.",
        "Developer Tools eligibility",
        "Effective environment",
        "Demo-safe mode",
        "Security mode",
        "Foundation",
        "Demo screens after restart",
        "Diagnostics after restart",
        "Developer Tools are unavailable under the current safe runtime policy.",
        "Enable demo screens or diagnostics, save, and restart SafeDesk.",
        "Developer Tools will be available from the Developer section after restart.",
        "root=context.project_root",
    ):
        assert text in source
    for forbidden in (
        "config.local.json",
        "filedialog",
        "JSON editor",
        "password_entry",
        "recovery_code",
        "panic_code",
        "restart(",
    ):
        assert forbidden not in source

    cancel_body = source.split("def _cancel_restore", 1)[1].split("def _confirm_restore", 1)[0]
    assert "restore_defaults" not in cancel_body
