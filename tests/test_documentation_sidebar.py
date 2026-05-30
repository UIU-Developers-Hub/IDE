import unittest

import qt_helpers  # noqa: F401
from ui.documentation_sidebar import DocumentationSidebar


class TestDocumentationSidebar(unittest.TestCase):
    def setUp(self):
        self.sidebar = DocumentationSidebar()

    def test_set_widget_content(self):
        content = "def test_function():\n    pass"
        self.sidebar.set_widget_content(content)
        rendered = self.sidebar.text_browser.toPlainText()
        self.assertIn("test_function", rendered)


if __name__ == "__main__":
    unittest.main()
