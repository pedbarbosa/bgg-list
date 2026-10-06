import unittest

from bgg_list.games import Game, filter_by_player_count, sort_games

GAMES = [
    Game("1", "Azul", year=2017, rank=50, min_players=2, max_players=4, playing_time=45),
    Game("2", "brass", year=2018, rank=5, min_players=2, max_players=4, playing_time=120),
    Game("3", "Codenames", rank=None, min_players=2, max_players=8, playing_time=15),
    Game("4", "Agricola", year=2007, rank=None, min_players=1, max_players=5, playing_time=120),
]

def names(games):
    return [game.name for game in games]

class SortTest(unittest.TestCase):
    def test_name_ignores_case(self):
        self.assertEqual(names(sort_games(GAMES, "name")), ["Agricola", "Azul", "brass", "Codenames"])

    def test_rank_puts_unranked_games_last_by_name(self):
        self.assertEqual(names(sort_games(GAMES, "rank")), ["brass", "Azul", "Agricola", "Codenames"])

    def test_year_puts_unknown_years_last(self):
        self.assertEqual(names(sort_games(GAMES, "year")), ["Agricola", "Azul", "brass", "Codenames"])

    def test_playtime_breaks_ties_by_name(self):
        self.assertEqual(names(sort_games(GAMES, "playtime")), ["Codenames", "Azul", "Agricola", "brass"])

class FilterTest(unittest.TestCase):
    def test_keeps_games_for_that_player_count(self):
        self.assertEqual(names(filter_by_player_count(GAMES, 1)), ["Agricola"])
        self.assertEqual(names(filter_by_player_count(GAMES, 8)), ["Codenames"])

    def test_no_player_count_keeps_everything(self):
        self.assertEqual(filter_by_player_count(GAMES, None), GAMES)

class GameTest(unittest.TestCase):
    def test_summaries(self):
        game = Game("13", "CATAN", min_players=3, max_players=4, categories=["Economic", "Negotiation", "Dice"])
        self.assertEqual(game.players, "3-4")
        self.assertEqual(game.category, "Economic, Negotiation")
        self.assertEqual(game.url, "https://boardgamegeek.com/boardgame/13")

    def test_no_categories(self):
        self.assertEqual(Game("1", "Azul").category, "N/A")

    def test_to_dict_includes_every_field_and_the_url(self):
        data = Game("13", "CATAN", categories=["Economic"], owners=["alice"]).to_dict()
        self.assertEqual(data["categories"], ["Economic"])
        self.assertEqual(data["owners"], ["alice"])
        self.assertEqual(data["url"], "https://boardgamegeek.com/boardgame/13")

if __name__ == "__main__":
    unittest.main()
