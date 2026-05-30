from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHBoxLayout, QTabWidget, QVBoxLayout, QWidget
from qfluentwidgets import CaptionLabel, PushButton, TransparentToolButton, FluentIcon


class TerminalPanel(QWidget):
    """Bottom-panel terminal tabs — like VS Code integrated terminal."""

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self._counter = 0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(8, 4, 8, 4)
        title = CaptionLabel("TERMINAL")
        title.setStyleSheet("font-weight: bold; letter-spacing: 0.5px;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        new_btn = TransparentToolButton(FluentIcon.ADD)
        new_btn.setToolTip("New Terminal")
        new_btn.setFixedSize(24, 24)
        new_btn.clicked.connect(self.new_terminal)
        header_layout.addWidget(new_btn)

        kill_btn = PushButton("Kill")
        kill_btn.setFixedHeight(24)
        kill_btn.clicked.connect(self.kill_current)
        header_layout.addWidget(kill_btn)

        layout.addWidget(header)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self._close_terminal)
        layout.addWidget(self.tabs)

    def _ensure_terminal(self):
        if self.tabs.count() == 0:
            self.new_terminal(start=False)

    def new_terminal(self, cwd=None, *, start=True):
        from ui.terminal_widget import TerminalWidget

        cwd = cwd or self.main_window._project_root
        self._counter += 1
        term = TerminalWidget(cwd)
        index = self.tabs.addTab(term, f"Terminal {self._counter}")
        self.tabs.setCurrentIndex(index)
        if start:
            term.start()
        return term

    def start_current(self):
        widget = self.tabs.currentWidget()
        if widget:
            widget.start()

    def kill_current(self):
        widget = self.tabs.currentWidget()
        if widget:
            widget.kill()

    def clear_current(self):
        widget = self.tabs.currentWidget()
        if widget:
            widget.clear()

    def _close_terminal(self, index):
        widget = self.tabs.widget(index)
        if widget:
            widget.kill()
        self.tabs.removeTab(index)
        if self.tabs.count() == 0:
            self.new_terminal(start=False)

    def set_project_root(self, path):
        for i in range(self.tabs.count()):
            widget = self.tabs.widget(i)
            if widget:
                widget.set_cwd(path)

    def shutdown_all(self):
        for i in range(self.tabs.count() - 1, -1, -1):
            widget = self.tabs.widget(i)
            if widget:
                widget.stop(shutdown=True)
                self.tabs.removeTab(i)

    def kill_all(self):
        for i in range(self.tabs.count() - 1, -1, -1):
            widget = self.tabs.widget(i)
            if widget:
                widget.stop(force=True)
                self.tabs.removeTab(i)
