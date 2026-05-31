import unittest

import qt_helpers  # noqa: F401
from ui.activity_bar import ActivityBar
from ui.main_window import AICompilerMainWindow


class TestVSCodeShell(unittest.TestCase):
    def setUp(self):
        self.main_window = AICompilerMainWindow()

    def tearDown(self):
        self.main_window.close()
        self.main_window.deleteLater()

    def test_sidebar_view_bar(self):
        bar = self.main_window.side_bar.view_bar
        self.assertIsNotNone(bar)
        self.assertEqual(len(bar._buttons), 5)

    def test_side_bar_and_bottom_panel(self):
        self.assertIsNotNone(self.main_window.side_bar)
        self.assertIsNotNone(self.main_window.bottom_panel)
        self.assertGreater(self.main_window.bottom_panel.stack.count(), 0)

    def test_show_settings_view(self):
        self.main_window.side_bar.show_view(ActivityBar.SETTINGS)
        self.assertEqual(
            self.main_window.side_bar.active_index(),
            ActivityBar.SETTINGS,
        )


if __name__ == "__main__":
    unittest.main()
