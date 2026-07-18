from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from safedesk.app import run_app


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    check_config_only = "--check-config" in args

    unsupported_args = [arg for arg in args if arg != "--check-config"]
    if unsupported_args:
        print(f"Unsupported argument: {unsupported_args[0]}")
        print("Usage: python main.py [--check-config]")
        return 2

    return run_app(check_config_only=check_config_only, root=PROJECT_ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
