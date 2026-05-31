from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QStackedWidget, QVBoxLayout, QWidget, QSizePolicy

from ui.activity_bar import ActivityBar
from ui.explorer_panel import ExplorerPanel
from ui.run_panel import RunPanel
from ui.search_panel import SearchPanel
from ui.settings_panel import SettingsPanel
from ui.sidebar_footer import SidebarFooter
from ui.sidebar_view_bar import SidebarViewBar
from ui.source_control_panel import SourceControlPanel
from ui.theme import BG_SIDEBAR, SIDEBAR_MAX_WIDTH, SIDEBAR_MIN_WIDTH, SIDEBAR_WIDTH


class SideBar(QWidget):
    """VS Code primary sidebar — icon view bar, panel stack, explorer footer."""

    view_changed = pyqtSignal(int)

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setMinimumWidth(SIDEBAR_MIN_WIDTH)
        self.setMaximumWidth(SIDEBAR_MAX_WIDTH)
        self.resize(SIDEBAR_WIDTH, self.height())
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        self.setStyleSheet(f"background: {BG_SIDEBAR}; border-right: 1px solid #1e1e1e;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.view_bar = SidebarViewBar()
        self.view_bar.view_changed.connect(self._on_view_bar)
        layout.addWidget(self.view_bar)

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
            self.stack.addWidget(panel)

        layout.addWidget(self.stack, 1)

        self.footer = SidebarFooter(main_window)
        layout.addWidget(self.footer)

        self._last_index = ActivityBar.EXPLORER
        self.show_view(ActivityBar.EXPLORER)

    def _on_view_bar(self, index):
        self._last_index = index
        self.show_view(index)
        self.view_changed.emit(index)

    def show_view(self, index):
        if 0 <= index < self.stack.count():
            self.stack.setCurrentIndex(index)
            self._last_index = index
            self.view_bar.set_active(index)
            self.footer.setVisible(index == ActivityBar.EXPLORER)
            if index == ActivityBar.SOURCE_CONTROL:
                self.source_control_panel.refresh()

    def set_active_view(self, index):
        self.show_view(index)

    def active_index(self):
        return self._last_index

    def set_root(self, path):
        self.explorer_panel.set_root(path)
        self.search_panel.set_root(path)
        self.source_control_panel.set_root(path)
