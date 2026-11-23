// Usage: node tests/browser/tools/dump_text.mjs <map.html> <out.json>
// Stores the visible text of fixed states of the map. Selects by tag, by visible text and by Leaflet's own classes,
// never by our ids, classes or JavaScript names, so the dump survives renames. The visible texts it clicks follow the
// language of the map (<html lang>).
import { chromium } from "@playwright/test";
import { writeFileSync } from "node:fs";
import { pathToFileURL } from "node:url";

const [html, out] = process.argv.slice(2);
// the visible texts the dump clicks or masks, per language of the map
const WORDS = {
  de: { layers: ["Mieteranteil", "Bodenrichtwert", "Stärkste Liste", "Sozialwohnungen"], quarters: "Stadtteile",
        districts: "Bezirke", public: "ABG und Nassauische Heimstätte", city: "Stadt", candidates: "Kandidaten",
        help: "Hilfe", grid: "Eigentum je 100-m-Feld", trend: "Trend", new_construction: "Neubau",
        only: " \\(nur (Stadtteile|Bezirke)\\)$", created: "Erstellt am \\d{1,2}\\.\\d{1,2}\\.\\d{4}", created_mask: "Erstellt am DATE" },
  en: { layers: ["Share of tenants", "Standard land value", "Strongest list", "Social housing"], quarters: "Districts",
        districts: "Sub-districts", public: "ABG and Nassauische Heimstätte", city: "City", candidates: "Candidates",
        help: "Help", grid: "Ownership per 100 m grid square", trend: "Trend", new_construction: "New housing",
        only: " \\((districts|sub-districts) only\\)$", created: "Created on \\d{1,2} [A-Z][a-z]+ \\d{4}", created_mask: "Created on DATE" },
};
const browser = await chromium.launch({ channel: "chrome", headless: true });
const context = await browser.newContext({ viewport: { width: 1400, height: 900 } });
const page = await context.newPage();
// an error of the page stops the dump: a dump of a broken map would compare as a change of texts. The requests the
// route below aborts (basemap tiles) are no error of the map.
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));
page.on("console", (m) => { if (m.type() === "error" && !m.text().startsWith("Failed to load resource")) errors.push(m.text()); });
// Leaflet's own hook collects every map, so the dump needs no name of ours to reach the layers
await page.addInitScript(() => {
  let leaflet;
  window.__maps = [];
  Object.defineProperty(window, "L", { configurable: true, get: () => leaflet, set: (v) => {
    leaflet = v;
    if (v && v.Map && !v.__dumpHook) { v.__dumpHook = true; v.Map.addInitHook(function () {
      window.__maps.push(this);
      // true while the map pans or zooms (a click on an area flies to it)
      this.on("movestart", () => { window.__moving = true; });
      this.on("moveend", () => { window.__moving = false; });
    }); }
  } });
});
await context.route("**/*", (route) => (/^(file|data|blob):/.test(route.request().url()) ? route.continue() : route.abort()));
await page.goto(pathToFileURL(html).href, { waitUntil: "load" });
await page.waitForFunction(() => window.APP && window.APP.ready, null, { timeout: 30000 });
await page.evaluate(() => document.fonts.ready);
const W = WORDS[(await page.evaluate(() => document.documentElement.lang)).slice(0, 2)];

// wait for the map to stand still (condition, no fixed time), then for the frames after it
const still = async () => { await page.waitForFunction(() => !window.__moving); await frames(); };
const frames = () => page.evaluate(() => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r))));
const text = (selector) => page.evaluate((s) => [...document.querySelectorAll(s)].map((e) => e.innerText).join("\n---\n"), selector);
const snapshot = async () => ({
  header: await text("header"),
  sidebar: await text("aside"),
  legend: await text(".legend"),
  footer: (await text("footer")).replace(new RegExp(W.created), W.created_mask),
});
const tab = async (label) => {
  await page.evaluate((l) => [...document.querySelectorAll("nav button")].find((b) => b.textContent.trim() === l).click(), label);
  await frames();
};
// labels and selects only in the visible tab
const choose = async (label) => {
  await page.evaluate(([l, only]) => {
    const section = [...document.querySelectorAll("aside section")].find((s) => s.offsetParent !== null);
    // choosing a layer that exists only at the other level switches the level and drops this suffix from the labels
    const bare = (t) => t.trim().replace(new RegExp(only), "");
    const found = [...section.querySelectorAll("label")].find((x) => bare(x.textContent) === bare(l) || x.textContent.trim().startsWith(l + " ("));
    if (!found) throw new Error(`label not found: ${l}`);
    found.querySelector("input").click();
  }, [label, W.only]);
  await frames();
};
const option = async (index) => {
  await page.evaluate((i) => {
    const section = [...document.querySelectorAll("aside section")].find((s) => s.offsetParent !== null);
    const select = section.querySelector("select");
    select.selectedIndex = i;
    select.dispatchEvent(new Event("change"));
  }, index);
  await frames();
};
const center = () => page.evaluate(() => {
  const r = document.querySelector("main > div").getBoundingClientRect();
  return { x: r.left + r.width / 2, y: r.top + r.height / 2 };
});
// fill colour of every area, the colours of the legend and the counts of the grid colours
const colours = () => page.evaluate(() => {
  const areas = {}, grid = {};
  window.__maps[0].eachLayer((l) => {
    const p = l.feature && l.feature.properties;
    if (p && p.id != null && l.options && l.options.fillColor) areas[p.id] = `${l.options.fillColor} ${l.options.fillOpacity} ${l.options.dashArray || ""}`;
    else if (!l.feature && l.options && l.options.fillColor && l.getBounds) grid[l.options.fillColor] = (grid[l.options.fillColor] || 0) + 1;
  });
  const legend = [...document.querySelectorAll(".legend i")].map((i) => i.getAttribute("style"));
  return { areas, legend, grid };
});
const radioLabels = () => page.evaluate((levels) => {
  const section = [...document.querySelectorAll("aside section")].find((s) => s.offsetParent !== null);
  return [...section.querySelectorAll("label")].filter((l) => l.querySelector('input[type="radio"]'))
    .map((l) => l.textContent.trim()).filter((t) => !levels.some((level) => t.startsWith(level + " (")));
}, [W.quarters, W.districts]);

const states = {};
states.start = await snapshot();
for (const label of W.layers) {
  await choose(label);
  states[`layer ${label}`] = await snapshot();
}
await choose(W.districts);
await choose(W.public);
states["layer districts"] = await snapshot();
await tab(W.candidates);
const options = await page.evaluate(() => [...document.querySelectorAll("aside section")].find((s) => s.offsetParent !== null).querySelector("select").options.length);
for (let i = 0; i < options; i++) {
  await option(i);
  states[`candidates ${i}`] = await snapshot();
}
await tab(W.help);
states.help = await snapshot();
await tab(W.city);
await choose(W.public);
const c = await center();
await page.mouse.click(c.x, c.y);
await still();
states["profile district"] = await snapshot();
// leave the map first, so no tooltip of the click point is left; then the area under the cursor opens its own
await page.mouse.move(0, 0);
await page.waitForFunction(() => !document.querySelector(".leaflet-tooltip"));
await page.mouse.move(c.x + 40, c.y + 40);
await page.waitForFunction(() => { const t = document.querySelector(".leaflet-tooltip"); return t && t.innerText.trim() !== ""; });
await frames();
states.tooltip = { tooltip: await text(".leaflet-tooltip") };
await tab(W.city);
await choose(W.quarters);
await page.mouse.click(c.x, c.y);
await still();
states["profile quarter"] = await snapshot();

await tab(W.city);
for (const level of [W.quarters, W.districts]) {
  await choose(level);
  for (const label of await radioLabels()) {
    await choose(label);
    states[`colours ${level} ${label}`] = await colours();
  }
}
await page.evaluate(() => window.__maps[0].setZoom(15));
await still();
await tab(W.city);
await page.evaluate((grid) => { const box = [...document.querySelectorAll("label")].find((l) => l.textContent.trim().startsWith(grid)); box.querySelector("input").click(); }, W.grid);
await frames();
// the grid is drawn when its rectangles are on the map
await page.waitForFunction(() => { let n = 0; window.__maps[0].eachLayer((l) => { if (!l.feature && l.options && l.options.fillColor && l.getBounds) n++; }); return n > 0; });
states["grid colours"] = (await colours()).grid;
await page.evaluate(() => window.__maps[0].setZoom(11));
await still();
await tab(W.candidates);
for (let i = 0; i < options; i++) {
  await option(i);
  states[`colours candidates ${i}`] = await colours();
}
// view „Trend“: visible text, every tooltip and every chart as markup
await page.evaluate((v) => [...document.querySelectorAll("header button")].find((b) => b.textContent.trim() === v).click(), W.trend);
await frames();
states.trend = await page.evaluate(() => {
  const view = [...document.querySelectorAll("section")].find((s) => s.offsetParent !== null && s.querySelector("svg"));
  return { text: view.innerText, tips: [...view.querySelectorAll("[data-tip]")].map((e) => e.getAttribute("data-tip")),
           svgs: [...view.querySelectorAll("svg")].map((s) => s.outerHTML) };
});
// view „Neubau“: the same, for its charts (the columns and the two charts of rents below them)
await page.evaluate((v) => [...document.querySelectorAll("header button")].find((b) => b.textContent.trim() === v).click(), W.new_construction);
await frames();
states.new_construction = await page.evaluate(() => {
  const view = [...document.querySelectorAll("section")].find((s) => s.offsetParent !== null && s.querySelector("svg"));
  return { text: view.innerText, tips: [...view.querySelectorAll("[data-tip]")].map((e) => e.getAttribute("data-tip")),
           svgs: [...view.querySelectorAll("svg")].map((s) => s.outerHTML) };
});

writeFileSync(out, JSON.stringify(states, null, 1));
await browser.close();
if (errors.length) {
  console.error(`console errors:\n${errors.join("\n")}`);
  process.exit(1);
}
console.log(`${Object.keys(states).length} states in ${out}`);
