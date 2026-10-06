import html
import xml.etree.ElementTree as ET

from .errors import BGGError

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

def parse_collection(xml_text):
    """Games in a collection response requested with stats=1, keyed by BGG id.

    The values are plain dicts of Game fields, so they can be cached as JSON.
    """
    games = {}
    for item in _root(xml_text).findall("item"):
        stats = item.find("stats")
        if stats is None:
            stats = ET.Element("stats")
        game_id = item.get("objectid")
        # A collection lists a game once per copy owned; the entries are the same game
        games[game_id] = {
            "id": game_id,
            "name": (item.findtext("name") or "Unknown").strip(),
            # BGG uses 0 for an unknown year
            "year": to_int(item.findtext("yearpublished")) or None,
            "rank": to_int(attr(stats, "rating/ranks/rank[@name='boardgame']")),
            "min_players": to_int(stats.get("minplayers"), 0),
            "max_players": to_int(stats.get("maxplayers"), 0),
            "playing_time": to_int(stats.get("playingtime"), 0),
        }
    return games

def parse_things(xml_text):
    """Details that rarely change, from a thing response, keyed by BGG id."""
    details = {}
    for item in _root(xml_text).findall("item"):
        details[item.get("id")] = {
            # BGG lists every name a game is known by, and the primary one isn't always first
            "name": attr(item, "name[@type='primary']") or attr(item, "name", default="Unknown"),
            "year": to_int(attr(item, "yearpublished")) or None,
            "min_age": to_int(attr(item, "minage"), 0),
            "categories": [link.get("value") for link in item.findall("link[@type='boardgamecategory']")],
            # Collections list expansions as board games; only the thing response tells them apart
            "expansion": item.get("type") == "boardgameexpansion",
            # BGG escapes the description twice (&amp;#10; for a new line); XML parsing undoes one
            "description": html.unescape(item.findtext("description") or "").strip(),
        }
    return details
