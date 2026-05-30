import html

import markdown
from PyQt6.QtWidgets import QDockWidget, QTextBrowser


class DocumentationSidebar(QDockWidget):
    """Optional docs panel — hidden by default like VS Code peek/hover."""

    def __init__(self):
        super().__init__("Documentation")
        self.text_browser = QTextBrowser()
        self.text_browser.setOpenExternalLinks(True)
        self.setWidget(self.text_browser)
        self.setMinimumWidth(280)
        self.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetClosable
        )
        self.hide()

    def set_widget_content(self, content):
        if content and content.strip():
            self.text_browser.setHtml(self._format(content))
        else:
            self.text_browser.setPlainText("No documentation for this symbol.")

    @staticmethod
    def _format(content):
        text = content.strip()
        if text.startswith("```") or "\n```" in text or text.count("\n") > 3:
            body = markdown.markdown(
                text,
                extensions=["fenced_code", "nl2br", "sane_lists"],
            )
        else:
            safe = html.escape(text).replace("\n", "<br>")
            body = f"<pre style='white-space:pre-wrap; margin:0;'>{safe}</pre>"
        return (
            "<div style='font-family:Segoe UI,sans-serif; padding:12px; font-size:13px;'>"
            f"{body}</div>"
        )
