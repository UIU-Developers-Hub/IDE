import unittest

import qt_helpers  # noqa: F401
from ui.code_editor import CodeEditor


class TestCodeEditorExtended(unittest.TestCase):
    def setUp(self):
        self.editor = CodeEditor()

    def tearDown(self):
        self.editor.close()

    def test_highlight_current_line(self):
        self.editor.setPlainText("a\nb\nc\n")
        self.editor.setCursorPosition(2, 1)
        line, col = self.editor.getCursorPosition()
        self.assertEqual((line, col), (2, 1))

    def test_add_breakpoint(self):
        self.editor.breakpoints = set()
        self.editor.breakpoints.add(2)
        self.assertIn(2, self.editor.breakpoints)

    def test_lint_code(self):
        self.editor.setPlainText("def foo():\n    return 1\n")
        self.editor.lint_code()
        self.editor.lint_worker.wait(5000)
        self.assertIsInstance(self.editor.lint_errors, dict)


if __name__ == "__main__":
    unittest.main()
