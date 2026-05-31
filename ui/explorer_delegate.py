"""File tree icons — VS Code / Material-style folder and file colors."""

import os

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QStyledItemDelegate

_FOLDER_ICONS = {
    "__pycache__": "fa5s.folder",
    ".vscode": "fa5s.folder",
    "core": "fa5s.microchip",
    "data": "fa5s.database",
    "tests": "fa5s.vial",
    "ui": "fa5s.window-maximize",
}

_FOLDER_COLORS = {
    "__pycache__": "#519aba",
    ".vscode": "#519aba",
    "core": "#519aba",
    "data": "#dcc154",
    "tests": "#4ec9b0",
    "ui": "#c586c0",
}

_FILE_ICONS = {
    ".gitignore": ("fa5s.git-alt", "#e37933"),
    "license": ("fa5s.certificate", "#e37933"),
    "readme.md": ("fa5s.info-circle", "#519aba"),
    "requirements.txt": ("fa5s.list", "#519aba"),
    "main.py": ("fa5s.file-code", "#519aba"),
    "main.spec": ("fa5s.file", "#cccccc"),
}


class ExplorerItemDelegate(QStyledItemDelegate):
    def __init__(self, proxy_model, file_model, parent=None):
        super().__init__(parent)
        self._proxy = proxy_model
        self._file_model = file_model

    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        option.textElideMode = Qt.TextElideMode.ElideMiddle
        if not index.isValid():
            return
        source_index = self._proxy.mapToSource(index)
        if not source_index.isValid():
            return
        path = self._file_model.filePath(source_index)
        name = os.path.basename(path)
        key = name.lower()
        try:
            import qtawesome as qta
            if self._file_model.isDir(source_index):
                fa = _FOLDER_ICONS.get(name)
                if fa:
                    color = _FOLDER_COLORS.get(name, "#519aba")
                    option.icon = qta.icon(fa, color=color)
            else:
                spec = _FILE_ICONS.get(key)
                if spec:
                    fa, color = spec
                    option.icon = qta.icon(fa, color=color)
        except Exception:
            pass
