// Phone layout (docs/design.md, Phone and tablet; Phone panel): the panel at the bottom of the map, the legend, the
// gestures, the tooltip on a tap, exploring an area, the views Trend, Neubau and Miete, the footer and the profile.
// Runs in the phone projects: webkit-iphone, webkit-iphone-se, chrome-390.
import { devices } from "@playwright/test";
import { test } from "../fixtures.mjs";
import { noOverflow, rect, settle } from "../helpers/common.mjs";
import { checkConstruction, checkRentBurden, checkTrend } from "../helpers/charts.mjs";
import { common, legendCollapsed, noteUnderTitle, viewButtons } from "../helpers/layout.mjs";
import { arrow, arrowLabel, drag, isClosed, isOpen, panel, realDrag, tab, tap, touchSeq } from "../helpers/touch.mjs";
import { drawnNc, drawnRentBurden, historyDrawnAt } from "../helpers/views.mjs";

const toggle = "#panel-toggle";
const LANDSCAPE = devices["iPhone 15 landscape"].viewport;
const activeTab = (page) => page.evaluate(() => document.querySelector('#tabs button[aria-pressed="true"]')?.dataset.tab);
// visible height of the panel when it is fully open: 60 % of main
const fullPanel = async (page) => (await page.evaluate(() => document.querySelector("main").getBoundingClientRect().height)) * 0.6;
// the start of the panel checks: the layer of private companies (OWN_COMPANY) on Stadtbezirke
const districtCompanies = (page) => page.evaluate(() => { APP.setLevel("quarter"); APP.setIndicator("OWN_COMPANY"); APP.setLevel("district"); });
// the start of the gestures: the panel closed, the tab Hilfe active
const closedOnHelp = async (page) => { await tap(page, tab("help")); await tap(page, toggle); };

// A point of the map in the strip from top to bottom (container px) where the finger hits an area, not a control or
// the tooltip; never the area of the last hit (window.lastArea). With `id`: a point of that area (lastArea is left
// alone). The point lies on whole px of the page (px, py): WebKit rounds the point of a tap to whole px, and the
// first hit of the scan lies at the edge of an area. x, y: the same point in container px.
const areaAt = (page, top, bottom, id = null) => page.evaluate(([top, bottom, id]) => {
  const m = APP.map, box = m.getContainer().getBoundingClientRect();
  for (let y = top + 30; y < bottom - 30; y += 10) for (let x = 40; x < m.getSize().x - 40; x += 10) {
    const px = Math.round(box.left + x), py = Math.round(box.top + y), cx = px - box.left, cy = py - box.top;
    // only points where the finger hits the map, not the legend, the zoom buttons or the tooltip
    if (document.elementFromPoint(px, py).closest(".leaflet-control, .leaflet-tooltip")) continue;
    const p = APP.areaAt(m.containerPointToLatLng([cx, cy]));
    if (!p) continue;
    if (id ? p.id === id : !window.lastArea || p.id !== window.lastArea) {
      if (!id) window.lastArea = p.id;
      return { x: cx, y: cy, px, py, id: p.id, name: p.name };
    }
  }
  return null;
}, [top, bottom, id]);
// the map tooltip: its text without the button, the button apart (height of its target), its box
const tip = (page) => page.evaluate(() => { const e = APP.map.hasLayer(APP.tip) && APP.tip.getElement(); if (!e) return null;
  const b = e.getBoundingClientRect(); const btn = e.querySelector(".tip-explore");
  return { text: e.textContent.replace(btn ? btn.textContent : "", ""), button: btn ? btn.textContent : null, explore: btn ? btn.dataset.explore : null, buttonHeight: btn ? btn.getBoundingClientRect().height : 0, width: b.width, height: b.height, top: b.top, bottom: b.bottom, left: b.left, right: b.right }; });
// the box of an area in container px, and whether it lies inside the map above `top`
const areaFits = (page, id, top) => page.evaluate(([id, top]) => {
  let layer; APP.layers[APP.state.level].eachLayer((l) => { if (l.feature.properties.id === id) layer = l; });
  const b = layer.getBounds(), nw = APP.map.latLngToContainerPoint(b.getNorthWest()), se = APP.map.latLngToContainerPoint(b.getSouthEast());
  return { nw: [nw.x, nw.y], se: [se.x, se.y], top, ok: nw.x >= -1 && nw.y >= -1 && se.x <= APP.map.getSize().x + 1 && se.y <= top + 1 };
}, [id, top]);

test("start: layout, closed panel, Frankfurt above the tab bar", async ({ mapPage: page, check, saveScreenshot }) => {
  await common({ page, check });
  const height = await page.evaluate(() => window.innerHeight);
  const map = await rect(page, "#map");
  const header = await rect(page, "#header");
  check(header.height <= 90, `compact header (${header.height} px)`);
  check(map.width >= (await page.evaluate(() => window.innerWidth)) - 1, "map uses the full width");
  check(map.height >= 0.6 * height, `map at least 60 % of the window high (${map.height} of ${height})`);
  // start: panel closed, only the tab bar, Frankfurt fits above it
  const tabs = await rect(page, "#tabs"), side = await panel(page);
  check(tabs.visible && tabs.bottom <= map.bottom + 1 && tabs.top >= map.top, "tab bar at the bottom of the map");
  check(side.height <= tabs.height + 3, "start: panel closed");
  check(await page.evaluate(() => [...document.querySelectorAll("#sidebar .tab")].every((t) => t.inert)), "start: tab content is inert");
  check(await page.evaluate((top) => { const b = APP.layers.district.getBounds(), m = APP.map;
    const nw = m.latLngToContainerPoint(b.getNorthWest()), se = m.latLngToContainerPoint(b.getSouthEast());
    return nw.y >= -2 && nw.x >= -2 && se.x <= m.getSize().x + 2 && se.y <= top + 2; }, tabs.top - map.top), "start: Frankfurt fits above the tab bar");
  await saveScreenshot("start");
});

test("legend: collapsed at the start, a tap opens and closes it", async ({ mapPage: page, check, saveScreenshot }) => {
  // the legend starts collapsed, a tap opens and closes it; it stays above the panel
  // docs/design.md, Legend: the note stays under the title, so a collapsed legend is title plus note
  const map = await rect(page, "#map"), tabs = await rect(page, "#tabs");
  let legend = await rect(page, ".legend");
  check(await legendCollapsed(page), `legend collapsed at the start (${legend.height} px)`);
  check(await noteUnderTitle(page, await page.evaluate(() => APP.meta[APP.state.indicator].legend_note)), "collapsed legend shows its note under the title");
  check(legend.bottom <= tabs.top + 1, "collapsed legend above the tab bar");
  await tap(page, ".legend");
  legend = await rect(page, ".legend");
  check(legend.height > 100, "tap opens the legend");
  check(legend.bottom <= tabs.top + 1 && legend.top >= map.top, "open legend between header and tab bar");
  await saveScreenshot("legend");
  await tap(page, ".legend");
  check(await legendCollapsed(page), "second tap closes the legend");
});

test("legend: the overlay key stays in the body, the grid key wraps", async ({ mapPage: page, check }) => {
  // 10 1.8: the overlay key lies in the body; the collapsed legend stays collapsed with an overlay on
  await page.evaluate(() => { APP.overlays.social_preservation.on = true; APP.updateOverlays(); });
  check(await page.evaluate(() => APP.legendDiv.querySelector(".legend-body > .legend-overlays .key-row") !== null) && await legendCollapsed(page),
    "collapsed legend keeps the overlay key in its body");
  // the grid key wraps: with all overlays and the grid on at zoom 15 the open legend does not scroll sideways
  await page.evaluate(() => { for (const u of Object.values(APP.overlays)) u.on = true; APP.map.setView(APP.map.getCenter(), 15, { animate: false }); APP.updateOverlays(); });
  await settle(page);
  await tap(page, ".legend");
  const lg = await page.evaluate(() => { const e = document.querySelector(".legend"), r = e.getBoundingClientRect(), m = document.getElementById("map").getBoundingClientRect();
    return { sw: e.scrollWidth, cw: e.clientWidth, inside: r.left >= m.left - 1 && r.right <= m.right + 1 }; });
  check(lg.sw <= lg.cw && lg.inside, "phone: open legend with all overlays and the grid does not overflow sideways: " + JSON.stringify(lg));
});

test("legend: every layer has its note under the title, collapsed within the limit", async ({ mapPage: page, check }) => {
  // every layer once: its note stands under the title and the collapsed legend stays within the limit (the longest
  // notes: HOU_RENTERS)
  for (const id of await page.evaluate(() => APP.data.catalog.filter((m) => m.layer).map((m) => m.id))) {
    await page.evaluate((i) => APP.setIndicator(i), id);
    const note = await page.evaluate((i) => APP.meta[i].legend_note, id);
    check(await page.evaluate((i) => APP.state.indicator === i, id) && note.length > 0 && await noteUnderTitle(page, note) && await legendCollapsed(page),
      `layer ${id}: note under the title, collapsed legend within the limit (${(await rect(page, ".legend")).height} px)`);
  }
});

test("the arrow opens and closes the panel", async ({ mapPage: page, check, saveScreenshot }) => {
  await page.evaluate(() => { APP.setLevel("district"); });
  const map = await rect(page, "#map"), tabs = await rect(page, "#tabs");
  // the arrow opens and closes the panel; ▲ when closed, ▼ when open
  const t = await rect(page, toggle);
  check(t && t.visible && t.width >= 40 && t.height >= 32 && t.top >= tabs.top - 1 && t.bottom <= tabs.bottom + 1, "arrow in the tab bar, at least 40 × 32 px");
  check(await arrow(page) === "▲ false", `closed: arrow ▲ (${await arrow(page)})`);
  // the label of the arrow says what a tap does: a label of its own when closed and when open
  const closedLabel = await arrowLabel(page);
  check(!!closedLabel && closedLabel !== "pressed", `closed: label of the arrow (${closedLabel})`);
  await tap(page, toggle);
  const side = await panel(page);
  check(await arrow(page) === "▼ true", `open: arrow ▼ (${await arrow(page)})`);
  const openLabel = await arrowLabel(page);
  check(!!openLabel && openLabel !== "pressed" && openLabel !== closedLabel, `open: label of the arrow (${openLabel})`);
  check(side.height > 150 && side.height <= 0.6 * map.height + 1, `open panel at most 60 % of the map (${side.height} of ${map.height})`);
  check(side.bottom <= map.bottom + 1, "panel ends at the bottom of the map");
  check(await page.evaluate(() => document.getElementById("tab-city").offsetHeight > 0), "arrow opens the active tab");
  const legend = await rect(page, ".legend");
  check(legend.bottom <= side.top + 1, "legend moves above the open panel");
  // 10 5.1: the switch line above the legend, not under the panel
  await districtCompanies(page);
  await settle(page);
  {
    const sw = await rect(page, ".legend-switch"), lg = await rect(page, ".legend"), pn = await panel(page);
    check(sw && sw.visible && sw.top >= map.top && sw.bottom <= lg.top + 1, "phone: switch line visible above the legend: " + JSON.stringify([sw, lg]));
    await tap(page, ".legend");
    const open = await rect(page, ".legend"), sw2 = await rect(page, ".legend-switch");
    check(open.bottom <= pn.top + 1 && sw2.top >= map.top, "phone: open legend and switch line stay above the open panel: " + JSON.stringify([open, sw2, pn.top]));
    await tap(page, ".legend");
  }
  check(await noOverflow(page), "open panel: no horizontal scrolling");
  // the written sum of the ⓘ stays inside the panel
  await page.evaluate(() => { APP.openTab("city"); document.querySelector('.info-button[data-info="OWN_PERSON"]').click(); });
  check(await page.evaluate(() => { const i = document.getElementById("info-OWN_PERSON"); i.querySelector(".sum")?.scrollIntoView({ block: "center" }); return !i.hidden && !!i.querySelector(".sum") && i.scrollWidth <= i.clientWidth; }), "phone: ⓘ with the sum has no horizontal scrolling");
  await saveScreenshot("sum");
  await page.evaluate(() => document.querySelector('.info-button[data-info="OWN_PERSON"]').click());
  await saveScreenshot("city");
  await tap(page, toggle);
  check((await panel(page)).height <= tabs.height + 3 && await arrow(page) === "▲ false", "arrow closes the panel");
});

test("a tab opens the closed panel, a second tap keeps it open", async ({ mapPage: page, check }) => {
  const closedLabel = await arrowLabel(page);
  // a tab switches the content and opens a closed panel; a second tap keeps it open
  await tap(page, tab("help"));
  check(await page.evaluate(() => document.getElementById("tab-help").offsetHeight > 0 && document.getElementById("tab-city").offsetHeight === 0),
    "tap on a tab opens the closed panel with that tab");
  check(await page.evaluate(() => document.querySelector("#tab-help .phone-only").offsetHeight > 0), "help: the Handy paragraph shows on the phone");
  await tap(page, tab("help"));
  check((await panel(page)).height > 150, "second tap on the active tab keeps the panel open");
  await tap(page, toggle);
  check(await activeTab(page) === "help", "closed panel keeps the active tab");
  check(closedLabel !== "pressed" && await arrowLabel(page) === closedLabel, "after tab taps: the arrow is no pressed button");
});

test("swipes open and close the panel", async ({ mapPage: page, check }) => {
  // swiping (docs/design.md, Phone panel): the panel is closed here, its tab is "help"
  await closedOnHelp(page);
  const tabs = await rect(page, "#tabs");
  const full = await fullPanel(page);
  let mid = (await drag(page, "#tabs", -20, 400)).mid;
  await settle(page);
  check(mid > tabs.height + 10 && await isClosed(page), `slow short drag up: panel follows (${mid}) and snaps back closed`);
  // slow drags decide by the position: more than half open opens
  const far = Math.round(full * 0.7);
  mid = (await drag(page, "#tabs", -far, 1500)).mid;
  await settle(page);
  check(Math.abs(mid - (tabs.height + far)) <= 12, `panel follows the finger (${mid} vs ${tabs.height + far})`);
  check(await isOpen(page), "slow long drag up on the head opens the panel");
  check(Math.abs((await panel(page)).height - full) <= 2, "opened by swipe: fully open");
  await drag(page, "#tab-help", far, 1500);
  await settle(page);
  check(await isClosed(page), "drag down in the content at its top closes the panel");
  check(await page.evaluate(() => [...document.querySelectorAll("#sidebar .tab")].every((t) => t.inert)), "closed by swipe: content inert");
  // a flick of 80 px in 60 ms: 1.33 px per ms nominal, about 1.07 with the 7 to 8 ms that a timer step of 6 ms takes,
  // twice the threshold of 0.5; 80 px is less than half the way on every phone (iPhone SE: 118 px), so only the speed
  // opens. (40 px in 60 ms measured 0.48 to 0.61 under load, and a busy machine let the panel stay closed.)
  await drag(page, "#tabs", -80, 60);
  await settle(page);
  check(await isOpen(page), "fast short flick up opens the panel");
  check(await page.evaluate(() => !document.getElementById("tab-help").inert), "open: content not inert");
  // a fast start, then a pause: the position decides, not the old speed (60 px down is less than half)
  await drag(page, "#tabs", 60, 60, 0, 800);
  await settle(page);
  check(await isOpen(page), "flick, pause, release: the position decides");
  await page.evaluate(() => { document.getElementById("tab-help").scrollTop = 200; });
  await drag(page, "#tab-help", 150, 300);
  await settle(page);
  check(await isOpen(page), "content scrolled down: drag down does not close");
  await page.evaluate(() => { document.getElementById("tab-help").scrollTop = 0; });
  // the same flick down from the open panel: 80 px is less than half, so only the speed closes
  await drag(page, "#tabs", 80, 60);
  await settle(page);
  check(await isClosed(page), "fast flick down on the head closes the panel");
  mid = (await drag(page, "#tabs", -40, 300, 150)).mid;
  await settle(page);
  check(mid <= tabs.height + 3 && await isClosed(page), `horizontal drag on the head does nothing (${mid})`);
  // a second finger ends the drag: the panel snaps, and the arrow works again
  await touchSeq(page, "#tabs", [["touchstart", 0, 1, 0], ["touchmove", -50, 1, 20], ["touchmove", -100, 1, 20], ["touchstart", -100, 2, 20], ["touchend", -100, 0, 20]]);
  await settle(page);
  const stuck = () => page.evaluate(() => APP.sidebar.style.transform !== "" || APP.sidebar.classList.contains("dragging"));
  check(!(await stuck()) && (await isOpen(page) || await isClosed(page)), "second finger: the panel snaps");
  const wasOpen = await isOpen(page);
  await tap(page, toggle);
  check(wasOpen ? await isClosed(page) : await isOpen(page), "second finger: the arrow still moves the panel");
  if (wasOpen) await tap(page, toggle);
  // a cancelled drag snaps as well
  await touchSeq(page, "#tabs", [["touchstart", 0, 1, 0], ["touchmove", -50, 1, 20], ["touchmove", -far, 1, 20], ["touchcancel", -far, 0, 20]]);
  await settle(page);
  check(!(await stuck()) && (await isOpen(page) || await isClosed(page)), "touchcancel: the panel snaps");
  if (await isOpen(page)) await tap(page, toggle);
  // a drag that starts while the panel slides takes it from where it is
  const slide = await touchSeq(page, "#tabs", [["arrow", 0, 0, 0], ["touchstart", 0, 1, 60], ["touchmove", 10, 1, 0], ["touchmove", 12, 1, 10]]);
  check(Math.abs(slide[3] - (slide[1] - 12)) <= 25, `drag during the slide: no jump (${slide.map(Math.round)})`);
  await touchSeq(page, "#tabs", [["touchend", 12, 0, 0]]);
  await settle(page);
});

test("real touch: a drag from a tab moves the panel, a drag in the content scrolls it", async ({ mapPage: page, check, browserName }) => {
  // the DevTools protocol exists only in Chrome
  test.skip(browserName !== "chromium", "realDrag needs the DevTools protocol (Chrome only)");
  await closedOnHelp(page);
  const far = Math.round((await fullPanel(page)) * 0.7);
  // real touch input: a drag that starts on a tab moves the panel and does not switch the tab
  const k = await rect(page, tab("candidates"));
  // clearly a flick: 200 px in 150 ms (above 0.5 px per ms)
  await realDrag(page, k.left + k.width / 2, k.top + k.height / 2, -200, 150);
  await settle(page);
  check(await isOpen(page) && await activeTab(page) === "help",
    "real drag up from a tab opens the panel and keeps the tab");
  const c = await rect(page, "#tab-help");
  await realDrag(page, c.left + c.width / 2, c.top + 150, -120);
  await settle(page);
  check(await isOpen(page) && await page.evaluate(() => document.getElementById("tab-help").scrollTop > 30), "real drag up in the content scrolls it");
  await page.evaluate(() => { document.getElementById("tab-help").scrollTop = 0; });
  await realDrag(page, c.left + c.width / 2, c.top + 40, far, 1000);
  await settle(page);
  check(await isClosed(page), "real drag down in the content at its top closes the panel");
});

test("touch targets, inputs, a slider, the count line and a hit of the list", async ({ mapPage: page, check, saveScreenshot }) => {
  await districtCompanies(page);
  const map = await rect(page, "#map");
  const full = await fullPanel(page);
  // touch targets and font sizes (pointer: coarse)
  await tap(page, tab("city"));
  const sizes = await page.evaluate(() => ({
    n: [document.querySelectorAll("#tab-city .choice label").length, document.querySelectorAll("#tab-city .info-button").length],
    rows: Math.min(...[...document.querySelectorAll("#tab-city .choice label")].filter((l) => l.offsetParent).map((l) => l.getBoundingClientRect().height)),
    info: Math.min(...[...document.querySelectorAll("#tab-city .info-button")].map((b) => Math.min(b.offsetWidth, b.offsetHeight))),
  }));
  check(sizes.n[0] > 10 && sizes.n[1] > 10, `layer rows and ⓘ found (${sizes.n})`);
  check(sizes.rows >= 32, `layer rows at least 32 px high (${sizes.rows})`);
  check(sizes.info >= 32, `ⓘ at least 32 px (${sizes.info})`);
  await tap(page, tab("candidates"));
  const inputs = await page.evaluate(() => [...document.querySelectorAll("#tab-candidates select, #tab-candidates input:not([type=range]):not([type=checkbox])")]
    .map((e) => parseFloat(getComputedStyle(e).fontSize)));
  check(inputs.length > 0 && inputs.every((f) => f >= 16), `inputs at 16 px, iOS does not zoom (${inputs})`);
  await saveScreenshot("candidates");
  // a drag on a slider moves the slider, not the panel
  await page.evaluate(() => { document.getElementById("tab-candidates").scrollTop = 0; });
  await drag(page, "#tab-candidates input[type=range]", Math.round(full * 0.7), 1500);
  await settle(page);
  check(await isOpen(page), "drag on a slider leaves the panel open");

  check(await page.evaluate(() => { const b = document.getElementById("match-count"); return !b.hidden && b.offsetHeight >= 32; }), "count line visible, 32 px high");
  await tap(page, "#match-count");
  let side = await panel(page);
  check(await page.evaluate(([top, bottom]) => { const r = document.getElementById("matches").getBoundingClientRect(); return r.top >= top - 1 && r.top < bottom; }, [side.top, side.bottom]),
    "a tap on the count line scrolls the hits into the open panel");

  // a hit in the list zooms into the visible part above the panel
  await tap(page, "#matches li[data-id]");
  side = await panel(page);
  check(await page.evaluate((top) => { const id = document.querySelector("#matches li[data-id]").dataset.id;
    let c; APP.layers.district.eachLayer((l) => { if (l.feature.properties.id === id) c = APP.map.latLngToContainerPoint(l.getBounds().getCenter()); });
    return c && c.y > 0 && c.y < top; }, side.top - map.top), "hit of the list lies above the panel");
});

test("taps on the map: the tooltip stays, the panel stays, the profile follows", async ({ mapPage: page, check, saveScreenshot }) => {
  // taps on the map: the tooltip stays, the panel stays as it is, the profile follows in the background
  await districtCompanies(page);
  await page.evaluate(() => { APP.map.fitBounds(APP.layers.district.getBounds(), { animate: false }); });
  await settle(page);
  const map = await rect(page, "#map"), tabs = await rect(page, "#tabs");
  for (const round of [1, 2]) {
    const target = await areaAt(page, 0, tabs.top - map.top);
    check(target !== null, `round ${round}: an area on the map`);
    if (!target) break;
    await page.touchscreen.tap(target.px, target.py);
    await settle(page);
    // the tooltip must last: the pause gives a late close (mouse emulation after a tap) the time to happen
    await page.waitForTimeout(800);
    const shown = await tip(page);
    check(shown && shown.text.includes(target.name) && shown.width > 80 && shown.height > 20, `round ${round}: tooltip stays with the tapped area (${JSON.stringify(shown)})`);
    check(shown && shown.left >= map.left - 1 && shown.right <= map.right + 1 && shown.top >= map.top - 1, `round ${round}: tooltip inside the map (${JSON.stringify(shown)} map ${JSON.stringify(map)} tap ${target.x},${target.y})`);
    check(shown && !(shown.left <= map.left + target.x && map.left + target.x <= shown.right && shown.top <= map.top + target.y && map.top + target.y <= shown.bottom),
      `round ${round}: tooltip does not cover the tapped point`);
    check((await panel(page)).height <= tabs.height + 3 && await arrow(page) === "▲ false", `round ${round}: closed panel stays closed`);
    check(await activeTab(page) === "city", `round ${round}: active tab unchanged`);
    check(await page.evaluate((n) => document.getElementById("tab-area").textContent.includes(n), target.name), `round ${round}: profile follows in the background`);
    if (round === 1) await saveScreenshot("tooltip");
  }
});

test("the tooltip button explores the area", async ({ mapPage: page, check }) => {
  // the tooltip button explores the area (docs/design.md, Exploring an area)
  await districtCompanies(page);
  await page.evaluate(() => { APP.map.fitBounds(APP.layers.district.getBounds(), { animate: false }); });
  await settle(page);
  const map = await rect(page, "#map"), tabs = await rect(page, "#tabs");
  const center = () => page.evaluate(() => [APP.map.getCenter().lat, APP.map.getCenter().lng]);
  const stateArea = () => page.evaluate(() => APP.state.area);
  const profileName = () => page.evaluate(() => document.querySelector("#tab-area h2")?.textContent);
  const tapPoint = (target) => page.touchscreen.tap(target.px, target.py);
  const A = await areaAt(page, 0, tabs.top - map.top);
  check(A !== null, "explore: an area A on the map");
  if (!A) return;
  const before = await center();
  await page.evaluate(([x, y]) => { window.aLatLng = APP.map.containerPointToLatLng([x, y]); }, [A.x, A.y]);
  await tapPoint(A);
  await settle(page);
  const shownA = await tip(page);
  check(shownA && !!shownA.button?.trim() && shownA.explore === A.id && shownA.buttonHeight >= 32, `explore: tooltip of A has the button of 32 px (${JSON.stringify(shownA)})`);
  check((await panel(page)).height <= tabs.height + 3 && await activeTab(page) === "city" && await stateArea() === null, "explore: tap on A keeps panel closed, tab Stadt, not exploring");
  check(JSON.stringify(await center()) === JSON.stringify(before), "explore: a plain tap does not move the map");
  // the button flies to the area (Leaflet flyToBounds): wait for the end of the flight
  await page.evaluate(() => { window.flown = false; APP.map.once("moveend", () => { window.flown = true; }); });
  await tap(page, ".tip-explore");
  const flown = await page.waitForFunction(() => window.flown, null, { timeout: 3000 }).then(() => true, () => false);
  await settle(page);
  const sideA = await panel(page);
  check(flown && sideA.height > 150 && await activeTab(page) === "area" && await stateArea() === A.id, "explore: the button opens the panel on Gebiet and explores A");
  const fits = await areaFits(page, A.id, sideA.top - map.top);
  check(fits.ok, `explore: A lies inside the map above the panel (${JSON.stringify(fits)})`);
  const nameA = await profileName();
  // zoom out so that other areas lie in the strip above the panel
  await page.evaluate(() => { APP.map.setZoomAround(window.aLatLng, APP.map.getZoom() - 2, { animate: false }); });
  await settle(page);
  const B = await areaAt(page, 0, sideA.top - map.top);
  check(B !== null, "explore: an area B above the panel");
  if (B) {
    await tapPoint(B);
    await settle(page);
    const shownB = await tip(page);
    check(shownB && shownB.text.includes(B.name) && !!shownB.button?.trim() && shownB.explore === B.id, `explore: tooltip of B has the button (${JSON.stringify(shownB)})`);
    check(await profileName() === nameA && await stateArea() === A.id && await activeTab(page) === "area", "explore: a tap on B keeps profile and focus on A");
  }
  // a tap on A again, on a point of A found after the zoom (the point of the first tap can lie at the edge now)
  const A2 = await areaAt(page, 0, sideA.top - map.top, A.id);
  if (A2) await tapPoint(A2);
  await settle(page);
  const shownA2 = await tip(page);
  check(shownA2 && shownA2.button === null && shownA2.text.includes(A.name), `explore: tooltip of the explored area has no button (${JSON.stringify(shownA2)})`);
  await tap(page, toggle);
  check(await stateArea() === A.id && (await panel(page)).height <= tabs.height + 3, "explore: closing the panel keeps exploring A");
  const sizeE = page.viewportSize();
  await page.setViewportSize(LANDSCAPE);
  await settle(page);
  await page.setViewportSize(sizeE);
  await settle(page);
  check(await stateArea() === A.id, "explore: turned across and back, still exploring A");
  const sideBack = await panel(page);
  const fitsBack = await areaFits(page, A.id, sideBack.top - (await page.evaluate(() => APP.map.getContainer().getBoundingClientRect().top)));
  check(fitsBack.ok, `explore: A still lies inside the map above the panel after turning (${JSON.stringify(fitsBack)})`);
  await tap(page, tab("city"));
  await settle(page);
  check(await stateArea() === null, "explore: tab Stadt ends exploring");
  await page.evaluate(() => { APP.map.setView(APP.layers.district.getBounds().getCenter(), 13, { animate: false }); });
  await settle(page);
  const C = await areaAt(page, 0, (await panel(page)).top - map.top);
  check(C !== null, "explore: an area C above the panel");
  if (C) {
    await tapPoint(C);
    await settle(page);
    check(await stateArea() === null && await activeTab(page) === "city", "explore: a tap on C does not explore");
    await tap(page, tab("area"));
    await settle(page);
    check(await stateArea() === C.id, "explore: tab Gebiet explores C");
  }
});

test("open panel: a tap on the map keeps it, a long legend fits above it", async ({ mapPage: page, check, saveScreenshot }) => {
  await districtCompanies(page);
  const map = await rect(page, "#map");
  // with the panel open a tap on the map keeps the panel and its tab; the tooltip stays above the panel
  await tap(page, toggle);
  let side = await panel(page);
  // zoomed in, so a small phone has areas in the strip above the panel too
  await page.evaluate(() => { APP.map.setView(APP.layers.district.getBounds().getCenter(), 13, { animate: false }); });
  await settle(page);
  const target = await areaAt(page, 0, side.top - map.top);
  if (target) {
    await page.touchscreen.tap(target.px, target.py);
    await settle(page);
    const shown = await tip(page);
    check(shown && shown.text.includes(target.name) && shown.bottom <= side.top + 1, "open panel: tooltip above the panel");
    check((await panel(page)).height > 150 && await activeTab(page) === "city",
      "open panel: tap on the map keeps panel and tab");
    await saveScreenshot("area");
  } else check(false, "open panel: an area above the panel");
  // a long legend (election) fits between header and open panel and scrolls
  await page.evaluate(() => APP.setIndicator("ELEC_STRONGEST"));
  await tap(page, ".legend");
  const legend = await rect(page, ".legend");
  side = await panel(page);
  check(legend.height > 60 && legend.top >= map.top - 1 && legend.bottom <= side.top + 1, `open panel: long legend fits above it (${legend.top}–${legend.bottom}, map ${map.top}, panel ${side.top})`);
});

test("a wide tooltip goes above or below the point; turning the phone; a tap beside the city", async ({ mapPage: page, check, saveScreenshot }) => {
  // a wide tooltip (title and range) has no room beside the point on a phone; the start shows Stadtteile with
  // ABG und Nassauische Heimstätte (OWN_PUBLIC) and the panel closed
  await page.evaluate(() => { APP.setLevel("quarter"); APP.setIndicator("OWN_PUBLIC"); });
  const map = await rect(page, "#map"), tabs = await rect(page, "#tabs");
  // zoomed in, every point lies in an area: near the top the tooltip goes below the point, lower down above it
  await page.evaluate(() => { APP.map.setView(APP.layers.district.getBounds().getCenter(), 14, { animate: false }); });
  await settle(page);
  const w = map.width;
  for (const [y, below] of [[30, true], [Math.round(map.height * 0.6), false]]) {
    await page.touchscreen.tap(map.left + w / 2, map.top + y);
    await settle(page);
    const shown = await tip(page);
    check(shown && (below ? shown.top > map.top + y : shown.bottom < map.top + y) && shown.left >= map.left - 1 && shown.right <= map.right + 1,
      `tooltip ${below ? "below" : "above"} the point at y ${y} (${JSON.stringify(shown)})`);
    // the count of the group comes with the tap (docs/texts.md, Map: tooltip): the tooltip ends with the dwellings of
    // the tapped area as APP.dwellingsText gives them, and the area has a count
    const count = await page.evaluate(() => { const p = APP.map.hasLayer(APP.tip) && APP.areaAt(APP.tip.getLatLng()), id = APP.state.indicator;
      return p ? { text: APP.dwellingsText(p[id + "_DWELLINGS"], p[id + "_DWELLINGS_HIGH"]), none: APP.dwellingsText(null, null) } : null; });
    // a count with a tilde is a number in the German format; no placeholder leaks into the text
    const formatOk = count && !/NaN|undefined|null|\{/.test(count.text) && (!count.text.startsWith("~") || /^~\d{1,3}(\.\d{3})*$/.test(count.text));
    check(shown && count && formatOk && count.text !== count.none && shown.text.endsWith(": " + count.text), `tap shows the dwellings of ABG and NH (${shown && shown.text})`);
    if (!below) await saveScreenshot("tooltip_dwellings");
  }
  await page.evaluate(() => { APP.map.fitBounds(APP.layers.district.getBounds(), { animate: false, paddingBottomRight: [0, APP.panelHeight()] }); });
  // turning the phone: medium layout across, back upright the closed panel and its arrow stay as they were
  const size = page.viewportSize();
  await page.setViewportSize(LANDSCAPE);
  await settle(page);
  check(Math.abs((await panel(page)).width - 320) <= 1 && await page.evaluate(() => document.getElementById("tab-city").offsetHeight > 0
    && APP.map.getContainer().style.getPropertyValue("--panel") === "0px" && [...document.querySelectorAll("#sidebar .tab")].every((t) => !t.inert)),
    "turned across: medium layout, no panel offset, content usable");
  await page.setViewportSize(size);
  await settle(page);
  check(await arrow(page) === "▲ false" && (await panel(page)).height <= tabs.height + 3
    && await page.evaluate(() => APP.map.getContainer().style.getPropertyValue("--panel") === APP.tabsHeight() + "px"), "turned back: panel closed, arrow ▲, offset of the tab bar");
  // a tap beside the city closes the tooltip. The fit and the turning closed the tooltip of the loop already (a move of
  // the map hides it), so a tap on an area opens one first.
  const shownBefore = await areaAt(page, 0, tabs.top - map.top);
  if (shownBefore) { await page.touchscreen.tap(shownBefore.px, shownBefore.py); await settle(page); }
  const opened = !!shownBefore && (await tip(page)) !== null;
  await page.touchscreen.tap(map.left + 8, map.top + 120);
  await settle(page);
  check(opened && await tip(page) === null, "tap beside the city closes the tooltip");
});

test("rent burden: the tooltip shows the income lines and the button", async ({ mapPage: page, check, saveScreenshot }) => {
  // the income breakdown of the rent burden: three more lines and the button fit in the tooltip
  await page.evaluate(() => { APP.setLevel("district"); APP.setIndicator("LIF_RENT_BURDEN_RATIO"); APP.map.fitBounds(APP.layers.district.getBounds(), { animate: false }); });
  await settle(page);
  const map = await rect(page, "#map"), tabs = await rect(page, "#tabs");
  await page.evaluate(() => { window.lastArea = null; });
  // areas without a value (the outlined ones) show no tooltip: take the next area
  let target = null, shown = null;
  for (let attempt = 0; attempt < 6 && !shown; attempt++) {
    target = await areaAt(page, 0, tabs.top - map.top);
    if (!target) break;
    await page.touchscreen.tap(target.px, target.py);
    await settle(page);
    shown = await tip(page);
  }
  check(target !== null, "rent burden: an area on the map");
  if (!target) return;
  // the lead and the three income groups of the breakdown, as the catalog in the page names them
  const want = await page.evaluate(() => { const m = APP.meta.LIF_RENT_BURDEN_RATIO; return [m.breakdown_lead, ...APP.breakdownFor(m).map((c) => c.title)]; });
  const lines = shown ? want.filter((t) => t && shown.text.includes(t)).length : 0;
  check(shown && want.length === 4 && lines === 4, `rent burden: the tooltip shows the three income lines (${shown && shown.text})`);
  check(shown && shown.left >= map.left - 1 && shown.right <= map.right + 1 && shown.top >= map.top - 1 && shown.bottom <= tabs.top + 1,
    `rent burden: tooltip inside the map (${JSON.stringify(shown)})`);
  check(shown && !(shown.left <= map.left + target.x && map.left + target.x <= shown.right && shown.top <= map.top + target.y && map.top + target.y <= shown.bottom),
    "rent burden: tooltip does not cover the tapped point");
  check(shown && !!shown.button?.trim() && shown.explore === target.id && shown.buttonHeight >= 32, "rent burden: the button stays in the tooltip");
  await saveScreenshot("tooltip_rent_burden");
});

test("view Trend: the charts at the width of the phone", async ({ mapPage: page, check, saveScreenshot }) => {
  // chart view and back
  await tap(page, '#views button[data-view="history"]');
  check(await noOverflow(page), "charts: no horizontal scrolling");
  await saveScreenshot("history");
  check(await historyDrawnAt(page, 0), "charts drawn at the width of the phone");
  await checkTrend(page, check, "charts");
  // turning the phone redraws them: across there is room for the wide drawing, back upright the narrow one again
  const upright = page.viewportSize();
  await page.setViewportSize(LANDSCAPE);
  check(await historyDrawnAt(page, 760), "charts turned across: the wide drawing");
  await page.setViewportSize(upright);
  check(await historyDrawnAt(page, 0), "charts turned back: drawn at the width of the phone");
  await checkTrend(page, check, "charts turned back");
  // a tap on a bar shows its tooltip inside the window, a tap beside it hides it
  // the bar of private companies in 2022 in the largest houses, found by its numbers in the payload
  const bar = await page.evaluate(() => { const h = APP.data.history, s = h.sizes.find((x) => x.size === "13_plus");
    const tips = [...document.querySelectorAll("svg.sizes rect[data-tip]")].map((r) => r.dataset.tip);
    const index = tips.findIndex((t) => t.startsWith(h.company.title) && t.includes("2022") && t.includes(APP.format(s.company["2022"], 0)));
    return { index, tip: tips[index] }; });
  const barSelector = `svg.sizes rect[data-tip] >> nth=${bar.index}`;
  await page.locator(barSelector).scrollIntoViewIfNeeded();
  await tap(page, barSelector);
  const chartTip = await rect(page, ".chart-tip");
  const viewWidth = await page.evaluate(() => window.innerWidth);
  check(chartTip && chartTip.visible && chartTip.left >= 0 && chartTip.right <= viewWidth && chartTip.top >= 0,
    "tap on a bar shows the tooltip inside the window: " + JSON.stringify(chartTip));
  check(bar.index >= 0 && await page.evaluate((t) => document.querySelector(".chart-tip").textContent === t, bar.tip), "tooltip names the bar");
  await tap(page, "#view-history .chart h2");
  check(await page.evaluate(() => document.querySelector(".chart-tip").hidden), "tap beside the bars hides the tooltip");
  await tap(page, '#views button[data-view="map"]');
  check(await page.evaluate(() => { const c = APP.map.getContainer(), s = APP.map.getSize(); return s.x === c.clientWidth && s.y === c.clientHeight && s.x > 0; }),
    "back from the charts: Leaflet knows the map size");
});

test("view Neubau: the charts at the width of the phone and across", async ({ mapPage: page, check, saveScreenshot }) => {
  // view Neubau and back
  await tap(page, '#views button[data-view="new_construction"]');
  check(await page.evaluate(() => !document.getElementById("view-new-construction").hidden && document.getElementById("view-history").hidden), "Neubau: the view shows, the Trend is hidden");
  check(await noOverflow(page), "Neubau: no horizontal scrolling");
  const vb = await viewButtons(page);
  check(vb.count === vb.expected.length && vb.views.join() === vb.expected.join() && vb.labels.every((l) => l.trim() !== ""), `one button per view with its label (${vb.labels})`);
  check(vb.lines.every((n) => n === 1) && Math.max(...vb.heights) - Math.min(...vb.heights) <= 1, `no view button wraps (heights ${vb.heights}, lines ${vb.lines})`);
  check(Math.max(...vb.tops) - Math.min(...vb.tops) <= 1 && vb.order && vb.right <= vb.width + 0.5, `the view buttons in one line inside the window (tops ${vb.tops}, right ${vb.right} of ${vb.width})`);
  check(vb.all <= vb.fewer + 4, `header no higher than with one button less plus 4 px (${vb.all} vs ${vb.fewer})`);
  await saveScreenshot("new_construction");
  check(await drawnNc(page, 0), "Neubau: rows drawn at the width of the phone");
  await checkConstruction(page, check, "Neubau");
  // the block of rents is higher than a phone: its top, then each chart from its title
  await page.evaluate(() => document.querySelector("#view-new-construction svg.rents").closest("figure").scrollIntoView());
  await saveScreenshot("housing_rents");
  for (const [k, id] of [[0, "nominal"], [1, "real"]]) {
    await page.evaluate((k) => document.querySelectorAll("#view-new-construction svg.rents")[k].closest(".sub").scrollIntoView(), k);
    await saveScreenshot(`housing_rents_${id}`);
  }
  const uprightConstruction = page.viewportSize();
  // a hop over the boundary of 700 px of room and back: from the phone to a window with room for the wide drawing, the key
  // goes and the note comes; then down to the landscape size (below 700 px of room on this phone), the key is back
  const rentsShown = () => page.evaluate(() => [...document.querySelectorAll("#view-new-construction div.sub")].map((sub) => {
    const shown = (e) => (e ? getComputedStyle(e).display !== "none" : null);
    return { key: shown(sub.querySelector(".key.rents-key")), note: shown(sub.querySelector("p.old-base-note")) }; }));
  const shownRight = (got, wide) => got.length === 2 && got.every((g) => g.key === !wide) && got[0].note === wide && got[1].note === null;
  await page.setViewportSize({ width: 1000, height: 600 });
  await settle(page);
  const roomWide = await page.evaluate(() => APP.newConstructionBody.clientWidth);
  check(roomWide >= 700, `Neubau, wide hop: the measured room reaches 700 px (${roomWide})`);
  check(await drawnNc(page, 760), `Neubau, wide hop (room ${roomWide} px): the wide drawing`);
  await checkConstruction(page, check, "Neubau, wide hop");
  check(shownRight(await rentsShown(), true), "Neubau, wide hop: the keys hidden, the note under chart 1 shown, none under chart 2");
  await page.setViewportSize(LANDSCAPE);
  await settle(page);
  const roomDown = await page.evaluate(() => APP.newConstructionBody.clientWidth);
  check(roomDown < 700 && await drawnNc(page, 0), `Neubau, wide hop down to the landscape size: the rows again (room ${roomDown} px)`);
  check(shownRight(await rentsShown(), false), "Neubau, wide hop down: the keys shown again, no note");
  await page.setViewportSize(uprightConstruction);
  await settle(page);
  check(await drawnNc(page, 0) && shownRight(await rentsShown(), false), "Neubau, wide hop back to the phone: the keys shown, no note");
  await page.setViewportSize(LANDSCAPE);
  // the wide drawing from 700 px of room (APP.CONSTRUCTION_WIDE), below it the rows; judged by the measured room
  await settle(page);
  const roomAcross = await page.evaluate(() => APP.newConstructionBody.clientWidth);
  check(await drawnNc(page, roomAcross >= 700 ? 760 : 0), `Neubau turned across (room ${roomAcross} px): ${roomAcross >= 700 ? "the wide drawing" : "the rows"}`);
  await checkConstruction(page, check, "Neubau turned across");
  await page.evaluate(() => document.querySelector("#view-new-construction svg.rents").closest("figure").scrollIntoView());
  await saveScreenshot("housing_rents_across");
  await page.setViewportSize(uprightConstruction);
  check(await drawnNc(page, 0), "Neubau turned back: rows drawn at the width of the phone");
  await checkConstruction(page, check, "Neubau turned back");
});

test("view Miete: the wage bars and the bars at the width of the phone and across", async ({ mapPage: page, check, saveScreenshot }) => {
  const r = await page.evaluate(() => APP.data.rent_burden);
  await tap(page, '#views button[data-view="rent_burden"]');
  check(await page.evaluate(() => !document.getElementById("view-rent-burden").hidden && document.querySelector("main").hidden), "Miete: the view shows, the map is hidden");
  check(await noOverflow(page), "Miete: no horizontal scrolling");
  const vb = await viewButtons(page);
  check(vb.count === 4 && vb.views.join() === vb.expected.join() && vb.labels.every((l) => l.trim() !== ""), `Miete: one button per view with its label (${vb.labels})`);
  check(vb.lines.every((n) => n === 1) && Math.max(...vb.heights) - Math.min(...vb.heights) <= 1, `Miete: no view button wraps (heights ${vb.heights}, lines ${vb.lines})`);
  check(Math.max(...vb.tops) - Math.min(...vb.tops) <= 1 && vb.order && vb.right <= vb.width + 0.5, `Miete: the four view buttons in one line inside the window (tops ${vb.tops}, right ${vb.right} of ${vb.width})`);
  check(vb.all <= vb.fewer + 4, `Miete: header no higher than with one button less plus 4 px (${vb.all} vs ${vb.fewer})`);
  check(await drawnRentBurden(page, 0), "Miete: the drawings at the width of the phone");
  await checkRentBurden(page, check, "Miete");
  await page.evaluate(() => document.querySelector("#view-rent-burden svg.wage").closest("figure").scrollIntoView());
  await saveScreenshot("rent_burden_wage");
  await page.evaluate(() => document.querySelector("#view-rent-burden svg.burden").closest("figure").scrollIntoView());
  await saveScreenshot("rent_burden_income");
  // a tap on a row of the wage bars shows its tooltip inside the window, a tap on a segment shows the tooltip of the segment
  const tipInside = async (selector, text) => {
    await page.locator(selector).scrollIntoViewIfNeeded();
    await tap(page, selector);
    const tipBox = await rect(page, "#view-rent-burden .chart-tip"), width = await page.evaluate(() => window.innerWidth);
    check(tipBox && tipBox.visible && tipBox.left >= 0 && tipBox.right <= width && tipBox.top >= 0, "Miete: the tooltip stands inside the window: " + JSON.stringify(tipBox));
    check(await page.evaluate(([t]) => document.querySelector("#view-rent-burden .chart-tip").textContent.includes(t), [text]), "Miete: the tooltip names the tapped element");
  };
  await tipInside("#view-rent-burden svg.wage g.row >> nth=0", r.wage.contracts[0].rows[0].tip);
  // the switch of the contract: touch targets of at least 32 px (docs/design.md), a tap shows the older contract
  const heights = await page.evaluate(() => [...document.querySelectorAll("#view-rent-burden .wage-switch button")].map((b) => b.getBoundingClientRect().height));
  check(heights.length === 2 && heights.every((h) => h >= 32), `Miete: the buttons of the switch are at least 32 px high (${heights})`);
  await tap(page, `#view-rent-burden .wage-switch button[data-contract="${r.wage.contracts[1].id}"]`);
  check(await page.evaluate(() => APP.wageContract) === r.wage.contracts[1].id, "Miete: a tap on the switch shows the older contract");
  await tap(page, `#view-rent-burden .wage-switch button[data-contract="${r.wage.contracts[0].id}"]`);
  await tipInside("#view-rent-burden svg.burden g.segment >> nth=1", r.low_income.bars[0].segments[1].tip);
  await tipInside("#view-rent-burden svg.burden g.label >> nth=2", r.low_income.bars[2].tip);
  await page.evaluate(() => { window.scrollTo(0, 0); document.getElementById("view-rent-burden").scrollTop = 0; });
  // turning the phone redraws them: across there is room for the wide drawing, upright the narrow one again
  const upright = page.viewportSize();
  await page.setViewportSize(LANDSCAPE);
  await settle(page);
  const across = await page.evaluate(() => APP.burdenBody.clientWidth);
  check(await drawnRentBurden(page, across >= 700 ? 760 : 0), `Miete turned across (room ${across} px): ${across >= 700 ? "the wide drawing" : "drawn at the width in px"}`);
  await checkRentBurden(page, check, "Miete turned across");
  await saveScreenshot("rent_burden_across");
  await page.setViewportSize(upright);
  check(await drawnRentBurden(page, 0), "Miete turned back: drawn at the width of the phone");
  await checkRentBurden(page, check, "Miete turned back");
});

test("the footer opens the source list within 40 % of the window", async ({ mapPage: page, check }) => {
  // the footer opens the source list and stays within 40 % of the window
  const height = await page.evaluate(() => window.innerHeight);
  await tap(page, "#footer summary");
  const footer = await rect(page, "#footer");
  check(footer.height > 40 && footer.height <= 0.4 * height + 1, `open footer at most 40 % high (${footer.height})`);
  check(await page.evaluate(() => { const text = document.getElementById("footer").textContent;
    return APP.data.sources.length > 0 && APP.data.sources.every((q) => text.includes(q.title)); }), "open footer lists the sources");
});

test("profile Gallus: the ownership table fits, the pressed row shows its mark", async ({ mapPage: page, check, saveScreenshot }) => {
  // the ownership table of the profile does not scroll sideways
  await page.evaluate(() => { APP.setLevel("quarter"); APP.showProfile("Gallus"); APP.openTab("area"); });
  await settle(page);
  // the table reaches into the free edge of the tab (docs/design.md, Profile and pressed row); its text ends inside the padding
  const profileTable = await page.evaluate(() => { const t = document.querySelector("#tab-area .table"), box = t.parentElement, pad = parseFloat(getComputedStyle(box).paddingRight);
    const text = (cell) => { const r = document.createRange(); r.selectNodeContents(cell); return r.getBoundingClientRect(); };
    const b = box.getBoundingClientRect();
    return { table: Math.round(text(t.rows[0].cells[t.rows[0].cells.length - 1]).right), room: Math.round(b.right - pad), box: box.scrollWidth - box.clientWidth,
             start: Math.round(text(t.rows[1].cells[0]).left - b.left), pad, head: [...t.rows[0].cells].map((c) => c.textContent.trim()) }; });
  // the text of the table starts and ends at the padding of the tab, and the tab itself does not scroll sideways
  // the head: an empty cell over the names, then the area and the city
  check(profileTable.head.length === 3 && profileTable.head[0] === "" && profileTable.head.slice(1).every((h) => h !== "") && profileTable.table <= profileTable.room + 1 && Math.abs(profileTable.start - profileTable.pad) <= 1 && profileTable.box <= 0,
    `profile Gallus: ownership table does not scroll sideways (${JSON.stringify(profileTable)})`);
  // WebKit draws no box-shadow on a table row: the mark of the pressed table row lies on its first cell
  const mark = await page.evaluate(() => { APP.chooseLayer("OWN_COOP"); const r = document.querySelector('#tab-area tr[data-layer="OWN_COOP"]');
    return { active: r.classList.contains("active"), cell: getComputedStyle(r.cells[0]).boxShadow }; });
  check(mark.active && /inset/.test(mark.cell) && mark.cell.includes("5px"), `profile Gallus: the pressed table row shows its mark (${JSON.stringify(mark)})`);
  await saveScreenshot("profile");
});

test("profile: the income bars of the rent burden fit the tab", async ({ mapPage: page, check }) => {
  // the income bars of the rent burden fit the width of the tab
  const bars = await page.evaluate(() => { APP.setLevel("district"); APP.showProfile(APP.properties("district").find((p) => p.survey_area === "West").id); APP.openTab("area");
    const box = document.querySelector("#tab-area .breakdown"), tab = document.getElementById("tab-area"), b = box?.getBoundingClientRect(), t = tab.getBoundingClientRect();
    return { rows: box ? box.querySelectorAll(".row").length : 0, left: b && b.left - t.left, right: b && t.right - b.right, scroll: tab.scrollWidth - tab.clientWidth,
      over: box ? [...box.querySelectorAll(".row > *")].filter((e) => e.getBoundingClientRect().right > t.right + 1).length : -1 }; });
  check(bars.rows === 3 && bars.left >= 0 && bars.right >= 0 && bars.scroll <= 0 && bars.over === 0, `profile: income bars fit the tab (${JSON.stringify(bars)})`);
});

test("details line in Gebiet", async ({ mapPage: page, check, saveScreenshot }) => {
  // the details line under the head of the profile (docs/design.md, Profile and pressed row): a touch target, and a
  // switch there keeps the panel open and the area explored
  await tap(page, toggle);
  await page.evaluate(() => { window.flown = false; APP.map.once("moveend", () => { window.flown = true; }); APP.explore("Bornheim"); });
  await page.waitForFunction(() => window.flown, null, { timeout: 3000 }).catch(() => {});
  await settle(page);
  const summary = "#tab-area details.area-details summary";
  const box = await rect(page, summary);
  check(box && box.visible && box.height >= 32, `details: the line is at least 32 px high (${JSON.stringify(box)})`);
  check(await isOpen(page) && await activeTab(page) === "area", "details: the panel is open on Gebiet");
  await saveScreenshot("area-details-closed");
  await tap(page, summary);
  const opened = await page.evaluate(() => document.querySelector("#tab-area details.area-details")?.open);
  check(opened === true && await isOpen(page), "details: a tap opens the line, the panel stays open");
  await tap(page, '#tab-area input[data-overlay="land_value"]');
  const s = await page.evaluate(() => ({ on: APP.overlays.land_value.on, area: APP.state.area }));
  check(s.on && s.area === "Bornheim" && await isOpen(page), "details: a tap on the checkbox switches the overlay, panel open, area kept " + JSON.stringify(s));
  await saveScreenshot("area-details");
});

test("reset button: 32 px, a tap fits the city above the closed panel", async ({ mapPage: page, check }) => {
  const b = await rect(page, ".zoom-reset"), zoom = await page.evaluate(() => APP.map.getZoom());
  check(b.width >= 32 && b.height >= 32, `reset button at least 32 x 32 px (${b.width} x ${b.height})`);
  const all = await page.evaluate(() => [".leaflet-control-zoom-in", ".zoom-reset", ".leaflet-control-zoom-out"].map((s) => {
    const r = document.querySelector(s).getBoundingClientRect(); return [r.width, r.height]; }));
  check(all.every(([w, h]) => w >= 32 && h >= 32) && all.every(([w]) => w === all[0][0]), `+, reset, − at least 32 px and equally wide: ${JSON.stringify(all)}`);
  await page.evaluate(() => APP.map.setView([50.11, 8.68], 16, { animate: false }));
  await settle(page);
  await tap(page, ".zoom-reset");
  await page.waitForFunction((z) => Math.abs(APP.map.getZoom() - z) <= 0.5, zoom);
  await settle(page);
  const tabs = await rect(page, "#tabs"), map = await rect(page, "#map");
  check(await page.evaluate((top) => { const b = APP.layers.district.getBounds(), m = APP.map;
    const nw = m.latLngToContainerPoint(b.getNorthWest()), se = m.latLngToContainerPoint(b.getSouthEast());
    return nw.y >= -2 && nw.x >= -2 && se.x <= m.getSize().x + 2 && se.y <= top + 2; }, tabs.top - map.top), "a tap fits Frankfurt above the tab bar");
});
