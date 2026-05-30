import os

from PyQt6.QtCore import Qt, QDir, QSortFilterProxyModel
from PyQt6.QtGui import QAction, QFileSystemModel
from PyQt6.QtWidgets import (
    QHBoxLayout, QLabel, QMenu, QTreeView, QVBoxLayout, QWidget,
)
from qfluentwidgets import SearchLineEdit, TransparentToolButton, FluentIcon

from ui.theme import BG_SIDEBAR, FG_HEADER


class ExplorerPanel(QWidget):
    """VS Code Explorer view — names only, no size/type columns."""

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self._root = os.getcwd()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QWidget()
        header.setStyleSheet(f"background: {BG_SIDEBAR};")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(12, 10, 8, 6)
        header_layout.setSpacing(6)

        title_row = QWidget()
        row = QHBoxLayout(title_row)
        row.setContentsMargins(0, 0, 0, 0)
        title = QLabel("EXPLORER")
        title.setStyleSheet(
            f"color: {FG_HEADER}; font-size: 11px; font-weight: 600; letter-spacing: 0.5px;"
        )
        refresh_btn = TransparentToolButton(FluentIcon.SYNC)
        refresh_btn.setFixedSize(22, 22)
        refresh_btn.setToolTip("Refresh Explorer")
        refresh_btn.clicked.connect(self.refresh)
        row.addWidget(title)
        row.addStretch()
        row.addWidget(refresh_btn)
        header_layout.addWidget(title_row)

        self.filter_input = SearchLineEdit()
        self.filter_input.setPlaceholderText("Filter files...")
        self.filter_input.setClearButtonEnabled(True)
        self.filter_input.textChanged.connect(self._apply_filter)
        header_layout.addWidget(self.filter_input)
        layout.addWidget(header)

        self.file_model = QFileSystemModel()
        self.file_model.setRootPath("")
        self.file_model.setFilter(
            QDir.Filter.AllDirs | QDir.Filter.Files | QDir.Filter.NoDotAndDotDot
        )

        self.proxy = QSortFilterProxyModel()
        self.proxy.setSourceModel(self.file_model)
        self.proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.proxy.setFilterKeyColumn(0)

        self.tree = QTreeView()
        self.tree.setModel(self.proxy)
        self.tree.setRootIndex(self.proxy.mapFromSource(self.file_model.index(self._root)))
        self.tree.setHeaderHidden(True)
        self.tree.setAnimated(True)
        self.tree.setIndentation(14)
        self.tree.setIconSize(self.tree.iconSize())
        self.tree.setUniformRowHeights(True)
        self.tree.setTextElideMode(Qt.TextElideMode.ElideMiddle)
        self.tree.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tree.setStyleSheet(f"""
            QTreeView {{
                background: {BG_SIDEBAR};
                border: none;
                padding: 4px 0;
            }}
            QTreeView::item {{
                height: 22px;
                padding: 0 8px;
            }}
        """)
        self.tree.clicked.connect(main_window.open_file_from_explorer)
        self.tree.doubleClicked.connect(main_window.open_file_from_explorer)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self.tree, 1)

        for col in range(1, self.file_model.columnCount()):
            self.tree.setColumnHidden(col, True)

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
        self.file_model.setRootPath(path)
        source_index = self.file_model.index(path)
        self.tree.setRootIndex(self.proxy.mapFromSource(source_index))

    def refresh(self):
        path = self._root
        self.file_model.setRootPath("")
        self.file_model.setRootPath(path)
        self.tree.setRootIndex(
            self.proxy.mapFromSource(self.file_model.index(path))
        )

    def _apply_filter(self, text):
        self.proxy.setFilterFixedString(text)

    def index_to_path(self, proxy_index):
        source_index = self.proxy.mapToSource(proxy_index)
        return self.file_model.filePath(source_index)
