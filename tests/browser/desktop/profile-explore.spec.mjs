// Profile, part two: exploring an area (a click focuses it, Stadt returns to the whole city), the profile rows
// that choose the layer, and the tab Gebiet that follows the state. The note of an empty tab is the one the page holds
// (APP.PROFILE_NOTE), rows are found by their data-layer.
import { test } from "../fixtures.mjs";
import { pointIn, rowDo, sameView, settleView, view } from "../helpers/profile.mjs";

const exploreState = (page) => page.evaluate(() => {
  const w = {}, fills = {};
  APP.layers.quarter.eachLayer((l) => { w[l.feature.properties.id] = l.options.weight; fills[l.feature.properties.id] = l.options.fillColor; });
  const b = APP.map.getBounds();
  return { area: APP.state.area, mode: APP.state.mode, tab: document.querySelector("#tabs button.active")?.dataset.tab,
    h2: document.querySelector("#tab-area h2")?.textContent, zoom: APP.map.getZoom(), center: APP.map.getCenter(), weights: w, fills,
    legend: APP.legendDiv.innerHTML, breaks: JSON.stringify(APP.breaks),
    size: APP.map.getSize().x === APP.map.getContainer().clientWidth && APP.map.getSize().y === APP.map.getContainer().clientHeight,
    bounds: [b.getSouth(), b.getWest(), b.getNorth(), b.getEast()] };
});

const rowState = (page) => page.evaluate(() => {
  const s = APP.state, pressed = [...document.querySelectorAll("#tab-area [data-layer][aria-pressed=true]")].map((r) => r.dataset.layer);
  const w = {}, fills = {};
  APP.layers.quarter.eachLayer((l) => { w[l.feature.properties.id] = l.options.weight; fills[l.feature.properties.id] = l.options.fillColor; });
  return { indicator: s.indicator, level: s.level, area: s.area, mode: s.mode, pressed, weights: w, fills,
    radio: document.querySelector('#tab-city input[name=indicator]:checked')?.value, legend: document.querySelector("#legend")?.textContent || APP.legendDiv.textContent,
    h2: document.querySelector("#tab-area h2")?.textContent, zoom: APP.map.getZoom(), center: APP.map.getCenter() };
});

// 7. Explore an area: a click focuses it, Stadt returns to the whole city
test.describe("explore an area", () => {
  test("a click explores, Stadt returns to the whole city", async ({ mapPage: page, check }) => {
    await settleView(page);
    const view0 = await view(page);
    const legend0 = await page.evaluate(() => APP.legendDiv.innerHTML), breaks0 = await page.evaluate(() => JSON.stringify(APP.breaks));
    const pt0 = await pointIn(page, "quarter", "Gallus");
    check(pt0 !== null, "explore: found a point in Gallus");
    if (!pt0) return;
    await page.mouse.click(pt0.x, pt0.y);
    await settleView(page);
    const e = await exploreState(page);
    check(e.area === "Gallus", "explore: a click on Gallus sets the area: " + e.area);
    check(e.tab === "area" && e.h2 === "Gallus", `explore: tab Gebiet with the profile of Gallus: ${e.tab} ${e.h2}`);
    const inView = await page.evaluate(() => { let f; APP.layers.quarter.eachLayer((l) => { if (l.feature.properties.id === "Gallus") f = l; }); return APP.map.getBounds().contains(f.getBounds()); });
    check(inView, "explore: the map shows all of Gallus");
    check(e.zoom > view0.zoom, `explore: the map zoomed in (${view0.zoom} to ${e.zoom})`);
    check(e.weights.Gallus === 3, "explore: Gallus has a heavy outline");
    check(Object.entries(e.fills).every(([id, c]) => id === "Gallus" || c === "#e8e8e8"), "explore: every other Stadtteil is grey");
    check(e.legend === legend0 && e.breaks === breaks0, "explore: legend and classes stay those of the whole city");
    const tip = await page.evaluate(() => { let b; APP.layers.quarter.eachLayer((l) => { if (l.feature.properties.id === "Bockenheim") b = l; });
      const c = b.getBounds().getCenter(); return APP.tipHtml(c) || ""; });
    const bockenheimValue = await page.evaluate(() => { const p = APP.properties("quarter").find((x) => x.id === "Bockenheim"); return APP.valueText(APP.state.indicator, p[APP.state.indicator], p); });
    check(tip.includes("Bockenheim") && tip.includes(bockenheimValue), "explore: hover still shows a grey area: " + tip);
    await page.mouse.click(pt0.x, pt0.y);
    await settleView(page);
    check((await exploreState(page)).area === "Gallus", "explore: a click on the explored area does nothing");
    const ptB = await pointIn(page, "quarter", "Bockenheim");
    check(ptB !== null, "explore: found a point in Bockenheim");
    if (ptB) {
      await page.mouse.click(ptB.x, ptB.y);
      await settleView(page);
      const e2 = await exploreState(page);
      check(e2.area === "Bockenheim" && e2.h2 === "Bockenheim", `explore: a click on Bockenheim moves the focus: ${e2.area} ${e2.h2}`);
    }
    await page.evaluate(() => APP.openTab("help"));
    check((await exploreState(page)).area === "Bockenheim", "explore: Hilfe keeps exploring");
    await page.evaluate(() => { APP.openView("history"); APP.openView("map"); });
    await settleView(page);
    const e3 = await exploreState(page);
    check(e3.area === "Bockenheim" && e3.size && e3.weights.Bockenheim === 3, "explore: the round trip through Trend keeps the focus and the map size");
    await page.evaluate(() => APP.openTab("city"));
    await settleView(page);
    const e4 = await exploreState(page);
    check(e4.area === null, "explore: Stadt ends the exploring");
    check(sameView(e4, view0), "explore: Stadt restores the view of before");
    check(Object.values(e4.fills).every((c) => c !== "#e8e8e8"), "explore: no Stadtteil stays grey");
    await page.evaluate(() => APP.openTab("area"));
    await settleView(page);
    check((await exploreState(page)).area === "Bockenheim", "explore: the tab Gebiet explores the last profile again");
  });

  test("Gebiet without a profile and areaFor", async ({ mapPage: page, check }) => {
    await page.evaluate(() => APP.openTab("area"));
    const fresh = await page.evaluate(() => ({ area: APP.state.area, note: document.getElementById("tab-area").innerHTML === APP.PROFILE_NOTE }));
    check(fresh.area === null && fresh.note, "explore: Gebiet without a profile shows the note: " + JSON.stringify(fresh));
    const mapping = await page.evaluate(() => [APP.areaFor("213", "district", "quarter"), APP.areaFor("Gallus", "quarter", "district"), APP.areaFor("Gallus", "quarter", "quarter")]);
    check(JSON.stringify(mapping) === JSON.stringify(["Nordend-West", null, "Gallus"]), "explore: areaFor maps the level: " + JSON.stringify(mapping));
    // no area of the new level fits: the tab shows the note, not a stale profile
    await page.evaluate(() => { APP.explore("Gallus"); APP.openTab("city"); APP.setLevel("district"); APP.openTab("area"); });
    const stale = await page.evaluate(() => ({ area: APP.state.area, profile: APP.profileId(), note: document.getElementById("tab-area").innerHTML === APP.PROFILE_NOTE, rows: document.querySelectorAll("#tab-area [data-layer]").length }));
    check(stale.area === null && stale.profile === null && stale.rows === 0 && stale.note, "explore: no area fits the level, the tab shows the note: " + JSON.stringify(stale));
  });

  test("explore in the candidates", async ({ mapPage: page, check }) => {
    await page.evaluate(() => { APP.openTab("city"); APP.setLevel("quarter"); });
    await page.evaluate(() => { APP.openTab("candidates"); APP.setTemplate("coop"); });
    await settleView(page);
    const pt0 = await pointIn(page, "quarter", "Gallus");
    check(pt0 !== null, "explore, candidates: found a point in Gallus");
    if (!pt0) return;
    await page.mouse.click(pt0.x, pt0.y);
    await settleView(page);
    const c = await page.evaluate(() => {
      let own, other; const base = { weight: 0.8, color: "#555", opacity: 1, fillOpacity: 0.75, dashArray: null };
      APP.layers.quarter.eachLayer((l) => { if (l.feature.properties.id === "Gallus") own = [l.options.fillColor, APP.styleCandidates(l.feature.properties, base).fillColor];
        else other = other || l.options.fillColor; });
      return { mode: APP.state.mode, area: APP.state.area, own, other };
    });
    check(c.mode === "candidates" && c.area === "Gallus" && c.own[0] === c.own[1] && c.other === "#e8e8e8", "explore, candidates: Gallus keeps its candidate colour: " + JSON.stringify(c));
    const hit = await page.evaluate(() => ({ hit: APP.data.hit_border, kept: APP.styleExplore({ id: APP.state.area }, { color: APP.data.hit_border, weight: 3.5 }), plain: APP.styleExplore({ id: APP.state.area }, { color: "#555", weight: 0.8 }) }));
    check(hit.kept.color === hit.hit && hit.kept.weight >= 3.5 && hit.plain.color === "#000000" && hit.plain.weight === 3, "explore, candidates: the explored area keeps the border of a full hit: " + JSON.stringify(hit));
    await page.evaluate(() => APP.openTab("candidates"));
    await settleView(page);
    const c2 = await page.evaluate(() => { const f = []; APP.layers.quarter.eachLayer((l) => f.push(l.options.fillColor)); return { area: APP.state.area, grey: f.includes("#e8e8e8") }; });
    check(c2.area === null && !c2.grey, "explore, candidates: the candidates tab ends the exploring: " + JSON.stringify(c2));
  });
});

// 8. Profile rows choose the layer, the level follows
test.describe("profile rows choose the layer", () => {
  test("a row chooses the layer, by click and by key", async ({ mapPage: page, check }) => {
    await settleView(page);
    const v0 = await view(page);
    await page.evaluate(() => { APP.setState({ level: "quarter", indicator: "OWN_PUBLIC" }); APP.explore("Gallus"); });
    await settleView(page);
    const a = await page.evaluate(() => ({
      pressed: document.querySelector('tr[data-layer="OWN_PUBLIC"]')?.getAttribute("aria-pressed"),
      none: !document.querySelector('[data-layer="OWN_NONPROFIT"]') && !document.querySelector('[data-layer="SH_COUNT"]'),
      bad: [...document.querySelectorAll("#tab-area [data-layer]")].filter((r) => APP.meta[r.dataset.layer]?.layer !== true).map((r) => r.dataset.layer),
      attrs: [...document.querySelectorAll("#tab-area [data-layer]")].every((r) => r.getAttribute("role") === "button" && r.getAttribute("tabindex") === "0"),
      count: document.querySelectorAll("#tab-area [data-layer]").length }));
    check(a.pressed === "true", "rows: the table row of the active layer is pressed: " + JSON.stringify(a));
    check(a.none, "rows: rows without a layer carry no data-layer");
    check(a.bad.length === 0 && a.attrs && a.count > 5, "rows: every data-layer id is a layer, with role and tabindex: " + JSON.stringify(a));
    await rowDo(page, "OWN_COOP", "click");
    await settleView(page);
    const b = await rowState(page);
    check(b.indicator === "OWN_COOP" && b.level === "quarter" && b.area === "Gallus" && b.mode === "layer", "rows: a table row chooses the layer: " + JSON.stringify([b.indicator, b.level, b.area]));
    check(b.pressed.length === 1 && b.pressed[0] === "OWN_COOP", "rows: only the chosen row is pressed: " + JSON.stringify(b.pressed));
    check(b.radio === "OWN_COOP", "rows: the radio in Stadt follows: " + b.radio);
    check(b.weights.Gallus === 3 && b.fills.Bockenheim === "#e8e8e8", "rows: Gallus stays focused after the row click");
    const coop = await page.evaluate(() => APP.meta.OWN_COOP.title);
    check((b.legend || "").includes(coop), "rows: the legend names the layer: " + JSON.stringify([coop, b.legend]));
    await rowDo(page, "HOU_RENTERS", "focus");
    await page.keyboard.press("Enter");
    check((await rowState(page)).indicator === "HOU_RENTERS", "rows: Enter on a focused row chooses the layer");
    await rowDo(page, "OWN_COOP", "focus");
    await page.keyboard.press("Space");
    check((await rowState(page)).indicator === "OWN_COOP", "rows: Space on a focused row chooses the layer");
    await page.evaluate(() => APP.openTab("city"));
    await settleView(page);
    const c = await rowState(page);
    check(c.indicator === "OWN_COOP" && c.area === null, "rows: Stadt keeps the chosen layer: " + c.indicator);
    check(sameView(c, v0), "rows: Stadt restores the view of before");
  });

  test("the pressed row", async ({ mapPage: page, check }) => {
    // the pressed row (docs/design.md, Profile and pressed row): its mark lies in the edge of the tab, its bar has the map colour
    const pressedRow = () => page.evaluate(() => {
      const rgb = (c) => { const d = document.createElement("i"); d.style.color = c; document.body.append(d); const v = getComputedStyle(d).color; d.remove(); return v; };
      const r = document.querySelector("#tab-area [data-layer].active");
      const title = r.querySelector("td, span"), h3 = document.querySelector("#tab-area h3");
      const range = document.createRange();
      range.selectNodeContents(title);
      const fill = r.querySelector(".bar span");
      // the colour the map draws: the explored area keeps its class colour
      let drawn;
      APP.layers[APP.state.level].eachLayer((l) => { if (l.feature.properties.id === APP.profileId()) drawn = l.options.fillColor; });
      const css = fill && getComputedStyle(fill);
      return { id: r.dataset.layer, gap: range.getBoundingClientRect().left - r.getBoundingClientRect().left,
        aligned: Math.abs(range.getBoundingClientRect().left - h3.getBoundingClientRect().left) < 1,
        bold: Number(getComputedStyle(title).fontWeight) >= 700,
        fill: css?.backgroundColor, border: css?.boxShadow, map: drawn && rgb(drawn),
        accent: rgb(getComputedStyle(document.documentElement).getPropertyValue("--bar-plain").trim()),
        others: [...document.querySelectorAll("#tab-area .row[data-layer]:not(.active):not([data-layer^=ELEC_]) .bar span")].map((s) => getComputedStyle(s).backgroundColor) };
    });
    await page.evaluate(() => { APP.setState({ level: "quarter", indicator: "OWN_PUBLIC", mode: "layer" }); APP.explore("Gallus"); });
    await settleView(page);
    const t = await pressedRow();
    check(t.id === "OWN_PUBLIC" && t.gap >= 10 && t.aligned, "pressed row: the title of a table row starts in line with the headings: " + JSON.stringify(t));
    await rowDo(page, "SOC_UNEMPLOYED", "click");
    await settleView(page);
    const g = await pressedRow();
    check(g.id === "SOC_UNEMPLOYED" && g.gap >= 10 && g.aligned && g.bold, "pressed row: the mark does not cover the title: " + JSON.stringify(g));
    check(g.fill === g.map && g.fill !== g.accent, "pressed row: the bar has the colour of Gallus on the map: " + JSON.stringify([g.fill, g.map]));
    check(/inset/.test(g.border || ""), "pressed row: the bar has a thin border: " + g.border);
    check(g.others.length > 3 && g.others.every((c) => c === g.accent), "pressed row: the other bars stay plain grey: " + JSON.stringify(g.others));
    // the colour follows the layer: the classes of the layer before do not count
    await rowDo(page, "SOC_MIN_INCOME", "click");
    await settleView(page);
    const m = await pressedRow();
    check(m.id === "SOC_MIN_INCOME" && m.fill === m.map, "pressed row: the bar takes the class of the new layer: " + JSON.stringify([m.fill, m.map]));
    await rowDo(page, "ELEC_SPD", "click");
    await settleView(page);
    const e = await page.evaluate(() => [...document.querySelectorAll("#tab-area .row[data-layer^=ELEC_]")].filter((r) => r.querySelector(".bar span"))
      .map((r) => ({ id: r.dataset.layer, fill: getComputedStyle(r.querySelector(".bar span")).backgroundColor })));
    const spd = await pressedRow();
    check(spd.id === "ELEC_SPD" && spd.fill === spd.map, "pressed row: the SPD bar has the colour of Gallus on the map: " + JSON.stringify([spd.fill, spd.map]));
    check(new Set(e.filter((x) => x.id !== "ELEC_SPD").map((x) => x.fill)).size > 2 && !e.some((x) => x.id !== "ELEC_SPD" && x.fill === spd.accent),
      "pressed row: the other party bars keep their colours: " + JSON.stringify(e));
    // a small Bezirk is grey on the map: its bar keeps the plain grey. The build has none today, so one Bezirk is made small here.
    const small = await page.evaluate(() => { const p = APP.properties("district").find((x) => x.HOU_RENTERS != null); p.small = 1; return p.id; });
    await page.evaluate((id) => { APP.openTab("city"); APP.setState({ level: "district", indicator: "HOU_RENTERS", mode: "layer" }); APP.explore(id); }, small);
    await settleView(page);
    const s = await pressedRow();
    await page.evaluate((id) => { APP.properties("district").find((x) => x.id === id).small = 0; }, small);
    check(s.id === "HOU_RENTERS" && s.fill === s.accent, "pressed row: a small Bezirk keeps the plain bar: " + JSON.stringify([small, s.fill]));
    // keyboard focus: a solid outline inside the row
    await rowDo(page, "HOU_RENTERS", "focus");
    const f = await page.evaluate(() => { const c = getComputedStyle(document.activeElement); return { style: c.outlineStyle, width: c.outlineWidth, offset: c.outlineOffset }; });
    check(f.style === "solid" && f.width === "2px" && parseFloat(f.offset) < 0, "pressed row: a focused row shows an outline inside: " + JSON.stringify(f));
  });

  test("rows on a district", async ({ mapPage: page, check }) => {
    // a district: a row of its own level keeps the level, a Stadtteil-only row goes to the Stadtteil
    await page.evaluate(() => { APP.setState({ level: "district", indicator: "HOU_RENTERS", mode: "layer" }); APP.explore("213"); });
    await settleView(page);
    await rowDo(page, "HOU_RENTERS", "click");
    await settleView(page);
    const d = await rowState(page);
    check(d.level === "district" && d.area === "213", "rows, district: a row of the level keeps level and area: " + JSON.stringify([d.level, d.area]));
    await rowDo(page, "OWN_PUBLIC", "click");
    await settleView(page);
    const e = await rowState(page);
    check(e.level === "quarter" && e.area === "Nordend-West" && e.h2 === "Nordend-West", "rows, district: a Stadtteil-only row switches to the Stadtteil profile: " + JSON.stringify([e.level, e.area, e.h2]));
    check(e.weights["Nordend-West"] === 3, "rows, district: the Stadtteil is focused on the map");
    const inView = await page.evaluate(() => { let f; APP.layers.quarter.eachLayer((l) => { if (l.feature.properties.id === "Nordend-West") f = l; }); return APP.map.getBounds().contains(f.getBounds()); });
    check(inView, "rows, district: the map shows the Stadtteil");
    await page.evaluate(() => { APP.openTab("city"); APP.setState({ level: "district", indicator: "HOU_RENTERS", mode: "layer" }); APP.explore("213"); });
    await settleView(page);
    await rowDo(page, "OWN_PUBLIC", "focus");
    const rowId = await page.evaluate(() => document.activeElement.dataset.layer);
    await page.keyboard.press("Enter");
    await settleView(page);
    const kept = await page.evaluate(() => ({ id: document.activeElement?.dataset?.layer, inTab: !!document.activeElement?.closest("#tab-area") }));
    check(rowId && kept.id === rowId && kept.inTab, "rows, district: the keyboard focus stays on the row after the level switch: " + JSON.stringify([rowId, kept]));
    await page.evaluate(() => APP.openTab("city"));
    await settleView(page);
    await page.evaluate(() => { APP.setState({ level: "district", indicator: "HOU_RENTERS", mode: "layer" }); APP.explore("213"); });
    await settleView(page);
    await rowDo(page, "ELEC_SPD", "click");
    await settleView(page);
    const f = await rowState(page);
    check(f.indicator === "ELEC_SPD" && f.level === "quarter", "rows, district: an election row goes to the Stadtteil: " + JSON.stringify([f.indicator, f.level]));
  });

  test("rows in the candidates on districts", async ({ mapPage: page, check }) => {
    // candidates on districts: a row leads back to the layer and keeps the explored level
    await page.evaluate(() => { APP.openTab("candidates"); APP.setTemplate("social_preservation"); });
    await settleView(page);
    const pt = await pointIn(page, "district", "213");
    check(pt !== null, "rows, candidates: found a point in district 213");
    if (!pt) return;
    await page.mouse.click(pt.x, pt.y);
    await settleView(page);
    await rowDo(page, "HOU_RENTERS", "click");
    await settleView(page);
    const g = await rowState(page);
    check(g.mode === "layer" && g.level === "district" && g.area === "213", "rows, candidates: a row switches to the layer and keeps the level: " + JSON.stringify([g.mode, g.level, g.area]));
  });
});

// 9. Profile follows the state: the tab Gebiet never shows a stale profile
test.describe("the tab Gebiet follows the state", () => {
  const tabMatches = (page) => page.evaluate(() => {
    const s = APP.state, tab = document.getElementById("tab-area");
    const shown = APP.profileId();
    if (s.area !== null && shown !== s.area) return false;
    if (shown === null) return tab.innerHTML === APP.PROFILE_NOTE;
    const p = APP.properties(s.level).find((x) => x.id === shown);
    return Boolean(p) && tab.querySelector("h2")?.textContent === p.name;
  });

  test("steps of the state", async ({ mapPage: page, check }) => {
    const steps = [
      ["showProfile Gallus", () => APP.showProfile("Gallus", false)],
      ["setLevel district", () => APP.setLevel("district")],
      ["openTab area", () => APP.openTab("area")],
      ["district, showProfile 213", () => { APP.setLevel("district"); APP.showProfile("213", false); }],
      ["openTab area explores 213", () => APP.openTab("area")],
      ["chooseLayer OWN_PUBLIC", () => APP.chooseLayer("OWN_PUBLIC")],
      ["openTab city", () => APP.openTab("city")],
      ["setLevel district", () => APP.setLevel("district")],
      ["candidates coop", () => { APP.openTab("candidates"); APP.setTemplate("coop"); }],
      ["candidates social_preservation", () => { APP.openTab("candidates"); APP.setTemplate("social_preservation"); }],
      ["openTab city again", () => APP.openTab("city")],
    ];
    for (const [label, fn] of steps) {
      await page.evaluate(fn);
      await settleView(page);
      check(await tabMatches(page), "profile follows the state after: " + label + " " + JSON.stringify(await page.evaluate(() => [APP.state.level, APP.state.area, APP.state.profile])));
    }
    const gone = await page.evaluate(() => { APP.openTab("city"); APP.setLevel("quarter"); APP.showProfile("Gallus", false); APP.setLevel("district");
      return { shown: APP.profileId(), kept: APP.state.profile, note: document.getElementById("tab-area").innerHTML === APP.PROFILE_NOTE }; });
    check(gone.shown === null && gone.kept?.id === "Gallus" && gone.note, "profile follows the state: a level without a match shows the note and keeps the choice: " + JSON.stringify(gone));
  });

  // round trips through a level without a match: the tab Gebiet shows the last area again
  const trips = [
    ["explore Gallus, Kandidaten, Stadt", "Gallus", () => { APP.openTab("city"); APP.setLevel("quarter"); APP.explore("Gallus"); APP.openTab("candidates"); APP.openTab("city"); APP.openTab("area"); }],
    ["explore 213, coop, Stadt", "213", () => { APP.openTab("city"); APP.setLevel("district"); APP.explore("213"); APP.openTab("candidates"); APP.setTemplate("coop"); APP.openTab("city"); APP.setLevel("district"); APP.openTab("area"); }],
    ["touch tap Gallus, Kandidaten, Stadt", "Gallus", () => { APP.openTab("city"); APP.setLevel("quarter"); APP.showProfile("Gallus", false); APP.openTab("candidates"); APP.openTab("city"); APP.setLevel("quarter"); APP.openTab("area"); }],
  ];
  for (const [label, id, fn] of trips) {
    test(`round trip: ${label}`, async ({ mapPage: page, check }) => {
      await page.evaluate(() => { APP.openTab("city"); APP.setLevel("quarter"); APP.setState({ profile: null }, false); });
      await page.evaluate(fn);
      await settleView(page);
      const r = await page.evaluate(() => ({ area: APP.state.area, shown: APP.profileId(), h2: document.querySelector("#tab-area h2")?.textContent }));
      check(r.area === id, "profile round trip, " + label + ": " + JSON.stringify(r));
      check(await tabMatches(page), "profile round trip tab matches, " + label);
    });
  }
});
