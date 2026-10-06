# 🎲 BGG Collection Exporter

This Python script fetches your **BoardGameGeek (BGG)** board game collection and generates:
- A **CSV export** of your full collection with game stats and links
- An optional **JSON export** of the same data, for web pages or other tools
- A **printable table** (optional filtering/sorting) in the terminal

Perfect for tracking your library, sharing with friends, or organizing game nights!

## 🔧 Features

- ✅ Supports **one or more BGG usernames**
- 🎯 Filter games by **number of players**
- 📊 Sort by: `rank`, `name`, `year`, or `playtime`
- 🧑 Displays **owner(s)** when multiple users are provided
- 🧩 Optionally leaves **expansions** out
- 💾 **Caches** API results, and falls back on them when BGG is unavailable
- 🤖 Runs **unattended** (cron, CI) when there's no terminal to prompt
- 📁 CSV export with:
  - Game details
  - Categories
  - Owners
  - Direct **BoardGameGeek links**

## 🚀 Getting Started

### 1. Clone the repo

```
git clone https://github.com/pedbarbosa/bgg-list.git
cd bgg-list
```

> The `bgg-list` script needs the `bgglist/` folder next to it, so copying the script on its own is no longer enough.

### 2. Install Required Packages

Two external packages are required: `requests` and `python-dotenv`

You can install them with:

```
pip install -r requirements.txt
```

Then run `./bgg-list` from the repository folder. Or install the tool, which adds a `bgg-list` command you can run from any folder:

```
pip install .
```

### 3. Add your BoardGameGeek API key

BoardGameGeek requires every XML API request to carry an API key (BGG calls it a token). Without one, the API returns `401 Unauthorized`.

1. Register an application at [boardgamegeek.com/applications](https://boardgamegeek.com/applications). A non-commercial application is fine for personal use.
2. Once BGG approves it, create a token for the application.
3. Copy the example file and paste the token into it:

```
cp .env_example .env
```

```
BGG_API_KEY=your-token-here
```

`.env` is listed in `.gitignore`, so the key stays out of the repository. The script looks for the key in this order, using the first it finds:

1. A `BGG_API_KEY` already set in your environment
2. `.env` in the folder you run the command from
3. `.env` in the repository folder (when running from a clone)

If you installed with `pip install .`, keep `.env` in the folder you run `bgg-list` from, or set `BGG_API_KEY` in your shell profile.

## 🧪 Usage

Run the script with:

```
./bgg-list
```

You’ll be prompted to enter:

- One or more **BoardGameGeek usernames** (comma-separated)
- An optional **player count filter**
- An optional **field to sort by**

Example interaction:

```
Enter BoardGameGeek username(s) (comma-separated if multiple): alice,bob
Filter by number of players? (press Enter to skip): 4
Sort field (name, rank, year, playtime)? (press Enter to use default 'name'): playtime
```

Alternatively, you can pass in the values as options:

```
./bgg-list -u alice -p 4 -s playtime
```

When there's no terminal (for example under cron or in CI), the script doesn't prompt: pass usernames with `-u`; with no `-p` or `-s` it lists every game, sorted by name.

### Options

| Option | What it does |
| --- | --- |
| `-u`, `--users` | Comma-separated BGG usernames |
| `-p`, `--players` | Only list games for this number of players |
| `-s`, `--sort` | Sort the table by `name` (default), `rank`, `year` or `playtime` |
| `-x`, `--no-expansions` | Leave expansions out of the collection |
| `-o`, `--output FILE` | Where to write the CSV (default `bgg_collection.csv`) |
| `--no-csv` | Don't write the CSV |
| `--json FILE` | Also write the full collection as JSON |
| `--refresh` | Ask BGG for new data even where the cache is still fresh |
| `--cache-dir DIR` | Where to keep cached API results (default `~/.cache/bgg-list`) |
| `-h`, `--help` | Show the options |

## 💾 Cache

API results are cached in `~/.cache/bgg-list` (or `$XDG_CACHE_HOME/bgg-list`):

- **Collections**, including each game's rank, player count and play time, are reused for **an hour**.
- **Game details** (name, year, minimum age and categories) are reused for **30 days**, since they rarely change.

Cached data doesn't expire on its own. Once it's older than those times, the script asks BGG for a new copy. If BGG can't provide one (it's down, erroring or rejecting the key), the script says so and uses the cached copy instead. Use `--refresh` to ask BGG for everything again, or delete the folder to start over.

## 📁 Output

- A CSV file, `bgg_collection.csv` in the working directory unless `-o` says otherwise.
- With `--json`, a JSON file with the same games (all categories included), the usernames, and when it was generated.
- The CSV includes:

  - Game name  
  - Year published  
  - BGG Rank (or `–` if unranked)  
  - Min/Max Players  
  - Play time  
  - Minimum age  
  - Categories (up to 2)  
  - Owner(s)  
  - Direct URL to BGG page

## 📚 BoardGameGeek API

This project uses the [BoardGameGeek XML API2](https://boardgamegeek.com/wiki/page/BGG_XML_API2) to fetch:
- User collections, with stats (rank, player count, play time)
- Game details (primary name, year, minimum age, categories), up to 20 games per request

Every request sends your key as an `Authorization: Bearer` header to `https://boardgamegeek.com/xmlapi2` (BGG asks that the `www.` subdomain not be used). If BGG rejects the key (`401` or `403`) and there's nothing cached to fall back on, the script stops and tells you to check `BGG_API_KEY`. You can see your usage at [boardgamegeek.com/applications](https://boardgamegeek.com/applications) under "Usage".

The script is gentle with the API: requests are at least a second apart, rate limits (`429`) and server errors (`5xx`) are retried with increasing waits (honouring BGG's `Retry-After`), and the `202 Accepted` BGG sends while it prepares a collection is retried every 5 seconds for up to 2 minutes.

## 🛠️ Development

The code lives in the `bgglist` package; `bgg-list` is a thin entry point.

| Module | Responsibility |
| --- | --- |
| `client.py` | HTTP calls to the XML API: auth, retries, throttling, the 202 queue |
| `parsing.py` | BGG XML to plain data |
| `cache.py` | JSON cache files |
| `collection.py` | Combining users, owners and details, and the cache policy |
| `games.py` | The `Game` model, filtering and sorting |
| `output.py` | Terminal table, CSV and JSON |
| `cli.py` | Options, prompts and `.env` loading |

Run the tests (standard library only, nothing calls BGG):

```
python3 -m unittest discover
```
