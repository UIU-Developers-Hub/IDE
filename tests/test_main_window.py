import os
import tempfile
import unittest

from PyQt6.QtTest import QTest

from core.constants import DATA_DIR, SETTINGS_PATH
import qt_helpers  # noqa: F401
from ui.main_window import AICompilerMainWindow


class TestAICompilerMainWindow(unittest.TestCase):
    def setUp(self):
        self.main_window = AICompilerMainWindow()

    def tearDown(self):
        self.main_window.close()
        self.main_window.deleteLater()

    def test_save_user_settings(self):
        self.main_window.save_user_settings()
        self.assertTrue(os.path.exists(SETTINGS_PATH))

    def test_run_code(self):
        fd, path = tempfile.mkstemp(suffix=".py", dir=DATA_DIR)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write("print('Hello, World!')")

        editor = self.main_window.add_new_tab(file_path=path, content="print('Hello, World!')")
        self.main_window.tab_widget.setCurrentWidget(editor)
        self.main_window.run_code()
        QTest.qWait(1500)

        output = self.main_window.output_text.toPlainText()
        self.assertIn("Hello, World!", output)
        os.remove(path)


if __name__ == "__main__":
    unittest.main()
