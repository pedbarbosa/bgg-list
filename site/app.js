// Filtering and sorting first (tested with node --test), then the page itself.

const byName = (a, b) => a.name.localeCompare(b.name, undefined, { sensitivity: "base" });

// Unranked games and unknown years sort last, as in the command-line tool
const missingLast = (field) => (a, b) => {
  const x = a[field];
  const y = b[field];
  if (x == null || y == null) {
    return (x == null) - (y == null) || byName(a, b);
  }
  return x - y || byName(a, b);
};

const COMPARATORS = {
  name: byName,
  rank: missingLast("rank"),
  year: missingLast("year"),
  playtime: (a, b) => a.playing_time - b.playing_time || byName(a, b),
};

export function sortGames(games, field) {
  return [...games].sort(COMPARATORS[field] ?? byName);
}

export function filterGames(games, { query = "", players = null, maxTime = null, owner = "", hideExpansions = false } = {}) {
  const needle = query.trim().toLowerCase();
  const matches = (text) => text.toLowerCase().includes(needle);
  return games.filter((game) =>
    (!hideExpansions || !game.expansion) &&
    (!needle || matches(game.name) || game.categories.some(matches)) &&
    (players == null || (game.min_players <= players && players <= game.max_players)) &&
    // A game with an unknown play time (0) can't promise to fit
    (maxTime == null || (game.playing_time > 0 && game.playing_time <= maxTime)) &&
    (!owner || game.owners.includes(owner))
  );
}

export function formatPlayers({ min_players: min, max_players: max }) {
  if (!min && !max) return "–";
  return min === max ? String(min) : `${min}–${max}`;
}

// The page

const MAX_PLAYER_OPTION = 12;

function readCriteria(form) {
  const data = new FormData(form);
  const number = (key) => (data.get(key) ? Number(data.get(key)) : null);
  return {
    query: data.get("q") ?? "",
    players: number("players"),
    maxTime: number("time"),
    owner: data.get("owner") ?? "",
    // Expansions are hidden unless asked for
    hideExpansions: data.get("expansions") !== "show",
    sort: data.get("sort") || "name",
  };
}

// Keep the filters in the address so a filtered list can be shared
function saveToUrl(form) {
  const params = new URLSearchParams();
  for (const [key, value] of new FormData(form)) {
    if (value && !(key === "sort" && value === "name")) params.set(key, value);
  }
  const search = params.toString();
  history.replaceState(null, "", search ? `?${search}` : location.pathname);
}

function restoreFromUrl(form) {
  for (const [key, value] of new URLSearchParams(location.search)) {
    const field = form.elements.namedItem(key);
    if (field) field.value = value;
  }
}

function addOptions(select, values, label = String) {
  select.append(...values.map((value) => new Option(label(value), value)));
}

function addCell(row, label, content, className) {
  const cell = row.insertCell();
  cell.dataset.label = label;
  if (className) cell.className = className;
  cell.append(...(Array.isArray(content) ? content : [content]));
}

function renderRows(tbody, games, showOwners) {
  tbody.replaceChildren(...games.map((game) => {
    const row = document.createElement("tr");
    const link = Object.assign(document.createElement("a"), {
      href: game.url,
      textContent: game.name,
      target: "_blank",
      rel: "noopener",
    });
    const name = [link];
    if (game.expansion) {
      name.push(Object.assign(document.createElement("span"), { className: "tag", textContent: "Expansion" }));
    }
    addCell(row, "Game", name, "name");
    addCell(row, "Year", String(game.year ?? "–"));
    addCell(row, "Rank", String(game.rank ?? "–"));
    addCell(row, "Players", formatPlayers(game));
    addCell(row, "Time", game.playing_time ? `${game.playing_time} min` : "–");
    addCell(row, "Age", game.min_age ? `${game.min_age}+` : "–");
    addCell(row, "Categories", game.categories.join(", ") || "–", "categories");
    if (showOwners) addCell(row, "Owner", game.owners.join(", "), "owner");
    return row;
  }));
}

function showMessage(text) {
  const message = document.getElementById("message");
  message.textContent = text;
  message.hidden = false;
}

async function init() {
  const form = document.getElementById("filters");
  const table = document.getElementById("games");
  const count = document.getElementById("count");

  let data;
  try {
    const response = await fetch("collection.json", { cache: "no-cache" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    data = await response.json();
  } catch (error) {
    document.getElementById("meta").textContent = "";
    showMessage(`Couldn't load the collection (${error.message}).`);
    return;
  }

  const games = data.games;
  const showOwners = data.users.length > 1;
  const updated = new Date(data.generated_at).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
  document.getElementById("meta").textContent =
    `${games.length} games owned by ${data.users.join(", ")} · Updated ${updated}`;

  const mostPlayers = Math.min(MAX_PLAYER_OPTION, Math.max(1, ...games.map((game) => game.max_players)));
  addOptions(form.elements.players, Array.from({ length: mostPlayers }, (_, i) => i + 1),
    (n) => `${n} player${n === 1 ? "" : "s"}`);
  if (showOwners) {
    addOptions(form.elements.owner, data.users);
    document.getElementById("owner-filter").hidden = false;
    document.getElementById("owner-column").hidden = false;
  }
  const expansions = games.filter((game) => game.expansion).length;
  // Only offer the choice when the collection has expansions
  document.getElementById("expansions-filter").hidden = expansions === 0;
  restoreFromUrl(form);

  const update = () => {
    const criteria = readCriteria(form);
    const shown = sortGames(filterGames(games, criteria), criteria.sort);
    renderRows(table.tBodies[0], shown, showOwners);
    table.hidden = shown.length === 0;
    document.getElementById("message").hidden = true;
    if (shown.length === 0) showMessage("No games match these filters.");
    count.textContent = shown.length === games.length
      ? `Showing all ${games.length} games`
      : `Showing ${shown.length} of ${games.length} games`;
    // Only count the expansions the other filters would have shown
    const hidden = criteria.hideExpansions
      ? filterGames(games, { ...criteria, hideExpansions: false }).length - shown.length
      : 0;
    if (hidden > 0) {
      count.textContent += ` (${hidden} expansion${hidden === 1 ? "" : "s"} hidden)`;
    }
    saveToUrl(form);
  };

  form.addEventListener("input", update);
  form.addEventListener("submit", (event) => event.preventDefault());
  // Fields only hold their reset values after the reset event has finished
  form.addEventListener("reset", () => setTimeout(update));
  update();
}

if (typeof document !== "undefined") init();
