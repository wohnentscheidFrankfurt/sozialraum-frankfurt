// Overlay of the building gaps (docs/design.md, Overlays): row and ⓘ in "Stadt", one key row, tooltip of a counted
// gap and of a gap to check on site, the layer GAP_AREA and the link.
import { test } from "../fixtures.mjs";
import { hoverAt } from "../helpers/layers.mjs";

const setOn = (page, on) => page.evaluate((v) => APP.setOverlay("building_gaps", v), on);
// a point inside the largest gap of a kind (counts 1 or 0), verified with APP.inPolygon
const pointIn = (page, counts) => page.evaluate((c) => {
  let best = null;
  for (const f of APP.data.building_gaps.features) {
    if (f.properties.counts !== c) continue;
    const poly = f.geometry.type === "Polygon" ? f.geometry.coordinates : f.geometry.coordinates[0];
    const xs = poly[0].map((p) => p[0]), ys = poly[0].map((p) => p[1]);
    const size = (Math.max(...xs) - Math.min(...xs)) * (Math.max(...ys) - Math.min(...ys));
    if (!best || size > best.size) best = { f, size, xs, ys };
  }
  if (!best) return null;
  const [x0, x1] = [Math.min(...best.xs), Math.max(...best.xs)], [y0, y1] = [Math.min(...best.ys), Math.max(...best.ys)];
  for (let i = 1; i < 20; i++) for (let j = 1; j < 20; j++) {
    const lng = x0 + (x1 - x0) * i / 20, lat = y0 + (y1 - y0) * j / 20;
    // the mouse comes from 3 px beside the point: the point and its eight neighbours lie inside
    const d = 0.00003, around = [-d, 0, d].flatMap((a) => [-d, 0, d].map((b) => [lng + a, lat + b]));
    if (around.every(([x, y]) => APP.inPolygon(best.f.geometry, x, y))) return { point: [lat, lng], text: best.f.properties.text };
  }
  return null;
}, counts);

test("row, ⓘ, off at start", async ({ mapPage: page, check }) => {
  await page.evaluate(() => APP.openTab("city"));
  const row = await page.evaluate(() => {
    const c = document.querySelector('#tab-city input[data-overlay="building_gaps"]');
    if (!c) return null;
    const r = c.closest(".layer-row"), b = r.querySelector(".info-button");
    b.click();
    const info = document.getElementById("info-overlay-building_gaps");
    return { title: APP.data.overlays.building_gaps.title, label: r.textContent.trim(), checked: c.checked, open: !info.hidden, text: protocolText(info) };
  });
  check(row && row.label.startsWith(row.title), "overlay row: " + row?.label);
  check(row && !row.checked, "off at start");
  check(row && row.open && /Quelle/.test(row.text) && /Stand/.test(row.text) && /Regel/.test(row.text), "ⓘ holds Quelle, Stand, Regel: " + row?.text);
});

test("tooltip of a counted gap and of a gap to check on site, one key row", async ({ mapPage: page, check }) => {
  await page.evaluate(() => APP.setIndicator("OWN_PUBLIC"));
  await setOn(page, true);
  const counted = await pointIn(page, 1), site = await pointIn(page, 0);
  check(counted && site, "test points found: " + JSON.stringify({ counted, site }));
  const tip = await page.evaluate(() => APP.data.overlays.building_gaps.tip);
  for (const [kind, p] of [["counted", counted], ["site", site]]) {
    if (!p) continue;
    await page.evaluate(([la, ln]) => { APP.openTab("city"); APP.map.setView([la, ln], 17, { animate: false }); APP.updateOverlays(); }, p.point);
    const rows = await hoverAt(page, p.point);
    check(rows.some((t) => t.includes(tip) && t.includes(p.text)), `${kind}: tooltip holds "${tip}" and the text: ${rows.join(" | ")}`);
    if (kind === "counted") check(p.text.includes("Platz zum Beispiel"), "counted text holds „Platz zum Beispiel“: " + p.text);
    else check(/vor Ort geprüft/.test(p.text) && !p.text.includes("Zählt nicht"), "site text: " + p.text);
  }
  const keys = await page.evaluate(() => ({ rows: [...document.querySelectorAll(".legend-overlays .key-row")].map((r) => r.textContent.trim()),
    swatches: [...document.querySelectorAll(".legend-overlays .key-row")].filter((r) => r.textContent.trim() === "Baulücke")
      .reduce((n, r) => n + r.querySelectorAll(".key-swatch").length, 0), key: APP.data.overlays.building_gaps.key }));
  check(keys.key === "Baulücke" && keys.rows.filter((r) => r === "Baulücke").length === 1 && keys.swatches === 1, "one key row Baulücke: " + keys.rows.join(" | "));
  const drawn = await page.evaluate(() => ({ layer: APP.map.hasLayer(APP.overlays.building_gaps.layer), casing: APP.map.hasLayer(APP.overlays.building_gaps.casing) }));
  check(drawn.layer && drawn.casing, "layer and casing are drawn: " + JSON.stringify(drawn));
});

test("layer GAP_AREA is selectable in Stadt", async ({ mapPage: page, check }) => {
  await page.evaluate(() => { APP.setLevel("district"); APP.openTab("city"); APP.setIndicator("GAP_AREA"); });
  const got = await page.evaluate(() => {
    const label = document.querySelector('label[data-id="GAP_AREA"]');
    return { row: label && label.textContent.trim(), title: APP.meta.GAP_AREA.title, legend: APP.legendDiv.textContent, indicator: APP.state.indicator,
      city: APP.t("legend.city", { value: APP.valueText("GAP_AREA", APP.data.city_values.GAP_AREA) }) };
  });
  check(got.row && got.row.startsWith(got.title), "layer row in Stadt: " + got.row);
  check(got.indicator === "GAP_AREA" && got.legend.includes(got.city), "layer selected, legend: " + got.legend);
});

test("link overlays=building_gaps round-trips", async ({ mapPage: page, check }) => {
  await setOn(page, true);
  const hash = await page.evaluate(() => location.hash);
  check(/overlays=[^&]*building_gaps/.test(hash), "the link has the overlay: " + hash);
  await page.evaluate((h) => { location.hash = "#karte/zoom=13&center=50.11,8.68&level=quarter&layer=OWN_PUBLIC&overlays=building_gaps"; }, hash);
  await page.reload();
  await page.waitForFunction(() => window.APP && APP.overlays);
  const on = await page.evaluate(() => ({ on: APP.overlays.building_gaps.on, box: document.querySelector('#tab-city input[data-overlay="building_gaps"]').checked }));
  check(on.on && on.box, "the link switches the overlay on: " + JSON.stringify(on));
});
