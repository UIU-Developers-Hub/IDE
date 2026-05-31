"""Local file history for the sidebar TIMELINE view."""

import hashlib
import json
import os
from datetime import datetime, timezone

from core.constants import DATA_DIR

HISTORY_DIR = os.path.join(DATA_DIR, "local_history")
MAX_ENTRIES_PER_FILE = 50
MAX_SNAPSHOT_BYTES = 512_000


def _file_key(path: str) -> str:
    normalized = os.path.normcase(os.path.abspath(path))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:32]


def timeline_label(path: str | None) -> str:
    if not path:
        return ""
    return f"{_file_key(path)[:8]}-{_file_key(path)[8:16]}-{_file_key(path)[16:24]}…"


class LocalHistory:
    def __init__(self, base_dir: str = HISTORY_DIR):
        self._base = base_dir
        os.makedirs(self._base, exist_ok=True)

    def _meta_path(self, file_path: str) -> str:
        return os.path.join(self._base, f"{_file_key(file_path)}.json")

    def record_save(self, file_path: str, content: str) -> None:
        if not file_path or len(content.encode("utf-8")) > MAX_SNAPSHOT_BYTES:
            return
        meta_path = self._meta_path(file_path)
        try:
            if os.path.exists(meta_path):
                with open(meta_path, encoding="utf-8") as handle:
                    data = json.load(handle)
            else:
                data = {"path": file_path, "entries": []}
        except (json.JSONDecodeError, OSError):
            data = {"path": file_path, "entries": []}

        stamp = datetime.now(timezone.utc).isoformat()
        entry_id = hashlib.sha256(f"{stamp}:{content}".encode()).hexdigest()[:12]
        snap_dir = os.path.join(self._base, _file_key(file_path))
        os.makedirs(snap_dir, exist_ok=True)
        snap_path = os.path.join(snap_dir, f"{entry_id}.txt")
        try:
            with open(snap_path, "w", encoding="utf-8") as handle:
                handle.write(content)
        except OSError:
            return

        entries = data.get("entries", [])
        entries.insert(0, {
            "id": entry_id,
            "label": "File Saved",
            "timestamp": stamp,
        })
        data["entries"] = entries[:MAX_ENTRIES_PER_FILE]
        try:
            with open(meta_path, "w", encoding="utf-8") as handle:
                json.dump(data, handle, indent=2)
        except OSError:
            pass

    def list_entries(self, file_path: str | None) -> list[dict]:
        if not file_path:
            return []
        meta_path = self._meta_path(file_path)
        if not os.path.exists(meta_path):
            return []
        try:
            with open(meta_path, encoding="utf-8") as handle:
                data = json.load(handle)
            return data.get("entries", [])
        except (json.JSONDecodeError, OSError):
            return []

    def read_snapshot(self, file_path: str, entry_id: str) -> str | None:
        snap_path = os.path.join(self._base, _file_key(file_path), f"{entry_id}.txt")
        if not os.path.isfile(snap_path):
            return None
        try:
            with open(snap_path, encoding="utf-8") as handle:
                return handle.read()
        except OSError:
            return None
