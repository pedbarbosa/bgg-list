import xml.etree.ElementTree as ET

from .games import Game

def parse_collection_ids(xml_text):
    root = ET.fromstring(xml_text)
    return [item.attrib['objectid'] for item in root.findall('item')]

def parse_things(xml_text):
    """Games in a thing response requested with stats=1."""
    games = []
    for item in ET.fromstring(xml_text).findall("item"):
        rank = None
        ranks = item.find("statistics").find("ratings").find("ranks")
        for entry in ranks.findall("rank"):
            if entry.attrib.get("name") == "boardgame":
                value = entry.attrib.get("value")
                if value.isdigit():
                    rank = int(value)
                break

        year = item.find("yearpublished").attrib.get("value", "")
        categories = [link.attrib['value'] for link in item.findall("link") if link.attrib.get("type") == "boardgamecategory"]

        games.append(Game(
            id=item.attrib.get("id"),
            name=item.find("name").attrib.get("value", "Unknown"),
            year=int(year) if year.isdigit() else None,
            rank=rank,
            min_players=int(item.find("minplayers").attrib.get("value", "1")),
            max_players=int(item.find("maxplayers").attrib.get("value", "1")),
            playing_time=int(item.find("playingtime").attrib.get("value", "0")),
            min_age=int(item.find("minage").attrib.get("value", "0")),
            categories=categories,
        ))
    return games
