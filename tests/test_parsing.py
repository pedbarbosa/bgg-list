import unittest
import xml.etree.ElementTree as ET

from bgg_list.errors import BGGError
from bgg_list.parsing import attr, parse_collection, parse_things, to_int
from tests.fakes import fixture

class AttrTest(unittest.TestCase):
    def setUp(self):
        self.item = ET.fromstring('<item><name type="alternate" value="B"/><name type="primary" value="A"/><minage/></item>')

    def test_returns_the_attribute(self):
        self.assertEqual(attr(self.item, "name"), "B")

    def test_follows_predicates(self):
        self.assertEqual(attr(self.item, "name[@type='primary']"), "A")

    def test_missing_child_returns_default(self):
        self.assertEqual(attr(self.item, "yearpublished", default="N/A"), "N/A")

    def test_missing_attribute_returns_default(self):
        self.assertEqual(attr(self.item, "minage", default="0"), "0")

class ToIntTest(unittest.TestCase):
    def test_converts_numbers(self):
        self.assertEqual(to_int("12"), 12)

    def test_falls_back_for_text_and_none(self):
        self.assertIsNone(to_int("Not Ranked"))
        self.assertEqual(to_int(None, 0), 0)

class ParseCollectionTest(unittest.TestCase):
    def setUp(self):
        self.games = parse_collection(fixture("collection.xml"))

    def test_lists_each_game_once_even_with_several_copies(self):
        self.assertEqual(list(self.games), ["13", "174430", "325", "9999"])

    def test_reads_the_stats(self):
        self.assertEqual(self.games["13"], {
            "id": "13",
            "name": "CATAN",
            "year": 1995,
            "rank": 500,
            "min_players": 3,
            "max_players": 4,
            "playing_time": 120,
        })

    def test_uses_the_board_game_rank_rather_than_a_family_rank(self):
        self.assertEqual(self.games["174430"]["rank"], 3)

    def test_unranked_games_have_no_rank(self):
        self.assertIsNone(self.games["325"]["rank"])

    def test_missing_stats_and_year_fall_back_to_defaults(self):
        self.assertEqual(self.games["9999"], {
            "id": "9999",
            "name": "Homemade Prototype",
            "year": None,
            "rank": None,
            "min_players": 0,
            "max_players": 0,
            "playing_time": 0,
        })

    def test_error_response_raises(self):
        with self.assertRaisesRegex(BGGError, "Invalid username specified"):
            parse_collection(fixture("errors.xml"))

    def test_invalid_xml_raises(self):
        with self.assertRaisesRegex(BGGError, "isn't valid XML"):
            parse_collection("<items><item>")

class ParseThingsTest(unittest.TestCase):
    def setUp(self):
        self.details = parse_things(fixture("thing.xml"))

    def test_reads_the_details_and_only_categories_from_links(self):
        self.assertEqual(self.details["13"], {
            "name": "CATAN",
            "year": 1995,
            "min_age": 10,
            "categories": ["Economic", "Negotiation"],
            "expansion": False,
        })

    def test_uses_the_primary_name_even_when_it_is_not_first(self):
        self.assertEqual(self.details["174430"]["name"], "Gloomhaven")

    def test_recognises_expansions(self):
        self.assertTrue(self.details["325"]["expansion"])
        self.assertFalse(self.details["174430"]["expansion"])

    def test_year_zero_and_missing_fields_fall_back_to_defaults(self):
        self.assertEqual(self.details["325"], {
            "name": "CATAN: Seafarers",
            "year": None,
            "min_age": 0,
            "categories": [],
            "expansion": True,
        })

if __name__ == "__main__":
    unittest.main()
