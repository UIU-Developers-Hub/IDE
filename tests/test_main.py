import os
import tempfile
import unittest

from PyQt6.QtTest import QTest

from core.constants import DATA_DIR
import qt_helpers  # noqa: F401
from ui.main_window import AICompilerMainWindow


class TestAICompilerMainWindow(unittest.TestCase):
    def setUp(self):
        self.main_window = AICompilerMainWindow()

    def tearDown(self):
        self.main_window.close()
        self.main_window.deleteLater()

    def _run_editor_code(self, source):
        fd, path = tempfile.mkstemp(suffix=".py", dir=DATA_DIR)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(source)
        editor = self.main_window.add_new_tab(file_path=path, content=source)
        self.main_window.tab_widget.setCurrentWidget(editor)
        self.main_window.run_code()
        QTest.qWait(1500)
        return path

    def test_code_execution(self):
        path = self._run_editor_code("print('Hello, World!')")
        output = self.main_window.output_text.toPlainText()
        self.assertIn("Hello, World!", output)
        os.remove(path)

    def test_invalid_code_execution(self):
        path = self._run_editor_code("def x ")
        output = self.main_window.output_text.toPlainText()
        self.assertTrue(output)
        os.remove(path)


if __name__ == "__main__":
    unittest.main()
