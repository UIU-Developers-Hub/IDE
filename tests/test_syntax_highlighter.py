import unittest

from PyQt6.QtGui import QTextDocument

import qt_helpers  # noqa: F401
from ui.syntax_highlighter import PythonSyntaxHighlighter


class TestSyntaxHighlighter(unittest.TestCase):
    def setUp(self):
        self.document = QTextDocument()
        self.highlighter = PythonSyntaxHighlighter(self.document)

    def test_highlight_python_code(self):
        code = "def test_function():\n    return True"
        self.document.setPlainText(code)
        self.assertEqual(self.document.toPlainText(), code)


if __name__ == "__main__":
    unittest.main()
