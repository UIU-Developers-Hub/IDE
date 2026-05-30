import logging
import os

import qtawesome as qta
from PyQt6.QtGui import QIcon

logger = logging.getLogger(__name__)

ICONS_DIR = os.path.join(os.path.dirname(__file__), "icons")
DEFAULT_COLOR = "#c5c5c5"

FA_MAP = {
    "file-new.svg": "fa5s.file",
    "file-open.svg": "fa5s.folder-open",
    "file-save.svg": "fa5s.save",
    "file-exit.svg": "fa5s.sign-out-alt",
    "edit-copy.svg": "fa5s.copy",
    "edit-cut.svg": "fa5s.cut",
    "edit-paste.svg": "fa5s.paste",
    "help-content.svg": "fa5s.question-circle",
    "run": "fa5s.play",
    "stop": "fa5s.stop",
    "debug": "fa5s.bug",
    "format": "fa5s.magic",
    "imports": "fa5s.sort",
    "find": "fa5s.search",
    "lint": "fa5s.exclamation-triangle",
    "font": "fa5s.font",
    "explorer": "fa5s.folder",
    "settings": "fa5s.cog",
    "close": "fa5s.times",
    "git": "fa5s.code-branch",
    "files": "fa5s.file-code",
    "batch": "fa5s.list-ol",
}


def _svg_icon(name: str) -> QIcon:
    path = os.path.join(ICONS_DIR, name)
    return QIcon(path) if os.path.exists(path) else QIcon()


def icon(name: str, color: str = DEFAULT_COLOR) -> QIcon:
    fa_name = FA_MAP.get(name)
    if fa_name:
        try:
            return qta.icon(fa_name, color=color)
        except Exception as exc:
            logger.debug("qtawesome icon failed for %s: %s", name, exc)

    if name.endswith(".svg"):
        return _svg_icon(name)
    return QIcon()
