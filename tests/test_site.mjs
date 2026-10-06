// Tests for the web page's filtering and sorting: node --test tests/test_site.mjs

import assert from "node:assert/strict";
import { test } from "node:test";

import { filterGames, formatPlayers, sortGames } from "../site/app.js";

const game = (name, fields = {}) => ({
  name,
  year: 2020,
  rank: null,
  min_players: 2,
  max_players: 4,
  playing_time: 60,
  categories: [],
  owners: ["alice"],
  ...fields,
});

const GAMES = [
  game("Azul", { year: 2017, rank: 50, playing_time: 45, categories: ["Abstract Strategy"] }),
  game("brass", { year: 2018, rank: 5, playing_time: 120, owners: ["alice", "bob"] }),
  game("Codenames", { year: null, max_players: 8, playing_time: 15, categories: ["Party Game", "Word Game"] }),
  game("Agricola", { year: 2007, min_players: 1, max_players: 5, playing_time: 120, owners: ["bob"] }),
  game("Mystery Box", { playing_time: 0, expansion: true }),
];

const names = (games) => games.map((g) => g.name);

test("sorts by name ignoring case", () => {
  assert.deepEqual(names(sortGames(GAMES, "name")), ["Agricola", "Azul", "brass", "Codenames", "Mystery Box"]);
});

test("puts unranked games last, then by name", () => {
  assert.deepEqual(names(sortGames(GAMES, "rank")), ["brass", "Azul", "Agricola", "Codenames", "Mystery Box"]);
});

test("puts unknown years last", () => {
  assert.deepEqual(names(sortGames(GAMES, "year")), ["Agricola", "Azul", "brass", "Mystery Box", "Codenames"]);
});

test("sorts by play time, breaking ties by name, with unknown times last", () => {
  assert.deepEqual(names(sortGames(GAMES, "playtime")), ["Codenames", "Azul", "Agricola", "brass", "Mystery Box"]);
});

test("sorts by players, by the smallest then the largest count", () => {
  assert.deepEqual(names(sortGames(GAMES, "players")), ["Agricola", "Azul", "brass", "Mystery Box", "Codenames"]);
});

test("sorts by age, with unknown ages last", () => {
  const games = [game("Teen", { min_age: 14 }), game("Unknown", { min_age: 0 }), game("Kids", { min_age: 6 })];
  assert.deepEqual(names(sortGames(games, "age")), ["Kids", "Teen", "Unknown"]);
});

test("reverses the order but keeps unknown values last", () => {
  assert.deepEqual(names(sortGames(GAMES, "rank", "desc")), ["Azul", "brass", "Agricola", "Codenames", "Mystery Box"]);
  assert.deepEqual(names(sortGames(GAMES, "name", "desc")), ["Mystery Box", "Codenames", "brass", "Azul", "Agricola"]);
});

test("an unknown sort field sorts by name", () => {
  assert.deepEqual(names(sortGames(GAMES, "colour")), names(sortGames(GAMES, "name")));
});

test("does not change the original list", () => {
  const before = names(GAMES);
  sortGames(GAMES, "rank");
  assert.deepEqual(names(GAMES), before);
});

test("searches names and categories", () => {
  assert.deepEqual(names(filterGames(GAMES, { query: "AZ" })), ["Azul"]);
  assert.deepEqual(names(filterGames(GAMES, { query: "party" })), ["Codenames"]);
});

test("filters by player count", () => {
  assert.deepEqual(names(filterGames(GAMES, { players: 1 })), ["Agricola"]);
  assert.deepEqual(names(filterGames(GAMES, { players: 8 })), ["Codenames"]);
});

test("filters by play time, leaving out unknown times", () => {
  assert.deepEqual(names(filterGames(GAMES, { maxTime: 45 })), ["Azul", "Codenames"]);
});

test("filters by owner", () => {
  assert.deepEqual(names(filterGames(GAMES, { owner: "bob" })), ["brass", "Agricola"]);
});

test("no filters keeps everything", () => {
  assert.equal(filterGames(GAMES).length, GAMES.length);
});

test("can hide expansions", () => {
  assert.deepEqual(names(filterGames(GAMES, { hideExpansions: true })), ["Azul", "brass", "Codenames", "Agricola"]);
  assert.equal(filterGames(GAMES, { hideExpansions: false }).length, GAMES.length);
});

test("formats player counts", () => {
  assert.equal(formatPlayers(game("A", { min_players: 3, max_players: 4 })), "3–4");
  assert.equal(formatPlayers(game("A", { min_players: 2, max_players: 2 })), "2");
  assert.equal(formatPlayers(game("A", { min_players: 0, max_players: 0 })), "–");
});
