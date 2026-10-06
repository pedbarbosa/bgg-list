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
- 🌐 A responsive **web page** of the collection, served from a Docker container that keeps it up to date
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

> The `bgg-list` script needs the `bgg_list/` folder next to it, so copying the script on its own is no longer enough.

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
| `-o`, `--output FILE` | Where to write the CSV (default `bgg-list.csv`) |
| `--no-csv` | Don't write the CSV |
| `--json FILE` | Also write the full collection as JSON |
| `--no-table` | Don't print the table, or ask for its filter and sort |
| `--refresh` | Ask BGG for new data even where the cache is still fresh |
| `--cache-dir DIR` | Where to keep cached API results (default `~/.cache/bgg-list`) |
| `-h`, `--help` | Show the options |

## 💾 Cache

API results are cached in `~/.cache/bgg-list` (or `$XDG_CACHE_HOME/bgg-list`):

- **Collections**, including each game's rank, player count and play time, are reused for **an hour**.
- **Game details** (name, year, minimum age and categories) are reused for **30 days**, since they rarely change.

Cached data doesn't expire on its own. Once it's older than those times, the script asks BGG for a new copy. If BGG can't provide one (it's down, erroring or rejecting the key), the script says so and uses the cached copy instead. Use `--refresh` to ask BGG for everything again, or delete the folder to start over.

## 📁 Output

- A CSV file, `bgg-list.csv` in the working directory unless `-o` says otherwise.
- With `--json`, a JSON file with the same games (all categories included, and whether each is an expansion), the usernames, and when it was generated.
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

## 🌐 Web page

`site/` holds a static page that lists the collection with search, player-count, play-time and owner filters, and sorting. Expansions are hidden by default; the Expansions dropdown shows them, tagged "Expansion" (it only appears when the collection has any). It's a table on wide screens and cards on phones, and the filters are kept in the address so a filtered list can be shared (for example `?players=4&time=60&expansions=show`).

The page only reads a generated `collection.json`, so BoardGameGeek is only ever called from the server and the key never reaches a browser. The footer shows BGG's "Powered by BGG" logo (`site/assets/powered_by_K_01_SM.png`), linked to BoardGameGeek, which BGG's [XML API terms](https://boardgamegeek.com/wiki/page/XML_API_Terms_of_Use) require on public pages.

### Running it in a container

The `Dockerfile` builds an image that fetches the collection, serves the page on port 8000, and refreshes the collection on a schedule:

```
docker build -t bgg-list .
docker run -d --name bgg-list -p 8000:8000 \
  -e BGG_API_KEY=your-token-here \
  -e BGG_USERS=alice,bob \
  -v bgg-list-cache:/cache \
  bgg-list
```

Then open http://localhost:8000.

| Variable | What it does |
| --- | --- |
| `BGG_API_KEY` | Your BoardGameGeek API key (required) |
| `BGG_USERS` | Comma-separated BGG usernames (required) |
| `BGG_REFRESH_HOURS` | Hours between refreshes (default `24`) |
| `BGG_OPTIONS` | Extra `bgg-list` options for each refresh, such as `-x` to leave expansions out |
| `PORT` | Port to serve on inside the container (default `8000`) |

- Pass the key at run time (`-e`, `--env-file .env`, or your platform's secrets); it's never built into the image, and `.dockerignore` keeps `.env` out of it.
- Mount a volume on `/cache` so the API cache survives restarts and new versions of the image.
- If a refresh fails (BGG down, key rejected), the page keeps serving the last good data.
- The page is served by Python's built-in web server, which is fine for a home network. To put it on the internet, run it behind a reverse proxy that handles HTTPS, such as Caddy, Traefik or nginx.
- Arguments after the image name run `bgg-list` once instead, for example `docker run --rm -e BGG_API_KEY=... bgg-list -u alice -p 4`.

### Previewing it locally

```
./bgg-list -u alice,bob --no-csv --json site/collection.json
python3 -m http.server -d site
```

Then open http://localhost:8000. `site/collection.json` is ignored by Git.

## 📚 BoardGameGeek API

This project uses the [BoardGameGeek XML API2](https://boardgamegeek.com/wiki/page/BGG_XML_API2) to fetch:
- User collections, with stats (rank, player count, play time)
- Game details (primary name, year, minimum age, categories), up to 20 games per request

Every request sends your key as an `Authorization: Bearer` header to `https://boardgamegeek.com/xmlapi2` (BGG asks that the `www.` subdomain not be used). If BGG rejects the key (`401` or `403`) and there's nothing cached to fall back on, the script stops and tells you to check `BGG_API_KEY`. You can see your usage at [boardgamegeek.com/applications](https://boardgamegeek.com/applications) under "Usage".

The script is gentle with the API: requests are at least a second apart, rate limits (`429`) and server errors (`5xx`) are retried with increasing waits (honouring BGG's `Retry-After`), and the `202 Accepted` BGG sends while it prepares a collection is retried every 5 seconds for up to 2 minutes.

## 🛠️ Development

The code lives in the `bgg_list` package; `bgg-list` is a thin entry point. Everything else is named `bgg-list` (the repository, the command, the CSV and the cache folder); the package uses an underscore only because Python import names can't contain hyphens.

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

The web page's filtering and sorting have their own tests, run with Node 22:

```
node --test tests/test_site.mjs
```

GitHub Actions runs both on every pull request and push to `main`, on the Python version in `.python-version` with the pinned `requirements.txt`. It also checks that `pip install .` gives a working `bgg-list` command.
