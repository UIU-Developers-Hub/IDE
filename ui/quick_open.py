import os

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QVBoxLayout
from qfluentwidgets import CaptionLabel, ListWidget, SearchLineEdit


class QuickOpenDialog(QDialog):
    """Ctrl+P fuzzy file picker for the project."""

    def __init__(self, root_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Quick Open")
        self.setMinimumWidth(540)
        self._root = root_path
        self._files = self._collect_files(root_path)
        self._selected_path = None

        layout = QVBoxLayout(self)
        hint = CaptionLabel("Type to filter · Enter to open · Esc to cancel")
        layout.addWidget(hint)

        self.input = SearchLineEdit()
        self.input.setPlaceholderText("Search files by name...")
        self.input.textChanged.connect(self._filter)
        self.input.returnPressed.connect(self._accept_current)
        layout.addWidget(self.input)

        self.list = ListWidget()
        self.list.itemDoubleClicked.connect(self._accept_item)
        self.list.itemActivated.connect(self._accept_item)
        layout.addWidget(self.list)

        self._populate(self._files)
        self.input.setFocus()

    def _collect_files(self, root):
        skip = {".git", "__pycache__", "venv", ".venv", "myenv", "newenv", "node_modules"}
        results = []
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in skip and not d.startswith(".")]
            for name in filenames:
                if name.startswith("."):
                    continue
                full = os.path.join(dirpath, name)
                rel = os.path.relpath(full, root)
                results.append((rel.replace("\\", "/"), full))
        return sorted(results, key=lambda x: x[0].lower())

    def _populate(self, files):
        self.list.clear()
        for rel, full in files[:200]:
            self.list.addItem(rel)
            item = self.list.item(self.list.count() - 1)
            item.setData(Qt.ItemDataRole.UserRole, full)
        if self.list.count():
            self.list.setCurrentRow(0)

    def _filter(self, text):
        needle = text.lower().strip()
        if not needle:
            filtered = self._files
        else:
            filtered = [
                (rel, full) for rel, full in self._files
                if all(part in rel.lower() for part in needle.split())
            ]
        self._populate(filtered)

    def _accept_current(self):
        item = self.list.currentItem()
        if item:
            self._accept_item(item)

    def _accept_item(self, item):
        self._selected_path = item.data(Qt.ItemDataRole.UserRole)
        self.accept()

    def selected_path(self):
        return self._selected_path
