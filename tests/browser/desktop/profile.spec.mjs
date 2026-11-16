// Profile: the tab Gebiet of an area, the overlays above it, a click through an overlay, the townscape statutes,
// and the rows that show a share only. Texts of the map are compared with the payload and the catalog of the page
// (APP), never with a literal (docs/texts.md, Where texts live).
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { test } from "../fixtures.mjs";
import { integers, paths } from "../helpers/common.mjs";
import { clickPoint, commonStart, profileBlocks, sectionDates, zoomDone } from "../helpers/profile.mjs";

// the head of the tab Gebiet: name, the line under it, and the area of the payload with its formatted residents
const profileHead = (page, id) => page.evaluate((aid) => {
  const p = APP.properties(APP.state.level).find((x) => x.id === aid);
  return { h2: document.querySelector("#tab-area h2")?.textContent, sub: document.querySelector("#tab-area h2 + p")?.textContent,
    name: p.name, pop: APP.format(p.POP, 0), active: document.querySelector("#tab-area").classList.contains("active") };
}, id);

test.describe("profile and overlays", () => {
  test("profile of Altstadt", async ({ mapPage: page, check }) => {
    const profile = await page.evaluate(() => { APP.setLevel("district"); APP.showProfile("10"); return document.getElementById("tab-area").textContent; });
    check(profile.includes("Altstadt"), "profile shows the name");
    // the closing note of the profile: one bold note after the election block
    const end = await page.evaluate(() => { const e = document.getElementById("tab-area").lastElementChild;
      return { note: e.matches("p.note") && e.children.length === 1 && e.firstElementChild.tagName === "STRONG", text: e.textContent }; });
    check(end.note && end.text.trim() !== "", "profile shows the note");
    // the election block of a district: its heading is the election group of the catalog with the year, the note
    // under it names the Stadtteil the results come from
    const election = await page.evaluate(() => {
      const row = document.querySelector('#tab-area .row[data-layer^="ELEC_"]');
      let h = row?.previousElementSibling;
      while (h && h.tagName !== "H3") h = h.previousElementSibling;
      return { head: h?.textContent, group: APP.meta.ELEC_STRONGEST.group, note: h?.nextElementSibling?.matches("p.note") ? h.nextElementSibling.textContent : null,
        quarter: APP.quarterOf(APP.properties("district").find((x) => x.id === "10")).name };
    });
    check(election.head && new RegExp(`^${election.group} \\d{4}$`).test(election.head) && election.note && election.note.includes(election.quarter),
      "profile shows the election of the quarter: " + JSON.stringify(election));
    check(await page.evaluate(() => document.querySelector("#tab-area").classList.contains("active")), "profile opens the area tab");
  });

  test("overlays, owner colours and the grid", async ({ mapPage: page, check }) => {
    await page.evaluate(() => { APP.setLevel("district"); APP.showProfile("10"); });
    await zoomDone(page); // a running zoom animation from fitBounds would swallow setZoom
    const overlayState = await page.evaluate(() => {
      APP.overlays.grid.on = true;
      APP.map.setZoom(15, { animate: false });
      APP.updateOverlays();
      return { grid: APP.map.hasLayer(APP.overlays.grid.layer), preservation: APP.map.hasLayer(APP.overlays.social_preservation.layer), pattern: Boolean(document.getElementById("hatch")) };
    });
    check(overlayState.grid && overlayState.preservation && overlayState.pattern, "overlays and hatching visible: " + JSON.stringify(overlayState));
    // the owner groups take the colours of the view Trend (docs/design.md, Owner groups)
    const ownerColors = await page.evaluate(() => Object.fromEntries(APP.OWNERSHIP.map((e) => [e.id, e.color])));
    check(JSON.stringify(ownerColors) === JSON.stringify({ OWN_PUBLIC: "#d40000", OWN_STATE: "#ffc9c2", OWN_COOP: "#8c0000",
      OWN_COMPANY: "#262626", OWN_PERSON: "#a6a6a6", OWN_NONPROFIT: "#f07067" }), "owner colours as in Trend: " + JSON.stringify(ownerColors));
    // the light grey of Privatpersonen und WEG ends darker in its ramp, still grey (docs/design.md, Ramps)
    const personEnd = await page.evaluate(() => APP.rampFor(APP.meta.OWN_PERSON)[4]);
    check(/^#([0-9a-f]{2})\1\1$/.test(personEnd) && personEnd < "#a6a6a6", "OWN_PERSON: ramp ends in a darker grey: " + personEnd);
    // the grid cells use the owner colours (not Leaflet's default blue)
    const gridColors = await page.evaluate(() => {
      const owner = new Set(APP.OWNERSHIP.map((e) => e.color));
      const cells = APP.overlays.grid.layer.getLayers();
      return { cells: cells.length, wrong: cells.filter((l) => !owner.has(l.options.fillColor)).length };
    });
    check(gridColors.cells > 0 && gridColors.wrong === 0, "grid cells use the owner colours, not Leaflet's default: " + JSON.stringify(gridColors));
    await page.evaluate(() => { APP.map.setZoom(12, { animate: false }); APP.updateOverlays(); });
    check(!(await page.evaluate(() => APP.map.hasLayer(APP.overlays.grid.layer))), "grid disappears below zoom 14");
  });

  test("tooltip heads", async ({ mapPage: page, check }) => {
    // the bold head of a tooltip, before the first line break
    const head = (tip) => (/^<strong>([^<]*)<\/strong><br>/.exec(tip) || [])[1];
    const tip = await page.evaluate(() => { APP.setLevel("district"); return APP.tooltipHead(APP.properties("district").find((p) => p.id === "213")); });
    const name = await page.evaluate(() => APP.properties("district").find((p) => p.id === "213").name);
    check(head(tip)?.startsWith(name + " (") && /\b213\)$/.test(head(tip)), "tooltip names the district with its number: " + tip);
    const quarterTip = await page.evaluate(() => { APP.setLevel("quarter"); const t = APP.tooltipHead(APP.properties("quarter").find((p) => p.name === "Nordend-West")); APP.setLevel("district"); return t; });
    check(head(quarterTip) === "Nordend-West", "tooltip of a Stadtteil has no number: " + quarterTip);
    const gallusTip = await page.evaluate(() => { APP.setLevel("quarter"); const t = APP.tooltipHead(APP.properties("quarter").find((p) => p.name === "Gallus")); APP.setLevel("district"); return t; });
    check(gallusTip.includes("Gallus") && !gallusTip.includes("<button"), "desktop tooltip has no explore button: " + gallusTip);
  });
});

// 3b. A click through land values and grid opens the profile of the area underneath
for (const [u, zoom] of [["land_value", 0], ["grid", 15]]) {
  test(`click through ${u} opens the profile underneath`, async ({ mapPage: page, check }) => {
    await zoomDone(page);
    const pt = await clickPoint(page, u, zoom);
    check(pt !== null, `${u}: found a point in district 213 under the overlay`);
    if (!pt) return;
    await page.mouse.click(pt.x, pt.y);
    const h = await profileHead(page, "213");
    check(h.h2 === h.name && h.sub?.includes(`213 · ${h.pop} `), `click through ${u} opens the profile of district 213: ${JSON.stringify(h)}`);
    check(h.active, `click through ${u} opens the area tab`);
  });
}

// 3c. Profile: no rank line in the deprivation index (it ran opposite to the index) and date of the protection data
test.describe("profile parts", () => {
  test("deprivation index and planning block", async ({ mapPage: page, check }) => {
    await page.evaluate(() => { APP.setLevel("district"); APP.showProfile("213"); });
    // docs/texts.md, Map: tooltip. The profile row names the rank as the tooltip does
    // the rank has no city value, neither in the legend nor in the profile row: every line of the legend body has a
    // swatch (the city value is a line without one), and none is the white of a missing value
    check(await page.evaluate(() => { APP.setIndicator("SOC_INDEX"); const body = APP.legendDiv.querySelector(".legend-body").cloneNode(true);
      body.querySelector(".legend-overlays")?.remove();
      const lines = body.innerHTML.split("<br>").filter((l) => l.trim() !== "");
      return lines.length > 1 && lines.every((l) => l.startsWith("<i ")) && !/background:\s*#ffffff/i.test(body.innerHTML); }),
    "legend SOC_INDEX: neither Median nor Ganz Frankfurt");
    check(await page.evaluate(() => { const row = document.querySelector('#tab-area .row[data-layer="SOC_INDEX"]');
      const p = APP.properties("district").find((x) => x.id === "213");
      return row && row.querySelector("strong").textContent === APP.rankText("SOC_INDEX", p.SOC_INDEX, "district")
        && !row.querySelector("span.note") && !row.querySelector(".city"); }),
    "profile row SOC_INDEX shows the rank, no Median and no city value");
    // the planning block names no date and shows only the statutes and plans the area has
    const planning = await page.evaluate(() => {
      const p = APP.properties("district").find((x) => x.id === "213");
      return { known: [p.social_preservation_names, p.PROT_SOCIAL > 0 ? APP.withUnit("PROT_SOCIAL", p.PROT_SOCIAL) : null, p.social_preservation_pending_names,
        p.townscape_names, p.townscape_pending_names, p.pending_plan_names].filter(Boolean) };
    });
    const { blocks } = await profileBlocks(page);
    const plan = blocks.planning;
    check(plan && plan.date === null && plan.strong.length > 0 && plan.strong.every((v) => v !== "" && planning.known.includes(v)), "planning block: no as-of line, no empty rows: " + JSON.stringify([plan, planning.known]));
  });

  test("short profile parts and dates", async ({ mapPage: page, check }) => {
    // docs/texts.md, Area names: short profile parts
    const plain = await page.evaluate(() => {
      APP.setLevel("district");
      const p = APP.properties("district").find((x) => !x.social_preservation_names && !x.social_preservation_pending_names);
      APP.showProfile(p.id, false);
      return p.id;
    });
    // without any Milieuschutz the planning block opens with one note
    const plainPlan = (await profileBlocks(page)).blocks.planning;
    check(plainPlan && plainPlan.items[0] === "note" && plainPlan.notes.length === 1 && plainPlan.notes[0].trim() !== "",
      "profile without Milieuschutz says so in one line: " + JSON.stringify([plain, plainPlan]));
    const osthafen = await page.evaluate(() => { APP.showProfile("261", false); return { sub: document.querySelector("#tab-area h2 + p").textContent,
      quarter: APP.properties("district").find((x) => x.id === "261").quarter }; });
    check(osthafen.sub.includes("· " + osthafen.quarter), "profile of Osthafen names its quarter: " + JSON.stringify(osthafen));
    // every group heading names the dates of its rows, each once (docs/texts.md, Map: profile)
    const district = (await profileBlocks(page)).blocks;
    const want = {};
    for (const s of ["situation", "rent", "stock", "land"]) want[s] = await sectionDates(page, s, "261", "district");
    check(Object.entries(want).every(([s, d]) => d !== "" && district[s]?.date === d), "group headings carry their date: " + JSON.stringify([want, Object.values(district).map((b) => b.date)]));
    // the ownership heading (only on a Stadtteil) names only 2022; how 2011 is used says the ⓘ of each layer
    const ownership = await page.evaluate(() => ({ estimate: APP.meta.OWN_PUBLIC.as_of.split(" · ") }));
    await page.evaluate(() => { APP.setLevel("quarter"); APP.showProfile("Gallus", false); });
    const gallusOwn = (await profileBlocks(page)).blocks.ownership;
    check(gallusOwn && gallusOwn.date === ownership.estimate[0] && ownership.estimate.length > 1, "ownership heading without 2011: " + JSON.stringify([gallusOwn?.date, ownership]));
    check(Object.keys(district)[0] === "ownership" && district.ownership.date === gallusOwn?.date,
      "a district has the ownership heading of its Stadtteil, first: " + JSON.stringify(Object.values(district).map((b) => b.date)));
    // the construction year counts dwellings of 2011 (pipeline/use_cases/construction_year/README.md): its group names each date once
    const stock = district.stock?.date?.split(", ") ?? [];
    const pre1919 = await page.evaluate(() => APP.meta.HOU_PRE1919.as_of.split(" · "));
    check(stock.length >= 3 && new Set(stock).size === stock.length && pre1919.every((d) => stock.includes(d)),
      "Wohnungsbestand names 2025, 2022 and 2011 once: " + JSON.stringify([stock, pre1919]));
  });

  test("blocks by topic", async ({ mapPage: page, check }) => {
    // docs/texts.md, Map: profile: the blocks by topic, the same on a Bezirk and a Stadtteil; survey and Stadtteil values
    // come after the own rows, each group with one note (singular for one value, plural for more or with breakdown bars)
    await page.evaluate(() => { APP.setLevel("district"); APP.showProfile("213", false); });
    const district = await profileBlocks(page);
    const area = await page.evaluate(() => { const p = APP.properties("district").find((x) => x.id === "213"); return { survey: p.survey_area, quarter: APP.quarterOf(p).name }; });
    await page.evaluate(() => { APP.setLevel("quarter"); APP.showProfile("Gallus", false); });
    const quarter = await profileBlocks(page);
    // the tab Stadt: a heading per choice; the level choice, the groups of the catalog, the overlays
    const layers = await page.evaluate(() => { APP.openTab("city");
      return [...document.querySelectorAll("#tab-city h3")].map((h) => {
        const c = h.nextElementSibling, ids = [...c.querySelectorAll("label[data-id]")].map((l) => l.dataset.id).filter((id) => APP.meta[id]);
        const sections = [...new Set(ids.map((id) => APP.meta[id].section))];
        return c.querySelector('input[name="level"]') ? "level" : c.querySelector("input[data-overlay]") ? "overlays"
          : sections.length === 1 && h.textContent.trim() === APP.meta[ids[0]].group ? sections[0] : "?" + h.textContent; }); });
    const HEADS = ["ownership", "situation", "rent", "stock", "land", "planning", "election"];
    check(JSON.stringify(district.sections) === JSON.stringify(HEADS), "Bezirk 213: blocks by topic: " + JSON.stringify(district.sections));
    check(JSON.stringify(quarter.sections) === JSON.stringify(HEADS), "Gallus: blocks by topic: " + JSON.stringify(quarter.sections));
    const b = district.blocks;
    check(JSON.stringify(b.situation?.items) === JSON.stringify(["SOC_MIN_INCOME", "SOC_UNEMPLOYED", "SOC_INDEX", "note", "LIF_ATTACHMENT"])
      && b.situation.notes[0].endsWith(` ${area.survey}.`),
    "Bezirk 213: Soziale Lage, own rows, then the survey value with its note: " + JSON.stringify(b.situation));
    check(JSON.stringify(b.rent?.items) === JSON.stringify(["HOU_RENTERS", "HOU_RENT", "note", "LIF_RENT_BURDEN_RATIO", "breakdown"])
      && b.rent.notes[0].endsWith(` ${area.survey}.`),
    "Bezirk 213: Miete, own rows, then the survey values with their note: " + JSON.stringify(b.rent));
    const rentDates = await sectionDates(page, "rent", "213", "district");
    check(b.rent?.date === rentDates && rentDates.split(", ").length === 3, "Bezirk 213: Miete names its dates once: " + JSON.stringify([b.rent?.date, rentDates]));
    // one value under a note (Soziale Lage, Sozialwohnungen) reads alike, more values (Miete) read otherwise
    const [one, more, fromQuarter] = [b.situation?.notes[0] ?? "", b.rent?.notes[0] ?? "", b.stock?.notes.at(-1) ?? ""];
    check(JSON.stringify(b.stock?.items.slice(-2)) === JSON.stringify(["note", "SH_SHARE"]) && fromQuarter.endsWith(` ${area.quarter}.`)
      && commonStart(one, fromQuarter) > commonStart(one, more),
    "Bezirk 213: Sozialwohnungen of the Stadtteil last, with the singular note: " + JSON.stringify([b.stock, one, more]));
    check(JSON.stringify(b.land?.items) === JSON.stringify(["LAND_VALUE", "ROOF_FLAT", "GAP_AREA"]) && b.planning && b.planning.date === null,
      "Bezirk 213: Boden holds the Bodenrichtwert, the flat roofs and the building gaps, Planung names no date: " + JSON.stringify([b.land, b.planning]));
    const q = quarter.blocks;
    const gallusRent = await sectionDates(page, "rent", "Gallus", "quarter");
    check(JSON.stringify(q.rent?.items) === JSON.stringify(["HOU_RENTERS", "HOU_RENT"]) && q.rent.date === gallusRent && !gallusRent.includes(","),
      "Gallus: Miete without survey values: " + JSON.stringify([q.rent, gallusRent]));
    const surveyIds = await page.evaluate(() => APP.data.catalog.filter((m) => m.survey_area).map((m) => m.id));
    const gallusItems = ["situation", "rent", "stock", "land"].flatMap((s) => q[s]?.items ?? []);
    check(q.stock?.items[0] === "SH_SHARE" && !gallusItems.includes("note") && !gallusItems.some((id) => surveyIds.includes(id)),
      "Gallus: Sozialwohnungen first, no survey note: " + JSON.stringify(q.stock));
    check(JSON.stringify(layers) === JSON.stringify(["level", "ownership", "situation", "rent", "stock", "land", "election", "overlays"]),
      "Stadt: the same topics in the same order: " + JSON.stringify(layers));
    const layerHeads = await page.evaluate(() => [...document.querySelectorAll("#tab-city h3")].map((h) => h.textContent.trim()));
    const all = [...Object.values(district.blocks), ...Object.values(quarter.blocks)].map((x) => x.head).concat(layerHeads);
    check(!all.some((h) => h.startsWith("Umfrage") || h.includes("Belastung") || h === "Schutz" || h === "Lage"),
      "no heading Umfrage, Belastung, Schutz or Lage alone: " + JSON.stringify(all));
  });

  test("construction classes, counts and the ⓘ of profile rows", async ({ mapPage: page, check }) => {
    const construction = await page.evaluate(() => {
      APP.setLevel("district");
      APP.openTab("city");
      const labels = Object.fromEntries([...document.querySelectorAll('#tab-city label[data-id]')].map((l) => [l.dataset.id, l.textContent.trim()]));
      // the construction-year layers: the shares of the catalog from the Zensus table of dwellings by Baujahr
      const yearIds = APP.data.catalog.filter((m) => m.layer === true && !m.count_of && /\bBaujahr\b/.test(m.source)).map((m) => m.id);
      const first = APP.properties("district")[0];
      APP.showProfile(first.id, false);
      const rowOf = (id) => document.querySelector(`#tab-area .row[data-layer="${id}"]`);
      const rows = ["HOU_PRE1919", "HOU_1949_1978"].map((id) => { const r = rowOf(id);
        return r && { id, strong: r.querySelectorAll("strong").length, value: r.querySelector("strong").textContent, share: APP.valueText(id, first[id], first), text: r.textContent }; });
      // the count stands in the tooltip, under the share: rounded to 10, "unter 10" below
      // (docs/texts.md, Map: tooltip); the step comes from the catalog
      APP.setIndicator("HOU_PRE1919");
      const line = (p) => APP.tooltipText(p).split("<br>").slice(2).join("<br>");
      const byCount = APP.properties("district").filter((p) => p.HOU_PRE1919_DWELLINGS != null && p.HOU_PRE1919 != null)
        .sort((a, b) => a.HOU_PRE1919_DWELLINGS - b.HOU_PRE1919_DWELLINGS);
      const small = byCount[0], large = byCount.at(-1), count = APP.meta.HOU_PRE1919_DWELLINGS;
      const cases = [null, 0, 9, 10, 14, 15, 1235].map((x) => APP.roundedCount(x, count.round_to));
      // the ⓘ of the layer explains the count of the tooltip
      const info = protocolText(document.getElementById("info-HOU_PRE1919"));
      // every profile row without its own layer has an ⓘ (otherwise its protocol is out of reach); no other row has one
      APP.showProfile(APP.properties("quarter")[0].id, false);
      const infoRows = [...document.querySelectorAll("#tab-area .row")].filter((r) => !r.closest(".breakdown")).map((r) => {
        const title = r.querySelector("span").childNodes[0].textContent.trim();
        return [APP.data.catalog.find((x) => x.title === title), !!r.querySelector(".info-button"), r.textContent];
      }).filter(([m]) => m);
      return { labels, yearIds, titles: { HOU_PRE1919: APP.meta.HOU_PRE1919.title, HOU_1949_1978: APP.meta.HOU_1949_1978.title },
        countIds: APP.data.catalog.filter((m) => m.count_of).map((m) => m.id), rows, cases, info, rule: APP.meta.HOU_PRE1919.rule, step: count.round_to,
        unit: count.unit, missing: APP.valueText("OWN_COOP", null),
        small: [small.HOU_PRE1919_DWELLINGS, line(small)], large: [large.HOU_PRE1919_DWELLINGS, line(large)],
        noInfo: infoRows.filter(([m, b]) => m.layer === false && !b).map(([, , t]) => t),
        extraInfo: infoRows.filter(([m, b]) => m.layer !== false && b).map(([, , t]) => t) };
    });
    // exactly the two construction classes, each under its catalog title; no third class (the old Altbau vor 1949)
    const yearLabels = construction.yearIds.filter((id) => id in construction.labels);
    check(JSON.stringify(construction.yearIds) === JSON.stringify(["HOU_PRE1919", "HOU_1949_1978"]) && JSON.stringify(yearLabels) === JSON.stringify(construction.yearIds)
      && construction.labels.HOU_PRE1919 === construction.titles.HOU_PRE1919 && construction.labels.HOU_1949_1978 === construction.titles.HOU_1949_1978
      && !construction.countIds.some((id) => id in construction.labels),
    "layers: both construction classes, no Altbau vor 1949, no counts: " + JSON.stringify([construction.yearIds, yearLabels, construction.titles, construction.countIds.filter((id) => id in construction.labels)]));
    check(construction.rows.every((r) => r && r.strong === 1 && r.value === r.share && !r.text.includes(" · ")),
      "profile shows the shares of both classes, no count: " + JSON.stringify(construction.rows));
    // one rounding only: the city value 16.44673 shows as 16,4 % (stored with eight decimals, not 16.45)
    check(await page.evaluate(() => APP.withUnit("HOU_PRE1919", APP.data.city_values.HOU_PRE1919)) === "16,4 %",
      "city value of Altbau vor 1919 rounded once to 16,4 %");
    check(await page.evaluate(() => APP.valueText("HOU_PRE1919", APP.data.city_values.HOU_PRE1919)) === "~16,4 %"
      && await page.evaluate(() => APP.valueText("OWN_COOP", null)) === "k. A.", "tilde at an estimated share, none at a missing value");
    // below the step one text that names the step and is no number; above it the count rounded to the step
    const [none, zero, nine, ...rounded] = construction.cases;
    check(construction.step === 10 && none === construction.missing && zero === nine && zero.includes("10") && !/^[\d.]+$/.test(zero)
      && rounded.join("|") === "10|10|20|1.240", "rounding of counts: " + construction.cases.join("|"));
    // the tooltip line of the count: the unit of the count in the catalog, a colon, the count
    const below = zero;
    check(construction.small[1] === `${construction.unit}: ` + (construction.small[0] < 10 ? below : "~" + (10 * Math.round(construction.small[0] / 10)).toLocaleString("de-DE")),
      "tooltip: smallest count of Altbau, 'unter 10' below 10: " + JSON.stringify(construction.small));
    check(construction.large[1] === `${construction.unit}: ~` + (10 * Math.round(construction.large[0] / 10)).toLocaleString("de-DE"),
      "tooltip: largest count of Altbau rounded to 10: " + JSON.stringify(construction.large));
    // the rule of the layer in the catalog names the step and the text below it; the ⓘ shows that rule
    check(construction.rule.includes(` ${construction.step} `) && construction.rule.includes(below) && construction.info.includes(construction.rule),
      "the ⓘ of Altbau vor 1919 explains the rounding of the tooltip: " + construction.info);
    check(construction.noInfo.length === 0, "profile rows without a layer have an ⓘ: " + construction.noInfo.join(" | "));
    check(construction.extraInfo.length === 0, "profile rows with a layer have no ⓘ of their own: " + construction.extraInfo.join(" | "));
  });

  test("profile heads of a Stadtteil and a Bezirk", async ({ mapPage: page, check }) => {
    const first = await page.evaluate(() => { APP.setLevel("quarter"); const id = APP.properties("quarter")[0].id; APP.showProfile(id); return id; });
    const quarter = await profileHead(page, first);
    const ranks = await page.evaluate(() => { const rank = APP.data.catalog.filter((m) => m.rank > 0).map((m) => m.id);
      return document.querySelectorAll(rank.map((id) => `#tab-area [data-layer="${id}"]`).join(",")).length; });
    check(quarter.sub?.includes(quarter.pop) && ranks === 0, "quarter profile shows no rank: " + JSON.stringify([quarter, ranks]));
    // a Stadtteil names its residents first; a Bezirk names its number before them
    check(quarter.sub?.startsWith(quarter.pop + " ") && !(await page.evaluate(() => document.querySelector("#tab-area .note.shared"))),
      "quarter profile names no district number: " + JSON.stringify(quarter));
    await page.evaluate(() => { APP.setLevel("district"); APP.showProfile("343"); });
    const district = await profileHead(page, "343");
    check(district.h2 === district.name && district.sub?.includes(`343 · ${district.pop} `) && district.sub.indexOf("343") < district.sub.indexOf(district.pop)
      && district.sub.includes("2022"), "district profile: name, then number and residents: " + JSON.stringify(district));
  });
});

// 3e. Townscape statutes (§ 172 Abs. 1 Nr. 1): grey overlay, profile row, click through
test("townscape statutes", async ({ mapPage: page, check, saveScreenshot }) => {
  const townscapeDistrict = readFileSync(join(dirname(paths.candidatesCsv), "protection_by_district.csv"), "utf8").trim().split(/\r?\n/).slice(1)
    .map((line) => line.split(",")).find((cols) => cols.join(",").includes("Alt-Sachsenhausen"))?.[0];
  check(Boolean(townscapeDistrict), "protection_by_district.csv names a district with Alt-Sachsenhausen");
  const townscape = await page.evaluate(() => {
    const u = APP.overlays.townscape;
    if (!u) return null;
    const before = { on: u.on, shown: APP.map.hasLayer(u.layer) };
    APP.openTab("city");
    const box = document.querySelector('#tab-city input[data-overlay="townscape"]');
    box.click(); // like in the UI: click the checkbox
    const after = { on: u.on, shown: APP.map.hasLayer(u.layer), checked: box.checked };
    box.click();
    return { before, after, end: APP.map.hasLayer(u.layer), pending: Boolean(APP.overlays.townscape_pending) };
  });
  check(townscape && townscape.before.on === false && townscape.before.shown === false, "townscape is off by default: " + JSON.stringify(townscape));
  check(townscape && townscape.after.on && townscape.after.shown && townscape.after.checked && !townscape.end && townscape.pending, "townscape can be switched on and off with the checkbox: " + JSON.stringify(townscape));
  const townscapeCounts = await page.evaluate(() => [APP.data.townscape?.features.length ?? null, APP.data.townscape_pending?.features.length ?? null]);
  check(townscapeCounts[0] === 32 && townscapeCounts[1] === 4, "townscape statutes: 32 valid, 4 in procedure: " + townscapeCounts);
  if (!townscapeDistrict) return;
  // the planning block shows the townscape statutes of the district, as the payload names them
  const townscapeRow = () => page.evaluate((id) => { const p = APP.properties("district").find((x) => x.id === id);
    return { names: p.townscape_names, h2: document.querySelector("#tab-area h2")?.textContent, name: p.name,
      row: [...document.querySelectorAll("#tab-area .row strong")].some((s) => s.textContent === p.townscape_names) }; }, townscapeDistrict);
  await page.evaluate((id) => { APP.setLevel("district"); APP.showProfile(id); }, townscapeDistrict);
  const shown = await townscapeRow();
  check(shown.row && shown.names.includes("Alt-Sachsenhausen"), `profile of district ${townscapeDistrict} names Alt-Sachsenhausen in the block Planung`);
  await zoomDone(page);
  const pt = await clickPoint(page, "townscape", 0, townscapeDistrict);
  check(pt !== null, `townscape: found a point in district ${townscapeDistrict} under a townscape area`);
  if (!pt) return;
  await page.mouse.click(pt.x, pt.y);
  const clicked = await townscapeRow();
  check(clicked.h2 === clicked.name && clicked.row, `click through townscape opens the profile of district ${townscapeDistrict}: ${JSON.stringify(clicked)}`);
  await zoomDone(page);
  await page.evaluate(() => {
    const f = APP.data.townscape.features.find((x) => x.properties.title.includes("Alt-Sachsenhausen"));
    const m = L.geoJSON(f).getBounds().getCenter();
    APP.overlays.social_preservation.on = true; APP.overlays.townscape_pending.on = true; APP.setIndicator("OWN_PUBLIC");
    APP.map.setView([m.lat, m.lng], 15, { animate: false });
    APP.updateOverlays();
  });
  await page.mouse.move(200, 800);
  await saveScreenshot("townscape");
});

// 5.3, 5.4 profile: a row shows the share only, its count stands in the tooltip
// (docs/texts.md, Map: profile); the area sentence follows the election
test("rows show the share only", async ({ mapPage: page, check }) => {
  const r = await page.evaluate(() => {
    const rowOf = (id) => document.querySelector(`#tab-area .row[data-layer="${id}"]`);
    const strong = (id) => rowOf(id).querySelector("strong").textContent;
    // a row holds its title, one value and the city value, nothing else
    const parts = (id) => { const row = rowOf(id); return { strong: row.querySelectorAll("strong").length, text: row.textContent,
      rest: [...row.childNodes].filter((n) => n.nodeType === Node.TEXT_NODE && n.textContent.trim() !== "").length }; };
    APP.setLevel("district"); APP.showProfile("10");
    const p = APP.properties("district").find((x) => x.id === "10");
    const countIds = APP.data.catalog.filter((m) => m.count_of).map((m) => m.id), countTitles = APP.data.catalog.filter((m) => m.count_of).map((m) => m.title);
    const out = { counts: [...document.querySelectorAll("#tab-area [data-layer]")].filter((e) => countIds.includes(e.dataset.layer)).map((e) => e.dataset.layer)
      .concat([...document.querySelectorAll("#tab-area .row > span:first-child")].map((e) => e.textContent.trim()).filter((t) => countTitles.includes(t))) };
    out.pre = [strong("HOU_PRE1919"), APP.valueText("HOU_PRE1919", p.HOU_PRE1919, p)];
    out.post = [strong("HOU_1949_1978"), APP.valueText("HOU_1949_1978", p.HOU_1949_1978, p)];
    out.rows = ["HOU_PRE1919", "HOU_1949_1978"].map(parts);
    out.preInfo = !!rowOf("HOU_PRE1919").querySelector(".info-button");
    APP.setIndicator("SH_SHARE"); APP.setIndicator("HOU_RENTERS");
    rowOf("HOU_PRE1919").click();
    out.clicked = APP.state.indicator;
    APP.setLevel("quarter"); APP.showProfile("Bornheim");
    const q = APP.properties("quarter").find((x) => x.id === "Bornheim");
    out.sh = [strong("SH_SHARE"), APP.valueText("SH_SHARE", q.SH_SHARE, q)];
    out.shRow = parts("SH_SHARE");
    out.shInfo = !!rowOf("SH_SHARE").querySelector(".info-button");
    const t = document.getElementById("tab-area"), turnout = rowOf("ELEC_TURNOUT"), next = turnout.nextElementSibling;
    const closing = next && next.matches("p.note") && next.textContent.trim() !== "" ? next.textContent : null;
    out.after = Boolean(closing) && next === t.lastElementChild;
    out.once = [...t.querySelectorAll("p.note")].filter((e) => e.textContent === closing).length;
    out.turnout = { children: [...turnout.children].map((c) => c.tagName), value: turnout.querySelector("strong").textContent, share: APP.format(q.ELEC_TURNOUT, 1) + " %" };
    APP.setLevel("district"); APP.showProfile("10");
    return out;
  });
  check(r.pre[0] === r.pre[1], "10 5.4: Altbau row with the share only: " + JSON.stringify(r.pre));
  check(r.post[0] === r.post[1], "10 5.4: Nachkriegsbau row with the share only: " + JSON.stringify(r.post));
  check([...r.rows, r.shRow].every((x) => x.strong === 1 && x.rest === 0 && !x.text.includes(" · ")),
    "10 5.4: no count in the rows of Sozialwohnungen, Altbau, Nachkriegsbau: " + JSON.stringify([...r.rows, r.shRow]));
  check(JSON.stringify(r.turnout.children) === JSON.stringify(["SPAN", "STRONG"]) && r.turnout.value === r.turnout.share, "10 5.4: the turnout row has no count: " + JSON.stringify(r.turnout));
  check(r.counts.length === 0, "10 5.4: no row of a count of its own: " + r.counts.join(" | "));
  check(r.sh[0] === r.sh[1], "10 5.4: Sozialwohnungen row with the share only: " + JSON.stringify(r.sh));
  check(r.clicked === "HOU_PRE1919", "10 5.4: a click on the row shows the share layer: " + r.clicked);
  check(!r.preInfo && !r.shInfo, "10 5.4: rows of Altbau and Sozialwohnungen have no ⓘ of their own (their layer has it): " + JSON.stringify([r.preInfo, r.shInfo]));
  check(r.after && r.once === 1, "10 5.3: the area sentence follows the Wahl block, once: " + JSON.stringify([r.after, r.once]));
  const bezirk = await page.evaluate(() => { APP.setLevel("district"); APP.showProfile("213");
    const q = APP.quarterOf(APP.properties("district").find((x) => x.id === "213"));
    const row = document.querySelector('#tab-area .row[data-layer="SH_SHARE"]');
    return [row.querySelector("strong").textContent, APP.valueText("SH_SHARE", q.SH_SHARE, q)]; });
  check(bezirk[0] === bezirk[1], "10 5.4: Bezirk 213 shows the share of Nordend-West: " + JSON.stringify(bezirk));
  const rank = await page.evaluate(() => { APP.setLevel("quarter"); APP.showProfile("Gallus"); APP.setLevel("district"); APP.showProfile("213");
    const p = APP.properties("district").find((x) => x.id === "213");
    const row = document.querySelector('#tab-area .row[data-layer="SOC_INDEX"]');
    // the map level differs from the level of the profile: the total stays the number of Bezirke with a value
    APP.setLevel("quarter");
    return { shown: row.querySelector("strong").textContent, want: APP.rankText("SOC_INDEX", p.SOC_INDEX, "district"), rank: p.SOC_INDEX,
      total: APP.meta.SOC_INDEX.rank }; });
  // the rank text holds the rank of the area (a tie: the ranks on both sides) and the number of Bezirke
  // (docs/texts.md, Map: tooltip)
  const shownRanks = integers(rank.shown);
  const ranks = Number.isInteger(rank.rank) ? [rank.rank] : [rank.rank - 0.5, rank.rank + 0.5];
  check(rank.shown === rank.want && JSON.stringify(shownRanks) === JSON.stringify([...ranks, rank.total]) && rank.total === 114,
    "10 2.1: profile row of the index reads the rank: " + JSON.stringify([rank, shownRanks]));
});
