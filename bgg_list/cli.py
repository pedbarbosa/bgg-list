import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from .cache import Cache, default_cache_dir
from .client import BGGClient, create_session
from .collection import build_collection
from .errors import BGGAuthError
from .games import SORT_FIELDS, filter_by_player_count, sort_games
from .output import export_to_csv, export_to_json, print_table

# The repository folder when running from a clone (site-packages when installed)
ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SORT = "name"

def load_api_key():
    # load_dotenv never overrides a value that's already set, so the environment wins,
    # then a .env in the current folder, then one in the repository folder
    for env_file in (Path.cwd() / ".env", ROOT / ".env"):
        load_dotenv(env_file)
    api_key = os.getenv("BGG_API_KEY", "").strip()
    if not api_key:
        raise SystemExit("❌ BGG_API_KEY is not set. Copy .env_example to .env and add your BoardGameGeek API key.")
    return api_key

def ask(prompt):
    # Only prompt when someone is at the terminal, so the script can also run unattended
    return input(prompt) if sys.stdin.isatty() else ""

def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Fetch BGG board game collections.", add_help=False)
    parser.add_argument('-u', '--users', help='Comma-separated list of BGG usernames')
    parser.add_argument('-p', '--players', help='Only list games for this number of players', type=int)
    parser.add_argument('-s', '--sort', choices=SORT_FIELDS, help=f'Field to sort the table by (default: {DEFAULT_SORT})')
    parser.add_argument('-x', '--no-expansions', action='store_true', help='Leave expansions out of the collection')
    parser.add_argument('-o', '--output', default='bgg-list.csv', metavar='FILE', help='CSV file for the full collection (default: %(default)s)')
    parser.add_argument('--no-csv', action='store_true', help="Don't write the CSV file")
    parser.add_argument('--json', metavar='FILE', help='Also write the full collection to this JSON file')
    parser.add_argument('--refresh', action='store_true', help='Ask BGG for new data even where the cache is still fresh')
    parser.add_argument('--cache-dir', default=default_cache_dir(), help='Where to keep cached API results (default: %(default)s)')
    parser.add_argument('-h', '--help', action='help', help='Show this help message and exit')
    return parser.parse_args(argv)

def choose_sort_field():
    sort_field = ask(f"Sort field (name, rank, year, playtime)? (press Enter to use default '{DEFAULT_SORT}'): ").strip().lower() or DEFAULT_SORT
    while sort_field not in SORT_FIELDS:
        sort_field = ask(f"Invalid sort field. Enter 'name', 'rank', 'year' or 'playtime' (press Enter to use default '{DEFAULT_SORT}'): ").strip().lower() or DEFAULT_SORT
    return sort_field

def main(argv=None):
    args = parse_args(argv)
    client = BGGClient(create_session(load_api_key()))

    users = args.users or ask("Enter BoardGameGeek username(s) (comma-separated if multiple): ")
    usernames = [u.strip() for u in users.split(',') if u.strip()]
    if not usernames:
        raise SystemExit("❌ No usernames given. Pass them with -u, for example: ./bgg-list -u alice,bob")

    try:
        all_games = build_collection(client, Cache(args.cache_dir), usernames, args.no_expansions, args.refresh)
    except BGGAuthError as e:
        raise SystemExit(f"❌ {e}")

    if not all_games:
        print("❌ No games found.")
        return

    # The exports always hold the full collection, in alphabetical order
    if not args.no_csv:
        export_to_csv(all_games, args.output)
    if args.json:
        export_to_json(all_games, args.json, usernames)

    player_count = args.players
    if player_count is None:
        answer = ask("Filter by number of players? (press Enter to skip): ").strip()
        player_count = int(answer) if answer.isdigit() else None

    sort_field = args.sort or choose_sort_field()

    filtered = filter_by_player_count(all_games, player_count)
    sorted_filtered = sort_games(filtered, sort_field)

    if not sorted_filtered:
        print("❌ No games match your filter.")
        return

    # Show owner column in table only if multiple users
    print_table(sorted_filtered, show_owner=(len(usernames) > 1))
