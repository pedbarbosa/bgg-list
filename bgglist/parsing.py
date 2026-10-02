import xml.etree.ElementTree as ET

from .errors import BGGError
from .games import Game

def attr(element, path, name="value", default=None):
    """An attribute of the first child matching path, or default if either is missing."""
    child = element.find(path)
    if child is None:
        return default
    return child.attrib.get(name, default)

def to_int(value, default=None):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

def _root(xml_text):
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        raise BGGError(f"BoardGameGeek sent a response that isn't valid XML ({e})") from e

    # Some errors, such as an unknown username, come back as XML with a 200 status
    if root.tag in ("errors", "error"):
        message = (root.findtext(".//message") or "unknown error").strip()
        raise BGGError(f"BoardGameGeek returned an error: {message}")
    return root

def parse_collection_ids(xml_text):
    # A collection lists a game once per copy owned
    return list(dict.fromkeys(item.get("objectid") for item in _root(xml_text).findall("item")))

def parse_things(xml_text):
    """Games in a thing response requested with stats=1."""
    games = []
    for item in _root(xml_text).findall("item"):
        games.append(Game(
            id=item.get("id"),
            # BGG lists every name a game is known by, and the primary one isn't always first
            name=attr(item, "name[@type='primary']") or attr(item, "name", default="Unknown"),
            # BGG uses 0 for an unknown year
            year=to_int(attr(item, "yearpublished")) or None,
            rank=to_int(attr(item, "statistics/ratings/ranks/rank[@name='boardgame']")),
            min_players=to_int(attr(item, "minplayers"), 0),
            max_players=to_int(attr(item, "maxplayers"), 0),
            playing_time=to_int(attr(item, "playingtime"), 0),
            min_age=to_int(attr(item, "minage"), 0),
            categories=[link.get("value") for link in item.findall("link[@type='boardgamecategory']")],
        ))
    return games
