"""Collapsible section header (workspace folder, etc.)."""

import os

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QWidget

from ui.theme import FG_HEADER, FG_PRIMARY


class SidebarSectionHeader(QWidget):
    """VS Code workspace folder row: chevron + uppercase project name."""

    toggled = pyqtSignal(bool)

    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self._expanded = True
        self._title = title

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 2)
        layout.setSpacing(4)

        self.chevron = QLabel("▼")
        self.chevron.setFixedWidth(12)
        self.chevron.setStyleSheet(f"color: {FG_HEADER}; font-size: 10px;")
        layout.addWidget(self.chevron)

        self.title = QLabel(title)
        self.title.setStyleSheet(
            f"color: {FG_PRIMARY}; font-size: 11px; font-weight: 600; "
            f"letter-spacing: 0.5px;"
        )
        layout.addWidget(self.title, 1)

        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_title(self, path: str):
        name = os.path.basename(path.rstrip("/\\")) or path
        self._title = name.upper()
        self.title.setText(self._title)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._expanded = not self._expanded
            self.chevron.setText("▼" if self._expanded else "▶")
            self.toggled.emit(self._expanded)
        super().mousePressEvent(event)

    def is_expanded(self):
        return self._expanded
