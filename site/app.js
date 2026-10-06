// Filtering and sorting first (tested with node --test), then the page itself.

const byName = (a, b) => a.name.localeCompare(b.name, undefined, { sensitivity: "base" });

// What each sortable column sorts by; null means unknown (unranked, no year, 0 players...)
const SORT_KEYS = {
  name: null,
  year: (game) => game.year,
  rank: (game) => game.rank,
  players: (game) => (game.min_players ? [game.min_players, game.max_players] : null),
  playtime: (game) => game.playing_time || null,
  age: (game) => game.min_age || null,
};

export const SORT_FIELDS = Object.keys(SORT_KEYS);

const compare = (x, y) => (Array.isArray(x) ? x[0] - y[0] || x[1] - y[1] : x - y);

export function sortGames(games, field = "name", direction = "asc") {
  const sign = direction === "desc" ? -1 : 1;
  const key = SORT_KEYS[field];
  return [...games].sort((a, b) => {
    if (!key) return sign * byName(a, b);
    const x = key(a);
    const y = key(b);
    // Unknown values sort last whichever way the column is sorted; ties sort by name
    if (x == null || y == null) return (x == null) - (y == null) || byName(a, b);
    return sign * compare(x, y) || byName(a, b);
  });
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
  };
}

// Keep the filters and sort in the address so a filtered list can be shared
function saveToUrl(form, sort) {
  const params = new URLSearchParams();
  for (const [key, value] of new FormData(form)) {
    if (value) params.set(key, value);
  }
  if (sort.field !== "name") params.set("sort", sort.field);
  if (sort.direction === "desc") params.set("order", "desc");
  const search = params.toString();
  history.replaceState(null, "", search ? `?${search}` : location.pathname);
}

function restoreFromUrl(form, sort) {
  const params = new URLSearchParams(location.search);
  for (const [key, value] of params) {
    const field = form.elements.namedItem(key);
    if (field) field.value = value;
  }
  if (SORT_FIELDS.includes(params.get("sort"))) sort.field = params.get("sort");
  if (params.get("order") === "desc") sort.direction = "desc";
}

function showSort(table, sort) {
  for (const cell of table.tHead.rows[0].cells) {
    if (!cell.dataset.sort) continue;
    const active = cell.dataset.sort === sort.field;
    cell.setAttribute("aria-sort", !active ? "none" : sort.direction === "asc" ? "ascending" : "descending");
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

function detailsButton(kind, label, game, text) {
  const button = Object.assign(document.createElement("button"), { type: "button", className: `details ${kind}` });
  Object.assign(button.dataset, { kind: label, game: game.name, text });
  button.setAttribute("aria-label", `${label}: ${game.name}`);
  button.setAttribute("aria-controls", "popover");
  button.setAttribute("aria-expanded", "false");
  button.append(Object.assign(document.createElement("span"), { className: "label", textContent: label }));
  return button;
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
    if (showOwners) addCell(row, "Owner", game.owners.join(", "), "owner");
    const details = [];
    if (game.description) details.push(detailsButton("about", "About", game, game.description));
    if (game.categories.length) details.push(detailsButton("categories", "Categories", game, game.categories.join(", ")));
    addCell(row, "Details", details, "details-cell");
    return row;
  }));
}

// The popup for a game's description or categories: it opens on hover with a
// mouse, or on a tap or click, and closes with its × button, Escape, or a tap elsewhere
function setUpPopover(table) {
  const popover = document.getElementById("popover");
  const kind = document.getElementById("popover-kind");
  const game = document.getElementById("popover-game");
  const text = document.getElementById("popover-text");
  const canHover = matchMedia("(hover: hover) and (pointer: fine)").matches;
  let anchor = null;
  let hideTimer;

  // Beside the button where there's room (wide screens), so it doesn't cover the buttons
  // of the rows below; otherwise below it, or above if it doesn't fit; always inside the window
  const place = () => {
    const margin = 8;
    const button = anchor.getBoundingClientRect();
    const { offsetWidth: width, offsetHeight: height } = popover;
    const beside = button.left - width - 6;
    if (beside >= margin) {
      popover.style.left = `${beside}px`;
      popover.style.top = `${Math.min(Math.max(margin, button.top), innerHeight - height - margin)}px`;
      return;
    }
    const left = Math.min(Math.max(margin, button.left), innerWidth - width - margin);
    const below = button.bottom + 6;
    const top = below + height <= innerHeight - margin ? below : Math.max(margin, button.top - height - 6);
    popover.style.left = `${left}px`;
    popover.style.top = `${top}px`;
  };

  const open = (button) => {
    clearTimeout(hideTimer);
    if (button === anchor) return;
    anchor?.setAttribute("aria-expanded", "false");
    anchor = button;
    kind.textContent = button.dataset.kind;
    game.textContent = button.dataset.game;
    text.textContent = button.dataset.text;
    popover.hidden = false;
    text.scrollTop = 0;
    place();
    button.setAttribute("aria-expanded", "true");
  };

  const close = () => {
    clearTimeout(hideTimer);
    if (!anchor) return;
    popover.hidden = true;
    anchor.setAttribute("aria-expanded", "false");
    anchor = null;
  };

  // Give the pointer time to move from the button into the popup
  const closeSoon = () => {
    clearTimeout(hideTimer);
    hideTimer = setTimeout(close, 250);
  };

  table.addEventListener("click", (event) => {
    const button = event.target.closest("button.details");
    if (!button) return;
    // With a mouse, hovering has already opened it, so a click leaves it open
    if (button === anchor && !canHover) close();
    else open(button);
  });
  if (canHover) {
    table.addEventListener("mouseover", (event) => {
      const button = event.target.closest("button.details");
      if (button) open(button);
    });
    table.addEventListener("mouseout", (event) => {
      if (event.target.closest("button.details")) closeSoon();
    });
    popover.addEventListener("mouseenter", () => clearTimeout(hideTimer));
    popover.addEventListener("mouseleave", closeSoon);
  }

  const closeAndRefocus = () => {
    const button = anchor;
    close();
    button?.focus();
  };
  popover.querySelector(".popover-close").addEventListener("click", closeAndRefocus);
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && anchor) closeAndRefocus();
  });
  document.addEventListener("click", (event) => {
    if (anchor && !popover.contains(event.target) && !event.target.closest("button.details")) close();
  });
  addEventListener("scroll", () => anchor && place(), { passive: true });
  addEventListener("resize", close);
  return close;
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
  const sort = { field: "name", direction: "asc" };
  restoreFromUrl(form, sort);
  const closePopover = setUpPopover(table);

  const update = () => {
    closePopover();
    const criteria = readCriteria(form);
    const shown = sortGames(filterGames(games, criteria), sort.field, sort.direction);
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
    showSort(table, sort);
    saveToUrl(form, sort);
  };

  // A new column sorts ascending; choosing the sorted column again reverses it
  table.tHead.addEventListener("click", (event) => {
    const field = event.target.closest("[data-sort]")?.dataset.sort;
    if (!field) return;
    sort.direction = field === sort.field && sort.direction === "asc" ? "desc" : "asc";
    sort.field = field;
    update();
  });
  form.addEventListener("input", update);
  form.addEventListener("submit", (event) => event.preventDefault());
  // Fields only hold their reset values after the reset event has finished
  form.addEventListener("reset", () => setTimeout(update));
  update();
}

if (typeof document !== "undefined") init();
