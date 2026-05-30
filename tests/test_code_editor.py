import unittest
from unittest.mock import patch

import qt_helpers  # noqa: F401
from ui.code_editor import CodeEditor


class TestCodeEditor(unittest.TestCase):
    def setUp(self):
        self.editor = CodeEditor()

    def tearDown(self):
        self.editor.close()

    @patch("PyQt6.QtWidgets.QFileDialog.getSaveFileName", return_value=("", ""))
    def test_editor_accepts_text(self, _mock_dialog):
        self.editor.setPlainText("print('Hello, World!')")
        self.assertEqual(self.editor.toPlainText(), "print('Hello, World!')")


if __name__ == "__main__":
    unittest.main()
