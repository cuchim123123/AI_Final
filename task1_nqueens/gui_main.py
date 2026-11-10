"""Entry point to launch the N-Queens PySide6 GUI."""
from __future__ import annotations

import sys
from nqueens_gui.app import MainWindow, create_app


def main():
    app = create_app()
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
