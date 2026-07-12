from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.gui.navigation import ALARM_SYSTEM, SCREEN_NAMES


def test_alarm_system_is_admin_console_only_and_gate_routing_remains_intact():
    main_source = (SRC / "safedesk" / "gui" / "main_window.py").read_text(encoding="utf-8")
    launch_source = (SRC / "safedesk" / "gui" / "screens" / "launch_screen.py").read_text(encoding="utf-8")
    public_source = (SRC / "safedesk" / "gui" / "screens" / "public_lock_screen.py").read_text(encoding="utf-8")
    tray_source = (SRC / "safedesk" / "background_agent" / "tray_controller.py").read_text(encoding="utf-8")
    shortcut_source = (SRC / "safedesk" / "global_shortcut" / "shortcut_manager.py").read_text(encoding="utf-8")

    assert ALARM_SYSTEM in SCREEN_NAMES
    assert "ALARM_SYSTEM: AlarmSystemScreen" in main_source
    assert "self.show_admin_gate(screen_name)" in main_source
    assert "Alarm System" not in launch_source
    assert "Alarm System" not in public_source
    assert "Alarm System" not in tray_source
    assert "Alarm System" not in shortcut_source


def test_only_alarm_system_screen_starts_a_preview():
    excluded = SRC / "safedesk" / "gui" / "screens" / "alarm_system_screen.py"
    relevant = (
        *tuple(
            path
            for path in (SRC / "safedesk" / "gui" / "screens").glob("*.py")
            if path != excluded
        ),
        *tuple((SRC / "safedesk" / "global_shortcut").glob("*.py")),
        *tuple((SRC / "safedesk" / "background_agent").glob("*.py")),
        *tuple((SRC / "safedesk" / "lockdown_display").glob("*.py")),
        *tuple((SRC / "safedesk" / "interaction_lock").glob("*.py")),
    )

    assert "start_preview(" in excluded.read_text(encoding="utf-8")
    for path in relevant:
        assert "start_preview(" not in path.read_text(encoding="utf-8")


def test_phase24_production_sources_have_no_unsafe_audio_or_security_operations():
    files = (
        *tuple((SRC / "safedesk" / "alarm").glob("*.py")),
        SRC / "safedesk" / "gui" / "screens" / "alarm_system_screen.py",
    )
    source = "\n".join(path.read_text(encoding="utf-8") for path in files)
    forbidden = (
        "SND_" + "LOOP",
        "sub" + "process",
        "os." + "system",
        "shell=" + "True",
        "start" + "file",
        "ff" + "play",
        "vl" + "c",
        "pygame." + "mixer",
        "play" + "sound",
        "simple" + "audio",
        "py" + "dub",
        "py" + "caw",
        "SetMaster" + "Volume",
        "SetWindows" + "HookEx",
        "Block" + "Input",
        "py" + "nput",
        "import key" + "board",
        "win" + "reg",
        "sch" + "tasks",
        "Run" + "Once",
        "shutdown" + " /s",
        "shutdown." + "exe",
        "requests." + "post",
        "sm" + "tp",
        "send_" + "email",
        "send_" + "otp",
        "Video" + "Capture(",
        "DeepFace." + "verify",
        "DeepFace." + "find",
    )

    for text in forbidden:
        assert text not in source
