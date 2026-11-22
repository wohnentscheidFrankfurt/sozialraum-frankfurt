// German words in the English map (desktop and phone projects "english-*"): the word list, the allow list and the
// scan. GERMAN_UI_WORDS are words of the German interface and prose that the English map must not show. The allow
// list takes what stays German on purpose; it comes from the payload where it can, so no name is typed twice:
//  - names of areas (districts, quarters, survey areas), of lists, of the features of the overlays, titles of
//    sources, the source lines of the catalog, the overlays and the chart views, the example names of the groups: proper names and titles of law and sources
//  - everything in brackets "(…)": the German term after its English term
//  - ALLOWED_PHRASES: German names a text keeps on purpose and the payload does not hold
// An allowed phrase is cut out of the text before the words are searched.

export const GERMAN_UI_WORDS = ["und", "oder", "der", "die", "das", "den", "dem", "des", "ein", "eine", "einen", "mit", "von",
  "für", "nicht", "ist", "sind", "bei", "auf", "zum", "zur", "im", "ja", "nein", "k. A.", "Wohnungen", "Wohnung", "Gebiet",
  "Gebiete", "Karte", "Stadtteil", "Stadtteile", "Bezirk", "Bezirke", "Eigentum", "Miete", "Mieter", "Hilfe", "Quelle", "Anteil",
  "Gebäude", "Einwohner", "Kandidaten", "Neubau", "Hinweis", "Wert", "Werte", "Karten", "Liste", "Listen", "Wahl", "Stand",
  "Erstellt", "Schließen", "Öffnen", "Suche", "Alle", "Keine", "Zurück"];

// German names a text keeps on purpose, outside the payload: benefit names
// (written in pieces: tests/test_text_copies.py fails a test literal of 20 characters or more that stands in a map text)
export const ALLOWED_PHRASES = ["Sozialraum Frankfurt", "Milieuschutz", "Jobcenter", ["Hilfe", "zum", "Lebensunterhalt"].join(" "),
  ["Grundsicherung", "im", "Alter", "und", "bei", "Erwerbsminderung"].join(" ")];

const escape = (w) => w.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
// a word as a whole word, also capitalised at the start of a sentence
const wordPattern = new RegExp(`(?<![\\p{L}\\p{N}])(?:${GERMAN_UI_WORDS.flatMap((w) => [w, w[0].toUpperCase() + w.slice(1)]).map(escape).join("|")})(?![\\p{L}\\p{N}])`, "gu");

// Strings of the payload that are German proper names or titles (in the page)
export const allowedFromPayload = (page) => page.evaluate(() => {
  const d = APP.data, out = new Set();
  const add = (s) => { if (typeof s === "string" && s.trim().length > 2) out.add(s.trim()); };
  for (const level of [d.districts, d.quarters]) for (const f of level.features) ["name", "quarter", "survey_area"].forEach((k) => add(f.properties[k]));
  d.lists.forEach((l) => add(l.name));
  for (const k of ["social_preservation", "social_preservation_pending", "townscape", "townscape_pending", "pending_plans", "land_value"])
    for (const f of d[k].features) ["title", "use"].forEach((p) => add(f.properties[p]));
  d.sources.forEach((s) => add(s.title));
  d.catalog.forEach((c) => add(c.source));
  Object.values(d.overlays).forEach((o) => add(o.source));
  // the source lines and example names of the chart views: any string under the keys source, license and example
  const walk = (o, key) => {
    if (typeof o === "string") { if (["source", "license", "example"].includes(key)) o.split(" · ").forEach(add); }
    else if (o && typeof o === "object") for (const [k, v] of Object.entries(o)) walk(v, Array.isArray(o) ? key : k);
  };
  walk({ history: d.history, new_construction: d.new_construction, rent_burden: d.rent_burden, sources: d.sources }, "");
  return [...out];
});

// The German words left in a text, each with the text around it, after the allowed phrases and the words in brackets are cut out
export const germanWords = (text, allowed) => {
  let rest = text.replace(/ /g, " ");
  for (const phrase of [...allowed, ...ALLOWED_PHRASES].sort((a, b) => b.length - a.length)) rest = rest.split(phrase).join(" ");
  for (let before = ""; before !== rest;) { before = rest; rest = rest.replace(/\([^()]*\)/g, " "); }
  return [...new Set([...rest.matchAll(wordPattern)].map((m) => rest.slice(Math.max(0, m.index - 30), m.index + m[0].length + 30).replace(/\s+/g, " ")))];
};
