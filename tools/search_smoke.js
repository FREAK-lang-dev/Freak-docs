/* Headless smoke test for the docs search index.
 *
 * Mirrors the scoring and de-duplication in site/assets/app.js so the index can
 * be exercised without a browser. Fails (exit 1) if any query below returns no
 * results, or if the control query returns any.
 *
 *   node tools/search_smoke.js
 */

"use strict";

const fs = require("fs");
const path = require("path");

const INDEX = path.join(__dirname, "..", "site", "assets", "search-index.js");

global.window = {};
eval(fs.readFileSync(INDEX, "utf8"));
const index = window.SEARCH_INDEX;

function esc(t) {
  return t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function score(rec, tokens) {
  const heading = (rec.h || "").toLowerCase();
  const title = (rec.t || "").toLowerCase();
  const text = (rec.x || "").toLowerCase();
  let total = 0;
  for (const t of tokens) {
    let s = 0;
    if (title === t) s += 60;
    if (heading === t) s += 55;
    if (heading.indexOf(t) === 0) s += 34;
    else if (heading.indexOf(t) !== -1) s += 22;
    if (title.indexOf(t) !== -1) s += 10;
    const at = text.indexOf(t);
    if (at !== -1) {
      s += 12;
      if (new RegExp("\\b" + esc(t), "i").test(text)) s += 8;
      if (at < 120) s += 3;
    }
    if (s === 0) return 0;
    total += s;
  }
  return total + Math.max(0, 8 - Math.floor((rec.x || "").length / 120));
}

function search(q) {
  const tokens = q.toLowerCase().split(/\s+/).filter(Boolean);
  const scored = index
    .map((r) => ({ r, s: score(r, tokens) }))
    .filter((x) => x.s > 0)
    .sort((a, b) => b.s - a.s);
  const seen = {}, per = {}, out = [];
  for (const item of scored) {
    const key = item.r.p + "#" + item.r.a;
    if (seen[key]) continue;
    seen[key] = 1;
    per[item.r.p] = (per[item.r.p] || 0) + 1;
    if (per[item.r.p] <= 3) out.push(item);
    if (out.length >= 25) break;
  }
  return out;
}

/* Terms a reader would plausibly type. Each must return at least one hit. */
const MUST_MATCH = [
  "coloured output", "ansi", "truecolour", "NO_COLOR", "escape",
  "256-colour", "cursor", "erase line", "SGR", "reverse video", "strikethrough",
  "ByteBuffer", "word_builder", "List", "List::filled", "socket",
  "hangar", "hangar_modules", "package", "dependencies", "concatenate",
  "same line", "newline", "carriage return", "progress", "push", "pop",
  "parse_status", "checked parsing",
  "array_sort_word", "segfault", "case-insensitive", "reserved words",
  "training arc", "give back", "interpolation", "substring", "freak check",
  "pipe", "hangar", "doctrine", "closure", "variant", "eventually",
  "fixed point", "shape field", "process args", "extern", "dyn",
];

/* Must return nothing. */
const MUST_NOT_MATCH = ["zzzznothingatall"];

let failures = 0;
console.log(`index: ${index.length} records\n`);

for (const q of MUST_MATCH) {
  const hits = search(q);
  if (hits.length === 0) {
    console.log(`FAIL  no hits for "${q}"`);
    failures++;
  } else {
    const top = hits[0].r;
    console.log(`ok    ${q.padEnd(20)} -> ${top.t} # ${top.h}`);
  }
}

for (const q of MUST_NOT_MATCH) {
  if (search(q).length !== 0) {
    console.log(`FAIL  unexpected hits for "${q}"`);
    failures++;
  } else {
    console.log(`ok    ${q.padEnd(20)} -> (correctly empty)`);
  }
}

console.log(failures ? `\n${failures} failure(s)` : "\nall search smoke checks passed");
process.exit(failures ? 1 : 0);
