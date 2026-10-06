import csv
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from bgg_list.games import Game
from bgg_list.output import export_to_csv, export_to_json, print_table

GAMES = [
    Game("822", "Carcassonne", year=2000, rank=200, min_players=2, max_players=5, playing_time=45,
         min_age=7, categories=["City Building", "Medieval", "Territory"], owners=["alice"]),
    Game("13", "CATAN", year=None, rank=None, min_players=3, max_players=4, playing_time=120,
         min_age=10, owners=["alice", "bob"]),
]

class ExportTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        # A folder that doesn't exist yet, to check exports create it
        self.folder = Path(temp.name) / "out"

    def test_csv(self):
        path = self.folder / "games.csv"
        with redirect_stdout(io.StringIO()):
            export_to_csv(GAMES, path)
        with open(path, newline="", encoding="utf-8") as file:
            rows = list(csv.reader(file))
        self.assertEqual(rows, [
            ["Game", "Year", "Board Game Rank", "Players", "Play time", "Min age", "Category", "Owner", "URL"],
            ["Carcassonne", "2000", "200", "2-5", "45", "7", "City Building, Medieval", "alice", "https://boardgamegeek.com/boardgame/822"],
            ["CATAN", "N/A", "-", "3-4", "120", "10", "N/A", "alice, bob", "https://boardgamegeek.com/boardgame/13"],
        ])

    def test_json(self):
        path = self.folder / "games.json"
        with redirect_stdout(io.StringIO()):
            export_to_json(GAMES, path, ["alice", "bob"])
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(payload["source"], "BoardGameGeek")
        self.assertEqual(payload["users"], ["alice", "bob"])
        self.assertEqual([game["name"] for game in payload["games"]], ["Carcassonne", "CATAN"])
        self.assertEqual(payload["games"][0]["categories"], ["City Building", "Medieval", "Territory"])
        self.assertIsNone(payload["games"][1]["rank"])

class PrintTableTest(unittest.TestCase):
    def table(self, show_owner):
        output = io.StringIO()
        with redirect_stdout(output):
            print_table(GAMES, show_owner=show_owner)
        return output.getvalue()

    def test_rows(self):
        table = self.table(show_owner=False)
        self.assertIn("CATAN                          | N/A  | -     | 3-4       | 120   | 10  | N/A", table)
        self.assertNotIn("Owner", table)

    def test_owner_column(self):
        table = self.table(show_owner=True)
        self.assertIn("| Owner", table)
        self.assertIn("| alice, bob", table)

if __name__ == "__main__":
    unittest.main()
