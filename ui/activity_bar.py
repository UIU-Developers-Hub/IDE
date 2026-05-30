from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtWidgets import QToolButton, QVBoxLayout, QWidget, QSizePolicy

from ui.icons_util import icon
from ui.theme import ACTIVITY_BAR_BG, ACTIVITY_BAR_FG, ACTIVITY_BAR_ACTIVE, ACTIVITY_BAR_WIDTH


class ActivityBar(QWidget):
    """VS Code–style vertical icon rail (fixed width, not resizable)."""

    view_changed = pyqtSignal(int)

    EXPLORER = 0
    SEARCH = 1
    SOURCE_CONTROL = 2
    RUN = 3
    SETTINGS = 4

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ActivityBar")
        self.setFixedWidth(ACTIVITY_BAR_WIDTH)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self._buttons = []
        self._active = self.EXPLORER

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(2)

        for index, (name, icon_name, tip) in enumerate((
            ("explorer", "explorer", "Explorer (Ctrl+Shift+E)"),
            ("search", "find", "Search (Ctrl+Shift+F)"),
            ("scm", "git", "Source Control (Ctrl+Shift+G)"),
            ("run", "run", "Run and Debug"),
            ("settings", "settings", "Settings"),
        )):
            btn = QToolButton()
            btn.setCheckable(True)
            btn.setAutoExclusive(False)
            btn.setIcon(icon(icon_name, ACTIVITY_BAR_FG))
            btn.setIconSize(QSize(22, 22))
            btn.setToolTip(tip)
            btn.setFixedSize(ACTIVITY_BAR_WIDTH, ACTIVITY_BAR_WIDTH)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, i=index: self._on_click(i))
            layout.addWidget(btn, 0, Qt.AlignmentFlag.AlignHCenter)
            self._buttons.append(btn)

        layout.addStretch()
        self._buttons[self.EXPLORER].setChecked(True)
        self._apply_style()

    def _apply_style(self):
        self.setStyleSheet(f"""
            #ActivityBar {{
                background: {ACTIVITY_BAR_BG};
                border-right: 1px solid #252526;
            }}
            #ActivityBar QToolButton {{
                background: transparent;
                border: none;
                border-left: 2px solid transparent;
                border-radius: 0;
                padding: 10px;
            }}
            #ActivityBar QToolButton:hover {{
                color: {ACTIVITY_BAR_ACTIVE};
            }}
            #ActivityBar QToolButton:checked {{
                border-left: 2px solid {ACTIVITY_BAR_ACTIVE};
            }}
        """)

    def _on_click(self, index):
        self.view_changed.emit(index)

    def set_active(self, index):
        self._active = index
        for i, btn in enumerate(self._buttons):
            btn.setChecked(i == index)

    def active_index(self):
        return self._active
