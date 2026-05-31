import json
import logging
import os
import sys

import jedi
from concurrent.futures import ThreadPoolExecutor
from PyQt6.QtCore import Qt, QThread, QFileSystemWatcher, QSize, QTimer
from PyQt6.QtGui import (
    QAction, QColor, QFont, QKeySequence, QShortcut, QTextCharFormat,
    QTextCursor,
)
from PyQt6.QtWidgets import (
    QApplication, QFileDialog, QHBoxLayout, QInputDialog,
    QLineEdit, QMainWindow, QMenu, QMessageBox, QPlainTextEdit,
    QSplitter, QStatusBar, QTabBar, QTabWidget, QToolButton, QVBoxLayout,
    QWidget, QFontDialog, QLabel,
)

from core.code_runner_thread import CodeRunner, Signals
from core.constants import (
    BATCH_RESULTS_PATH, RECENT_FILES_PATH, SESSION_PATH, SETTINGS_PATH,
)
from core.debugger_thread import DebuggerThread
from core.format_worker import FormatWorker
from ui.command_palette import CommandPalette
from ui.activity_bar import ActivityBar
from ui.bottom_panel import BottomPanel
from ui.code_editor import CodeEditor
from ui.dialogs import FindReplaceDialog, GoToLineDialog
from ui.documentation_sidebar import DocumentationSidebar
from ui.problems_panel import ProblemsPanel
from ui.quick_open import QuickOpenDialog
from ui.side_bar import SideBar
from ui.title_bar import TitleBar
from ui.terminal_panel import TerminalPanel
from ui.welcome_widget import WelcomeWidget
from core.git_service import GitService
from ui.theme import (
    ERROR, WARNING, SIDEBAR_MAX_WIDTH, SIDEBAR_MIN_WIDTH, SIDEBAR_WIDTH,
)
from ui.icons_util import icon

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logging.getLogger("jedi").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

OUTPUT_COLORS = {
    "error": "#f44747",
    "warning": "#cca700",
    "info": "#d4d4d4",
}


class AICompilerMainWindow(QMainWindow):
    RECENT_FILES_LIMIT = 10

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyDitor")
        self.resize(1200, 800)

        self.thread_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="runner")
        self.debugger_thread = None
        self.active_runner = None
        self.recent_files = []
        self._last_lint_data = []
        self.format_worker = None
        self._project_root = os.getcwd()
        self._welcome_tab_index = None
        self._sidebar_visible = True
        self._panel_visible = True
        self._last_activity = ActivityBar.EXPLORER
        self._untitled_seq = 0
        self._docs_visible = False
        self._nav_history: list[int] = []
        self._nav_index = -1
        self._nav_lock = False

        self._enable_custom_title_bar()
        self.setup_ui()
        self.setup_shortcuts()
        self.load_user_settings()
        self.restore_session()
        self._sync_untitled_counter()
        if self.tab_widget.count() == 0:
            self.show_welcome_tab()

    def _enable_custom_title_bar(self):
        """Replace the native Windows title bar with the Cursor-style menu bar."""
        self.menuBar().setVisible(False)
        if sys.platform == "win32":
            self.setWindowFlags(
                Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint
            )

    def _toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
        if hasattr(self, "title_bar"):
            self.title_bar.update_maximize_icon(self.isMaximized())

    def setup_ui(self):
        self.recent_files = self.load_recent_files()

        self.setup_status_bar()

        self.side_bar = SideBar(self)
        self.side_bar.view_changed.connect(self._on_activity_view)
        self.side_bar.set_root(self._project_root)
        self.explorer_panel = self.side_bar.explorer_panel

        self.fs_watcher = QFileSystemWatcher(self)
        self.fs_watcher.fileChanged.connect(self._on_external_file_changed)
        self._watch_directory(self._project_root)

        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.setTabsClosable(False)
        self.tab_widget.setMovable(True)
        tab_bar = self.tab_widget.tabBar()
        tab_bar.setExpanding(False)
        tab_bar.setElideMode(Qt.TextElideMode.ElideRight)
        tab_bar.setDrawBase(False)
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        self._setup_new_tab_button()

        self.setup_bottom_panel()

        self.documentation_sidebar = DocumentationSidebar()
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.documentation_sidebar)
        self.documentation_sidebar.hide()

        editor_splitter = QSplitter(Qt.Orientation.Vertical)
        editor_splitter.addWidget(self.tab_widget)
        editor_splitter.addWidget(self.bottom_panel)
        editor_splitter.setStretchFactor(0, 1)
        editor_splitter.setStretchFactor(1, 0)
        editor_splitter.setSizes([700, 220])
        self._editor_splitter = editor_splitter

        self._main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self._main_splitter.addWidget(self.side_bar)
        self._main_splitter.addWidget(editor_splitter)
        self._main_splitter.setStretchFactor(0, 0)
        self._main_splitter.setStretchFactor(1, 1)
        self._main_splitter.setHandleWidth(4)
        self._main_splitter.setSizes([SIDEBAR_WIDTH, 900])
        self._main_splitter.setCollapsible(0, False)
        self._main_splitter.setChildrenCollapsible(False)

        self._outline_timer = QTimer(self)
        self._outline_timer.setSingleShot(True)
        self._outline_timer.setInterval(400)
        self._outline_timer.timeout.connect(
            lambda: self.side_bar.footer.outline.refresh()
        )

        self.title_bar = TitleBar(self)

        shell = QWidget()
        shell_layout = QVBoxLayout(shell)
        shell_layout.setContentsMargins(0, 0, 0, 0)
        shell_layout.setSpacing(0)
        shell_layout.addWidget(self.title_bar)
        shell_layout.addWidget(self._main_splitter, 1)
        self.setCentralWidget(shell)

        self.update_git_status()
        self.bottom_panel.tab_changed.connect(self._on_bottom_panel_tab_changed)

    def setup_bottom_panel(self):
        self.bottom_panel = BottomPanel()
        self.bottom_panel.connect_close(self.toggle_bottom_panel)

        self.problems_panel = ProblemsPanel()
        self.problems_panel.issue_activated.connect(self._go_to_problem)
        self._panel_problems_index = self.bottom_panel.add_tab(
            self.problems_panel, "Problems",
        )

        output_container = QWidget()
        output_layout = QVBoxLayout(output_container)
        output_layout.setContentsMargins(0, 0, 0, 0)
        self.output_text = QPlainTextEdit()
        self.output_text.setReadOnly(True)
        output_layout.addWidget(self.output_text)
        self._panel_output_index = self.bottom_panel.add_tab(
            output_container, "Output", on_clear=self.clear_output,
        )

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Program input (stdin)...")
        self.bottom_panel.add_tab(self.input_field, "Input")

        self.terminal_panel = TerminalPanel(self)
        self._panel_terminal_index = self.bottom_panel.add_tab(
            self.terminal_panel, "Terminal",
            on_clear=self.clear_terminal,
        )

        self.io_tabs = self.bottom_panel.stack

    def _on_activity_view(self, index):
        if self._sidebar_visible and self._last_activity == index:
            self.toggle_side_bar(force_hide=True)
            return
        self._last_activity = index
        self._sidebar_visible = True
        self.side_bar.show()
        self.side_bar.show_view(index)

    def toggle_side_bar(self, force_hide=None):
        if force_hide is True:
            self._sidebar_visible = False
        elif force_hide is False:
            self._sidebar_visible = True
        else:
            self._sidebar_visible = not self._sidebar_visible
        self.side_bar.setVisible(self._sidebar_visible)

    def toggle_bottom_panel(self):
        self._panel_visible = not self._panel_visible
        self.bottom_panel.setVisible(self._panel_visible)

    def show_terminal_panel(self):
        if not self._panel_visible:
            self.toggle_bottom_panel()
        self.bottom_panel.set_current_index(self._panel_terminal_index)
        self.terminal_panel._ensure_terminal()
        widget = self.terminal_panel.tabs.currentWidget()
        if widget:
            widget.start()
            widget.input.setFocus()

    def toggle_terminal(self):
        if self._panel_visible and self.bottom_panel.current_index() == self._panel_terminal_index:
            self.toggle_bottom_panel()
        else:
            self.show_terminal_panel()

    def clear_terminal(self):
        self.terminal_panel.clear_current()

    def _on_bottom_panel_tab_changed(self, index):
        if index == self._panel_output_index:
            self.bottom_panel.set_clear_callback(self.clear_output)
        elif index == self._panel_terminal_index:
            self.bottom_panel.set_clear_callback(self.clear_terminal)

    def update_git_status(self):
        if not hasattr(self, "_status_git"):
            return
        git = GitService(self._project_root)
        if git.is_repo():
            branch = git.current_branch() or "main"
            self._status_git.setText(f"⎇ {branch}")
        else:
            self._status_git.setText("— no git")

    def open_folder_at(self, folder):
        if not folder or not os.path.isdir(folder):
            return
        self._project_root = folder
        self.side_bar.set_root(folder)
        self.terminal_panel.set_project_root(folder)
        self._status_project.setText(os.path.basename(folder))
        self._watch_directory(folder)
        self.update_git_status()
        self.side_bar.source_control_panel.refresh()
        self.statusBar().showMessage(f"Opened folder: {folder}", 3000)

    def show_output_panel(self):
        if not self._panel_visible:
            self.toggle_bottom_panel()
        self.bottom_panel.set_current_index(self._panel_output_index)

    def setup_status_bar(self):
        status = QStatusBar()
        self.setStatusBar(status)
        self._status_project = QLabel(os.path.basename(self._project_root))
        self._status_git = QLabel("—")
        self._status_lint = QLabel("✓ 0")
        self._status_position = QLabel("Ln 1, Col 1")
        self._status_encoding = QLabel("UTF-8")
        self._status_language = QLabel(
            f"Python {sys.version_info.major}.{sys.version_info.minor}"
        )
        for widget in (
            self._status_project,
            self._status_git,
            self._status_lint,
            self._status_position,
            self._status_encoding,
            self._status_language,
        ):
            widget.setStyleSheet("color: #ffffff; padding: 0 8px;")
        status.addWidget(self._status_project)
        status.addWidget(self._status_git)
        status.addPermanentWidget(self._status_lint)
        status.addPermanentWidget(self._status_position)
        status.addPermanentWidget(self._status_encoding)
        status.addPermanentWidget(self._status_language)

    def _show_activity(self, index):
        self._on_activity_view(index)

    def new_terminal(self):
        self.terminal_panel.new_terminal(self._project_root)
        self.show_terminal_panel()

    def _git_commit_prompt(self):
        self._show_activity(ActivityBar.SOURCE_CONTROL)
        self.side_bar.source_control_panel.commit_input.setFocus()

    def _git_push(self):
        self._show_activity(ActivityBar.SOURCE_CONTROL)
        self.side_bar.source_control_panel.push()

    def _git_pull(self):
        self._show_activity(ActivityBar.SOURCE_CONTROL)
        self.side_bar.source_control_panel.pull()

    def _git_refresh(self):
        self._show_activity(ActivityBar.SOURCE_CONTROL)
        self.side_bar.source_control_panel.refresh()
        self.update_git_status()

    def show_command_palette(self):
        dialog = CommandPalette(self)
        dialog.exec()

    def toggle_documentation(self):
        self._docs_visible = not self._docs_visible
        if self._docs_visible:
            self.documentation_sidebar.show()
            editor = self.current_editor()
            if editor:
                self.update_documentation(editor)
        else:
            self.documentation_sidebar.hide()

    def _sync_untitled_counter(self):
        max_n = 0
        for index in range(self.tab_widget.count()):
            editor = self.tab_widget.widget(index)
            if isinstance(editor, CodeEditor) and not editor.file_path:
                name = getattr(editor, "untitled_name", "")
                if name.startswith("Untitled-"):
                    try:
                        max_n = max(max_n, int(name.split("-", 1)[1]))
                    except ValueError:
                        pass
        self._untitled_seq = max_n

    def _next_untitled_name(self):
        self._untitled_seq += 1
        return f"Untitled-{self._untitled_seq}"

    def _setup_new_tab_button(self):
        btn = QToolButton()
        btn.setObjectName("NewTabButton")
        btn.setIcon(icon("plus", "#969696"))
        btn.setIconSize(QSize(14, 14))
        btn.setFixedSize(36, 36)
        btn.setToolTip("New Tab (Ctrl+N)")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(self.add_new_tab)
        btn.setStyleSheet(
            "QToolButton#NewTabButton { background: transparent; border: none; "
            "border-radius: 4px; margin-right: 4px; }"
            "QToolButton#NewTabButton:hover { background: #3e3e42; }"
        )
        self.tab_widget.setCornerWidget(btn, Qt.Corner.TopRightCorner)

    def _add_tab_close_button(self, index):
        bar = self.tab_widget.tabBar()
        btn = QToolButton()
        btn.setIcon(icon("close", "#969696"))
        btn.setIconSize(QSize(12, 12))
        btn.setFixedSize(20, 20)
        btn.setToolTip("Close (Ctrl+W)")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(
            "QToolButton { background: transparent; border: none; border-radius: 3px; }"
            "QToolButton:hover { background: #3e3e42; }"
        )
        btn.clicked.connect(self._on_tab_close_clicked)
        bar.setTabButton(index, QTabBar.ButtonPosition.RightSide, btn)

    def _on_tab_close_clicked(self):
        bar = self.tab_widget.tabBar()
        button = self.sender()
        for i in range(bar.count()):
            if bar.tabButton(i, QTabBar.ButtonPosition.RightSide) is button:
                self.close_tab(i)
                return

    def show_welcome_tab(self):
        if self._welcome_tab_index is not None:
            self.tab_widget.setCurrentIndex(self._welcome_tab_index)
            return
        welcome = WelcomeWidget(self)
        self._welcome_tab_index = self.tab_widget.addTab(welcome, "Welcome")
        self._add_tab_close_button(self._welcome_tab_index)
        self.tab_widget.setCurrentIndex(self._welcome_tab_index)

    def close_welcome_tab(self):
        if self._welcome_tab_index is None:
            return
        for index in range(self.tab_widget.count()):
            if isinstance(self.tab_widget.widget(index), WelcomeWidget):
                self.tab_widget.removeTab(index)
                break
        self._welcome_tab_index = None

    def show_quick_open(self):
        dialog = QuickOpenDialog(self._project_root, self)
        if dialog.exec() and dialog.selected_path():
            self._open_file_path(dialog.selected_path())

    def clear_output(self):
        self.output_text.clear()
        self.statusBar().showMessage("Output cleared.", 2000)

    def show_problems_panel(self):
        if not self._panel_visible:
            self.toggle_bottom_panel()
        self.bottom_panel.set_current_index(self._panel_problems_index)

    def _go_to_problem(self, line, _text):
        editor = self.current_editor()
        if editor:
            editor.go_to_line(line)

    def setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+N"), self, activated=self.add_new_tab)
        QShortcut(QKeySequence("Ctrl+O"), self, activated=self.open_file)
        QShortcut(QKeySequence("Ctrl+S"), self, activated=self.save_file)
        QShortcut(QKeySequence("Ctrl+Shift+S"), self, activated=self.save_file_as)
        QShortcut(QKeySequence("Ctrl+W"), self, activated=self.close_current_tab)
        QShortcut(QKeySequence("F5"), self, activated=self.run_code)
        QShortcut(QKeySequence("Shift+F5"), self, activated=self.stop_execution)
        QShortcut(QKeySequence("Ctrl+T"), self, activated=self.run_tests)
        QShortcut(QKeySequence("Ctrl+F"), self, activated=self.show_find_dialog)
        QShortcut(QKeySequence("Ctrl+H"), self, activated=self.show_replace_dialog)
        QShortcut(QKeySequence("Ctrl+G"), self, activated=self.show_go_to_line)
        QShortcut(QKeySequence("Ctrl+/"), self, activated=self.toggle_comment)
        QShortcut(QKeySequence("Ctrl+B"), self, activated=self.toggle_side_bar)
        QShortcut(QKeySequence("Ctrl+J"), self, activated=self.toggle_bottom_panel)
        QShortcut(QKeySequence("Ctrl+Shift+E"), self, activated=lambda: self._show_activity(ActivityBar.EXPLORER))
        QShortcut(QKeySequence("Ctrl+Shift+F"), self, activated=lambda: self._show_activity(ActivityBar.SEARCH))
        QShortcut(QKeySequence("Ctrl+Shift+G"), self, activated=lambda: self._show_activity(ActivityBar.SOURCE_CONTROL))
        QShortcut(QKeySequence("Ctrl+`"), self, activated=self.toggle_terminal)
        QShortcut(QKeySequence("Ctrl+Shift+`"), self, activated=self.new_terminal)
        QShortcut(QKeySequence("Ctrl+Enter"), self, activated=self._git_commit_prompt)
        QShortcut(QKeySequence("Ctrl+Shift+M"), self, activated=self.show_problems_panel)
        QShortcut(QKeySequence("Ctrl+Shift+P"), self, activated=self.show_command_palette)
        QShortcut(QKeySequence("Ctrl+Shift+I"), self, activated=self.toggle_documentation)
        QShortcut(QKeySequence("Alt+Left"), self, activated=self.navigate_back)
        QShortcut(QKeySequence("Alt+Right"), self, activated=self.navigate_forward)
        QShortcut(QKeySequence("Ctrl+A"), self, activated=self.select_all)
        QShortcut(QKeySequence("Ctrl+P"), self, activated=self.show_quick_open)
        QShortcut(QKeySequence("Ctrl+Shift+L"), self, activated=self.show_lint_report)
        QShortcut(QKeySequence("Shift+Alt+F"), self, activated=self.format_document)
        QShortcut(QKeySequence("Ctrl+Alt+I"), self, activated=self.organize_imports)

    def _watch_directory(self, folder):
        if not folder or not os.path.isdir(folder):
            return
        current = self.fs_watcher.directories()
        if current:
            self.fs_watcher.removePaths(current)
        self.fs_watcher.addPath(folder)

    def _on_external_file_changed(self, path):
        if not os.path.isfile(path):
            return
        for index in range(self.tab_widget.count()):
            editor = self.tab_widget.widget(index)
            if not isinstance(editor, CodeEditor) or editor.file_path != path:
                continue
            if not editor.document().isModified():
                self._reload_editor_from_disk(editor, path)
                return
            reply = QMessageBox.question(
                self,
                "File Changed",
                f"{os.path.basename(path)} was modified externally.\nReload?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._reload_editor_from_disk(editor, path)
            return

    def _reload_editor_from_disk(self, editor, path):
        try:
            with open(path, encoding="utf-8") as handle:
                editor.setPlainText(handle.read())
            editor.document().setModified(False)
            self.update_tab_title(editor)
            self.statusBar().showMessage(f"Reloaded: {path}", 3000)
        except OSError as exc:
            self.statusBar().showMessage(f"Reload failed: {exc}", 5000)

    def _on_tab_changed(self, index):
        if index >= 0:
            self._record_navigation(index)
        editor = self.current_editor()
        if editor:
            self.update_documentation(editor)
            self.update_status_bar(editor)
            self.update_tab_title(editor)
        self._refresh_sidebar_footer()

    def _record_navigation(self, tab_index: int):
        if self._nav_lock:
            return
        if self._nav_index >= 0 and self._nav_history[self._nav_index] == tab_index:
            return
        self._nav_history = self._nav_history[: self._nav_index + 1]
        self._nav_history.append(tab_index)
        self._nav_index = len(self._nav_history) - 1
        self._update_nav_buttons()

    def _update_nav_buttons(self):
        if hasattr(self, "title_bar"):
            self.title_bar.update_nav_buttons(
                self._nav_index > 0,
                self._nav_index < len(self._nav_history) - 1,
            )

    def navigate_back(self):
        if self._nav_index <= 0:
            return
        self._nav_lock = True
        self._nav_index -= 1
        self.tab_widget.setCurrentIndex(self._nav_history[self._nav_index])
        self._nav_lock = False
        self._update_nav_buttons()

    def navigate_forward(self):
        if self._nav_index >= len(self._nav_history) - 1:
            return
        self._nav_lock = True
        self._nav_index += 1
        self.tab_widget.setCurrentIndex(self._nav_history[self._nav_index])
        self._nav_lock = False
        self._update_nav_buttons()

    def select_all(self):
        editor = self.current_editor()
        if editor:
            editor.selectAll()

    def _schedule_outline_refresh(self):
        self._outline_timer.start()

    def _refresh_sidebar_footer(self):
        if hasattr(self, "side_bar"):
            self.side_bar.footer.refresh()

    def _sidebar_width(self):
        sizes = self._main_splitter.sizes()
        return max(SIDEBAR_MIN_WIDTH, min(SIDEBAR_MAX_WIDTH, sizes[0])) if sizes else SIDEBAR_WIDTH

    def update_status_bar(self, editor):
        line, col = editor.getCursorPosition()
        self._status_position.setText(f"Ln {line + 1}, Col {col + 1}")
        project = os.path.basename(self._project_root)
        self._status_project.setText(project)
        self._update_window_title(editor)

    def update_tab_title(self, editor):
        for index in range(self.tab_widget.count()):
            if self.tab_widget.widget(index) is editor:
                if editor.file_path:
                    base = os.path.basename(editor.file_path)
                else:
                    base = getattr(editor, "untitled_name", "Untitled-1")
                suffix = " ●" if editor.document().isModified() else ""
                self.tab_widget.setTabText(index, base + suffix)
                break
        self._update_window_title(editor)

    def _update_window_title(self, editor):
        if editor.file_path:
            fname = os.path.basename(editor.file_path)
        else:
            fname = getattr(editor, "untitled_name", "Untitled-1")
        modified = " ●" if editor.document().isModified() else ""
        project = os.path.basename(self._project_root)
        self.setWindowTitle(f"{fname}{modified} - {project} - PyDitor")

    def current_editor(self):
        widget = self.tab_widget.currentWidget()
        return widget if isinstance(widget, CodeEditor) else None

    def update_documentation(self, editor):
        if not self._docs_visible:
            return

        cursor = editor.textCursor()
        line = cursor.blockNumber() + 1
        column = cursor.positionInBlock()
        source = editor.toPlainText()

        if not source.strip():
            return

        try:
            script = jedi.Script(code=source, path=editor.file_path or "<stdin>")
            names = script.help(line, column)
            if not names:
                return
            doc = names[0].docstring()
            if not doc:
                desc = str(names[0].description or "")
                if not desc or desc in ("None", "NoneType", "instance"):
                    return
                doc = desc
            self.documentation_sidebar.set_widget_content(doc)
        except Exception as exc:
            logger.debug("Documentation lookup failed: %s", exc)

    def add_new_tab(self, file_path=None, content=""):
        self.close_welcome_tab()
        editor = CodeEditor(main_window=self)
        editor.file_path = file_path
        if not file_path:
            editor.untitled_name = self._next_untitled_name()
        if content:
            editor.setPlainText(content)
            editor.document().setModified(False)

        title = (
            os.path.basename(file_path) if file_path else editor.untitled_name
        )
        index = self.tab_widget.addTab(editor, title)
        self._add_tab_close_button(index)
        self.tab_widget.setCurrentIndex(index)
        editor.document().modificationChanged.connect(
            lambda _modified: self.update_tab_title(editor)
        )
        editor.textChanged.connect(self._schedule_outline_refresh)
        self.update_status_bar(editor)
        self._refresh_sidebar_footer()
        return editor

    def close_current_tab(self):
        self.close_tab(self.tab_widget.currentIndex())

    def close_tab(self, index):
        widget = self.tab_widget.widget(index)
        if isinstance(widget, WelcomeWidget):
            self.tab_widget.removeTab(index)
            self._welcome_tab_index = None
            return

        editor = widget
        if not isinstance(editor, CodeEditor):
            self.tab_widget.removeTab(index)
            if self.tab_widget.count() == 0:
                self.show_welcome_tab()
            return

        if editor.document().isModified():
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "Save changes before closing?",
                QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel,
            )
            if reply == QMessageBox.StandardButton.Save:
                previous = self.tab_widget.currentIndex()
                self.tab_widget.setCurrentIndex(index)
                if not self.save_file():
                    self.tab_widget.setCurrentIndex(previous)
                    return
            elif reply == QMessageBox.StandardButton.Cancel:
                return

        editor.close()
        self.tab_widget.removeTab(index)
        if self.tab_widget.count() == 0:
            self.show_welcome_tab()

    def _ensure_saved(self, editor):
        if editor.file_path and not editor.document().isModified():
            return True

        if not editor.file_path:
            self.statusBar().showMessage("Save the file before running.", 4000)
            reply = QMessageBox.warning(
                self,
                "Save File",
                "The file must be saved before running. Save now?",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Cancel,
            )
            if reply != QMessageBox.StandardButton.Save:
                return False
        elif editor.document().isModified():
            reply = QMessageBox.warning(
                self,
                "Unsaved Changes",
                "Save changes before running?",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Cancel,
            )
            if reply != QMessageBox.StandardButton.Save:
                return False

        return self.save_file()

    def run_code(self):
        editor = self.current_editor()
        if not editor:
            return

        if not self._ensure_saved(editor):
            return

        self.output_text.clear()
        self.show_output_panel()
        self.statusBar().showMessage(f"Running: {editor.file_path}", 3000)

        signals = Signals()
        signals.output_received.connect(self.handle_output)
        signals.error_received.connect(lambda msg: self.handle_output(msg, "error"))

        runner = CodeRunner(
            editor.file_path,
            self.input_field.text(),
            signals=signals,
        )
        self.active_runner = runner
        self.thread_pool.submit(self._run_and_clear, runner)

    def _run_and_clear(self, runner):
        try:
            runner.run()
        finally:
            self.active_runner = None

    def stop_execution(self):
        if self.active_runner:
            self.active_runner.kill()
            self.handle_output("Execution stopped.", "warning")
            self.statusBar().showMessage("Execution stopped.", 3000)
        elif self.debugger_thread and self.debugger_thread.isRunning():
            self.debugger_thread.stop()
            self.handle_output("Debugger stopped.", "warning")
            self.statusBar().showMessage("Debugger stopped.", 3000)
        else:
            self.statusBar().showMessage("Nothing is running.", 2000)

    def run_tests(self):
        editor = self.current_editor()
        if not editor or not editor.toPlainText().strip():
            self.statusBar().showMessage("No code to run.", 3000)
            return

        self.output_text.clear()
        self.show_output_panel()

        signals = Signals()
        signals.output_received.connect(self.handle_output)
        signals.error_received.connect(lambda msg: self.handle_output(msg, "error"))

        runner = CodeRunner.from_source(editor.toPlainText(), signals=signals)
        self.active_runner = runner
        self.thread_pool.submit(self._run_and_clear, runner)

    def handle_output(self, message, message_type="info"):
        cursor = self.output_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        fmt = QTextCharFormat()
        fmt.setForeground(QColor(OUTPUT_COLORS.get(message_type, OUTPUT_COLORS["info"])))
        cursor.setCharFormat(fmt)
        cursor.insertText(message.rstrip() + "\n")
        self.output_text.setTextCursor(cursor)
        self.output_text.ensureCursorVisible()

    def process_lint_results(self, lint_data):
        self._last_lint_data = lint_data or []
        self.problems_panel.update_issues(self._last_lint_data)

        if not lint_data:
            self._status_lint.setText("✓ 0")
            self._status_lint.setStyleSheet("color: #ffffff; padding: 0 8px;")
            self.statusBar().showMessage("No lint issues.", 3000)
            return

        errors = sum(
            1 for item in lint_data
            if item["message"].split()[0].startswith(("E", "F"))
        )
        warnings = len(lint_data) - errors
        self._status_lint.setText(f"ⓧ {errors}  ⚠ {warnings}")
        color = ERROR if errors else (WARNING if warnings else "#ffffff")
        self._status_lint.setStyleSheet(f"color: {color}; padding: 0 8px;")
        self.statusBar().showMessage(
            f"Lint: {errors} error(s), {warnings} warning(s)  (Ctrl+Shift+L for details)",
            5000,
        )

    def show_lint_report(self):
        if not self._last_lint_data:
            self.statusBar().showMessage("No lint results yet.", 3000)
            return
        self.show_problems_panel()

    def show_find_dialog(self):
        self._show_find_replace(replace=False)

    def show_replace_dialog(self):
        self._show_find_replace(replace=True)

    def _show_find_replace(self, replace=False):
        editor = self.current_editor()
        if not editor:
            return

        dialog = FindReplaceDialog(self, replace=replace)

        selected = editor.textCursor().selectedText().replace("\u2029", "\n")
        if selected and "\n" not in selected:
            dialog.find_input.setText(selected)

        while True:
            result = dialog.exec()
            if result == 0:
                break

            find = dialog.search_text()
            if not find:
                continue

            case = dialog.is_case_sensitive()
            if result == 1:
                if not editor.find_text(find, case_sensitive=case):
                    self.statusBar().showMessage(f"Not found: {find}", 3000)
            elif result == 2:
                if not editor.find_text(find, backward=True, case_sensitive=case):
                    self.statusBar().showMessage(f"Not found: {find}", 3000)
            elif result == 3:
                editor.replace_current(
                    find, dialog.replacement_text(), case_sensitive=case
                )
            elif result == 4:
                count = editor.replace_all(
                    find, dialog.replacement_text(), case_sensitive=case
                )
                self.statusBar().showMessage(f"Replaced {count} occurrence(s).", 3000)
                break

    def show_go_to_line(self):
        editor = self.current_editor()
        if not editor:
            return

        current = editor.textCursor().blockNumber() + 1
        maximum = editor.blockCount()
        dialog = GoToLineDialog(self, current_line=current, max_line=maximum)
        if dialog.exec() and dialog.line_number() is not None:
            line = dialog.line_number()
            if 1 <= line <= maximum:
                editor.go_to_line(line)
            else:
                self.statusBar().showMessage(f"Line must be between 1 and {maximum}.", 4000)

    def toggle_comment(self):
        editor = self.current_editor()
        if editor:
            editor.toggle_comment()

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Python File", os.getcwd(), "Python Files (*.py);;All Files (*)"
        )
        if file_path:
            self._open_file_path(file_path)

    def _open_file_path(self, file_path):
        for index in range(self.tab_widget.count()):
            editor = self.tab_widget.widget(index)
            if isinstance(editor, CodeEditor) and editor.file_path == file_path:
                self.tab_widget.setCurrentIndex(index)
                self.statusBar().showMessage(f"Already open: {file_path}", 2000)
                return

        try:
            with open(file_path, encoding="utf-8") as handle:
                content = handle.read()
        except OSError as exc:
            self.statusBar().showMessage(f"Could not open file: {exc}", 5000)
            return

        self.add_new_tab(file_path=file_path, content=content)
        self.add_to_recent_files(file_path)
        self.statusBar().showMessage(f"Opened: {file_path}", 3000)

    def load_recent_files(self):
        if not os.path.exists(RECENT_FILES_PATH):
            return []
        try:
            with open(RECENT_FILES_PATH, encoding="utf-8") as handle:
                files = json.load(handle)
            return [path for path in files if os.path.isfile(path)][: self.RECENT_FILES_LIMIT]
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Could not load recent files: %s", exc)
            return []

    def save_file(self):
        editor = self.current_editor()
        if not editor:
            return False

        if editor.file_path is None:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save Python File", os.getcwd(), "Python Files (*.py);;All Files (*)"
            )
            if not file_path:
                return False
            editor.file_path = file_path

        try:
            with open(editor.file_path, "w", encoding="utf-8") as handle:
                handle.write(editor.toPlainText())
        except OSError as exc:
            self.statusBar().showMessage(f"Save failed: {exc}", 5000)
            return False

        editor.document().setModified(False)
        tab_name = os.path.basename(editor.file_path)
        self.tab_widget.setTabText(self.tab_widget.currentIndex(), tab_name)
        self.update_tab_title(editor)
        self.add_to_recent_files(editor.file_path)
        self.side_bar.footer.timeline._history.record_save(
            editor.file_path, editor.toPlainText()
        )
        self._refresh_sidebar_footer()
        self.statusBar().showMessage(f"Saved: {editor.file_path}", 3000)
        return True

    def save_file_as(self):
        editor = self.current_editor()
        if not editor:
            return False
        editor.file_path = None
        return self.save_file()

    def add_to_recent_files(self, file_path):
        if file_path in self.recent_files:
            self.recent_files.remove(file_path)
        self.recent_files.insert(0, file_path)
        self.recent_files = self.recent_files[: self.RECENT_FILES_LIMIT]
        self.save_recent_files()

    def save_recent_files(self):
        try:
            with open(RECENT_FILES_PATH, "w", encoding="utf-8") as handle:
                json.dump(self.recent_files, handle, indent=2)
        except OSError as exc:
            logger.warning("Could not save recent files: %s", exc)

    def show_recent_files(self):
        menu = QMenu("Recent Files", self)
        if not self.recent_files:
            empty = QAction("(No recent files)", self)
            empty.setEnabled(False)
            menu.addAction(empty)
        else:
            for path in self.recent_files:
                action = QAction(path, self)
                action.triggered.connect(lambda checked=False, p=path: self._open_file_path(p))
                menu.addAction(action)
        btn = self.title_bar.menu_button("File")
        if btn:
            menu.exec(btn.mapToGlobal(btn.rect().bottomLeft()))
        else:
            menu.exec(self.title_bar.mapToGlobal(self.title_bar.rect().bottomLeft()))

    def load_user_settings(self):
        if not os.path.exists(SETTINGS_PATH):
            return
        try:
            with open(SETTINGS_PATH, encoding="utf-8") as handle:
                settings = json.load(handle)
        except (json.JSONDecodeError, OSError):
            return

        font = QFont(
            settings.get("font_family", "Consolas"),
            settings.get("font_size", 12),
        )
        self.apply_font_settings(font)

        width = settings.get("sidebar_width", SIDEBAR_WIDTH)
        width = max(SIDEBAR_MIN_WIDTH, min(SIDEBAR_MAX_WIDTH, int(width)))
        total = max(self.width(), width + 400)
        self._main_splitter.setSizes([width, total - width])

    def save_user_settings(self):
        editor = self.current_editor()
        font = editor.font() if editor else QFont("Consolas", 12)
        settings = {
            "font_family": font.family(),
            "font_size": font.pointSize(),
            "sidebar_width": self._sidebar_width(),
        }
        with open(SETTINGS_PATH, "w", encoding="utf-8") as handle:
            json.dump(settings, handle, indent=2)

    def open_font_dialog(self):
        editor = self.current_editor()
        current = editor.font() if editor else QFont("Consolas", 12)
        font, ok = QFontDialog.getFont(current, self)
        if ok:
            self.apply_font_settings(font)
            self.save_user_settings()

    def apply_font_settings(self, font):
        for index in range(self.tab_widget.count()):
            editor = self.tab_widget.widget(index)
            if isinstance(editor, CodeEditor):
                editor.setFont(font)
        self.input_field.setFont(font)
        self.output_text.setFont(font)

    def create_new_folder(self):
        index = self.explorer_panel.tree.currentIndex()
        base = self.explorer_panel.index_to_path(index)
        folder_path = base if os.path.isdir(base) else os.path.dirname(base)

        name, ok = QInputDialog.getText(self, "New Folder", "Folder name:")
        if not ok or not name.strip():
            return

        target = os.path.join(folder_path, name.strip())
        try:
            os.makedirs(target, exist_ok=False)
            self.explorer_panel.refresh()
            self.statusBar().showMessage(f"Created folder: {target}", 3000)
        except OSError as exc:
            self.statusBar().showMessage(f"Could not create folder: {exc}", 5000)

    def open_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Open Folder", self._project_root)
        if folder:
            self.open_folder_at(folder)

    def format_document(self):
        editor = self.current_editor()
        if not editor:
            return
        self._run_format_worker(editor, mode="format")

    def organize_imports(self):
        editor = self.current_editor()
        if not editor:
            return
        self._run_format_worker(editor, mode="imports")

    def _run_format_worker(self, editor, mode="format"):
        if self.format_worker and self.format_worker.isRunning():
            self.format_worker.stop()

        self.format_worker = FormatWorker(editor.toPlainText(), mode=mode)
        self.format_worker.format_done.connect(
            lambda text: self._apply_formatted_code(editor, text, mode)
        )
        self.format_worker.format_failed.connect(
            lambda msg: self.statusBar().showMessage(f"Format failed: {msg}", 5000)
        )
        self.format_worker.start()
        label = "Formatting" if mode == "format" else "Sorting imports"
        self.statusBar().showMessage(f"{label}...", 2000)

    def _apply_formatted_code(self, editor, text, mode):
        if text and text != editor.toPlainText():
            editor.setPlainText(text)
            editor.document().setModified(True)
            self.update_tab_title(editor)
            editor.lint_code()
        action = "Formatted" if mode == "format" else "Imports organized"
        self.statusBar().showMessage(f"{action}.", 3000)

    def start_debugger(self):
        editor = self.current_editor()
        if not editor or not editor.toPlainText().strip():
            self.statusBar().showMessage("No code to debug.", 3000)
            return

        if self.debugger_thread and self.debugger_thread.isRunning():
            self.debugger_thread.stop()

        self.output_text.clear()
        self.show_output_panel()

        self.debugger_thread = DebuggerThread(
            editor.toPlainText(),
            breakpoints=editor.breakpoints,
        )
        self.debugger_thread.output_received.connect(
            lambda msg: self.handle_output(msg, "info")
        )
        self.debugger_thread.error_received.connect(
            lambda msg: self.handle_output(msg, "error")
        )
        self.debugger_thread.start()

        bp_count = len(editor.breakpoints)
        if bp_count:
            msg = f"Debugger started with {bp_count} breakpoint(s)."
        else:
            msg = "Debugger started."
        self.statusBar().showMessage(msg, 3000)

    def continue_debugger(self):
        if self.debugger_thread:
            self.debugger_thread.send_command("continue")

    def step_debugger(self):
        if self.debugger_thread:
            self.debugger_thread.send_command("step")

    def open_file_from_explorer(self, index):
        path = self.explorer_panel.index_to_path(index)
        if not os.path.isfile(path):
            return
        ext = os.path.splitext(path)[1].lower()
        if ext in (".py", ".txt", ".md", ".json", ".toml", ".cfg", ".ini", ".yaml", ".yml"):
            self._open_file_path(path)

    def insert_snippet(self, code_snippet):
        editor = self.current_editor()
        if not editor:
            self.statusBar().showMessage("No active editor.", 3000)
            return
        editor.textCursor().insertText(code_snippet)
        self.statusBar().showMessage("Snippet inserted.", 2000)

    def run_batch_test(self):
        input_file, _ = QFileDialog.getOpenFileName(
            self, "Open Batch Test File", os.getcwd(), "Text Files (*.txt);;All Files (*)"
        )
        if input_file:
            self.batch_test(self.sample_function, input_file)

    def batch_test(self, function, input_file_path):
        self.output_text.clear()
        self.show_output_panel()
        results = []

        try:
            with open(input_file_path, encoding="utf-8") as handle:
                test_cases = [line for line in handle if line.strip()]
        except OSError as exc:
            self.statusBar().showMessage(f"Could not read test file: {exc}", 5000)
            return

        for i, case in enumerate(test_cases, start=1):
            parts = case.strip().split()
            try:
                args = [int(arg) for arg in parts]
                result = function(*args)
                line = f"Test {i}: {args} -> {result}"
            except ValueError:
                line = f"Test {i}: invalid input {case.strip()!r}"
            except Exception as exc:
                line = f"Test {i}: error {exc}"

            results.append(line)
            self.handle_output(line, "info")

        try:
            with open(BATCH_RESULTS_PATH, "w", encoding="utf-8") as handle:
                handle.write("\n".join(results) + "\n")
        except OSError as exc:
            self.statusBar().showMessage(f"Could not save results: {exc}", 5000)

    @staticmethod
    def sample_function(*args):
        return sum(args)

    def restore_session(self):
        if not os.path.exists(SESSION_PATH):
            return

        try:
            with open(SESSION_PATH, encoding="utf-8") as handle:
                session_data = json.load(handle)
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Could not restore session: %s", exc)
            return

        for file_info in session_data.get("open_files", []):
            path = file_info.get("file_path")
            content = file_info.get("content", "")
            breakpoints = file_info.get("breakpoints", [])

            if path and os.path.isfile(path):
                editor = self.add_new_tab(file_path=path, content=content)
            elif content.strip():
                editor = self.add_new_tab(content=content)
                saved_name = file_info.get("untitled_name")
                if saved_name:
                    editor.untitled_name = saved_name
                    self.update_tab_title(editor)
            else:
                continue

            if breakpoints:
                editor.breakpoints = set(breakpoints)
                editor._refresh_breakpoints()

        index = session_data.get("current_tab_index", 0)
        if 0 <= index < self.tab_widget.count():
            self.tab_widget.setCurrentIndex(index)

    def save_session(self):
        session_data = {
            "open_files": [],
            "current_tab_index": self.tab_widget.currentIndex(),
        }

        seen_untitled = set()
        for index in range(self.tab_widget.count()):
            editor = self.tab_widget.widget(index)
            if isinstance(editor, CodeEditor):
                text = editor.toPlainText()
                if not editor.file_path:
                    if not text.strip():
                        continue
                    key = hash(text)
                    if key in seen_untitled:
                        continue
                    seen_untitled.add(key)
                session_data["open_files"].append({
                    "file_path": editor.file_path,
                    "content": text,
                    "breakpoints": sorted(editor.breakpoints),
                    "untitled_name": getattr(editor, "untitled_name", None),
                })

        try:
            with open(SESSION_PATH, "w", encoding="utf-8") as handle:
                json.dump(session_data, handle, indent=2)
        except OSError as exc:
            logger.warning("Could not save session: %s", exc)

    def closeEvent(self, event):
        self.save_session()
        self.save_user_settings()

        if self.debugger_thread and self.debugger_thread.isRunning():
            self.debugger_thread.stop()

        if self.format_worker and self.format_worker.isRunning():
            self.format_worker.stop()

        for index in range(self.tab_widget.count()):
            editor = self.tab_widget.widget(index)
            if isinstance(editor, CodeEditor) and hasattr(editor, "lint_worker"):
                if editor.lint_worker.isRunning():
                    editor.lint_worker.stop()

        if hasattr(self, "terminal_panel"):
            self.terminal_panel.shutdown_all()

        if hasattr(self, "fs_watcher"):
            dirs = self.fs_watcher.directories()
            files = self.fs_watcher.files()
            if dirs:
                self.fs_watcher.removePaths(dirs)
            if files:
                self.fs_watcher.removePaths(files)

        for thread in self.findChildren(QThread):
            if thread.isRunning():
                thread.quit()
                thread.wait(2000)

        self.thread_pool.shutdown(wait=False, cancel_futures=True)
        event.accept()


if __name__ == "__main__":
    app = QApplication([])
    window = AICompilerMainWindow()
    window.show()
    app.exec()
