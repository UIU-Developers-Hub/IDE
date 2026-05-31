import os

from PyQt6.QtCore import Qt, QDir, QSortFilterProxyModel
from PyQt6.QtGui import QAction, QFileSystemModel
from PyQt6.QtWidgets import (
    QHBoxLayout, QLabel, QMenu, QTreeView, QVBoxLayout, QWidget,
)
from qfluentwidgets import TransparentToolButton, FluentIcon

from ui.explorer_delegate import ExplorerItemDelegate
from ui.sidebar_section import SidebarSectionHeader
from ui.theme import BG_SIDEBAR, FG_HEADER


class ExplorerPanel(QWidget):
    """VS Code Explorer — section header, workspace tree, fills sidebar."""

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self._root = os.getcwd()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header_row = QWidget()
        header_layout = QHBoxLayout(header_row)
        header_layout.setContentsMargins(12, 10, 8, 4)

        title = QLabel("EXPLORER")
        title.setStyleSheet(
            f"color: {FG_HEADER}; font-size: 11px; font-weight: 600; "
            f"letter-spacing: 0.6px;"
        )
        header_layout.addWidget(title)
        header_layout.addStretch()

        refresh_btn = TransparentToolButton(FluentIcon.SYNC)
        refresh_btn.setFixedSize(22, 22)
        refresh_btn.setToolTip("Refresh Explorer")
        refresh_btn.clicked.connect(self.refresh)
        header_layout.addWidget(refresh_btn)
        layout.addWidget(header_row)

        self.workspace_header = SidebarSectionHeader()
        self.workspace_header.set_title(self._root)
        self.workspace_header.toggled.connect(self._on_workspace_toggle)
        layout.addWidget(self.workspace_header)

        self.tree = QTreeView()
        self.file_model = QFileSystemModel()
        self.file_model.setRootPath("")
        self.file_model.setFilter(
            QDir.Filter.AllDirs | QDir.Filter.Files | QDir.Filter.NoDotAndDotDot
        )

        self.proxy = QSortFilterProxyModel()
        self.proxy.setSourceModel(self.file_model)
        self.proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.proxy.setFilterKeyColumn(0)

        self.tree.setModel(self.proxy)
        self._apply_tree_root(self._root)
        self.tree.setHeaderHidden(True)
        self.tree.setAnimated(True)
        self.tree.setIndentation(14)
        self.tree.setUniformRowHeights(True)
        self.tree.setTextElideMode(Qt.TextElideMode.ElideMiddle)
        self.tree.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tree.setItemDelegate(
            ExplorerItemDelegate(self.proxy, self.file_model, self.tree)
        )
        self.tree.setStyleSheet(f"""
            QTreeView {{
                background: {BG_SIDEBAR};
                border: none;
                padding: 0 0 4px 0;
            }}
            QTreeView::item {{
                height: 22px;
                padding: 0 4px 0 0;
            }}
        """)
        self.tree.clicked.connect(main_window.open_file_from_explorer)
        self.tree.doubleClicked.connect(main_window.open_file_from_explorer)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self.tree, 1)

        for col in range(1, self.file_model.columnCount()):
            self.tree.setColumnHidden(col, True)

    def _apply_tree_root(self, path):
        self.file_model.setRootPath(path)
        source_index = self.file_model.index(path)
        self.tree.setRootIndex(self.proxy.mapFromSource(source_index))

    def _on_workspace_toggle(self, expanded):
        self.tree.setVisible(expanded)

    def _show_context_menu(self, pos):
        index = self.tree.indexAt(pos)
        path = self.index_to_path(index) if index.isValid() else self._root
        is_file = os.path.isfile(path) if path else False

        menu = QMenu(self)
        if is_file:
            open_action = QAction("Open", self)
            open_action.triggered.connect(lambda: self.main_window._open_file_path(path))
            menu.addAction(open_action)
            menu.addSeparator()

        new_file = QAction("New File", self)
        new_file.triggered.connect(self.main_window.add_new_tab)
        menu.addAction(new_file)

        new_folder = QAction("New Folder", self)
        new_folder.triggered.connect(self.main_window.create_new_folder)
        menu.addAction(new_folder)

        refresh = QAction("Refresh", self)
        refresh.triggered.connect(self.refresh)
        menu.addAction(refresh)

        menu.exec(self.tree.viewport().mapToGlobal(pos))

    def set_root(self, path):
        self._root = path
        self.workspace_header.set_title(path)
        self._apply_tree_root(path)

    def refresh(self):
        path = self._root
        self.file_model.setRootPath("")
        self._apply_tree_root(path)

    def index_to_path(self, proxy_index):
        source_index = self.proxy.mapToSource(proxy_index)
        return self.file_model.filePath(source_index)
