import os
import sys

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplication

from ui.main_window import AICompilerMainWindow
from ui.theme import apply_fluent_theme, apply_theme


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("PyDitor")
    ui_font = QFont("Segoe UI", 9)
    if not ui_font.exactMatch():
        ui_font = QFont("Segoe UI", 9)
    app.setFont(ui_font)
    apply_fluent_theme()
    apply_theme(app)

    window = AICompilerMainWindow()
    window.show()
    exit_code = app.exec()

    # Qt/QScintilla on Windows can crash during native DLL teardown (0xC0000409).
    if sys.platform == "win32":
        os._exit(exit_code)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
