"""The combined collection of one or more users, built from the API and the cache.

Cached data is used while it's fresh. Once it's stale, BoardGameGeek is asked
for a new copy; if it can't provide one, the stale copy is used instead.
"""

from collections import defaultdict

from .client import THING_BATCH_SIZE
from .errors import BGGAuthError, BGGError
from .games import Game

# Collections change when games are bought or sold; the rank in them changes daily
COLLECTION_TTL = 60 * 60
# Names, years, ages and categories rarely change
DETAILS_TTL = 30 * 24 * 60 * 60

def _describe_age(seconds):
    for unit, size in (("day", 86400), ("hour", 3600), ("minute", 60)):
        if seconds >= size:
            count = int(seconds // size)
            return f"{count} {unit}{'' if count == 1 else 's'}"
    return "less than a minute"

def load_collection(client, cache, username, exclude_expansions=False, refresh=False, log=print):
    """A user's games keyed by BGG id, as plain dicts of Game fields."""
    key = f"{username.lower()}|{'base-games' if exclude_expansions else 'all'}"
    cached, age = cache.get("collections", key)
    if cached is not None and not refresh and age < COLLECTION_TTL:
        return cached

    try:
        games = client.get_collection(username, exclude_expansions)
    except BGGError as e:
        if cached is None:
            raise
        log(f"⚠️  {e}")
        log(f"   Using the copy of {username}'s collection cached {_describe_age(age)} ago.")
        return cached

    cache.set("collections", key, games)
    return games

def load_details(client, cache, game_ids, refresh=False, log=print):
    """Names, years, ages and categories keyed by BGG id, for the ids that have them."""
    details = {}
    to_fetch = []
    for game_id in game_ids:
        cached, age = cache.get("details", game_id)
        if cached is not None:
            details[game_id] = cached
        if cached is None or refresh or age >= DETAILS_TTL:
            to_fetch.append(game_id)

    for i in range(0, len(to_fetch), THING_BATCH_SIZE):
        batch = to_fetch[i:i + THING_BATCH_SIZE]
        try:
            fetched = client.get_things(batch)
        except BGGAuthError as e:
            # Every other batch would be rejected too
            log(f"⚠️  {e}")
            log("   Using cached game details where there are any.")
            break
        except BGGError as e:
            log(f"⚠️  {e}")
            log("   Using cached details for those games where there are any.")
            continue

        for game_id, data in fetched.items():
            cache.set("details", game_id, data)
            details[game_id] = data

    return details

def build_collection(client, cache, usernames, exclude_expansions=False, refresh=False, log=print):
    """Every game the users own, with who owns each one.

    Raises BGGAuthError if the key is rejected and there's no cached collection
    to fall back on; other errors only skip the user they affect.
    """
    entries = {}
    owners = defaultdict(set)
    try:
        for username in usernames:
            log(f"Fetching collection for {username}...")
            try:
                games = load_collection(client, cache, username, exclude_expansions, refresh, log)
            except BGGAuthError:
                raise
            except BGGError as e:
                log(f"Error with user '{username}': {e}")
                continue
            for game_id, entry in games.items():
                entries.setdefault(game_id, entry)
                owners[game_id].add(username)

        if not entries:
            return []

        log(f"Total unique games found: {len(entries)}")
        details = load_details(client, cache, list(entries), refresh, log)
    finally:
        cache.save()

    # A game without details (BGG unavailable, nothing cached) still has its collection data
    return [
        Game(**{**entry, **details.get(game_id, {}), "owners": sorted(owners[game_id])})
        for game_id, entry in entries.items()
    ]
