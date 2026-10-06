from dataclasses import asdict, dataclass, field

@dataclass
class Game:
    id: str
    name: str
    year: int | None = None
    rank: int | None = None
    min_players: int = 0
    max_players: int = 0
    playing_time: int = 0
    min_age: int = 0
    categories: list[str] = field(default_factory=list)
    expansion: bool = False
    owners: list[str] = field(default_factory=list)

    @property
    def url(self):
        return f"https://boardgamegeek.com/boardgame/{self.id}"

    @property
    def players(self):
        return f"{self.min_players}-{self.max_players}"

    @property
    def category(self):
        # Short summary for the table and CSV: the first two categories
        return ", ".join(self.categories[:2]) if self.categories else "N/A"

    def to_dict(self):
        return {**asdict(self), "url": self.url}

SORT_FIELDS = ("name", "rank", "year", "playtime")

# Unranked games and games without a year sort last; ties sort by name
_SORT_KEYS = {
    "name": lambda game: game.name.lower(),
    "rank": lambda game: (game.rank is None, game.rank or 0, game.name.lower()),
    "year": lambda game: (game.year is None, game.year or 0, game.name.lower()),
    "playtime": lambda game: (game.playing_time, game.name.lower()),
}

def filter_by_player_count(games, player_count):
    if player_count is None:
        return list(games)
    return [game for game in games if game.min_players <= player_count <= game.max_players]

def sort_games(games, sort_field):
    return sorted(games, key=_SORT_KEYS[sort_field])
