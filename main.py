"""
Main entry point for the Web Crawler Application.

Modular version with properly organized components:
- Workers for background tasks
- GUI components in logical groups
- Centralized configuration
- Clean imports and dependencies
"""

import sys
from PyQt6.QtWidgets import QApplication

from gui.main_window import MainApp


def main():
    """Launch the Web Crawler Application."""
    app = QApplication(sys.argv)
    main_app = MainApp()
    main_app.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
