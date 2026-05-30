import os

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QVBoxLayout
from qfluentwidgets import CaptionLabel, ListWidget, SearchLineEdit

from ui.activity_bar import ActivityBar


class CommandPalette(QDialog):
    """VS Code Command Palette (Ctrl+Shift+P)."""

    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        self.setWindowTitle("Command Palette")
        self.setMinimumWidth(560)
        self._commands = self._build_commands()
        self._selected = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        hint = CaptionLabel("Type a command name · Enter to run · Esc to cancel")
        layout.addWidget(hint)

        self.input = SearchLineEdit()
        self.input.setPlaceholderText("> Type a command...")
        self.input.textChanged.connect(self._filter)
        self.input.returnPressed.connect(self._run_current)
        layout.addWidget(self.input)

        self.list = ListWidget()
        self.list.itemDoubleClicked.connect(self._run_item)
        self.list.itemActivated.connect(self._run_item)
        layout.addWidget(self.list)

        self._populate(self._commands)
        self.input.setFocus()

    def _build_commands(self):
        mw = self.main_window
        return [
            ("New File", "Ctrl+N", mw.add_new_tab),
            ("Open File", "Ctrl+O", mw.open_file),
            ("Quick Open", "Ctrl+P", mw.show_quick_open),
            ("Save", "Ctrl+S", mw.save_file),
            ("Save As", "Ctrl+Shift+S", mw.save_file_as),
            ("Open Folder", "Ctrl+Shift+O", mw.open_folder),
            ("Close Editor", "Ctrl+W", mw.close_current_tab),
            ("Find", "Ctrl+F", mw.show_find_dialog),
            ("Replace", "Ctrl+H", mw.show_replace_dialog),
            ("Go to Line", "Ctrl+G", mw.show_go_to_line),
            ("Toggle Comment", "Ctrl+/", mw.toggle_comment),
            ("Format Document", "Shift+Alt+F", mw.format_document),
            ("Organize Imports", "Ctrl+Alt+I", mw.organize_imports),
            ("Run Python File", "F5", mw.run_code),
            ("Stop", "Shift+F5", mw.stop_execution),
            ("Run Buffer", "Ctrl+T", mw.run_tests),
            ("Start Debugging", "Ctrl+Shift+D", mw.start_debugger),
            ("Show Explorer", "Ctrl+Shift+E", lambda: mw._show_activity(ActivityBar.EXPLORER)),
            ("Show Search", "Ctrl+Shift+F", lambda: mw._show_activity(ActivityBar.SEARCH)),
            ("Show Source Control", "Ctrl+Shift+G", lambda: mw._show_activity(ActivityBar.SOURCE_CONTROL)),
            ("Show Run and Debug", None, lambda: mw._show_activity(ActivityBar.RUN)),
            ("Toggle Terminal", "Ctrl+`", mw.toggle_terminal),
            ("New Terminal", "Ctrl+Shift+`", mw.new_terminal),
            ("Git Commit", "Ctrl+Enter", mw._git_commit_prompt),
            ("Git Push", None, mw._git_push),
            ("Git Pull", None, mw._git_pull),
            ("Toggle Side Bar", "Ctrl+B", mw.toggle_side_bar),
            ("Toggle Panel", "Ctrl+J", mw.toggle_bottom_panel),
            ("Show Problems", "Ctrl+Shift+M", mw.show_problems_panel),
            ("Toggle Documentation", None, mw.toggle_documentation),
            ("Font Settings", None, mw.open_font_dialog),
            ("Clear Output", None, mw.clear_output),
        ]

    def _label(self, name, shortcut):
        return f"{name}    {shortcut}" if shortcut else name

    def _populate(self, commands):
        self.list.clear()
        for name, shortcut, callback in commands:
            label = self._label(name, shortcut)
            self.list.addItem(label)
            item = self.list.item(self.list.count() - 1)
            item.setData(Qt.ItemDataRole.UserRole, callback)
        if self.list.count():
            self.list.setCurrentRow(0)

    def _filter(self, text):
        needle = text.lower().strip()
        if not needle:
            filtered = self._commands
        else:
            filtered = [
                cmd for cmd in self._commands
                if all(part in cmd[0].lower() for part in needle.split())
            ]
        self._populate(filtered)

    def _run_current(self):
        item = self.list.currentItem()
        if item:
            self._run_item(item)

    def _run_item(self, item):
        callback = item.data(Qt.ItemDataRole.UserRole)
        if callback:
            self.accept()
            callback()
