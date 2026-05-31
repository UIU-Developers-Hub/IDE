"""PyDitor visual theme — VS Code Dark+ inspired."""

import os

_UI_DIR = os.path.dirname(__file__)
_TAB_CLOSE_ICON = os.path.join(_UI_DIR, "icons", "tab-close.svg").replace("\\", "/")

ACCENT = "#007acc"
ACCENT_HOVER = "#1f8ad2"
BG_EDITOR = "#1e1e1e"
BG_SIDEBAR = "#252526"
BG_PANEL = "#1e1e1e"
BG_INPUT = "#3c3c3c"
BG_TITLE = "#181818"
TITLE_BAR_HEIGHT = 36
TITLE_BAR_BORDER = "#2b2b2b"
TITLE_MENU_FG = "#cccccc"
TITLE_MENU_HOVER_BG = "#2a2d2e"
TITLE_ICON_FG = "#9d9d9d"
TITLE_ICON_HOVER_FG = "#e0e0e0"
TITLE_BRAND_FG = "#9d9d9d"
ACTIVITY_BAR_BG = "#333333"
ACTIVITY_BAR_FG = "#858585"
ACTIVITY_BAR_ACTIVE = "#ffffff"
FG_PRIMARY = "#cccccc"
FG_MUTED = "#858585"
FG_HEADER = "#bbbbbb"
BORDER = "#3e3e42"
TAB_INACTIVE = "#2d2d2d"
TAB_ACTIVE = "#1e1e1e"
PANEL_HEADER_BG = "#252526"
STATUS_BAR_BG = "#007acc"
ERROR = "#f44747"
WARNING = "#cca700"
SUCCESS = "#4ec9b0"
SIDEBAR_WIDTH = 300
SIDEBAR_MIN_WIDTH = 170
SIDEBAR_MAX_WIDTH = 600
ACTIVITY_BAR_WIDTH = 48

EXTRA_STYLESHEET = f"""
QMainWindow {{
    background-color: {BG_EDITOR};
}}
QMenuBar {{
    background: {BG_TITLE};
    color: {FG_PRIMARY};
    border-bottom: 1px solid {BORDER};
    padding: 2px 0;
}}
QMenuBar::item {{
    padding: 4px 10px;
    background: transparent;
}}
QMenuBar::item:selected {{
    background: #2a2d2e;
}}
QMenu {{
    background: {BG_SIDEBAR};
    color: {FG_PRIMARY};
    border: 1px solid {BORDER};
}}
QMenu::item:selected {{
    background: #094771;
}}
QTabWidget::pane {{
    border: none;
    background: {TAB_ACTIVE};
    top: -1px;
}}
QTabBar {{
    background: {TAB_INACTIVE};
    border-bottom: 1px solid {BORDER};
}}
QTabBar::tab {{
    background: {TAB_INACTIVE};
    color: {FG_MUTED};
    padding: 9px 28px 9px 14px;
    border: none;
    border-right: 1px solid #1a1a1a;
    min-width: 80px;
    max-width: 200px;
    font-size: 13px;
}}
QTabBar::tab:selected {{
    background: {TAB_ACTIVE};
    color: #ffffff;
    border-top: 1px solid {ACCENT};
}}
QTabBar::tab:hover:!selected {{
    background: #1f1f1f;
    color: {FG_PRIMARY};
}}
QTabBar::close-button {{
    image: url({_TAB_CLOSE_ICON});
    subcontrol-origin: padding;
    subcontrol-position: right;
    width: 16px;
    height: 16px;
    margin: 2px 4px;
}}
QTabBar::close-button:hover {{
    image: url({_TAB_CLOSE_ICON});
    background: #3e3e42;
    border-radius: 3px;
}}
QTreeView {{
    background: {BG_SIDEBAR};
    border: none;
    color: {FG_PRIMARY};
    outline: none;
    font-size: 13px;
}}
QTreeView::item {{
    padding: 2px 0;
    height: 22px;
}}
QTreeView::item:hover {{
    background: #2a2d2e;
}}
QTreeView::item:selected {{
    background: #094771;
}}
QPlainTextEdit, QTextEdit {{
    background: {BG_EDITOR};
    color: {FG_PRIMARY};
    border: none;
    selection-background-color: #264f78;
    font-family: Consolas, 'Cascadia Code', monospace;
    font-size: 13px;
}}
QLineEdit {{
    background: {BG_INPUT};
    color: {FG_PRIMARY};
    border: 1px solid {BORDER};
    padding: 4px 8px;
    selection-background-color: #264f78;
}}
QStatusBar {{
    background: {STATUS_BAR_BG};
    color: #ffffff;
    border: none;
    min-height: 22px;
}}
QStatusBar QLabel {{
    color: #ffffff;
    padding: 0 10px;
    font-size: 12px;
}}
QDockWidget {{
    color: {FG_HEADER};
    titlebar-close-icon: none;
}}
QDockWidget::title {{
    background: {BG_SIDEBAR};
    padding: 6px 10px;
    border-bottom: 1px solid {BORDER};
    text-align: left;
}}
QSplitter::handle {{
    background: {BORDER};
}}
QSplitter::handle:horizontal {{
    width: 1px;
}}
QSplitter::handle:vertical {{
    height: 1px;
}}
QListWidget {{
    background: {BG_SIDEBAR};
    border: none;
    color: {FG_PRIMARY};
    outline: none;
    font-size: 12px;
}}
QListWidget::item {{
    padding: 4px 8px;
}}
QListWidget::item:hover {{
    background: #2a2d2e;
}}
QListWidget::item:selected {{
    background: #094771;
}}
QsciScintilla {{
    background: {BG_EDITOR};
    border: none;
}}
"""


def apply_fluent_theme():
    """Apply PyQt6-Fluent-Widgets dark theme and VS Code accent."""
    from qfluentwidgets import Theme, setTheme, setThemeColor

    setTheme(Theme.DARK)
    setThemeColor(ACCENT)


def apply_theme(app):
    """Apply VS Code supplemental styles."""
    current = app.styleSheet() or ""
    app.setStyleSheet(current + EXTRA_STYLESHEET)
