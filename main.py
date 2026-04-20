import argparse
import sys
from pathlib import Path


def _resource_root() -> Path:
    """
    Return the correct base directory whether running:
    - from source:  the game_hub/ folder itself
    - from PyInstaller exe:  the _MEIPASS temp folder
    """
    if getattr(sys, "frozen", False):
        # Running inside a PyInstaller bundle
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    # Running from source — go up one level from this file
    return Path(__file__).resolve().parent


def main() -> int:
    parser = argparse.ArgumentParser(description="Neon Game Hub")
    parser.add_argument(
        "--smoke-test", action="store_true",
        help="Create the window and exit after one event cycle.",
    )
    args = parser.parse_args()

    from PyQt6.QtWidgets import QApplication
    from hub.ui.main_window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("Neon Game Hub")

    window = MainWindow(resource_root=_resource_root())

    if args.smoke_test:
        app.processEvents()
        return 0

    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
