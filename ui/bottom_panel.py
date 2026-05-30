from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout, QStackedWidget, QToolButton, QVBoxLayout, QWidget,
)

from ui.theme import BG_PANEL, BORDER, FG_MUTED, FG_PRIMARY, PANEL_HEADER_BG


class BottomPanel(QWidget):
    """VS Code–style bottom panel with tab strip and actions."""

    tab_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tabs = []
        self._buttons = []
        self._visible = True
        self._clear_callback = None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        header = QWidget()
        header.setFixedHeight(36)
        header.setStyleSheet(f"background: {PANEL_HEADER_BG}; border-top: 1px solid {BORDER};")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(8, 0, 4, 0)
        header_layout.setSpacing(0)

        self._tab_bar = QWidget()
        self._tab_layout = QHBoxLayout(self._tab_bar)
        self._tab_layout.setContentsMargins(0, 0, 0, 0)
        self._tab_layout.setSpacing(0)
        header_layout.addWidget(self._tab_bar)
        header_layout.addStretch()

        self._action_bar = QWidget()
        action_layout = QHBoxLayout(self._action_bar)
        action_layout.setContentsMargins(0, 0, 0, 0)
        action_layout.setSpacing(0)

        self._clear_btn = QToolButton()
        self._clear_btn.setText("Clear")
        self._clear_btn.setToolTip("Clear panel output")
        self._clear_btn.setStyleSheet(self._action_style())
        self._clear_btn.clicked.connect(self._on_clear)
        action_layout.addWidget(self._clear_btn)

        self._close_btn = QToolButton()
        self._close_btn.setText("✕")
        self._close_btn.setToolTip("Hide Panel (Ctrl+J)")
        self._close_btn.setFixedWidth(32)
        self._close_btn.setStyleSheet(self._action_style())
        action_layout.addWidget(self._close_btn)

        header_layout.addWidget(self._action_bar)
        root.addWidget(header)

        self.stack = QStackedWidget()
        self.stack.setStyleSheet(f"background: {BG_PANEL};")
        root.addWidget(self.stack)

    @staticmethod
    def _action_style():
        return f"""
            QToolButton {{
                background: transparent;
                color: {FG_MUTED};
                border: none;
                padding: 6px 10px;
                font-size: 11px;
            }}
            QToolButton:hover {{
                color: {FG_PRIMARY};
                background: #2a2d2e;
            }}
        """

    def _tab_style(self, active=False):
        color = FG_PRIMARY if active else FG_MUTED
        border = "border-top: 2px solid #007acc;" if active else "border-top: 2px solid transparent;"
        return f"""
            QToolButton {{
                background: transparent;
                color: {color};
                border: none;
                {border}
                padding: 8px 14px;
                font-size: 11px;
                font-weight: {'600' if active else '400'};
            }}
            QToolButton:hover {{
                color: {FG_PRIMARY};
            }}
        """

    def _on_clear(self):
        if self._clear_callback:
            self._clear_callback()

    def add_tab(self, widget, title, on_clear=None):
        index = self.stack.addWidget(widget)
        self._tabs.append(title)

        btn = QToolButton()
        btn.setText(title.upper())
        btn.setCheckable(True)
        btn.setAutoExclusive(True)
        btn.setStyleSheet(self._tab_style(index == 0))
        btn.clicked.connect(lambda checked, i=index: self.set_current_index(i))
        self._tab_layout.addWidget(btn)
        self._buttons.append(btn)

        if index == 0:
            btn.setChecked(True)

        if on_clear is not None:
            self._clear_callback = on_clear

        return index

    def set_clear_callback(self, callback):
        self._clear_callback = callback

    def set_current_index(self, index):
        if 0 <= index < self.stack.count():
            self.stack.setCurrentIndex(index)
            for i, btn in enumerate(self._buttons):
                btn.setChecked(i == index)
                btn.setStyleSheet(self._tab_style(i == index))
            self.tab_changed.emit(index)

    def current_index(self):
        return self.stack.currentIndex()

    def index_of(self, widget):
        return self.stack.indexOf(widget)

    def set_panel_visible(self, visible):
        self._visible = visible
        self.setVisible(visible)

    def is_panel_visible(self):
        return self._visible

    def connect_close(self, callback):
        self._close_btn.clicked.connect(callback)
