"""Shared Qt application instance for tests."""

from PyQt6.QtWidgets import QApplication

_app = None


def get_qt_app():
    global _app
    if _app is None:
        _app = QApplication.instance() or QApplication(["PyDitor-Tests"])
    return _app


get_qt_app()
