from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QVBoxLayout
from qfluentwidgets import CheckBox, LineEdit, PrimaryPushButton, PushButton


class FindReplaceDialog(QDialog):
    def __init__(self, parent=None, replace=False):
        super().__init__(parent)
        self.setWindowTitle("Replace" if replace else "Find")
        self._replace_mode = replace

        self.find_input = LineEdit()
        self.find_input.setPlaceholderText("Search text...")
        self.replace_input = LineEdit()
        self.replace_input.setPlaceholderText("Replace with...")
        self.case_sensitive = CheckBox("Match case")

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Find:"))
        layout.addWidget(self.find_input)

        if replace:
            layout.addWidget(QLabel("Replace:"))
            layout.addWidget(self.replace_input)

        layout.addWidget(self.case_sensitive)

        row = QDialogButtonBox()
        self.find_next_btn = PrimaryPushButton("Find Next")
        self.find_prev_btn = PushButton("Find Previous")
        row.addButton(self.find_next_btn, QDialogButtonBox.ButtonRole.ActionRole)
        row.addButton(self.find_prev_btn, QDialogButtonBox.ButtonRole.ActionRole)
        if replace:
            self.replace_btn = PushButton("Replace")
            self.replace_all_btn = PushButton("Replace All")
            row.addButton(self.replace_btn, QDialogButtonBox.ButtonRole.ActionRole)
            row.addButton(self.replace_all_btn, QDialogButtonBox.ButtonRole.ActionRole)
        close_btn = PushButton("Close")
        close_btn.clicked.connect(self.reject)
        row.addButton(close_btn, QDialogButtonBox.ButtonRole.RejectRole)
        layout.addWidget(row)

        self.find_next_btn.clicked.connect(lambda: self.done(1))
        self.find_prev_btn.clicked.connect(lambda: self.done(2))
        if replace:
            self.replace_btn.clicked.connect(lambda: self.done(3))
            self.replace_all_btn.clicked.connect(lambda: self.done(4))
        self.find_input.returnPressed.connect(lambda: self.done(1))

    def search_text(self):
        return self.find_input.text()

    def replacement_text(self):
        return self.replace_input.text()

    def is_case_sensitive(self):
        return self.case_sensitive.isChecked()


class GoToLineDialog(QDialog):
    def __init__(self, parent=None, current_line=1, max_line=1):
        super().__init__(parent)
        self.setWindowTitle("Go to Line")
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel(f"Line (1 – {max_line}):"))
        self.line_input = LineEdit(str(current_line))
        layout.addWidget(self.line_input)

        buttons = QDialogButtonBox()
        ok_btn = PrimaryPushButton("Go")
        cancel_btn = PushButton("Cancel")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        buttons.addButton(ok_btn, QDialogButtonBox.ButtonRole.AcceptRole)
        buttons.addButton(cancel_btn, QDialogButtonBox.ButtonRole.RejectRole)
        layout.addWidget(buttons)

        self.line_input.selectAll()
        self.line_input.returnPressed.connect(self.accept)

    def line_number(self):
        try:
            return int(self.line_input.text())
        except ValueError:
            return None
