from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def test_phase25_production_sources_have_no_unsafe_operations():
    files = (
        *tuple((SRC / "safedesk" / "settings").glob("*.py")),
        *tuple((SRC / "safedesk" / "developer_tools").glob("*.py")),
        SRC / "safedesk" / "config" / "config_loader.py",
        SRC / "safedesk" / "config" / "validators.py",
        SRC / "safedesk" / "app" / "application.py",
        SRC / "safedesk" / "dashboard" / "dashboard_service.py",
        SRC / "safedesk" / "logging" / "sqlite_log_store.py",
        SRC / "safedesk" / "gui" / "navigation.py",
        SRC / "safedesk" / "gui" / "main_window.py",
        SRC / "safedesk" / "gui" / "startup_maximize.py",
        SRC / "safedesk" / "gui" / "screens" / "logging_dashboard_screen.py",
        SRC / "safedesk" / "gui" / "screens" / "settings_screen.py",
        SRC / "safedesk" / "gui" / "screens" / "developer_tools_screen.py",
        SRC / "safedesk" / "gui" / "screens" / "dashboard_placeholder_screen.py",
    )
    source = "\n".join(path.read_text(encoding="utf-8") for path in files)
    forbidden = (
        "sub" + "process",
        "os." + "system",
        "shell=" + "True",
        "start" + "file",
        "win" + "reg",
        "sch" + "tasks",
        "Run" + "Once",
        "SetWindows" + "HookEx",
        "Block" + "Input",
        "py" + "nput",
        "import key" + "board",
        "shutdown" + " /s",
        "shutdown." + "exe",
        "requests." + "post",
        "send_" + "email",
        "send_" + "otp",
        "Video" + "Capture(",
        "DeepFace." + "verify",
        "DeepFace." + "find",
        "SND_" + "LOOP",
        "arbitrary JSON editor",
    )
    for text in forbidden:
        assert text not in source

    action_sources = tuple(path for path in files if path.name != "validators.py")
    action_source = "\n".join(path.read_text(encoding="utf-8") for path in action_sources)
    assert "sm" + "tp" not in action_source


def test_launch_and_public_lock_have_no_settings_or_developer_tools_controls():
    launch = (SRC / "safedesk" / "gui" / "screens" / "launch_screen.py").read_text(encoding="utf-8")
    public = (SRC / "safedesk" / "gui" / "screens" / "public_lock_screen.py").read_text(encoding="utf-8")

    for text in ("Developer Tools", "Save Settings", "Restore Safe Defaults"):
        assert text not in launch
        assert text not in public


def test_settings_introduces_no_secret_developer_activation_or_gate_bypass():
    source = (SRC / "safedesk" / "gui" / "screens" / "settings_screen.py").read_text(encoding="utf-8")

    assert "There is no separate Developer Mode switch." in source
    for forbidden in ("secret click", "hidden shortcut", "bypass", "SAFEDESK_ENV", "os.environ"):
        assert forbidden not in source
