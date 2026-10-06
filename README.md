# 🎲 BGG Collection Exporter

This Python script fetches your **BoardGameGeek (BGG)** board game collection and generates:
- A **CSV export** of your full collection with game stats and links
- A **printable table** (optional filtering/sorting) in the terminal

Perfect for tracking your library, sharing with friends, or organizing game nights!

## 🔧 Features

- ✅ Supports **one or more BGG usernames**
- 🎯 Filter games by **number of players**
- 📊 Sort by: `rank`, `name`, `year`, or `playtime`
- 🧑 Displays **owner(s)** when multiple users are provided
- 📁 CSV export with:
  - Game details
  - Categories
  - Owners
  - Direct **BoardGameGeek links**

## 🚀 Getting Started

### 1. Clone the repo or copy the script

```
git clone https://github.com/pedbarbosa/bgg-list.git
cd bgg-list
```

> Or simply download the `bgg-list` file directly.

### 2. Install Required Packages

Two external packages are required: `requests` and `python-dotenv`

You can install them with:

```
pip install -r requirements.txt
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

`.env` is listed in `.gitignore`, so the key stays out of the repository. The script reads `.env` from its own folder; a `BGG_API_KEY` already set in your environment takes precedence.

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
Enter BoardGameGeek username(s): alice,bob
Filter by number of players? (press Enter to skip): 4
Sort by field: name, rank, year, playtime
Enter sort field (default = rank): playtime
```

Alternatively, you can pass in the values as options:

```
./bgg-list -u alice -p 4 -s playtime
```

## 📁 Output

- A CSV file called `bgg_collection.csv` will be saved in the working directory.
- The file includes:

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
- User collections
- Game details and stats

Every request sends your key as an `Authorization: Bearer` header to `https://boardgamegeek.com/xmlapi2` (BGG asks that the `www.` subdomain not be used). If BGG rejects the key (`401` or `403`), the script stops and tells you to check `BGG_API_KEY`. You can see your usage at [boardgamegeek.com/applications](https://boardgamegeek.com/applications) under "Usage".

Note: The API sometimes responds with `202 Accepted` while it queues your request — the script handles this automatically with retries.
