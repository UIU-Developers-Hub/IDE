from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QStackedWidget, QVBoxLayout, QWidget, QSizePolicy

from ui.activity_bar import ActivityBar
from ui.explorer_panel import ExplorerPanel
from ui.run_panel import RunPanel
from ui.search_panel import SearchPanel
from ui.settings_panel import SettingsPanel
from ui.source_control_panel import SourceControlPanel
from ui.theme import BG_SIDEBAR, SIDEBAR_WIDTH


class SideBar(QWidget):
    """VS Code primary sidebar — stacked views."""

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setFixedWidth(SIDEBAR_WIDTH)
        self.setMinimumWidth(SIDEBAR_WIDTH)
        self.setMaximumWidth(SIDEBAR_WIDTH)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self.setStyleSheet(f"background: {BG_SIDEBAR}; border-right: 1px solid #1e1e1e;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.stack = QStackedWidget()
        self.explorer_panel = ExplorerPanel(main_window)
        self.search_panel = SearchPanel(main_window)
        self.source_control_panel = SourceControlPanel(main_window)
        self.run_panel = RunPanel(main_window)
        self.settings_panel = SettingsPanel(main_window)

        for panel in (
            self.explorer_panel,
            self.search_panel,
            self.source_control_panel,
            self.run_panel,
            self.settings_panel,
        ):
            panel.setMaximumWidth(SIDEBAR_WIDTH)
            self.stack.addWidget(panel)

        layout.addWidget(self.stack)

    def show_view(self, index):
        if 0 <= index < self.stack.count():
            self.stack.setCurrentIndex(index)
            if index == ActivityBar.SOURCE_CONTROL:
                self.source_control_panel.refresh()

    def set_root(self, path):
        self.explorer_panel.set_root(path)
        self.search_panel.set_root(path)
        self.source_control_panel.set_root(path)
