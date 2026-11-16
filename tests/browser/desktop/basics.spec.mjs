// Basics: start view, formats, header, navigation, order of the tabs, the cover note, the two
// elections and the note under the legend title.
import { test } from "../fixtures.mjs";

test("start view", async ({ mapPage: page, check }) => {
  // docs/design.md, Views and tabs: the map starts on Stadtteile with ABG and Nassauische Heimstätte
  check(await page.evaluate(() => APP.state.level === "quarter" && APP.state.indicator === "OWN_PUBLIC"
    && document.querySelector('input[name="level"][value="quarter"]').checked && APP.map.hasLayer(APP.layers.quarter)),
  "start view: Stadtteile, ABG und Nassauische Heimstätte");
});

test("number format and escape", async ({ mapPage: page, check }) => {
  check(await page.evaluate(() => APP.format(1234.5, 1)) === "1.234,5", "number format");
  check(await page.evaluate(() => APP.escape('<a href="x">&')) === "&lt;a href=&quot;x&quot;&gt;&amp;", "escape");
});

test("footer: a source with a page links it in a new tab", async ({ mapPage: page, check }) => {
  // docs/design.md, Layouts: a source with a url links its title; the link opens a new tab
  const got = await page.evaluate(() => ({
    linked: APP.data.sources.filter((q) => q.url).map((q) => [q.title, q.url]),
    links: [...document.querySelectorAll("#footer a")].map((a) => [a.textContent, a.getAttribute("href"), a.target, a.rel]) }));
  check(got.linked.length > 0 && got.linked.some(([, url]) => url === "https://gemeinwohlbau.de/idee"), "the Gemeinwohlbau has its page");
  check(JSON.stringify(got.links) === JSON.stringify(got.linked.map(([title, url]) => [title, url, "_blank", "noopener"])),
    "footer: one link per source with a page: " + JSON.stringify(got.links));
});

test("header: title and heading", async ({ mapPage: page, check }) => {
  check(await page.title() === "Sozialraum Frankfurt", "title in the browser tab");
  check(await page.evaluate(() => document.querySelector("#header h1").textContent) === "Sozialraum Frankfurt", "heading");
});

test("Leaflet knows the real map size", async ({ mapPage: page, check }) => {
  check(await page.evaluate(() => { const c = APP.map.getContainer(), s = APP.map.getSize(); return s.x === c.clientWidth && s.y === c.clientHeight; }),
    "Leaflet knows the real map size (the footer is filled after start)");
});

test("layout: views, sidebar and legend", async ({ mapPage: page, check }) => {
  // Navigation (docs/design.md, Views and tabs): views in the header, map tabs on top of the sidebar at the left
  check(await page.evaluate(() => document.getElementById("views").getBoundingClientRect().left < window.innerWidth / 3
    && document.getElementById("tabs").getBoundingClientRect().left < 20
    && document.getElementById("sidebar").getBoundingClientRect().right <= document.getElementById("map").getBoundingClientRect().left),
  "views left in the header, sidebar with its tabs left of the map");
  check(await page.evaluate(() => document.querySelector(".leaflet-bottom.leaflet-right .legend") !== null), "legend at the bottom right");
  check(await page.evaluate(() => { const l = document.querySelector(".legend").getBoundingClientRect(), a = document.querySelector(".leaflet-control-attribution").getBoundingClientRect();
    return l.bottom <= a.top; }), "legend above the attribution, no overlap");
});

test("header fits in one row at 1024 and 1400 px", async ({ mapPage: page, check }) => {
  for (const width of [1024, 1400]) {
    await page.setViewportSize({ width, height: 900 });
    check(await page.evaluate(() => { const v = document.getElementById("views").getBoundingClientRect(), h = document.querySelector("#header h1").getBoundingClientRect();
      return v.top < h.bottom && h.top < v.bottom && h.right < v.left; }), `${width} px: title and views fit in one row`);
  }
});

test("order of the tabs", async ({ mapPage: page, check }) => {
  // Order of the tabs: area stands before candidates, buttons, sections and help lines alike. The help lines name a
  // tab by the label of its button.
  check(await page.evaluate(() => {
    const b = [...document.querySelectorAll("#tabs button[data-tab]")];
    const label = (tab) => b.find((x) => x.dataset.tab === tab).textContent.trim();
    const helpOrder = [...document.querySelectorAll("#tab-help p strong")].map((e) => e.textContent.replace(":", ""));
    return b.map((x) => x.dataset.tab).join() === "city,area,candidates,help"
      && b.every((x) => x.textContent.trim() !== "")
      && [...document.querySelectorAll("#sidebar .tab")].map((t) => t.id).join() === "tab-city,tab-area,tab-candidates,tab-help"
      && helpOrder.indexOf(label("area")) >= 0 && helpOrder.indexOf(label("area")) < helpOrder.indexOf(label("candidates"));
  }), "tabs in the order city, area, candidates, help (buttons, sections, help lines)");
});

test("navigation between views and tabs", async ({ mapPage: page, check }) => {
  const navState = () => page.evaluate(() => ({
    views: [...document.querySelectorAll("#views button")].filter((b) => b.getAttribute("aria-pressed") === "true" && b.classList.contains("active")).map((b) => b.dataset.view),
    tabs: [...document.querySelectorAll("#tabs button")].filter((b) => b.getAttribute("aria-pressed") === "true" && b.classList.contains("active")).map((b) => b.dataset.tab),
    section: [...document.querySelectorAll("#sidebar .tab.active")].map((t) => t.id),
    mapShown: !document.querySelector("main").hidden, historyShown: !document.getElementById("view-history").hidden,
    constructionShown: !document.getElementById("view-new-construction").hidden,
    rentShown: !document.getElementById("view-rent-burden").hidden,
  }));
  const expectNav = async (label, views, tab, history, construction = false, rent = false) => {
    const s = await navState();
    check(JSON.stringify(s) === JSON.stringify({ views: [views], tabs: [tab], section: ["tab-" + tab], mapShown: !history && !construction && !rent,
      historyShown: history, constructionShown: construction, rentShown: rent }), label + ": " + JSON.stringify(s));
  };
  for (const tab of ["candidates", "area", "help", "city"]) {
    await page.click(`#tabs button[data-tab="${tab}"]`);
    await expectNav(`tab ${tab}`, "map", tab, false);
  }
  await page.click('#views button[data-view="history"]');
  await expectNav("view Trend", "history", "city", true);
  await page.click('#views button[data-view="map"]');
  await expectNav("view Karte keeps the tab", "map", "city", false);
  await page.click('#views button[data-view="history"]');
  await page.evaluate(() => APP.openTab("candidates"));
  await expectNav("openTab from the chart view returns to the map", "map", "candidates", false);
  await page.evaluate(() => APP.openTab("history"));
  await expectNav("openTab ignores names without a section", "map", "candidates", false);
  await page.click('#views button[data-view="new_construction"]');
  await expectNav("view Neubau", "new_construction", "candidates", false, true);
  await page.click('#views button[data-view="history"]');
  await expectNav("from Neubau to Trend", "history", "candidates", true);
  await page.click('#views button[data-view="new_construction"]');
  await page.click('#views button[data-view="map"]');
  await expectNav("view Karte after Neubau", "map", "candidates", false);
  await page.click('#views button[data-view="new_construction"]');
  await page.evaluate(() => APP.openTab("city"));
  await expectNav("openTab from Neubau returns to the map", "map", "city", false);
  await page.click('#views button[data-view="rent_burden"]');
  await expectNav("view Miete", "rent_burden", "city", false, false, true);
  await page.click('#views button[data-view="new_construction"]');
  await expectNav("from Miete to Neubau", "new_construction", "city", false, true);
  await page.click('#views button[data-view="rent_burden"]');
  await page.click('#views button[data-view="history"]');
  await expectNav("from Miete to Trend", "history", "city", true);
  await page.click('#views button[data-view="rent_burden"]');
  await page.click('#views button[data-view="map"]');
  await expectNav("view Karte after Miete", "map", "city", false);
  await page.click('#views button[data-view="rent_burden"]');
  await page.evaluate(() => APP.openTab("candidates"));
  await expectNav("openTab from Miete returns to the map", "map", "candidates", false);
});

test("the cover note keeps standards mode", async ({ mapPage: page, check }) => {
  // The cover note is a comment between doctype and <html> and must not cost standards mode
  check(await page.evaluate(() => document.compatMode) === "CSS1Compat", "standards mode despite the comment");
});

test("the two elections", async ({ mapPage: page, check }) => {
  await page.evaluate(() => APP.setIndicator("ELEC_STRONGEST"));
  check(await page.evaluate(() => APP.state.level) === "quarter", "election switches to quarters");
  // There were two elections on 15.3.2026; the legend names the one shown: the title of the layer (catalog) plus a
  // suffix, the same suffix on both election layers
  const legendTitle = () => page.evaluate(() => ({ text: document.querySelector(".legend strong").textContent, title: APP.meta[APP.state.indicator].title }));
  const suffix = ({ text, title }) => (title && text.startsWith(title) ? text.slice(title.length).trim() : null);
  const strongest = await legendTitle();
  check(suffix(strongest), "legend names the election: " + JSON.stringify(strongest));
  await page.evaluate(() => APP.setIndicator("ELEC_CDU"));
  const share = await legendTitle();
  check(suffix(share) && suffix(share) === suffix(strongest), "legend of the share layer names the election: " + JSON.stringify(share));
  check(await page.evaluate(() => document.querySelector('label[data-id="ELEC_STRONGEST"]').textContent.trim() === APP.meta.ELEC_STRONGEST.title), "sidebar without election suffix");
  await page.evaluate(() => APP.setLevel("district"));
  // ownership only per Stadtteil, so districts fall back to the first district layer
  check(await page.evaluate(() => APP.state.indicator) === "SOC_MIN_INCOME", "districts fall back to SOC_MIN_INCOME");
  const other = await legendTitle();
  check(other.title && other.text === other.title, "legend of other indicators without election suffix: " + JSON.stringify(other));
});

test("note under the legend title", async ({ mapPage: page, check }) => {
  // an election layer (ELEC_CDU) on the district level, reached from ELEC_STRONGEST
  await page.evaluate(() => { APP.setIndicator("ELEC_STRONGEST"); APP.setIndicator("ELEC_CDU"); APP.setLevel("district"); });
  // docs/texts.md, Map: legend. One line under the legend title says what the number is, the same on both levels.
  // The text is the note of the layer in the catalog (APP.meta).
  const legendNote = () => page.evaluate(() => { const n = document.querySelector(".legend .legend-note");
    return n && { text: n.textContent, catalog: APP.meta[APP.state.indicator].legend_note,
      below: n.previousElementSibling.classList.contains("legend-title") && n.getBoundingClientRect().top >= n.previousElementSibling.getBoundingClientRect().bottom - 1 }; });
  const fromCatalog = (n) => n && n.catalog && n.text === n.catalog;
  let note = await legendNote();
  const districtNote = note && note.text;
  check(fromCatalog(note) && note.below, "district level: note under the title: " + JSON.stringify(note));
  await page.evaluate(() => APP.setLevel("quarter"));
  note = await legendNote();
  check(fromCatalog(note) && note.text === districtNote, "quarter level: the same note: " + JSON.stringify(note));
  await page.evaluate(() => { APP.setIndicator("ELEC_STRONGEST"); });
  note = await legendNote();
  check(fromCatalog(note), "ELEC_STRONGEST: note under the title: " + JSON.stringify(note));
  await page.evaluate(() => { APP.setLevel("district"); });
  await page.evaluate(() => APP.setIndicator("OWN_PUBLIC"));
  check(await page.evaluate(() => APP.state.level) === "quarter", "OWN_PUBLIC switches to quarters");
  note = await legendNote();
  check(fromCatalog(note), "OWN_PUBLIC: note: " + JSON.stringify(note));
});
