import json
import tempfile
import unittest
from pathlib import Path

from bgg_list.cache import CACHE_VERSION, Cache
from tests.fakes import FakeClock

class CacheTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.directory = Path(temp.name) / "cache"
        self.clock = FakeClock()

    def cache(self):
        return Cache(self.directory, clock=self.clock)

    def test_missing_entry(self):
        self.assertEqual(self.cache().get("details", "13"), (None, None))

    def test_returns_data_with_its_age(self):
        cache = self.cache()
        cache.set("details", "13", {"name": "CATAN"})
        self.clock.advance(30)
        self.assertEqual(cache.get("details", "13"), ({"name": "CATAN"}, 30))

    def test_stale_entries_are_kept(self):
        cache = self.cache()
        cache.set("details", "13", {"name": "CATAN"})
        self.clock.advance(10 * 365 * 24 * 60 * 60)
        self.assertEqual(cache.get("details", "13")[0], {"name": "CATAN"})

    def test_saved_entries_survive_a_new_run(self):
        cache = self.cache()
        cache.set("details", "13", {"name": "CATAN"})
        cache.save()
        self.clock.advance(5)
        self.assertEqual(self.cache().get("details", "13"), ({"name": "CATAN"}, 5))

    def test_nothing_is_written_without_changes(self):
        cache = self.cache()
        cache.get("details", "13")
        cache.save()
        self.assertFalse(self.directory.exists())

    def test_ignores_a_cache_from_another_version(self):
        self.directory.mkdir()
        content = {"version": CACHE_VERSION + 1, "entries": {"13": {"fetched_at": 0, "data": {}}}}
        (self.directory / "details.json").write_text(json.dumps(content))
        self.assertEqual(self.cache().get("details", "13"), (None, None))

    def test_ignores_a_corrupt_cache(self):
        self.directory.mkdir()
        (self.directory / "details.json").write_text("{not json")
        self.assertEqual(self.cache().get("details", "13"), (None, None))

if __name__ == "__main__":
    unittest.main()
