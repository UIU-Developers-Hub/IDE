import unittest

import qt_helpers  # noqa: F401
from ui.main_window import AICompilerMainWindow


class TestVSCodeShell(unittest.TestCase):
    def setUp(self):
        self.main_window = AICompilerMainWindow()

    def tearDown(self):
        self.main_window.close()
        self.main_window.deleteLater()

    def test_activity_bar_exists(self):
        self.assertIsNotNone(self.main_window.activity_bar)
        self.assertEqual(len(self.main_window.activity_bar._buttons), 5)

    def test_side_bar_and_bottom_panel(self):
        self.assertIsNotNone(self.main_window.side_bar)
        self.assertIsNotNone(self.main_window.bottom_panel)
        self.assertGreater(self.main_window.bottom_panel.stack.count(), 0)


if __name__ == "__main__":
    unittest.main()
