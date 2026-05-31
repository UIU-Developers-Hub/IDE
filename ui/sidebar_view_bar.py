"""Horizontal view switcher at the top of the primary sidebar (VS Code style)."""

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QToolButton, QWidget

from ui.activity_bar import ActivityBar
from ui.icons_util import icon
from ui.theme import BG_SIDEBAR, FG_MUTED, FG_PRIMARY


class SidebarViewBar(QWidget):
    view_changed = pyqtSignal(int)

    _BAR_VIEWS = (
        (ActivityBar.EXPLORER, "explorer", "Explorer (Ctrl+Shift+E)"),
        (ActivityBar.SEARCH, "find", "Search (Ctrl+Shift+F)"),
        (ActivityBar.SOURCE_CONTROL, "git", "Source Control (Ctrl+Shift+G)"),
        (ActivityBar.RUN, "run", "Run and Debug (Ctrl+Shift+D)"),
        (ActivityBar.SETTINGS, "settings", "Settings"),
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SidebarViewBar")
        self._buttons = []
        self._active = ActivityBar.EXPLORER

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(4)

        for index, icon_name, tip in self._BAR_VIEWS:
            btn = QToolButton()
            btn.setCheckable(True)
            btn.setAutoExclusive(True)
            btn.setIcon(icon(icon_name, FG_MUTED))
            btn.setIconSize(QSize(20, 20))
            btn.setToolTip(tip)
            btn.setFixedSize(32, 32)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _checked, i=index: self._select(i))
            layout.addWidget(btn)
            self._buttons.append((index, btn, icon_name))

        layout.addStretch()
        self._apply_style()
        self.set_active(ActivityBar.EXPLORER)

    def _apply_style(self):
        self.setStyleSheet(f"""
            #SidebarViewBar {{
                background: {BG_SIDEBAR};
                border-bottom: 1px solid #1e1e1e;
            }}
            #SidebarViewBar QToolButton {{
                background: transparent;
                border: none;
                border-radius: 6px;
                padding: 4px;
            }}
            #SidebarViewBar QToolButton:hover {{
                background: #2a2d2e;
            }}
            #SidebarViewBar QToolButton:checked {{
                background: #37373d;
            }}
        """)

    def _select(self, index):
        self.set_active(index)
        self.view_changed.emit(index)

    def set_active(self, index):
        self._active = index
        for idx, btn, icon_name in self._buttons:
            active = idx == index
            btn.setChecked(active)
            color = FG_PRIMARY if active else FG_MUTED
            btn.setIcon(icon(icon_name, color))

    def active_index(self):
        return self._active
