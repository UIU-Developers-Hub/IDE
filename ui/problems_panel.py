from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QVBoxLayout, QWidget

from ui.theme import ERROR, WARNING


class ProblemsPanel(QWidget):
    """VS Code Problems list — double-click jumps to line."""

    issue_activated = pyqtSignal(int, str)

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.list = QListWidget()
        self.list.itemDoubleClicked.connect(self._on_activate)
        layout.addWidget(self.list)

    def update_issues(self, lint_data):
        self.list.clear()
        if not lint_data:
            return

        for item in lint_data:
            line = item["line"]
            message = item["message"]
            code = message.split()[0] if message else ""
            is_error = code.startswith("E") or code.startswith("F")
            color = ERROR if is_error else WARNING

            text = f"Ln {line}, Col 1  {message}"
            list_item = QListWidgetItem(text)
            list_item.setData(Qt.ItemDataRole.UserRole, line)
            list_item.setForeground(QColor(color))
            self.list.addItem(list_item)

    def _on_activate(self, item):
        line = item.data(Qt.ItemDataRole.UserRole)
        self.issue_activated.emit(line, item.text())
