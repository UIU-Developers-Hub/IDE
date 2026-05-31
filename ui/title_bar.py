"""Cursor / VS Code–style top bar: wordmark, menus, layout controls, window chrome."""

import sys

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QAction, QFont
from PyQt6.QtWidgets import (
    QApplication, QHBoxLayout, QLabel, QMenu, QToolButton, QWidget,
)

from ui.activity_bar import ActivityBar
from ui.icons_util import icon
from ui.theme import (
    BG_SIDEBAR, BG_TITLE, BORDER, FG_PRIMARY, TITLE_BAR_BORDER, TITLE_BAR_HEIGHT,
    TITLE_ICON_FG, TITLE_MENU_FG,
    TITLE_MENU_HOVER_BG,
)


class _TitleDivider(QWidget):
    """Thin vertical rule between title bar sections."""

    def __init__(self, height: int = 18, parent=None):
        super().__init__(parent)
        self.setFixedSize(1, height)
        self.setStyleSheet(f"background: {TITLE_BAR_BORDER};")


class TitleBar(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setObjectName("TitleBar")
        self.setFixedHeight(TITLE_BAR_HEIGHT)
        self._menu_buttons: dict[str, QToolButton] = {}

        root = QHBoxLayout(self)
        root.setContentsMargins(10, 0, 0, 0)
        root.setSpacing(0)

        wordmark = QLabel("pyditor")
        wordmark_font = QFont("Segoe UI", 13)
        wordmark_font.setWeight(QFont.Weight.DemiBold)
        wordmark.setFont(wordmark_font)
        wordmark.setStyleSheet("color: #6eb3f7; padding: 0 10px 0 2px;")
        wordmark.setToolTip("PyDitor")
        root.addWidget(wordmark)
        root.addSpacing(4)

        menus = QHBoxLayout()
        menus.setSpacing(0)
        self._build_menus(menus)
        root.addLayout(menus)

        root.addSpacing(6)
        root.addWidget(_TitleDivider())
        root.addSpacing(4)

        nav = QHBoxLayout()
        nav.setSpacing(2)
        self._sidebar_btn = self._icon_button(
            "sidebar", "Toggle Side Bar (Ctrl+B)", main_window.toggle_side_bar,
        )
        nav.addWidget(self._sidebar_btn)
        self._back_btn = self._icon_button(
            "back", "Go Back (Alt+Left)", main_window.navigate_back,
        )
        self._back_btn.setEnabled(False)
        nav.addWidget(self._back_btn)
        self._forward_btn = self._icon_button(
            "forward", "Go Forward (Alt+Right)", main_window.navigate_forward,
        )
        self._forward_btn.setEnabled(False)
        nav.addWidget(self._forward_btn)
        root.addLayout(nav)

        root.addStretch(1)

        actions = QHBoxLayout()
        actions.setSpacing(2)
        self._panel_btn = self._icon_button(
            "panel", "Toggle Panel (Ctrl+J)", main_window.toggle_bottom_panel,
        )
        actions.addWidget(self._panel_btn)
        self._docs_btn = self._icon_button(
            "comment", "Toggle Documentation (Ctrl+Shift+I)",
            main_window.toggle_documentation,
        )
        actions.addWidget(self._docs_btn)
        self._settings_btn = self._icon_button(
            "settings", "Settings",
            lambda: main_window._show_activity(ActivityBar.SETTINGS),
        )
        actions.addWidget(self._settings_btn)
        root.addLayout(actions)

        if sys.platform == "win32":
            root.addSpacing(4)
            root.addWidget(_TitleDivider())
            self._window_controls = self._make_window_controls(main_window)
            root.addWidget(self._window_controls)

        self._apply_style()

    def _make_window_controls(self, mw) -> QWidget:
        wrap = QWidget()
        wrap.setObjectName("TitleWindowControls")
        lay = QHBoxLayout(wrap)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        icon_px = QSize(12, 12)

        min_btn = QToolButton()
        min_btn.setObjectName("TitleWinBtn")
        min_btn.setIcon(icon("win-minimize"))
        min_btn.setIconSize(icon_px)
        min_btn.setToolTip("Minimize")
        min_btn.setFixedSize(46, TITLE_BAR_HEIGHT)
        min_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        min_btn.clicked.connect(mw.showMinimized)
        lay.addWidget(min_btn)

        self._max_btn = QToolButton()
        self._max_btn.setObjectName("TitleWinBtn")
        self._max_btn.setIcon(icon("win-maximize"))
        self._max_btn.setIconSize(icon_px)
        self._max_btn.setToolTip("Maximize")
        self._max_btn.setFixedSize(46, TITLE_BAR_HEIGHT)
        self._max_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._max_btn.clicked.connect(mw._toggle_maximize)
        lay.addWidget(self._max_btn)

        close_btn = QToolButton()
        close_btn.setObjectName("TitleWinCloseBtn")
        close_btn.setIcon(icon("win-close"))
        close_btn.setIconSize(icon_px)
        close_btn.setToolTip("Close")
        close_btn.setFixedSize(46, TITLE_BAR_HEIGHT)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(mw.close)
        lay.addWidget(close_btn)

        return wrap

    def update_maximize_icon(self, maximized: bool):
        if hasattr(self, "_max_btn"):
            name = "win-restore" if maximized else "win-maximize"
            self._max_btn.setIcon(icon(name))
            self._max_btn.setToolTip("Restore Down" if maximized else "Maximize")

    def _apply_style(self):
        self.setStyleSheet(f"""
            #TitleBar {{
                background: {BG_TITLE};
                border-bottom: 1px solid {TITLE_BAR_BORDER};
            }}
            #TitleBar QToolButton#TitleMenuBtn {{
                background: transparent;
                border: none;
                color: {TITLE_MENU_FG};
                padding: 6px 9px;
                font-family: "Segoe UI";
                font-size: 12px;
            }}
            #TitleBar QToolButton#TitleMenuBtn:hover {{
                background: {TITLE_MENU_HOVER_BG};
                color: #ffffff;
            }}
            #TitleBar QToolButton#TitleIconBtn {{
                background: transparent;
                border: none;
                border-radius: 5px;
                padding: 6px;
                min-width: 28px;
                max-width: 28px;
                min-height: 28px;
                max-height: 28px;
            }}
            #TitleBar QToolButton#TitleIconBtn:hover {{
                background: {TITLE_MENU_HOVER_BG};
            }}
            #TitleBar QToolButton#TitleIconBtn:disabled {{
                opacity: 0.35;
            }}
            #TitleBar QToolButton#TitleMenuBtn::menu-indicator,
            #TitleBar QToolButton#TitleIconBtn::menu-indicator {{
                image: none;
                width: 0;
            }}
            #TitleBar QToolButton#TitleWinBtn,
            #TitleBar QToolButton#TitleWinCloseBtn {{
                background: transparent;
                border: none;
            }}
            #TitleBar QToolButton#TitleWinBtn:hover {{
                background: {TITLE_MENU_HOVER_BG};
            }}
            #TitleBar QToolButton#TitleWinCloseBtn:hover {{
                background: #e81123;
            }}
        """)

    def _icon_button(self, name: str, tip: str, slot) -> QToolButton:
        btn = QToolButton()
        btn.setObjectName("TitleIconBtn")
        btn.setIcon(icon(name, TITLE_ICON_FG))
        btn.setIconSize(QSize(15, 15))
        btn.setToolTip(tip)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(slot)
        return btn

    def _menu_button(self, label: str, menu: QMenu) -> QToolButton:
        btn = QToolButton()
        btn.setObjectName("TitleMenuBtn")
        btn.setText(label)
        btn.setMenu(menu)
        btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._menu_buttons[label] = btn
        return btn

    def _style_menu(self, menu: QMenu):
        menu.setStyleSheet(f"""
            QMenu {{
                background: {BG_SIDEBAR};
                color: {FG_PRIMARY};
                border: 1px solid {BORDER};
                padding: 4px 0;
                font-family: "Segoe UI";
                font-size: 12px;
            }}
            QMenu::item {{
                padding: 6px 28px 6px 20px;
            }}
            QMenu::item:selected {{
                background: #094771;
            }}
            QMenu::separator {{
                height: 1px;
                background: {BORDER};
                margin: 4px 8px;
            }}
        """)

    def _action(self, menu, label, slot, shortcut=None):
        action = QAction(label, self.main_window)
        if shortcut:
            action.setShortcut(shortcut)
        action.triggered.connect(slot)
        menu.addAction(action)
        return action

    def _build_menus(self, layout: QHBoxLayout):
        mw = self.main_window

        file_menu = QMenu(mw)
        self._style_menu(file_menu)
        for label, shortcut, slot in (
            ("New File", "Ctrl+N", mw.add_new_tab),
            ("Open File...", "Ctrl+O", mw.open_file),
            ("Quick Open...", "Ctrl+P", mw.show_quick_open),
            ("Command Palette...", "Ctrl+Shift+P", mw.show_command_palette),
            ("Save", "Ctrl+S", mw.save_file),
            ("Save As...", "Ctrl+Shift+S", mw.save_file_as),
            ("Open Folder...", "Ctrl+Shift+O", mw.open_folder),
            ("Recent Files", None, mw.show_recent_files),
        ):
            self._action(file_menu, label, slot, shortcut)
        file_menu.addSeparator()
        self._action(file_menu, "Exit", QApplication.instance().quit, "Ctrl+Q")
        layout.addWidget(self._menu_button("File", file_menu))

        edit_menu = QMenu(mw)
        self._style_menu(edit_menu)
        for label, shortcut, slot in (
            ("Find", "Ctrl+F", mw.show_find_dialog),
            ("Replace", "Ctrl+H", mw.show_replace_dialog),
            ("Go to Line", "Ctrl+G", mw.show_go_to_line),
            ("Toggle Comment", "Ctrl+/", mw.toggle_comment),
            ("Format Document", "Shift+Alt+F", mw.format_document),
            ("Organize Imports", "Ctrl+Alt+I", mw.organize_imports),
        ):
            self._action(edit_menu, label, slot, shortcut)
        layout.addWidget(self._menu_button("Edit", edit_menu))

        selection_menu = QMenu(mw)
        self._style_menu(selection_menu)
        self._action(selection_menu, "Select All", mw.select_all, "Ctrl+A")
        layout.addWidget(self._menu_button("Selection", selection_menu))

        view_menu = QMenu(mw)
        self._style_menu(view_menu)
        for label, shortcut, slot in (
            ("Explorer", "Ctrl+Shift+E", lambda: mw._show_activity(ActivityBar.EXPLORER)),
            ("Search", "Ctrl+Shift+F", lambda: mw._show_activity(ActivityBar.SEARCH)),
            ("Source Control", "Ctrl+Shift+G", lambda: mw._show_activity(ActivityBar.SOURCE_CONTROL)),
            ("Run and Debug", None, lambda: mw._show_activity(ActivityBar.RUN)),
            ("Terminal", "Ctrl+`", mw.toggle_terminal),
            ("New Terminal", "Ctrl+Shift+`", mw.new_terminal),
            ("Documentation", "Ctrl+Shift+I", mw.toggle_documentation),
            ("Toggle Side Bar", "Ctrl+B", mw.toggle_side_bar),
            ("Toggle Panel", "Ctrl+J", mw.toggle_bottom_panel),
            ("Problems", "Ctrl+Shift+M", mw.show_problems_panel),
            ("Clear Output", None, mw.clear_output),
        ):
            self._action(view_menu, label, slot, shortcut)
        layout.addWidget(self._menu_button("View", view_menu))

        go_menu = QMenu(mw)
        self._style_menu(go_menu)
        self._action(go_menu, "Go to Line...", mw.show_go_to_line, "Ctrl+G")
        self._action(go_menu, "Quick Open...", mw.show_quick_open, "Ctrl+P")
        self._action(go_menu, "Command Palette...", mw.show_command_palette, "Ctrl+Shift+P")
        layout.addWidget(self._menu_button("Go", go_menu))

        run_menu = QMenu(mw)
        self._style_menu(run_menu)
        for label, shortcut, slot in (
            ("Run File", "F5", mw.run_code),
            ("Stop", "Shift+F5", mw.stop_execution),
            ("Run Buffer", "Ctrl+T", mw.run_tests),
        ):
            self._action(run_menu, label, slot, shortcut)
        run_menu.addSeparator()
        debug_menu = run_menu.addMenu("Debug")
        self._style_menu(debug_menu)
        for label, slot in (
            ("Start Debugger", mw.start_debugger),
            ("Continue", mw.continue_debugger),
            ("Step", mw.step_debugger),
        ):
            self._action(debug_menu, label, slot)
        run_menu.addSeparator()
        git_menu = run_menu.addMenu("Git")
        self._style_menu(git_menu)
        for label, shortcut, slot in (
            ("Source Control", "Ctrl+Shift+G", lambda: mw._show_activity(ActivityBar.SOURCE_CONTROL)),
            ("Commit...", "Ctrl+Enter", mw._git_commit_prompt),
            ("Push", "Ctrl+Shift+K", mw._git_push),
            ("Pull", "Ctrl+Shift+U", mw._git_pull),
            ("Refresh Status", None, mw._git_refresh),
            ("Clone Repository...", None, mw.side_bar.source_control_panel.clone_repo),
            ("Publish to GitHub...", None, mw.side_bar.source_control_panel.publish_github),
        ):
            self._action(git_menu, label, slot, shortcut)
        layout.addWidget(self._menu_button("Run", run_menu))

        terminal_menu = QMenu(mw)
        self._style_menu(terminal_menu)
        self._action(terminal_menu, "New Terminal", mw.new_terminal, "Ctrl+Shift+`")
        self._action(terminal_menu, "Toggle Terminal", mw.toggle_terminal, "Ctrl+`")
        layout.addWidget(self._menu_button("Terminal", terminal_menu))

        help_menu = QMenu(mw)
        self._style_menu(help_menu)
        self._action(help_menu, "Command Palette...", mw.show_command_palette, "Ctrl+Shift+P")
        self._action(help_menu, "Documentation Sidebar", mw.toggle_documentation, "Ctrl+Shift+I")
        self._action(help_menu, "Font Settings...", mw.open_font_dialog)
        layout.addWidget(self._menu_button("Help", help_menu))

    def menu_button(self, name: str) -> QToolButton | None:
        return self._menu_buttons.get(name)

    def update_nav_buttons(self, can_back: bool, can_forward: bool):
        self._back_btn.setEnabled(can_back)
        self._forward_btn.setEnabled(can_forward)
        for btn, name, enabled in (
            (self._back_btn, "back", can_back),
            (self._forward_btn, "forward", can_forward),
        ):
            color = TITLE_ICON_FG if enabled else "#5a5a5a"
            btn.setIcon(icon(name, color))

    def _is_interactive_child(self, widget) -> bool:
        while widget and widget is not self:
            if isinstance(widget, QToolButton):
                return True
            widget = widget.parentWidget()
        return False

    def mousePressEvent(self, event):
        if (
            event.button() == Qt.MouseButton.LeftButton
            and sys.platform == "win32"
            and not self._is_interactive_child(self.childAt(event.position().toPoint()))
        ):
            handle = self.window().windowHandle()
            if handle:
                handle.startSystemMove()
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if not self._is_interactive_child(self.childAt(event.position().toPoint())):
                self.main_window._toggle_maximize()
                event.accept()
                return
        super().mouseDoubleClickEvent(event)
