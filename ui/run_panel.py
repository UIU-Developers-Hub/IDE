from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QVBoxLayout, QWidget
from qfluentwidgets import CaptionLabel, PrimaryPushButton, PushButton

from ui.icons_util import icon


class RunPanel(QWidget):
    """Run and Debug sidebar — VS Code run view (lite)."""

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 12)
        layout.setSpacing(8)

        run_btn = PrimaryPushButton("  Run Python File")
        run_btn.setIcon(icon("run"))
        run_btn.setToolTip("F5")
        run_btn.clicked.connect(main_window.run_code)
        layout.addWidget(run_btn)

        stop_btn = PushButton("  Stop")
        stop_btn.setIcon(icon("stop"))
        stop_btn.setToolTip("Shift+F5")
        stop_btn.clicked.connect(main_window.stop_execution)
        layout.addWidget(stop_btn)

        buffer_btn = PushButton("  Run Buffer")
        buffer_btn.setToolTip("Ctrl+T — run editor without saving")
        buffer_btn.clicked.connect(main_window.run_tests)
        layout.addWidget(buffer_btn)

        layout.addSpacing(12)
        debug_header = CaptionLabel("DEBUG")
        debug_header.setStyleSheet("font-weight: bold; letter-spacing: 1px;")
        layout.addWidget(debug_header)

        debug_btn = PushButton("  Start Debugging")
        debug_btn.setIcon(icon("debug"))
        debug_btn.setToolTip("Ctrl+Shift+D")
        debug_btn.clicked.connect(main_window.start_debugger)
        layout.addWidget(debug_btn)

        cont_btn = PushButton("  Continue")
        cont_btn.clicked.connect(main_window.continue_debugger)
        layout.addWidget(cont_btn)

        step_btn = PushButton("  Step Into")
        step_btn.clicked.connect(main_window.step_debugger)
        layout.addWidget(step_btn)

        layout.addStretch()
