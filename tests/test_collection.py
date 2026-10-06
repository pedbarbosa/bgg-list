import tempfile
import unittest
from pathlib import Path

from bgg_list.cache import Cache
from bgg_list.collection import COLLECTION_TTL, DETAILS_TTL, build_collection
from bgg_list.errors import BGGAuthError, BGGError
from tests.fakes import FakeClient, FakeClock, details, entry

COLLECTIONS = {
    "alice": {"13": entry("13", "Catan", rank=500), "822": entry("822", "Carcassonne", rank=200)},
    "bob": {"13": entry("13", "Catan", rank=500)},
}
THINGS = {"13": details("CATAN", categories=["Economic"]), "822": details("Carcassonne")}

def many_games(count):
    games = {str(i): entry(str(i), f"Game {i}") for i in range(count)}
    return {"alice": games}, {game_id: details(f"Game {game_id}") for game_id in games}

class BuildCollectionTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.clock = FakeClock()
        self.cache = Cache(Path(temp.name), clock=self.clock)
        self.logs = []

    def build(self, client, usernames=("alice", "bob"), **options):
        games = build_collection(client, self.cache, list(usernames), log=self.logs.append, **options)
        return {game.id: game for game in games}

    def test_combines_users_and_details(self):
        games = self.build(FakeClient(COLLECTIONS, THINGS))
        self.assertEqual(games["13"].owners, ["alice", "bob"])
        self.assertEqual(games["13"].name, "CATAN")
        self.assertEqual(games["13"].categories, ["Economic"])
        self.assertEqual(games["13"].rank, 500)
        self.assertEqual(games["822"].owners, ["alice"])

    def test_fresh_cache_needs_no_api_calls(self):
        self.build(FakeClient(COLLECTIONS, THINGS))
        client = FakeClient(COLLECTIONS, THINGS)
        games = self.build(client)
        self.assertEqual((client.collection_calls, client.thing_calls), ([], []))
        self.assertEqual(games["13"].name, "CATAN")

    def test_stale_collections_are_fetched_again_but_fresh_details_are_not(self):
        self.build(FakeClient(COLLECTIONS, THINGS))
        self.clock.advance(COLLECTION_TTL)
        client = FakeClient(COLLECTIONS, THINGS)
        self.build(client)
        self.assertEqual(len(client.collection_calls), 2)
        self.assertEqual(client.thing_calls, [])

    def test_stale_details_are_fetched_again(self):
        self.build(FakeClient(COLLECTIONS, THINGS))
        self.clock.advance(DETAILS_TTL)
        client = FakeClient(COLLECTIONS, THINGS)
        self.build(client)
        self.assertEqual(client.thing_calls, [["13", "822"]])

    def test_refresh_fetches_everything(self):
        self.build(FakeClient(COLLECTIONS, THINGS))
        client = FakeClient(COLLECTIONS, THINGS)
        self.build(client, refresh=True)
        self.assertEqual(len(client.collection_calls), 2)
        self.assertEqual(client.thing_calls, [["13", "822"]])

    def test_stale_data_stands_in_when_bgg_fails(self):
        self.build(FakeClient(COLLECTIONS, THINGS))
        self.clock.advance(DETAILS_TTL)
        error = BGGError("Couldn't reach BoardGameGeek")
        games = self.build(FakeClient(collection_error=error, things_error=error))
        self.assertEqual(games["13"].name, "CATAN")
        self.assertEqual(games["13"].owners, ["alice", "bob"])
        self.assertTrue(any("cached 30 days ago" in line for line in self.logs))

    def test_rejected_key_falls_back_to_the_cache(self):
        self.build(FakeClient(COLLECTIONS, THINGS))
        games = self.build(FakeClient(collection_error=BGGAuthError("rejected")), refresh=True)
        self.assertEqual(set(games), {"13", "822"})

    def test_rejected_key_without_a_cache_raises(self):
        with self.assertRaises(BGGAuthError):
            self.build(FakeClient(collection_error=BGGAuthError("rejected")))

    def test_other_errors_only_skip_that_user(self):
        games = self.build(FakeClient(COLLECTIONS, THINGS), usernames=["alice", "nobody"])
        self.assertEqual(set(games), {"13", "822"})
        self.assertIn("Error with user 'nobody': BoardGameGeek returned an error: Invalid username specified", self.logs)

    def test_no_games(self):
        self.assertEqual(build_collection(FakeClient(), self.cache, ["nobody"], log=self.logs.append), [])

    def test_details_are_fetched_in_batches_of_twenty(self):
        collections, things = many_games(45)
        client = FakeClient(collections, things)
        self.build(client, usernames=["alice"])
        self.assertEqual([len(batch) for batch in client.thing_calls], [20, 20, 5])

    def test_a_game_without_details_keeps_its_collection_data(self):
        games = self.build(FakeClient(COLLECTIONS, things_error=BGGError("BoardGameGeek returned 500")))
        self.assertEqual(games["13"].name, "Catan")
        self.assertEqual(games["13"].categories, [])

    def test_a_rejected_key_stops_further_detail_batches(self):
        collections, things = many_games(45)
        client = FakeClient(collections, things, things_error=BGGAuthError("rejected"))
        games = self.build(client, usernames=["alice"])
        self.assertEqual(len(client.thing_calls), 1)
        self.assertEqual(len(games), 45)

    def test_collections_with_and_without_expansions_are_cached_separately(self):
        self.build(FakeClient(COLLECTIONS, THINGS), usernames=["alice"])
        client = FakeClient(COLLECTIONS, THINGS)
        self.build(client, usernames=["alice"], exclude_expansions=True)
        self.assertEqual(client.collection_calls, [("alice", True)])

if __name__ == "__main__":
    unittest.main()
