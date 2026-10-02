import argparse
import os
from pathlib import Path

from dotenv import load_dotenv

from .cache import Cache, default_cache_dir
from .client import BGGClient, create_session
from .collection import build_collection
from .errors import BGGAuthError
from .games import SORT_FIELDS, filter_by_player_count, sort_games
from .output import export_to_csv, print_table

# The repository folder, where .env lives
ROOT = Path(__file__).resolve().parent.parent

def load_api_key():
    # Values already set in the environment take precedence over the .env file
    load_dotenv(ROOT / ".env")
    api_key = os.getenv("BGG_API_KEY", "").strip()
    if not api_key:
        raise SystemExit("❌ BGG_API_KEY is not set. Copy .env_example to .env and add your BoardGameGeek API key.")
    return api_key

def main():

    parser = argparse.ArgumentParser(description="Fetch BGG board game collections.", add_help=False)
    parser.add_argument('-u', '--users', help='Comma-separated list of BGG usernames')
    parser.add_argument('-p', '--players', help='Number of players', type=int)
    parser.add_argument('-s', '--sort', help='Field to sort by: name, rank, year, playtime', choices=SORT_FIELDS)
    parser.add_argument('-x', '--no-expansions', action='store_true', help='Leave expansions out of the collection')
    parser.add_argument('--refresh', action='store_true', help='Ask BGG for new data even where the cache is still fresh')
    parser.add_argument('--cache-dir', default=default_cache_dir(), help='Where to keep cached API results (default: %(default)s)')
    parser.add_argument('-h', '--help', action='help', help='Show this help message and exit')

    args = parser.parse_args()
    client = BGGClient(create_session(load_api_key()))

    if not args.users:
        args.users = input("Enter BoardGameGeek username(s) (comma-separated if multiple): ")
    usernames = [u.strip() for u in args.users.split(',') if u.strip()]

    try:
        all_games = build_collection(client, Cache(args.cache_dir), usernames, args.no_expansions, args.refresh)
    except BGGAuthError as e:
        raise SystemExit(f"❌ {e}")

    if not all_games:
        print("❌ No games found.")
        return

    # Export full collection to CSV (always alphabetical)
    export_to_csv(all_games)

    # Optional player num filter
    player_count = args.players
    if player_count is None:
        player_input = input("Filter by number of players? (press Enter to skip): ")
        player_count = int(player_input) if player_input.strip().isdigit() else None

    sort_field = args.sort
    if not sort_field:
        sort_field = input("Sort field (name, rank, year, playtime)? (press Enter to use default 'name'): ").strip().lower() or "name"
    while sort_field not in SORT_FIELDS:
        sort_field = input("Invalid sort field. Enter 'name', 'rank', 'year' or 'playtime' (press Enter to use default 'name'): ").strip().lower() or "name"

    filtered = filter_by_player_count(all_games, player_count)
    sorted_filtered = sort_games(filtered, sort_field)

    if not sorted_filtered:
        print("❌ No games match your filter.")
        return

    # Show owner column in table only if multiple users
    print_table(sorted_filtered, show_owner=(len(usernames) > 1))
