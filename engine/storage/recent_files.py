import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_RECENT_FILE_LIMIT = 10


@dataclass
class RecentFileEntry:
    """Metadata for one recently opened project file."""

    path: str
    last_opened: str
    pinned: bool = False

    @classmethod
    def from_data(cls, data):
        """Create an entry from JSON-safe data."""

        return cls(
            path=str(data.get("path", "")),
            last_opened=str(data.get("last_opened", "")),
            pinned=bool(data.get("pinned", False)),
        )

    def to_data(self):
        """Return JSON-safe recent file metadata."""

        return {
            "path": self.path,
            "last_opened": self.last_opened,
            "pinned": self.pinned,
        }


class RecentFilesManager:
    """Stores recent project files with timestamps and pin state."""

    def __init__(self, storage_path=None, max_count=DEFAULT_RECENT_FILE_LIMIT):

        self.storage_path = Path(storage_path) if storage_path else self._default_path()
        self.max_count = int(max_count or DEFAULT_RECENT_FILE_LIMIT)
        self._entries = {}
        self.load()

    # --------------------------------

    def add(self, path, pinned=False, timestamp=None):
        """Add or refresh a recent project path."""

        key = self._normalize(path)
        existing = self._entries.get(key)
        opened = timestamp or self._timestamp()

        if existing is None:
            existing = RecentFileEntry(key, opened, bool(pinned))
            self._entries[key] = existing
        else:
            existing.last_opened = opened
            existing.pinned = existing.pinned or bool(pinned)

        self._trim()
        self.save()

        return existing

    # --------------------------------

    def pin(self, path):
        """Pin a recent file so it remains listed."""

        entry = self._entry(path)

        if entry is not None:
            entry.pinned = True
            self.save()

        return entry

    # --------------------------------

    def unpin(self, path):
        """Remove the pinned state from a recent file."""

        entry = self._entry(path)

        if entry is not None:
            entry.pinned = False
            self._trim()
            self.save()

        return entry

    # --------------------------------

    def remove(self, path):
        """Remove a path from the recent file list."""

        removed = self._entries.pop(self._normalize(path), None)

        if removed is not None:
            self.save()

        return removed

    # --------------------------------

    def remove_missing(self):
        """Remove unpinned entries whose files no longer exist."""

        removed = []

        for key, entry in list(self._entries.items()):
            if entry.pinned:
                continue

            if not Path(entry.path).exists():
                removed.append(entry)
                self._entries.pop(key, None)

        if removed:
            self.save()

        return removed

    # --------------------------------

    def configure(self, max_count=None):
        """Update recent file settings."""

        if max_count is not None:
            self.max_count = max(1, int(max_count))
            self._trim()
            self.save()

    # --------------------------------

    def items(self):
        """Return entries sorted by pin state and last-opened time."""

        pinned = sorted(
            (entry for entry in self._entries.values() if entry.pinned),
            key=lambda entry: entry.last_opened,
            reverse=True,
        )
        unpinned = sorted(
            (entry for entry in self._entries.values() if not entry.pinned),
            key=lambda entry: entry.last_opened,
            reverse=True,
        )

        return pinned + unpinned

    # --------------------------------

    def paths(self):
        """Return recent file paths in display order."""

        return [entry.path for entry in self.items()]

    # --------------------------------

    def load(self):
        """Load recent file metadata from disk."""

        if not self.storage_path.exists():
            return

        try:
            with self.storage_path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (OSError, json.JSONDecodeError):
            return

        self.max_count = int(payload.get("max_count", self.max_count))
        self._entries = {
            entry.path: entry
            for entry in (
                RecentFileEntry.from_data(item)
                for item in payload.get("items", [])
            )
            if entry.path
        }
        self._trim()

    # --------------------------------

    def save(self):
        """Persist recent file metadata."""

        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "max_count": self.max_count,
            "items": [entry.to_data() for entry in self.items()],
        }

        with self.storage_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)

    # --------------------------------

    @property
    def count(self):
        """Return the number of tracked recent files."""

        return len(self._entries)

    # --------------------------------

    def _entry(self, path):

        return self._entries.get(self._normalize(path))

    # --------------------------------

    def _trim(self):

        unpinned = sorted(
            (entry for entry in self._entries.values() if not entry.pinned),
            key=lambda entry: entry.last_opened,
        )

        while len(self._entries) > self.max_count and unpinned:
            oldest = unpinned.pop(0)
            self._entries.pop(oldest.path, None)

    # --------------------------------

    def _normalize(self, path):

        return str(Path(path).expanduser().resolve())

    # --------------------------------

    def _timestamp(self):

        return datetime.now(timezone.utc).isoformat()

    # --------------------------------

    def _default_path(self):

        return Path.home() / ".kinematics_studio" / "recent_files.json"
