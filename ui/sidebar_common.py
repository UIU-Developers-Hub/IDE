"""Shared sidebar layout helpers."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QStyledItemDelegate, QWidget, QVBoxLayout

SIDEBAR_PAD = 12


class ElideMiddleDelegate(QStyledItemDelegate):
    """Truncate long paths in sidebar lists (VS Code style)."""

    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        option.textElideMode = Qt.TextElideMode.ElideMiddle


def sidebar_margins(layout: QVBoxLayout):
    layout.setContentsMargins(SIDEBAR_PAD, 8, SIDEBAR_PAD, 8)
    layout.setSpacing(8)
