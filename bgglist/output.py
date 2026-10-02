import csv
import json
from datetime import datetime, timezone
from pathlib import Path

def _alphabetical(games):
    return sorted(games, key=lambda game: game.name.lower())

def _prepare(filename):
    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path

def _year(game):
    return str(game.year) if game.year is not None else "N/A"

def _rank(game):
    return str(game.rank) if game.rank is not None else "-"

def print_table(games, show_owner=False):
    print("\nFiltered Board Game Collection:\n")

    header = f"{'Game':30} | {'Year':4} | {'Rank':5} | {'Players':9} | {'Time':5} | {'Age':3} | {'Category':25}"
    if show_owner:
        header += " | Owner"
    print(header)
    print("-" * len(header))

    for game in games:
        row = f"{game.name[:30]:30} | {_year(game):4} | {_rank(game):5} | {game.players:9} | {game.playing_time:<5} | {game.min_age:<3} | {game.category[:25]:25}"
        if show_owner:
            row += f" | {', '.join(game.owners)}"
        print(row)

def export_to_csv(games, filename="bgg_collection.csv"):
    with open(_prepare(filename), mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Game", "Year", "Board Game Rank", "Players", "Play time", "Min age", "Category", "Owner", "URL"])

        for game in _alphabetical(games):
            writer.writerow([
                game.name,
                _year(game),
                _rank(game),
                game.players,
                game.playing_time,
                game.min_age,
                game.category,
                ", ".join(game.owners),
                game.url,
            ])
    print(f"\n✅ Full collection exported to '{filename}'")

def export_to_json(games, filename, usernames):
    payload = {
        # BGG's terms ask for BoardGameGeek to be credited as the source of the data
        "source": "BoardGameGeek",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "users": list(usernames),
        "games": [game.to_dict() for game in _alphabetical(games)],
    }
    _prepare(filename).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✅ Full collection exported to '{filename}'")
