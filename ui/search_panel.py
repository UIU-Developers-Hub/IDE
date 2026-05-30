import os

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QVBoxLayout, QWidget
from qfluentwidgets import CaptionLabel, ListWidget, SearchLineEdit

from ui.sidebar_common import ElideMiddleDelegate, SIDEBAR_PAD
from ui.theme import BG_SIDEBAR


class SearchPanel(QWidget):
    """Sidebar search — find text in project files."""

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self._root = main_window._project_root

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SIDEBAR_PAD, 8, SIDEBAR_PAD, 8)
        layout.setSpacing(8)

        header = CaptionLabel("SEARCH")
        header.setStyleSheet("font-weight: bold; letter-spacing: 1px;")
        layout.addWidget(header)

        self.query = SearchLineEdit()
        self.query.setPlaceholderText("Search in files...")
        self.query.setClearButtonEnabled(True)
        self.query.returnPressed.connect(self._run_search)
        layout.addWidget(self.query)

        self.results = ListWidget()
        self.results.setItemDelegate(ElideMiddleDelegate(self.results))
        self.results.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.results.itemDoubleClicked.connect(self._open_result)
        self.results.setStyleSheet(f"background: {BG_SIDEBAR}; border: none;")
        layout.addWidget(self.results, 1)

    def set_root(self, path):
        self._root = path

    def _run_search(self):
        needle = self.query.text().strip().lower()
        self.results.clear()
        if not needle or not os.path.isdir(self._root):
            return

        skip = {".git", "__pycache__", "venv", ".venv", "node_modules", "myenv", "newenv"}
        matches = []
        for dirpath, dirnames, filenames in os.walk(self._root):
            dirnames[:] = [d for d in dirnames if d not in skip and not d.startswith(".")]
            for name in filenames:
                if not name.endswith((".py", ".txt", ".md", ".json", ".toml", ".cfg")):
                    continue
                full = os.path.join(dirpath, name)
                try:
                    with open(full, encoding="utf-8", errors="ignore") as handle:
                        for num, line in enumerate(handle, start=1):
                            if needle in line.lower():
                                rel = os.path.relpath(full, self._root).replace("\\", "/")
                                matches.append((full, num, line.strip()))
                                text = f"{rel}:{num}: {line.strip()[:60]}"
                                self.results.addItem(text)
                                item = self.results.item(self.results.count() - 1)
                                item.setToolTip(f"{rel}:{num}")
                                item.setData(Qt.ItemDataRole.UserRole, (full, num))
                                if len(matches) >= 100:
                                    return
                except OSError:
                    continue

    def _open_result(self, item):
        data = item.data(Qt.ItemDataRole.UserRole)
        if not data:
            return
        path, line = data
        self.main_window._open_file_path(path)
        editor = self.main_window.current_editor()
        if editor:
            editor.go_to_line(line)
