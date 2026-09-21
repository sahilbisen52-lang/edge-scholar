"""
EdgeScholar — Private On-Device AI Study Copilot
Entry point.
"""
from __future__ import annotations

import sys
import os


def main() -> None:
    # Ensure the project root is on the path
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    from app.core.logging_config import setup_logging
    setup_logging()

    from app.core.app_context import AppContext
    ctx = AppContext()

    # Launch Qt application
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt
    from app.ui.main_window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("EdgeScholar")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("EdgeScholar")
    app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    window = MainWindow(ctx)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
