// Shared tooltip (docs/design.md, Tooltip): hits at a point, the tooltip at the mouse, where it closes, the edge of the
// map, and the texts 2.1-2.4 (rank, survey area, grid sentence, unique titles).
import { test } from "../fixtures.mjs";
import { frames } from "../helpers/common.mjs";
import { hoverAt, numbers, openTooltips } from "../helpers/layers.mjs";

const GALLUS = [50.1001, 8.6366];
// SH_SHARE with the given overlays on, at a zoom and point
const gallusWith = (page, overlays, zoom = 15, point = GALLUS) => page.evaluate(([on, z, [lat, lng]]) => {
  APP.openTab("city"); APP.setIndicator("SH_SHARE");
  for (const [name, u] of Object.entries(APP.overlays)) u.on = on.includes(name);
  APP.map.setView([lat, lng], z, { animate: false });
  APP.updateOverlays();
}, [overlays, zoom, point]);
const hitsAt = (page, point) => page.evaluate(([lat, lng]) => APP.hitsAt(L.latLng(lat, lng)), point);
// The grid cell the tooltip shows (the one drawn last, as in APP.gridAt), read from the data: the largest group in the
// dative (payload), the "title count" rows of the groups with a count, the groups without one, and the tooltip row of
// the cell (APP.gridTip) as html and as text. The header after the first line depends on the flag of the cell
// (counted dwellings 2011 for a flagged cell, counted buildings 2022 otherwise): `header` is that of the cell,
// `otherHeader` that of the same cell with the flag turned, `year` the year the header must name.
const gridCellAt = (page, point) => page.evaluate(([lat, lng]) => {
  const { scale: k, rows } = APP.data.grid_cells;
  const cell = rows.filter(([s, w, dn, de]) => s / k <= lat && lat <= (s + dn) / k && w / k <= lng && lng <= (w + de) / k).slice(-1)[0];
  const [largest, flag, ...counts] = cell.slice(4);
  const div = document.createElement("div");
  div.innerHTML = APP.gridTip(cell.slice(4));
  const headerOf = (html) => html.split("</div>")[1].split("<div")[0];
  return { flag, counts, dative: APP.data.grid_dative[APP.data.grid_groups[largest]], tip: APP.gridTip(cell.slice(4)), text: div.textContent,
           header: headerOf(APP.gridTip(cell.slice(4))), otherHeader: headerOf(APP.gridTip([largest, 1 - flag, ...counts])), year: flag ? 2011 : 2022,
           first: div.firstElementChild.textContent,
           rows: APP.data.grid_groups.map((g, i) => (counts[i] > 0 ? `${APP.ownershipById[g].title} ${APP.format(counts[i], 0)}` : null)).filter(Boolean),
           empty: APP.data.grid_groups.map((g, i) => (counts[i] > 0 ? null : APP.ownershipById[g].title)).filter(Boolean) };
}, point);
// the header names the year of its flag, and the turned flag gives another header
const headerFits = (cell) => cell.header.trim() !== "" && cell.header !== cell.otherHeader && numbers(cell.header).includes(cell.year)
  && !numbers(cell.header).includes(cell.year === 2011 ? 2022 : 2011);
// the tip prefix of each overlay (payload)
const tipOf = (page) => page.evaluate(() => Object.fromEntries(Object.entries(APP.data.overlays).map(([k, o]) => [k, o.tip])));

test("hits at the Gallus point", async ({ mapPage: page, check }) => {
  await gallusWith(page, ["social_preservation", "pending_plans", "land_value", "grid"]);
  const hits = await hitsAt(page, GALLUS);
  check(hits.map((t) => t.name).join() === "social_preservation,pending_plans,land_value,grid", "hits at the Gallus point in overlay order: " + hits.map((t) => t.name).join());
  const gallusRows = hits.flatMap((t) => t.rows).join(" | ");
  // each row: the tip prefix of its overlay (payload), then the name of the statute or plan, or the land value with
  // the use of the zone (source vocabulary of BORIS)
  const tip = await tipOf(page);
  check(gallusRows.includes(`${tip.social_preservation} Östliches Gallusviertel`), "row Milieuschutz: " + gallusRows);
  check(gallusRows.includes(`${tip.pending_plans} Lahnstraße westlich der Schwalbacher Straße`), "row B-Plan");
  check(gallusRows.includes(`${tip.land_value} 1.600 €/m² (Wohngebiet, Mehrfamilienhäuser)`), "row Bodenrichtwert names area and building type");
  const gallusCell = await gridCellAt(page, GALLUS);
  // the row of the grid is the tooltip of the cell under the point: the largest group in its first line, the header
  // of its flag, the groups with a count, none without
  check(gallusCell.rows.length > 0 && hits.find((t) => t.name === "grid")?.rows.join() === gallusCell.tip && gallusCell.first.includes(gallusCell.dative)
    && headerFits(gallusCell) && gallusRows.includes(gallusCell.header)
    && gallusCell.rows.every((x) => gallusRows.includes(x)) && gallusCell.empty.every((t) => !gallusRows.includes(t + " ")) && !gallusRows.includes("Farbe:"),
    "grid tooltip: first line, counted buildings or dwellings by the flag, only groups with a count, no colour line: " + gallusRows);
  check(await page.evaluate(() => APP.data.grid_cells.rows.some((r) => r[5] === 1) && APP.data.grid_cells.rows.some((r) => r[5] === 0) &&
    APP.data.grid_cells.rows.every((r) => r.length === 6 + APP.data.grid_groups.length && r.every(Number.isInteger))),
    "grid rows: flagged cells exist, every corner, flag and count is an integer");
  check(await page.evaluate(([lat, lng]) => (APP.areaAt(L.latLng(lat, lng)) || {}).name, GALLUS) === "Gallus", "area at the Gallus point");
});

test("hits: invisible overlays, two plans, two zones, a cell edge", async ({ mapPage: page, check }) => {
  await gallusWith(page, ["social_preservation", "pending_plans", "grid"], 13.5);
  check((await hitsAt(page, GALLUS)).map((t) => t.name).join() === "social_preservation,pending_plans", "invisible overlays do not count (land value off, grid below zoom 14)");
  await gallusWith(page, ["pending_plans"], 15, [50.123635, 8.599449]);
  let hits = await hitsAt(page, [50.123635, 8.599449]);
  const tip = await tipOf(page);
  check(hits.length === 1 && hits[0].rows.length === 2 && hits[0].rows.includes(`${tip.pending_plans} Östlich A5 / Eschborner Landstraße`) &&
    hits[0].rows.includes(`${tip.pending_plans} Östlich A5 / Eschborner Landstraße - Teilbereich 2`) && !/\([A-Z]+\d+\)/.test(hits[0].rows.join()),
    "Rödelheim: both B-Pläne are there: " + JSON.stringify(hits));
  await gallusWith(page, ["land_value"], 15, [50.14501, 8.725937]);
  hits = await hitsAt(page, [50.14501, 8.725937]);
  // two zones on top of each other: one row each, told apart by the building type (docs/texts.md, Map: tooltip)
  check(hits.length === 1 && hits[0].rows.join("|") === `${tip.land_value} 1.000 €/m² (Mischgebiet, Ein- und Zweifamilienhäuser)|${tip.land_value} 1.000 €/m² (Mischgebiet, Mehrfamilienhäuser)`,
    "Seckbach: two zones give two rows: " + JSON.stringify(hits));
  await gallusWith(page, ["grid"], 16, [50.07569, 8.51901]);
  hits = await hitsAt(page, [50.07569, 8.51901]);
  const edgeCell = await gridCellAt(page, [50.07569, 8.51901]);
  check(hits.length === 1 && hits[0].rows.length === 1 && edgeCell.rows.length > 0 && edgeCell.rows.every((x) => hits[0].rows[0].includes(x)) &&
    hits[0].rows[0] === edgeCell.tip && edgeCell.first.includes(edgeCell.dative) && headerFits(edgeCell) && hits[0].rows[0].includes(edgeCell.header),
    "grid at a cell edge: only the top cell: " + JSON.stringify(hits));
});

test("hits: polygon holes, escaping, colours and the townscape row", async ({ mapPage: page, check }) => {
  check(await page.evaluate(() => {
    const g = { type: "Polygon", coordinates: [[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]], [[4, 4], [6, 4], [6, 6], [4, 6], [4, 4]]] };
    return APP.inPolygon(g, 2, 2) && !APP.inPolygon(g, 5, 5) && !APP.inPolygon(g, 11, 5);
  }), "a point in the hole of a polygon is no hit");
  check(await page.evaluate(() => APP.overlays.pending_plans.tip({ title: "<b>A&B</b>" }) === `${APP.data.overlays.pending_plans.tip} &lt;b&gt;A&amp;B&lt;/b&gt;`),
    "title is escaped, no brackets");
  const overlayColours = await page.evaluate(() => ["social_preservation", "social_preservation_pending", "townscape", "townscape_pending"]
    .map((k) => APP.overlays[k].layer.options.style.color).join());
  check(overlayColours === "#1a1a1a,#1a1a1a,#1d4f91,#1d4f91", "overlay colours: " + overlayColours);
  check(await page.evaluate(() => ["social_preservation", "townscape"].every((k) => APP.overlays[k].casing.options.style.color === "#ffffff")),
    "Milieuschutz and Ortsbild have a white casing");
  // without a date a word stands where the date stands, the rest is the same: prefix and "since" from the payload
  const townscape = await page.evaluate(() => { const info = APP.overlayInfo.townscape;
    return { none: APP.townscapeTip({ title: "X", date: "" }, info), dated: APP.townscapeTip({ title: "X", date: "1.2.2003" }, info), head: `${info.tip} X, ${info.since} ` }; });
  const [noneRest, datedRest] = [townscape.none, townscape.dated].map((t) => (t.startsWith(townscape.head) ? t.slice(townscape.head.length) : null));
  const missing = noneRest && datedRest?.startsWith("1.2.2003") ? noneRest.slice(0, noneRest.length - (datedRest.length - "1.2.2003".length)) : "";
  check(/^\p{L}+$/u.test(missing) && noneRest.endsWith(datedRest.slice("1.2.2003".length)) && !/undefined|null/.test(townscape.none),
    "townscape statute without date: " + JSON.stringify(townscape));
});

test("hits at a point take under 2 ms", async ({ mapPage: page, check }) => {
  await gallusWith(page, await page.evaluate(() => Object.keys(APP.overlays))); // all overlays on, zoom 15
  const ms = await page.evaluate(([lat, lng]) => {
    const p = L.latLng(lat, lng), t0 = performance.now();
    for (let i = 0; i < 100; i++) { APP.areaAt(p); APP.hitsAt(p); }
    return (performance.now() - t0) / 100;
  }, GALLUS);
  check(ms < 2, `hits at a point in ${ms.toFixed(2)} ms (limit 2 ms)`);
});

test("shared tooltip at the mouse at the Gallus point", async ({ mapPage: page, check, saveScreenshot }) => {
  await gallusWith(page, ["social_preservation", "pending_plans", "land_value", "grid"]);
  const gallusCell = await gridCellAt(page, GALLUS);
  const tips = await hoverAt(page, GALLUS);
  check(tips.length === 1, `exactly one tooltip at the Gallus point (${tips.length})`);
  const tt = tips.join("");
  // the area with the title (catalog) and the count line of SH_SHARE, then the rows of the overlays, the grid cell last
  const tip = await tipOf(page);
  const head = await page.evaluate(() => { const q = APP.properties("quarter").find((p) => p.name === "Gallus");
    return { title: APP.meta.SH_SHARE.title, count: APP.countLine(APP.meta.SH_SHARE, q) }; });
  const parts = ["Gallus", head.title + ": ", head.count, `${tip.social_preservation} Östliches Gallusviertel`,
    `${tip.pending_plans} Lahnstraße westlich der Schwalbacher Straße`, `${tip.land_value} 1.600 €/m² (Wohngebiet, Mehrfamilienhäuser)`,
    gallusCell.first, gallusCell.header, ...gallusCell.rows];
  check(headerFits(gallusCell) && parts.every((x) => tt.includes(x)) && parts.map((x) => tt.indexOf(x)).every((v, i, a) => i === 0 || v > a[i - 1]),
    "shared tooltip at the Gallus point, in order: " + tt);
  await saveScreenshot("tooltip");
});

test("a count stands in a line of its own under the share", async ({ mapPage: page, check }) => {
  // docs/texts.md, Map: tooltip
  const countTips = await page.evaluate(() => {
    const at = (level, id, name) => { APP.setLevel(level); APP.setIndicator(id); const p = APP.properties(level).find((x) => x.name === name);
      const c = APP.countFor(APP.meta[id]);
      return { tip: APP.tooltipText(p), title: APP.meta[id].title, unit: c?.unit, rounded: c && p[c.id] != null ? APP.roundedCount(p[c.id], c.round_to, !!c.estimate) : null }; };
    const q = APP.properties("quarter").find((p) => p.name === "Gallus"), shCount = APP.countFor(APP.meta.SH_SHARE);
    // the count of the report: 1.754 Sozialwohnungen in Gallus
    const countLine = `${shCount.unit}: ${APP.format(q[shCount.id], 0)}`;
    const out = { sh: at("quarter", "SH_SHARE", "Gallus").tip, countLine, count: q[shCount.id],
      shWant: `<strong>Gallus</strong><br>${APP.meta.SH_SHARE.title}: ${APP.valueText("SH_SHARE", q.SH_SHARE, q)}<br>${countLine}`,
      old: at("quarter", "HOU_PRE1919", "Gallus"), post: at("district", "HOU_1949_1978", "Gallus"),
      vacantAll: at("quarter", "HOU_VACANT_ALL", "Gallus"), vacantMarket: at("district", "HOU_VACANT_MARKET", "Gallus"),
      turnout: at("quarter", "ELEC_TURNOUT", "Altstadt") };
    // no line without the share or without the count
    const save = q.SH_COUNT;
    q.SH_COUNT = null; out.noCount = at("quarter", "SH_SHARE", "Gallus").tip; q.SH_COUNT = save;
    APP.setIndicator("SH_SHARE");
    return out;
  });
  check(countTips.count === 1754 && countTips.sh === countTips.shWant && countTips.shWant.endsWith("<br>" + countTips.countLine),
    "Sozialwohnungen tooltip names the count of the report in its own line: " + JSON.stringify([countTips.sh, countTips.shWant]));
  // three lines: the area, the share with a tilde, the count of the layer (catalog unit) rounded, with a tilde or "under 10"
  const counted = (o) => { const l = o.tip.split("<br>");
    return l.length === 3 && l[1].startsWith(o.title + ": ") && /: ~\d+,\d %$/.test(l[1]) && o.rounded && l[2] === `${o.unit}: ${o.rounded}` && /^(~[\d.]+|\D+ 10)$/.test(o.rounded); };
  check([countTips.old, countTips.post].every((o) => counted(o) && o.tip.startsWith("<strong>Gallus")),
    "tooltip of the construction years: the estimated count with a tilde: " + [countTips.old.tip, countTips.post.tip].join(" | "));
  check([countTips.vacantAll, countTips.vacantMarket].every(counted),
    "tooltip of the vacancy: the estimated count: " + [countTips.vacantAll.tip, countTips.vacantMarket.tip].join(" | "));
  // the voters of the eligible in Altstadt: 1.343 of 2.871
  const turnout = countTips.turnout.tip.split("<br>");
  check(turnout.length === 3 && turnout[2].startsWith(countTips.turnout.unit + ": ") && numbers(turnout[2]).join() === "1343,2871",
    "tooltip of the turnout in Altstadt: voters of the eligible: " + countTips.turnout.tip);
  check(countTips.noCount === countTips.shWant.replace("<br>" + countTips.countLine, ""), "a missing count leaves the share only: " + countTips.noCount);
});

test("tooltip in candidates mode, on Stadtteile, on districts and of the election", async ({ mapPage: page, check }) => {
  await page.evaluate(([lat, lng]) => { APP.openTab("candidates"); APP.setTemplate("coop"); APP.map.setView([lat, lng], 15, { animate: false }); }, GALLUS);
  let tt = (await hoverAt(page, GALLUS)).join("");
  // the plain name (no district number) and the candidate line of the area; its leading numbers are those of the
  // evaluation: "met of 3", or only 3 when all are met
  const cand = await page.evaluate(() => { const p = APP.properties("quarter").find((x) => x.name === "Gallus"), b = APP.evaluationById[p.id], n = APP.activeCriteria().length;
    return { line: APP.candidateLine(b, n), met: b?.met, full: b?.full, n, district: APP.LEVEL_SINGULAR.district }; });
  const lead = cand.full ? [cand.n] : [cand.met, cand.n];
  check(cand.n === 3 && tt.startsWith("Gallus" + cand.line) && !tt.includes(cand.district)
    && JSON.stringify(numbers(cand.line).slice(0, lead.length)) === JSON.stringify(lead), "tooltip in candidates mode: " + tt.slice(0, 120));
  await page.evaluate(([lat, lng]) => { APP.openTab("city"); APP.setLevel("district"); APP.setIndicator("OWN_PUBLIC");
    APP.map.setView([lat, lng], 15, { animate: false }); }, GALLUS);
  tt = (await hoverAt(page, GALLUS)).join("");
  // the ownership layers exist per Stadtteil only, so the map is on Stadtteile here: no number
  const ownTitle = await page.evaluate(() => APP.meta.OWN_PUBLIC.title);
  check(tt.startsWith(`Gallus${ownTitle}: `), "tooltip on Stadtteile: " + tt.slice(0, 90));
  await page.evaluate(() => { APP.setLevel("district"); APP.setIndicator("SOC_MIN_INCOME"); });
  tt = (await hoverAt(page, GALLUS)).join("");
  // the label of the district under the point (APP.areaLabel) names its number
  const area = await page.evaluate(([lat, lng]) => { const p = APP.areaAt(L.latLng(lat, lng));
    return p && { label: APP.areaLabel(p, "district"), id: p.id, title: APP.meta.SOC_MIN_INCOME.title }; }, GALLUS);
  check(area && area.label.startsWith("Gallus (") && area.label.includes(area.id) && tt.startsWith(`${area.label}${area.title}: `), "tooltip on districts carries the number: " + tt.slice(0, 90));
  const election = await page.evaluate(() => { APP.setIndicator("ELEC_CDU");
    return { head: APP.tooltipHead(APP.properties("quarter").find((x) => x.name === "Gallus")), title: APP.meta.ELEC_CDU.title, shown: APP.titleWithElection(APP.meta.ELEC_CDU) }; });
  // the title of the list share with the name of the election after it (source vocabulary)
  check(election.shown.startsWith(election.title + " ") && election.shown.endsWith("(Stadtverordnetenwahl)") && election.head.startsWith(`<strong>Gallus</strong><br>${election.shown}: `), "election tooltip names the Stadtverordnetenwahl: " + election.head);
});

test("where the tooltip shows and where it closes", async ({ mapPage: page, check }) => {
  await page.evaluate(() => { APP.openTab("city"); APP.setLevel("district"); APP.setIndicator("ELEC_CDU"); });
  await page.evaluate(() => { for (const u of Object.values(APP.overlays)) u.on = true;
    APP.map.setView([50.10, 8.40], 13, { animate: false }); APP.updateOverlays(); });
  check((await hoverAt(page, [50.10, 8.40])).length === 0, "no tooltip outside Frankfurt");
  await gallusWith(page, ["land_value"]);
  check((await hoverAt(page, GALLUS)).length === 1, "tooltip at the Gallus point with land value");
  // The sidebar lies left of the map
  await page.mouse.move(200, 400);
  await frames(page);
  check((await openTooltips(page)).length === 0, "mouse leaves the map: no tooltip");
  // Leaving from a spot without an area (grid cell at the city edge, outside the quarter polygons): the tooltip closes then too.
  // The point moves to the left map edge, next to the sidebar.
  const EDGE = [50.17292, 8.711958];
  await gallusWith(page, ["grid"], 18, EDGE);
  const edgePoint = await page.evaluate(([lat, lng]) => {
    const c = APP.map.getContainer(), r = c.getBoundingClientRect();
    APP.map.panBy([c.clientWidth / 2 - 10, 0], { animate: false });
    const q = APP.map.latLngToContainerPoint([lat, lng]);
    return { x: r.left + q.x, y: r.top + q.y, area: APP.areaAt(L.latLng(lat, lng)) };
  }, EDGE);
  await page.mouse.move(edgePoint.x + 3, edgePoint.y);
  await page.mouse.move(edgePoint.x, edgePoint.y);
  await frames(page);
  const tips = await openTooltips(page);
  const edgeCell = await gridCellAt(page, EDGE);
  check(edgePoint.area === null && tips.length === 1 && tips[0] === edgeCell.text, "tooltip at the city edge only with the grid: " + tips.join(" | "));
  await page.mouse.move(200, edgePoint.y);
  await frames(page);
  check((await openTooltips(page)).length === 0, "mouse leaves the map at a spot without an area: no tooltip");
  await gallusWith(page, ["land_value"]);
  await hoverAt(page, GALLUS);
  const legendCenter = await page.evaluate(() => { const b = document.querySelector(".legend").getBoundingClientRect(); return { x: b.left + b.width / 2, y: b.top + b.height / 2 }; });
  await page.mouse.move(legendCenter.x, legendCenter.y);
  await frames(page);
  check((await openTooltips(page)).length === 0, "no tooltip over the legend");
});

test("at the map edge the tooltip stays inside the map; zooming closes it", async ({ mapPage: page, check }) => {
  // on the right it flips to the left, at the top and bottom it moves in
  const insideFrame = async (x, y) => {
    await page.mouse.move(x - 3, y - 3);
    await page.mouse.move(x, y);
    await frames(page);
    return page.evaluate(() => {
      const c = APP.map.getContainer().getBoundingClientRect();
      const t = [...document.querySelectorAll(".leaflet-tooltip")].filter((e) => e.style.opacity !== "0");
      if (t.length !== 1) return `Tooltips: ${t.length}`;
      const r = t[0].getBoundingClientRect();
      return r.left >= c.left - 1 && r.right <= c.right + 1 && r.top >= c.top - 1 && r.bottom <= c.bottom + 1 ? "ok"
        : `outside: ${[r.left, r.right, r.top, r.bottom].map(Math.round)} map ${[c.left, c.right, c.top, c.bottom].map(Math.round)}`;
    });
  };
  await gallusWith(page, ["social_preservation", "pending_plans", "land_value", "grid"]);
  const frame = await page.evaluate(() => { const c = APP.map.getContainer().getBoundingClientRect(); return { l: c.left, r: c.right, t: c.top, b: c.bottom }; });
  // the legend with its key stands at the lower right: the right-edge probe lies above it
  const rightY = await page.evaluate((f) => { const l = document.querySelector(".legend").getBoundingClientRect(); return Math.min((f.t + f.b) / 2, l.top - 20); }, frame);
  for (const [side, x, y] of [["right", frame.r - 100, rightY], ["top", (frame.l + frame.r) / 2, frame.t + 15],
    ["bottom", (frame.l + frame.r) / 2, frame.b - 15]]) {
    const e = await insideFrame(x, y);
    check(e === "ok", `tooltip at the ${side} edge stays inside the map: ${e}`);
  }
  await hoverAt(page, GALLUS);
  await page.evaluate(() => APP.map.setZoom(14.5, { animate: false }));
  check((await openTooltips(page)).length === 0, "zooming closes the tooltip");
});

test("help names the tooltip, exploring and the tilde", async ({ mapPage: page, check }) => {
  // the help line of a tab starts with the label of its tab button; the phone paragraph names the button of the
  // touch tooltip (APP.tooltipHead on touch)
  const help = await page.evaluate(() => {
    const touch = APP.touch; APP.touch = () => true;
    const div = document.createElement("div"); div.innerHTML = APP.tooltipHead(APP.properties("quarter")[0]);
    APP.touch = touch;
    const tab = (t) => document.querySelector(`#tabs button[data-tab="${t}"]`).textContent.trim();
    const line = (t) => [...document.querySelectorAll("#tab-help p")].find((p) => p.querySelector("strong")?.textContent === tab(t) + ":")?.textContent ?? "";
    return { button: div.querySelector("[data-explore]")?.textContent, phone: document.querySelector("#tab-help .phone-only")?.textContent ?? "",
      area: line("area"), city: line("city"), cityLabel: tab("city"), text: document.getElementById("tab-help").textContent };
  });
  check(help.button && help.phone.includes(help.button), "help names the tooltip: " + JSON.stringify(help));
  check(help.area.length > help.cityLabel.length + 10 && help.area.includes(help.cityLabel) && !help.text.includes("Gebiet: Ein Klick zeigt alle Werte."),
    "help explains exploring an area: " + help.area);
  check(help.city.includes("(~)") && !help.text.includes("mit Spanne") && !help.text.includes("Bei geschätzten Anteilen prüft die Karte"),
    "help names the tilde, not the criteria rule: " + help.city);
});

// docs/texts.md, Map texts: 2.1-2.4 tooltips: rank, survey area, grid cell lines, no plan codes
test("texts 2.1-2.4: rank, survey area, grid sentence, unique titles", async ({ mapPage: page, check }) => {
  const t = await page.evaluate(() => {
    APP.setLevel("district"); APP.setIndicator("SOC_INDEX");
    const ps = APP.properties("district"), n = ps.filter((p) => p.SOC_INDEX != null).length;
    const whole = ps.find((p) => p.SOC_INDEX != null && Number.isInteger(p.SOC_INDEX)), half = ps.find((p) => p.SOC_INDEX != null && !Number.isInteger(p.SOC_INDEX));
    return { n, whole: whole && { v: whole.SOC_INDEX, text: APP.tooltipText(whole) }, half: half && { v: half.SOC_INDEX, text: APP.tooltipText(half) },
      r46: APP.rankText("SOC_INDEX", 46), r23: APP.rankText("SOC_INDEX", 23.5), title: APP.meta.SOC_INDEX.title };
  });
  // a rank holds the rank and the number of ranks; a tie holds both ranks
  check(t.n === 114 && numbers(t.r46).join() === "46,114" && numbers(t.r23).join() === "23,24,114" && t.r46.indexOf("46") < t.r46.indexOf("114"),
    "10 2.1: rankText: " + t.r46 + " | " + t.r23);
  const value = (x) => x && x.text.split("<br>")[1];
  check(t.whole && value(t.whole).startsWith(t.title + ": ") && numbers(value(t.whole)).join() === [t.whole.v, t.n].join(),
    "10 2.1: whole rank in the tooltip: " + (t.whole && t.whole.text));
  check(t.half && value(t.half).startsWith(t.title + ": ") && numbers(value(t.half)).join() === [t.half.v - 0.5, t.half.v + 0.5, t.n].join(),
    "10 2.1: tied rank in the tooltip: " + (t.half && t.half.text));
  const s = await page.evaluate(() => {
    const p = APP.properties("district").find((q) => q.survey_area && q.id === "10") || APP.properties("district").find((q) => q.survey_area);
    const out = {};
    // the value line: the title (catalog), the class, then the survey area of the district at the end
    for (const id of ["LIF_ATTACHMENT", "LIF_RENT_BURDEN_RATIO"]) { APP.setIndicator(id); out[id] = [APP.tooltipText(p), `${APP.meta[id].title}: ${APP.withUnit(id, p[id], p)} `, p.survey_area]; }
    APP.setIndicator("OWN_PUBLIC"); out.own = APP.tooltipText(p); out.area = p.survey_area;
    return out;
  });
  const surveyLine = ([tip, start, area]) => { const l = tip.split("<br>")[1] ?? ""; return l.startsWith(start) && l.endsWith(" " + area) && l.length > start.length + area.length + 1; };
  check(surveyLine(s.LIF_ATTACHMENT) && s.LIF_ATTACHMENT[0].split("<br>").length === 2, "10 2.2: attachment tooltip names the survey area: " + s.LIF_ATTACHMENT[0]);
  check(surveyLine(s.LIF_RENT_BURDEN_RATIO), "10 2.2: rent burden tooltip names the survey area: " + s.LIF_RENT_BURDEN_RATIO[0]);
  check(s.area && !s.own.includes(s.area), "10 2.2: OWN_PUBLIC names no survey area");
  // 2.3 every group the grid uses: one sentence, the same but for the group in the dative (payload)
  const g = await page.evaluate(() => ({ groups: APP.data.grid_groups, dative: APP.data.grid_dative,
    sentences: APP.data.grid_groups.map((x, i) => APP.gridTip([i, 0, ...APP.data.grid_groups.map(() => 0)]).split("</div>")[0]) }));
  const frame = g.sentences.map((t, i) => (g.dative[g.groups[i]] && t.split(g.dative[g.groups[i]]).length === 2 ? t.split(g.dative[g.groups[i]]) : null));
  check(g.groups.length === 6 && frame.every((f) => f && f[0].startsWith("<div>") && f[0].length > 5 && f[1].length > 0 && JSON.stringify(f) === JSON.stringify(frame[0])),
    "10 2.3: the sentence of each grid group: " + JSON.stringify(g.sentences));
  // 2.4 no codes; overlay titles stay unique
  check(await page.evaluate(() => ["social_preservation", "social_preservation_pending", "townscape", "townscape_pending", "pending_plans"].every((k) =>
    new Set(APP.data[k].features.map((f) => f.properties.title)).size === APP.data[k].features.length)), "10 2.4: titles of every overlay with features are unique");
});
