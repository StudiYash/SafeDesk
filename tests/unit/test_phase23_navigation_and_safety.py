from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.gui.navigation import INTRUDER_HISTORY, SCREEN_NAMES


def test_intruder_history_navigation_is_admin_console_only():
    main_source = (SRC / "safedesk" / "gui" / "main_window.py").read_text(encoding="utf-8")
    launch_source = (SRC / "safedesk" / "gui" / "screens" / "launch_screen.py").read_text(encoding="utf-8")
    public_lock_source = (SRC / "safedesk" / "gui" / "screens" / "public_lock_screen.py").read_text(encoding="utf-8")

    assert INTRUDER_HISTORY in SCREEN_NAMES
    assert "INTRUDER_HISTORY: IntruderHistoryScreen" in main_source
    assert "Intruder History" not in launch_source
    assert "Intruder History" not in public_lock_source
    assert "Return to Launch" not in public_lock_source
    assert "Return to Admin Console" not in public_lock_source
    assert "Developer Return" not in public_lock_source


def test_phase23_sources_do_not_add_automation_or_evidence_mutation():
    paths = (
        SRC / "safedesk" / "dashboard",
        SRC / "safedesk" / "intruder_history",
        SRC / "safedesk" / "gui" / "screens",
    )
    source = "\n".join(
        path.read_text(encoding="utf-8")
        for folder in paths
        for path in folder.glob("*.py")
        if path.name in {
            "dashboard_placeholder_screen.py",
            "intruder_history_screen.py",
            "dashboard_models.py",
            "dashboard_service.py",
            "intruder_history_models.py",
            "intruder_history_reader.py",
        }
    )
    forbidden = (
        "VideoCapture(",
        "cv2.VideoCapture",
        "DeepFace.verify",
        "DeepFace.find",
        "send_email",
        "send_otp",
        "smtp",
        "delete",
        "unlink",
        "remove(",
        "rmtree",
        "upload",
        "requests.post",
        "shutdown /s",
        "shutdown.exe",
        "BlockInput",
        "SetWindowsHookEx",
        "pynput",
        "import keyboard",
        "winreg",
        "schtasks",
        "RunOnce",
        "Start Menu\\\\Programs\\\\Startup",
    )

    for text in forbidden:
        assert text not in source
