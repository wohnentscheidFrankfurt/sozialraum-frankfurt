// Layers: the background map, ABG and Nassauische Heimstätte per Stadtteil, the ownership tooltips and profiles, the
// overlays, social housing and the survey layers on districts.
import { test } from "../fixtures.mjs";
import { frames } from "../helpers/common.mjs";
import { numbers } from "../helpers/layers.mjs";

test("background map comes from basemap.de", async ({ mapPage: page, check }) => {
  // the network is blocked on purpose: only the address is checked
  const tileUrl = await page.evaluate(() => APP.background._url);
  check(tileUrl.includes("geodatenzentrum.de") && tileUrl.includes("{z}/{y}/{x}"), "background map comes from basemap.de: " + tileUrl);
});

test("background tiles: BKG from file:, our proxy over http(s)", async ({ mapPage: page, check }) => {
  const urls = await page.evaluate(() => ["file:", "http:", "https:"].map((p) => APP.tileUrl(p)));
  check(urls[0].startsWith("https://sgx.geodatenzentrum.de/") && urls[0].endsWith("/{z}/{y}/{x}.png"), "file: " + urls[0]);
  check(urls[1] === "/sozialraum-frankfurt/kacheln/{z}/{y}/{x}.png", "http: " + urls[1]);
  check(urls[2] === urls[1], "https: " + urls[2]);
});

// pipeline/use_cases/public_housing/README.md
test("OWN_PUBLIC per Stadtteil: templates, layer, ramp and legend", async ({ mapPage: page, check }) => {
  check(await page.evaluate(() => APP.data.templates.map((v) => v.id).join()) === "social_preservation,coop,public_company",
    "templates: no ABG templates per district, one per Stadtteil");
  const publicLayer = await page.evaluate(() => {
    APP.openTab("city"); APP.setLevel("district");
    const label = document.querySelector('label[data-id="OWN_PUBLIC"]');
    const off = label.classList.contains("off");
    document.querySelector('#tab-city input[name="indicator"][value="OWN_PUBLIC"]').click(); // like in the UI
    const colors = new Set();
    APP.layers.quarter.eachLayer((l) => colors.add(l.options.fillColor));
    return { off, level: APP.state.level, active: APP.state.indicator, colors: [...colors], ramp: APP.rampFor(APP.meta.OWN_PUBLIC),
             legend: APP.legendDiv.textContent, city: APP.valueText("OWN_PUBLIC", APP.data.city_values.OWN_PUBLIC),
             districtValues: APP.properties("district").filter((p) => p.OWN_PUBLIC != null).length };
  });
  check(publicLayer.off && publicLayer.level === "quarter" && publicLayer.active === "OWN_PUBLIC", "OWN_PUBLIC: greyed on districts, a click switches to quarters: " + JSON.stringify(publicLayer));
  check(publicLayer.ramp[4] === "#d40000" && publicLayer.colors.length >= 3 && publicLayer.colors.every((c) => publicLayer.ramp.includes(c)),
    "OWN_PUBLIC: quarters in the ramp of #d40000: " + publicLayer.colors);
  check(publicLayer.city.startsWith("~") && publicLayer.legend.includes(": " + publicLayer.city) && (publicLayer.legend.match(/~/g) || []).length === 1
    && publicLayer.districtValues === 0, "OWN_PUBLIC: legend with city value ~, classes without tilde, no district has a value");
});

test("Gallus: tooltip and ownership profile", async ({ mapPage: page, check }) => {
  await page.evaluate(() => { APP.openTab("city"); APP.setIndicator("OWN_PUBLIC"); });
  const gallus = await page.evaluate(() => {
    const p = APP.properties("quarter").find((x) => x.id === "Gallus");
    const tip = APP.tooltipHead(p);
    // the parts of the tooltip from the catalog and the data: title, count (dwellingsText) and coverage
    const want = { title: APP.meta.OWN_PUBLIC.title, count: APP.dwellingsText(p.OWN_PUBLIC_DWELLINGS, p.OWN_PUBLIC_DWELLINGS_HIGH),
      coverage: APP.coverageText(p), cov: Math.round(p.COV_OWN) };
    APP.showProfile("Gallus");
    const table = [...document.querySelectorAll("#tab-area .table tr")].map((r) => r.textContent);
    const bar = [...document.querySelectorAll("#tab-area .stack span")].map((s) => s.title);
    const barColors = [...document.querySelectorAll("#tab-area .stack span")].map((s) => s.style.background);
    const head = [...document.querySelectorAll("#tab-area .table tr:first-child th")].map((th) => th.textContent.trim());
    return { tip, want, head, title: APP.meta.OWN_PUBLIC.title, old: !!document.querySelector("#tab-area .public-count, #info-profile-dwellings"), table, bar, barColors,
             shares: ["OWN_PUBLIC", "OWN_COOP", "OWN_COMPANY", "OWN_PERSON", "OWN_STATE", "OWN_NONPROFIT"].reduce((t, k) => t + p[k], 0) };
  });
  // docs/texts.md, Map: tooltip. The count of the group stands in the tooltip, below the share
  // four lines: name, share with a tilde, the count rounded to 50 with a tilde, the coverage (89 %, under 90 %)
  const lines = gallus.tip.split("<br>");
  check(lines.length === 4 && lines[0] === "<strong>Gallus</strong>" && lines[1].startsWith(gallus.want.title + ": ") && /: ~\d+,\d %$/.test(lines[1])
    && lines[2].endsWith(": " + gallus.want.count) && /^~\d\.\d[05]0$/.test(gallus.want.count)
    && lines[3] === gallus.want.coverage && numbers(lines[3])[0] === gallus.want.cov && gallus.want.cov < 90, "tooltip shows the estimate and the count with a tilde: " + gallus.tip);
  // the table has an empty first header, then area and city: two columns of values
  check(gallus.head.length === 3 && gallus.head[0] === "" && gallus.head.slice(1).every((h) => h !== "") && !gallus.old, "profile Gallus: shares only, no column and no line Wohnungen: " + gallus.head);
  check(gallus.bar.length === 6 && gallus.bar.every((t) => /: ~\d+,\d %$/.test(t)), "Gallus: hover of the ownership bar with a tilde: " + JSON.stringify(gallus.bar));
  check(gallus.barColors[0] === "rgb(212, 0, 0)" && gallus.barColors[2] === "rgb(140, 0, 0)", "Gallus: ownership bar in the colours of Trend: " + JSON.stringify(gallus.barColors));
  check(Math.abs(gallus.shares - 100) <= 0.1 && gallus.table.some((r) => r.startsWith(gallus.title)), "Gallus: shares add up to 100, table has the row: " + gallus.shares);
  check(gallus.table.length === 7 && gallus.table.slice(1).every((r) => /^[^~]+~\d+,\d\s?%~\d+,\d\s?%$/.test(r)), "Gallus: every share with a tilde, no range, no count: " + gallus.table.join(" | "));
});

test("tooltips of the ownership layers: count and coverage", async ({ mapPage: page, check, saveScreenshot }) => {
  await page.evaluate(() => { APP.openTab("city"); APP.setIndicator("OWN_PUBLIC"); APP.showProfile("Gallus"); });
  const ownTips = await page.evaluate(() => {
    APP.setLevel("quarter");
    // the tooltip and its expected parts: title (catalog), count line of the owner group (dwellingsText) or of the
    // layer (countLine), coverage (coverageText)
    const at = (id, name, level = "quarter") => { APP.setIndicator(id); const p = APP.properties(level).find((x) => x.name === name);
      const c = APP.countFor(APP.meta[id]);
      return { tip: APP.tooltipHead(p), title: APP.meta[id].title, coverage: APP.coverageText(p), countLine: APP.countLine(APP.meta[id], p),
        dwellings: id + "_DWELLINGS" in p ? APP.dwellingsText(p[id + "_DWELLINGS"], p[id + "_DWELLINGS_HIGH"]) : null,
        uncertain: p[id + "_DWELLINGS_HIGH"] - p[id + "_DWELLINGS"] > p[id + "_DWELLINGS"] / 3, unit: c?.unit,
        rounded: c && p[c.id] != null ? APP.roundedCount(p[c.id], c.round_to, !!c.estimate) : null }; };
    // HOU_PRE1919 has a count HOU_PRE1919_DWELLINGS of its own (count_of), but no owner group
    const out = { company: at("OWN_COMPANY", "Gallus"), ginnheim: at("OWN_COMPANY", "Ginnheim"), bonames: at("OWN_PUBLIC", "Bonames"), rent: at("HOU_RENT", "Gallus"),
                  old: at("HOU_PRE1919", "Gallus") };
    APP.setLevel("district");
    const first = APP.properties("district")[0].name;
    out.district = at("SOC_MIN_INCOME", first, "district");
    out.districtOld = at("HOU_1949_1978", first, "district");
    // the ⓘ of the layer explains the count
    APP.setLevel("quarter"); APP.setIndicator("OWN_PUBLIC");
    const info = document.getElementById("info-OWN_PUBLIC");
    out.info = protocolText(info);
    // the rule of the catalog, and the texts of the tooltip count it explains (APP.dwellingsText)
    out.rule = `${Object.fromEntries(APP.PROTOCOL).rule}: ${APP.meta.OWN_PUBLIC.rule}`;
    out.markers = [APP.dwellingsText(100, 150), APP.dwellingsText(100, 1000)];
    return out;
  });
  const lines = (o) => o.tip.split("<br>");
  const c = ownTips.company, cl = lines(c);
  check(cl.length === 4 && cl[0] === "<strong>Gallus</strong>" && cl[1].startsWith(c.title + ": ") && /: ~\d+,\d %$/.test(cl[1])
    && cl[2].endsWith(": " + c.dwellings) && c.coverage && cl[3] === c.coverage && numbers(c.coverage)[0] < 90,
    "tooltip of Gallus: count, then the coverage sentence (under 90 %): " + c.tip);
  check(ownTips.ginnheim.coverage === "" && lines(ownTips.ginnheim).length === 3, "tooltip of Ginnheim has no coverage sentence: " + ownTips.ginnheim.tip);
  // the upper end lies more than a third above the count: the line holds no number
  const b = ownTips.bonames;
  check(b.uncertain && lines(b).length === 3 && b.tip.endsWith(": " + b.dwellings) && !/\d/.test(b.dwellings) && b.dwellings !== "k. A.",
    "tooltip of Bonames, ABG: the count is too uncertain: " + b.tip);
  check([ownTips.rent, ownTips.district].every((o) => lines(o).length === 2 && o.countLine === "" && o.dwellings === null),
    "no count in the tooltip of a layer without one: " + [ownTips.rent.tip, ownTips.district.tip].join(" | "));
  // the construction years carry a count of their own (count_of), one line, without the coverage of the ownership
  check([ownTips.old, ownTips.districtOld].every((o) => lines(o).length === 3 && o.rounded && lines(o)[2] === `${o.unit}: ${o.rounded}`
    && /^(~[\d.]+|\D+ 10)$/.test(o.rounded) && o.tip.split(o.unit + ":").length === 2),
    "tooltip of the construction years: one line of its own count: " + [ownTips.old.tip, ownTips.districtOld.tip].join(" | "));
  check(!ownTips.info.includes("Im Tooltip steht") && ownTips.info.includes(ownTips.rule) && ownTips.markers.every((t) => t && !/\d/.test(t.replace("200", "")) && ownTips.rule.includes(t)),
    "ⓘ of OWN_PUBLIC explains the count of the tooltip: " + ownTips.info);
  await saveScreenshot("profile_gallus");
});

test("district profile: the values of its Stadtteil", async ({ mapPage: page, check }) => {
  // the note of the ownership block: the one before the stack
  const ownershipNote = () => document.querySelector("#tab-area .stack")?.previousElementSibling?.textContent ?? "";
  const district = await page.evaluate((noteFn) => {
    const note = new Function(`return (${noteFn})()`);
    APP.setLevel("quarter"); APP.showProfile(APP.quarterOf(APP.properties("district").find((x) => x.id === "10")).id);
    const quarterNote = note();
    APP.setLevel("district"); APP.showProfile("10");
    const t = document.getElementById("tab-area");
    return { text: t.textContent, rows: [...t.querySelectorAll(".table tr")].map((r) => r.textContent), note: note(), quarterNote,
             quarter: APP.quarterOf(APP.properties("district").find((x) => x.id === "10")).name, stack: t.querySelectorAll(".stack span").length };
  }, ownershipNote.toString());
  // A Bezirk shows the values of its Stadtteil (ownership block, Stadtteil-only rows): its note is the note of the
  // Stadtteil with a sentence before it that names the Stadtteil
  const from = district.note.slice(0, district.note.length - district.quarterNote.length);
  check(district.quarterNote && district.note.endsWith(district.quarterNote) && from.includes(district.quarter) && !district.quarterNote.includes(district.quarter)
    && !district.text.includes("Eigentum zeigt die Karte nur je Stadtteil.") && district.stack === 6 && district.rows.length === 7,
    "district profile: ownership of its Stadtteil: " + JSON.stringify({ stack: district.stack, rows: district.rows.length }));
  const viaDistrict = await page.evaluate(() => {
    // a row of a layer carries its id (data-layer)
    const rowOf = (t, id) => t.querySelector(`.row[data-layer="${id}"]`);
    const read = (id) => { const t = document.getElementById("tab-area"), r = rowOf(t, id);
      return r && { strong: r.querySelector("strong").textContent, bar: r.querySelector(".bar span").style.width, text: t.textContent }; };
    APP.setLevel("district"); APP.showProfile("213");
    const p = APP.properties("district").find((x) => x.id === "213"), q = APP.quarterOf(p);
    const t = document.getElementById("tab-area");
    const d = read("SH_SHARE");
    // the note of the rows of the Stadtteil (the last note before the row) names it; document order: own row, note,
    // Stadtteil row
    const before = (a, b) => Boolean(a && b) && Boolean(a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING);
    const note = [...t.querySelectorAll("p.note")].filter((n) => n.textContent.includes(q.name) && before(n, rowOf(t, "SH_SHARE"))).at(-1);
    const out = { d, q: q.name, expected: APP.valueText("SH_SHARE", q.SH_SHARE, q), note: note?.textContent,
      noteBeforeRow: before(note, rowOf(t, "SH_SHARE")),
      ownBefore: before(rowOf(t, "SOC_INDEX"), note) };
    APP.setLevel("quarter"); APP.showProfile("Nordend-West");
    out.quarterBar = read("SH_SHARE").bar;
    APP.showProfile("Gallus");
    // the heads of the notes about another area (APP.otherAreaNote), and the ownership note without a Stadtteil name
    const heads = [APP.otherAreaNote([APP.meta.SH_SHARE], ""), APP.otherAreaNote([], "")].map((h) => h.split(" ").slice(0, 3).join(" "));
    const g = document.getElementById("tab-area");
    out.gallusNotes = heads.some((h) => g.textContent.includes(h)) || (g.querySelector(".stack")?.previousElementSibling?.textContent ?? "Gallus").includes("Gallus");
    return out;
  });
  check(viaDistrict.q === "Nordend-West" && viaDistrict.d && viaDistrict.d.strong === viaDistrict.expected, "Bezirk 213: Sozialwohnungen of its Stadtteil, the share only: " + JSON.stringify(viaDistrict));
  check(viaDistrict.noteBeforeRow && viaDistrict.ownBefore, "Bezirk 213: own rows, then the note, then the Stadtteil rows: " + JSON.stringify(viaDistrict));
  check(viaDistrict.d && viaDistrict.d.bar === viaDistrict.quarterBar, "Bezirk 213: bar as in the Stadtteil: " + JSON.stringify(viaDistrict));
  check(!viaDistrict.gallusNotes, "a Stadtteil profile has no note about another area");
});

test("cell text of the line Wohnungen", async ({ mapPage: page, check }) => {
  // Text of the line Wohnungen in the tooltip on fixed values
  const cells = await page.evaluate(() => [[8, 8], [150, 199.9], [190, 210], [169, 215], [150, 230], [5715, null], [600, 800], [812.4, 925], [5715, 5847], [532, 787], [null, null]]
    .map(([v, h]) => APP.dwellingsText(v, h)).concat([APP.roundTo50(224.9), APP.roundTo50(225)]));
  // the rules: an upper end under 200 gives one text with the number 200 and no tilde; a count rounds to 50 with a
  // tilde; an upper end more than a third above the count gives one text without a number; a missing end reads k. A.
  const under = cells[0], uncertain = cells[4];
  check(under === cells[1] && JSON.stringify(numbers(under)) === "[200]" && !under.includes("~") && under !== "200"
    && JSON.stringify([cells[2], cells[3], cells[6], cells[7], cells[8]]) === JSON.stringify(["~200", "~150", "~600", "~800", "~5.700"])
    && uncertain === cells[9] && uncertain && !/\d|~/.test(uncertain) && uncertain !== "k. A."
    && cells[5] === "k. A." && cells[10] === "k. A." && cells[11] === 200 && cells[12] === 250,
    "cell text of Wohnungen: " + JSON.stringify(cells));
});

test("ownership only per Stadtteil: no criterion, no count shown", async ({ mapPage: page, check }) => {
  await page.evaluate(() => { APP.openTab("city"); APP.setLevel("district"); });
  // Ownership only per Stadtteil: the own query on districts offers no ownership criterion and no count
  const choice = await page.evaluate(() => { APP.openTab("candidates"); APP.setTemplate("custom");
    const ids = [...document.querySelectorAll("#criterion-new option")].map((o) => o.value);
    APP.openTab("city");
    return { ids, cityValues: ["OWN_PUBLIC_DWELLINGS", "OWN_PUBLIC_LOW", "OWN_COOP_LOW", "OWN_COOP_HIGH"].filter((k) => k in APP.data.city_values) }; });
  check(!choice.ids.some((id) => id.startsWith("OWN_")) && choice.ids.length > 0,
    "criteria list on districts without ownership: " + choice.ids.join());
  check(choice.cityValues.length === 0, "no city value for counts and range ends: " + choice.cityValues.join());
  // a count is a line of the tooltip only (docs/texts.md, Map: tooltip): no layer, no list of the
  // election, no criterion of the own query, on districts and on Stadtteile
  const countsShown = await page.evaluate(() => {
    const counts = APP.data.catalog.filter((m) => m.count_of).map((m) => m.id);
    APP.openTab("city");
    const layers = [...document.querySelectorAll('#tab-city input[name="indicator"]')].map((r) => r.value);
    const lists = [...document.querySelectorAll("#list-choice option")].map((o) => o.value);
    APP.openTab("candidates");
    const criteria = [], levels = [];
    for (const t of ["public_company", "custom"]) {
      APP.setTemplate(t);
      levels.push(APP.candidateLevel());
      criteria.push(...[...document.querySelectorAll("#criterion-new option")].map((o) => o.value));
    }
    APP.openTab("city");
    return { counts, levels, shown: [...layers, ...lists, ...criteria].filter((id) => counts.includes(id)) };
  });
  check(countsShown.counts.length === 6 && countsShown.counts.includes("ELEC_VOTERS") && countsShown.levels.join() === "quarter,district" && countsShown.shown.length === 0,
    "counts are in no layer list, no list choice and no criterion list: " + JSON.stringify(countsShown));
  check(await page.evaluate(() => { APP.setLevel("district"); APP.setIndicator("OWN_COOP"); return APP.state.level; }) === "quarter", "OWN_COOP switches to quarters");
});

test("overlays: ⓘ, grid legend and the townscape tooltip over land value zones", async ({ mapPage: page, check, saveScreenshot }) => {
  await page.evaluate(() => { APP.setLevel("district"); APP.setIndicator("OWN_PUBLIC"); APP.openTab("city"); });
  check(await page.evaluate(() => document.querySelectorAll("#overlays .info-button").length) === 8, "ⓘ on the 8 overlays with features");
  check(await page.evaluate(() => { const b = document.querySelector('#overlays .info-button[data-info="overlay-land_value"]'); if (!b) return false;
    b.click(); const i = document.getElementById("info-overlay-land_value"), o = APP.data.overlays.land_value, label = Object.fromEntries(APP.PROTOCOL);
    return Boolean(i) && !i.hidden && o.source.includes("BORIS") && protocolText(i).startsWith(`${label.source}: ${o.source}`)
      && Boolean(o.rule) && protocolText(i).includes(`${label.rule}: ${o.rule}`); }),
    "ⓘ land value zones opens with the source");
  check(await page.evaluate(() => document.querySelectorAll("#overlays .grid-legend i").length === APP.data.grid_groups.length),
    "grid legend with all groups");
  const point = await page.evaluate(() => {
    APP.overlays.land_value.on = true; APP.overlays.townscape.on = true; APP.updateOverlays();
    // point where a townscape area and a land value zone overlap
    const zoneRings = APP.data.land_value.features.flatMap((z) => (z.geometry.type === "Polygon" ? [z.geometry.coordinates[0]] : z.geometry.coordinates.map((p) => p[0])));
    for (const f of APP.data.townscape.features) {
      const ring = f.geometry.type === "Polygon" ? f.geometry.coordinates[0] : f.geometry.coordinates[0][0];
      const xs = ring.map((p) => p[0]), ys = ring.map((p) => p[1]);
      const [w, e, s, n] = [Math.min(...xs), Math.max(...xs), Math.min(...ys), Math.max(...ys)];
      for (let i = 1; i < 20; i++) for (let j = 1; j < 20; j++) {
        const lng = w + ((e - w) * i) / 20, lat = s + ((n - s) * j) / 20;
        if (APP.inRing(ring, lng, lat) && zoneRings.some((r) => APP.inRing(r, lng, lat))) {
          APP.map.fitBounds([[s, w], [n, e]], { animate: false });
          const r = document.getElementById("map").getBoundingClientRect(), p = APP.map.latLngToContainerPoint([lat, lng]);
          return { x: r.left + p.x, y: r.top + p.y };
        }
      }
    }
    return null;
  });
  check(point !== null, "found a point in a townscape area and a land value zone");
  if (point) {
    await page.mouse.move(point.x - 4, point.y - 4);
    await page.mouse.move(point.x, point.y);
    await frames(page);
    const tips = await page.evaluate(() => [...document.querySelectorAll(".leaflet-tooltip")].map((t) => t.textContent));
    // the rows start with the tip prefix of their overlay (payload)
    const prefix = await page.evaluate(() => [APP.data.overlays.townscape.tip, APP.data.overlays.land_value.tip]);
    check(tips.length === 1 && prefix.every((x) => x && tips[0].includes(x + " ")),
      `townscape and land value in the same tooltip (seen: ${tips.join(" | ").slice(0, 120)})`);
  }
  await saveScreenshot("overlays");
});

test("social housing 2025: quarters only", async ({ mapPage: page, check, saveScreenshot }) => {
  await page.evaluate(() => { APP.openTab("city"); APP.setLevel("district"); });
  await page.evaluate(() => APP.setIndicator("SH_SHARE"));
  check(await page.evaluate(() => APP.state.level) === "quarter", "SH_SHARE switches to quarters");
  await saveScreenshot("sw_ant");
  await page.evaluate(() => { APP.openTab("candidates"); APP.openTab("city"); });
  check(await page.evaluate(() => APP.state.level) === "quarter", "back from candidates to layers: quarter layer stays on quarters");
});
