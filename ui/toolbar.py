from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QApplication, QMenu, QToolBar

from ui.icons_util import icon


class Toolbar(QToolBar):
    def __init__(self, parent):
        super().__init__("Toolbar", parent)
        self.parent_widget = parent
        self.setMovable(False)
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self._build_actions()

    def _add_action(self, label, callback, shortcut=None, icon_name=None):
        action = QAction(icon(icon_name) if icon_name else icon(""), label, self)
        if shortcut:
            action.setShortcut(shortcut)
        action.triggered.connect(callback)
        self.addAction(action)
        return action

    def _build_actions(self):
        file_menu = QMenu("File", self)
        file_items = [
            ("New File", "Ctrl+N", self.parent_widget.add_new_tab, "file-new.svg"),
            ("Open File", "Ctrl+O", self.parent_widget.open_file, "file-open.svg"),
            ("Save File", "Ctrl+S", self.parent_widget.save_file, "file-save.svg"),
            ("New Folder", "Ctrl+Shift+N", self.parent_widget.create_new_folder, None),
            ("Open Folder", "Ctrl+Shift+O", self.parent_widget.open_folder, "file-open.svg"),
            ("Recent Files", None, self.parent_widget.show_recent_files, None),
        ]
        for label, shortcut, callback, icon_name in file_items:
            action = QAction(icon(icon_name) if icon_name else icon(""), label, self)
            if shortcut:
                action.setShortcut(shortcut)
            action.triggered.connect(callback)
            file_menu.addAction(action)

        exit_action = QAction(icon("file-exit.svg"), "Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(QApplication.instance().quit)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)
        self.addAction(file_menu.menuAction())

        self._add_action("Run", self.parent_widget.run_code, "F5", "run")
        self._add_action("Stop", self.parent_widget.stop_execution, "Shift+F5", "stop")
        self._add_action("Run Code", self.parent_widget.run_tests, "Ctrl+T")
        self._add_action("Debug", self.parent_widget.start_debugger, "Ctrl+Shift+D", "debug")

        self.addSeparator()

        edit_menu = QMenu("Edit", self)
        edit_items = [
            ("Find", "Ctrl+F", self.parent_widget.show_find_dialog, "find"),
            ("Replace", "Ctrl+H", self.parent_widget.show_replace_dialog, "find"),
            ("Go to Line", "Ctrl+G", self.parent_widget.show_go_to_line, None),
            ("Toggle Comment", "Ctrl+/", self.parent_widget.toggle_comment, None),
            ("Format Document", "Shift+Alt+F", self.parent_widget.format_document, "format"),
            ("Organize Imports", "Ctrl+Alt+I", self.parent_widget.organize_imports, "imports"),
            ("Lint Report", "Ctrl+Shift+L", self.parent_widget.show_lint_report, "lint"),
        ]
        for label, shortcut, callback, icon_name in edit_items:
            action = QAction(icon(icon_name) if icon_name else icon(""), label, self)
            action.setShortcut(shortcut)
            action.triggered.connect(callback)
            edit_menu.addAction(action)
        self.addAction(edit_menu.menuAction())

        self.addSeparator()

        snippets_menu = QMenu("Snippets", self)
        snippets = {
            "For Loop": "for i in range(10):\n    print(i)\n",
            "Function": "def my_function():\n    pass\n",
            "Class": "class MyClass:\n    def __init__(self):\n        pass\n",
            "If Statement": "if condition:\n    pass\n",
        }
        for name, code in snippets.items():
            snippet_action = QAction(name, self)
            snippet_action.triggered.connect(
                lambda checked=False, snippet=code: self.parent_widget.insert_snippet(snippet)
            )
            snippets_menu.addAction(snippet_action)
        self.addAction(snippets_menu.menuAction())

        self._add_action("Font", self.parent_widget.open_font_dialog, "Ctrl+Shift+F", "font")
        self._add_action("Batch Test", self.parent_widget.run_batch_test, icon_name="batch")
