from PyQt6.QtWidgets import QVBoxLayout, QWidget
from qfluentwidgets import CaptionLabel, PushButton

from ui.icons_util import icon


class SettingsPanel(QWidget):
    """Quick settings sidebar."""

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 12)
        layout.setSpacing(8)

        header = CaptionLabel("SETTINGS")
        header.setStyleSheet("font-weight: bold; letter-spacing: 1px;")
        layout.addWidget(header)

        font_btn = PushButton("  Font Settings")
        font_btn.setIcon(icon("font"))
        font_btn.clicked.connect(main_window.open_font_dialog)
        layout.addWidget(font_btn)

        folder_btn = PushButton("  Open Folder")
        folder_btn.setIcon(icon("file-open.svg"))
        folder_btn.clicked.connect(main_window.open_folder)
        layout.addWidget(folder_btn)

        batch_btn = PushButton("  Batch Test")
        batch_btn.setIcon(icon("batch"))
        batch_btn.clicked.connect(main_window.run_batch_test)
        layout.addWidget(batch_btn)

        layout.addStretch()
