"""Stand-ins for BoardGameGeek, the clock and files, shared by the tests."""

from pathlib import Path

from bgg_list.errors import BGGError

FIXTURES = Path(__file__).parent / "fixtures"

def fixture(name):
    return (FIXTURES / name).read_text(encoding="utf-8")

def entry(game_id, name, rank=None, min_players=2, max_players=4, playing_time=60, year=2020):
    """A collection entry, as parse_collection returns it."""
    return {
        "id": game_id,
        "name": name,
        "year": year,
        "rank": rank,
        "min_players": min_players,
        "max_players": max_players,
        "playing_time": playing_time,
    }

def details(name, min_age=10, categories=("Strategy",), year=2020, expansion=False):
    """Game details, as parse_things returns them."""
    return {"name": name, "year": year, "min_age": min_age, "categories": list(categories), "expansion": expansion}

class FakeClock:
    def __init__(self, now=1_000_000.0):
        self.now = now

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds

class FakeClient:
    """A BGGClient that answers from dictionaries and records each call."""

    def __init__(self, collections=None, things=None, collection_error=None, things_error=None):
        self.collections = collections or {}
        self.things = things or {}
        self.collection_error = collection_error
        self.things_error = things_error
        self.collection_calls = []
        self.thing_calls = []

    def get_collection(self, username, exclude_expansions=False):
        self.collection_calls.append((username, exclude_expansions))
        if self.collection_error:
            raise self.collection_error
        if username not in self.collections:
            raise BGGError("BoardGameGeek returned an error: Invalid username specified")
        return dict(self.collections[username])

    def get_things(self, game_ids):
        self.thing_calls.append(list(game_ids))
        if self.things_error:
            raise self.things_error
        return {game_id: self.things[game_id] for game_id in game_ids if game_id in self.things}
