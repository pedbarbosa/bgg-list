import time
import xml.etree.ElementTree as ET

import requests

from .parsing import parse_collection_ids, parse_things

# BGG asks for the bare domain: the www. subdomain can interfere with authorization
API_BASE = "https://boardgamegeek.com/xmlapi2"

def create_session(api_key):
    session = requests.Session()
    session.headers["Authorization"] = f"Bearer {api_key}"
    return session

def check_auth(response):
    if response.status_code in (401, 403):
        raise SystemExit(f"❌ BoardGameGeek rejected the API key ({response.status_code}). Check BGG_API_KEY in your .env file.")

def fetch_collection(session, username):
    print(f"Fetching collection for {username}...")
    url = f"{API_BASE}/collection?username={username}&own=1"
    response = session.get(url)

    while response.status_code == 202:
        print(f"{username}'s collection not ready. Retrying in 5 seconds...")
        time.sleep(5)
        response = session.get(url)

    check_auth(response)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch collection for {username}: {response.status_code}")

    return parse_collection_ids(response.text)

def fetch_game_details(session, game_ids, id_to_owners):
    games = {}

    for i in range(0, len(game_ids), 20):
        batch_ids = ",".join(game_ids[i:i+20])
        response = session.get(f"{API_BASE}/thing?id={batch_ids}&stats=1")
        time.sleep(1)

        check_auth(response)
        if response.status_code != 200:
            print(f"Failed to fetch batch: {batch_ids}")
            continue

        try:
            batch = parse_things(response.text)
        except ET.ParseError:
            print("Parse error for batch:", batch_ids)
            continue

        for game in batch:
            game.owners = sorted(id_to_owners.get(game.id, []))
            games[game.id] = game

    return list(games.values())
