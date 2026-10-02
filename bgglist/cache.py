import json
import os
import time
from pathlib import Path

# Bump when the shape of cached data changes, so old caches are ignored
CACHE_VERSION = 1

def default_cache_dir():
    return Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache") / "bgg-list"

class Cache:
    """API results stored as JSON, one file per namespace.

    Entries never expire on their own: each records when it was fetched, and
    callers decide whether that's recent enough. A stale entry is kept until a
    new copy replaces it, so it can stand in when BoardGameGeek can't provide one.
    """

    def __init__(self, directory, clock=time.time):
        self.directory = Path(directory)
        self.clock = clock
        self._namespaces = {}
        self._changed = set()

    def _path(self, namespace):
        return self.directory / f"{namespace}.json"

    def _entries(self, namespace):
        if namespace not in self._namespaces:
            try:
                content = json.loads(self._path(namespace).read_text(encoding="utf-8"))
            except (OSError, ValueError):
                content = None
            if not isinstance(content, dict) or content.get("version") != CACHE_VERSION:
                content = {"version": CACHE_VERSION, "entries": {}}
            self._namespaces[namespace] = content
        return self._namespaces[namespace]["entries"]

    def get(self, namespace, key):
        """The cached data and its age in seconds, or (None, None) if there's none."""
        entry = self._entries(namespace).get(key)
        if entry is None:
            return None, None
        return entry["data"], self.clock() - entry["fetched_at"]

    def set(self, namespace, key, data):
        self._entries(namespace)[key] = {"fetched_at": self.clock(), "data": data}
        self._changed.add(namespace)

    def save(self):
        if not self._changed:
            return
        self.directory.mkdir(parents=True, exist_ok=True)
        for namespace in self._changed:
            # Write to a temporary file first so an interrupted run can't leave half a cache
            path = self._path(namespace)
            temp = path.with_suffix(".tmp")
            temp.write_text(json.dumps(self._namespaces[namespace]), encoding="utf-8")
            os.replace(temp, path)
        self._changed.clear()
