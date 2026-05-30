from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QGridLayout, QVBoxLayout, QWidget
from qfluentwidgets import CaptionLabel, PrimaryPushButton, SubtitleLabel, TitleLabel

from ui.icons_util import icon


class WelcomeWidget(QWidget):
    """VS Code–style start page."""

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)

        logo = TitleLabel("PyDitor")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = SubtitleLabel("Edit. Run. Debug Python.")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(logo)
        layout.addWidget(subtitle)
        layout.addSpacing(16)

        grid = QGridLayout()
        grid.setSpacing(10)
        actions = [
            ("New File", "Ctrl+N", "file-new.svg", main_window.add_new_tab),
            ("Open File", "Ctrl+O", "file-open.svg", main_window.open_file),
            ("Open Folder", "Ctrl+Shift+O", "file-open.svg", main_window.open_folder),
            ("Quick Open", "Ctrl+P", "find", main_window.show_quick_open),
        ]
        for i, (label, shortcut, icon_name, callback) in enumerate(actions):
            btn = PrimaryPushButton(f"  {label}")
            btn.setIcon(icon(icon_name))
            btn.setToolTip(shortcut)
            btn.setMinimumWidth(220)
            btn.clicked.connect(lambda checked=False, cb=callback: self._action(cb))
            grid.addWidget(btn, i // 2, i % 2)

        layout.addLayout(grid)

        hints = CaptionLabel(
            "Show Explorer  Ctrl+Shift+E   ·   Toggle Panel  Ctrl+J   ·   Run  F5"
        )
        hints.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hints)

        layout.addStretch()

    def _action(self, callback):
        self.main_window.close_welcome_tab()
        callback()
