"""OUTLINE and TIMELINE sections at the bottom of the primary sidebar."""

from datetime import datetime

from PyQt6.QtCore import QEvent, Qt
from PyQt6.QtWidgets import (
    QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QTreeWidget,
    QTreeWidgetItem, QVBoxLayout, QWidget,
)

from core.local_history import LocalHistory, timeline_label
from core.outline import OutlineSymbol, can_outline_file, extract_python_outline
from ui.theme import BG_SIDEBAR, FG_HEADER, FG_MUTED, FG_PRIMARY

_EMPTY_OUTLINE = "The active editor cannot provide outline information."
_EMPTY_TIMELINE = (
    "Local History will track recent changes as you save them unless the file "
    "has been excluded or is too large."
)

_KIND_ICONS = {
    "class": "◇",
    "function": "ƒ",
    "method": "ƒ",
}


class _CollapsibleSection(QWidget):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self._expanded = False
        self._title = title

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.header = QWidget()
        self.header.setCursor(Qt.CursorShape.PointingHandCursor)
        header_layout = QVBoxLayout(self.header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(0)

        title_row = QWidget()
        row = QHBoxLayout(title_row)
        row.setContentsMargins(12, 6, 12, 2)

        self.title_label = QLabel(f"▶ {title}")
        self.title_label.setStyleSheet(
            f"color: {FG_HEADER}; font-size: 11px; font-weight: 600; "
            f"letter-spacing: 0.5px;"
        )
        row.addWidget(self.title_label)
        row.addStretch()

        self.subtitle_label = QLabel("")
        self.subtitle_label.setStyleSheet(f"color: {FG_MUTED}; font-size: 11px;")
        self.subtitle_label.hide()
        row.addWidget(self.subtitle_label)

        header_layout.addWidget(title_row)
        layout.addWidget(self.header)

        self.body = QWidget()
        self.body_layout = QVBoxLayout(self.body)
        self.body_layout.setContentsMargins(12, 0, 12, 8)
        self.body_layout.setSpacing(4)
        self.body.setVisible(self._expanded)
        layout.addWidget(self.body)

        self.message = QLabel("")
        self.message.setWordWrap(True)
        self.message.setStyleSheet(f"color: {FG_MUTED}; font-size: 12px;")
        self.message.hide()
        self.body_layout.addWidget(self.message)

        self.header.installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj is self.header and event.type() == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.LeftButton:
                self.set_expanded(not self._expanded)
                return True
        return super().eventFilter(obj, event)

    def set_expanded(self, expanded: bool):
        self._expanded = expanded
        self.title_label.setText(
            f"{'▼' if expanded else '▶'} {self._title}"
        )
        self.body.setVisible(expanded)

    def set_subtitle(self, text: str):
        if text:
            self.subtitle_label.setText(text)
            self.subtitle_label.show()
        else:
            self.subtitle_label.hide()

    def show_message(self, text: str):
        self.message.setText(text)
        self.message.show()

    def hide_message(self):
        self.message.hide()


class OutlineSection(_CollapsibleSection):
    def __init__(self, main_window, parent=None):
        super().__init__("OUTLINE", parent)
        self.main_window = main_window

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(12)
        self.tree.setMaximumHeight(160)
        self.tree.setStyleSheet(f"""
            QTreeWidget {{
                background: {BG_SIDEBAR};
                border: none;
                color: {FG_PRIMARY};
                font-size: 12px;
            }}
            QTreeWidget::item {{
                height: 20px;
            }}
        """)
        self.tree.itemDoubleClicked.connect(self._go_to_symbol)
        self.body_layout.addWidget(self.tree)
        self.tree.hide()
        self.show_message(_EMPTY_OUTLINE)

    def refresh(self):
        self.tree.clear()
        editor = self.main_window.current_editor()
        if not editor or not can_outline_file(editor.file_path):
            self.tree.hide()
            self.show_message(_EMPTY_OUTLINE)
            return

        try:
            symbols = extract_python_outline(editor.toPlainText())
        except SyntaxError:
            self.tree.hide()
            self.show_message(_EMPTY_OUTLINE)
            return

        if not symbols:
            self.tree.hide()
            self.show_message(_EMPTY_OUTLINE)
            return

        self.hide_message()
        self.tree.show()
        class_nodes: dict[str, QTreeWidgetItem] = {}
        for sym in symbols:
            self._add_symbol(sym, class_nodes)

    def _add_symbol(self, sym: OutlineSymbol, class_nodes: dict):
        prefix = _KIND_ICONS.get(sym.kind, "•")
        label = f"{prefix} {sym.name}"
        if sym.parent and sym.parent in class_nodes:
            item = QTreeWidgetItem(class_nodes[sym.parent], [label])
        else:
            item = QTreeWidgetItem(self.tree, [label])
        item.setData(0, Qt.ItemDataRole.UserRole, sym.line)
        if sym.kind == "class":
            class_nodes[sym.name] = item

    def _go_to_symbol(self, item: QTreeWidgetItem):
        line = item.data(0, Qt.ItemDataRole.UserRole)
        if line is None:
            return
        editor = self.main_window.current_editor()
        if editor:
            editor.go_to_line(line)


class TimelineSection(_CollapsibleSection):
    def __init__(self, main_window, parent=None):
        super().__init__("TIMELINE", parent)
        self.main_window = main_window
        self._history = LocalHistory()

        self.list = QListWidget()
        self.list.setMaximumHeight(140)
        self.list.setStyleSheet(f"""
            QListWidget {{
                background: {BG_SIDEBAR};
                border: none;
                color: {FG_PRIMARY};
                font-size: 12px;
            }}
        """)
        self.list.itemDoubleClicked.connect(self._restore_entry)
        self.body_layout.addWidget(self.list)
        self.list.hide()
        self.show_message(_EMPTY_TIMELINE)

    def refresh(self):
        self.list.clear()
        editor = self.main_window.current_editor()
        path = editor.file_path if editor else None
        self.set_subtitle(timeline_label(path) if path else "")

        if not path:
            self.list.hide()
            self.show_message(_EMPTY_TIMELINE)
            return

        entries = self._history.list_entries(path)
        if not entries:
            self.list.hide()
            self.show_message(_EMPTY_TIMELINE)
            return

        self.hide_message()
        self.list.show()
        for entry in entries:
            ts = entry.get("timestamp", "")
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                when = dt.astimezone().strftime("%Y-%m-%d %H:%M")
            except ValueError:
                when = ts[:16] if ts else ""
            text = f"{entry.get('label', 'File Saved')}  ·  {when}"
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, entry.get("id"))
            self.list.addItem(item)

    def _restore_entry(self, item: QListWidgetItem):
        entry_id = item.data(Qt.ItemDataRole.UserRole)
        editor = self.main_window.current_editor()
        if not editor or not editor.file_path or not entry_id:
            return
        content = self._history.read_snapshot(editor.file_path, entry_id)
        if content is None:
            return
        editor.setText(content)
        editor.document().setModified(True)
        self.main_window.update_tab_title(editor)
        self.main_window.side_bar.footer.outline.refresh()


class SidebarFooter(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.setObjectName("SidebarFooter")
        self.setStyleSheet(
            f"background: {BG_SIDEBAR}; border-top: 1px solid #1e1e1e;"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(0)

        self.outline = OutlineSection(main_window)
        self.timeline = TimelineSection(main_window)
        layout.addWidget(self.outline)
        layout.addWidget(self.timeline)

    def refresh(self):
        self.outline.refresh()
        self.timeline.refresh()
