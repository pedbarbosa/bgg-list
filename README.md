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

Only one external package is required: `requests`

You can install it with:

```
pip install -r requirements.txt
```

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

Note: The API sometimes responds with `202 Accepted` while it queues your request — the script handles this automatically with retries.
