// Overlay of the low flat roofs (docs/design.md, Overlays): row and ⓘ, minimum zoom 15, tooltip rows, the two key
// rows, and the layer ROOF_FLAT in "Stadt".
import { test } from "../fixtures.mjs";
import { hoverAt } from "../helpers/layers.mjs";

const view = (page, zoom, [lat, lng] = [50.1127, 8.7254]) => page.evaluate(([z, la, ln]) => {
  APP.openTab("city");
  APP.map.setView([la, ln], z, { animate: false });
  APP.updateOverlays();
}, [zoom, lat, lng]);
const setOn = (page, on) => page.evaluate((v) => APP.setOverlay("flat_roofs", v), on);
// a point inside the largest roof (by bounding box) of a kind (counts 1 or 0), verified with APP.inPolygon
const pointIn = (page, counts) => page.evaluate((c) => {
  let best = null;
  for (const f of APP.data.flat_roofs.features) {
    if (f.properties.counts !== c) continue;
    const poly = f.geometry.type === "Polygon" ? f.geometry.coordinates : f.geometry.coordinates[0];
    const xs = poly[0].map((p) => p[0]), ys = poly[0].map((p) => p[1]);
    const size = (Math.max(...xs) - Math.min(...xs)) * (Math.max(...ys) - Math.min(...ys));
    if (!best || size > best.size) best = { f, size, xs, ys };
  }
  const [x0, x1] = [Math.min(...best.xs), Math.max(...best.xs)], [y0, y1] = [Math.min(...best.ys), Math.max(...best.ys)];
  for (let i = 1; i < 20; i++) for (let j = 1; j < 20; j++) {
    const lng = x0 + (x1 - x0) * i / 20, lat = y0 + (y1 - y0) * j / 20;
    // the mouse comes from 3 px beside the point: the point and its eight neighbours at about 8 m lie inside
    const d = 0.0001, around = [-d, 0, d].flatMap((a) => [-d, 0, d].map((b) => [lng + a, lat + b]));
    if (around.every(([x, y]) => APP.inPolygon(best.f.geometry, x, y))) return { point: [lat, lng], text: best.f.properties.text };
  }
  return null;
}, counts);
// roof paths in the DOM: the SVG pane of the overlays holds them, found by their class
const roofPaths = (page) => page.evaluate(() => ({
  lines: document.querySelectorAll("path.flat-roof, path.flat-roof-not").length,
  casing: [...APP.overlays.flat_roofs.casing.getLayers()].length && APP.map.hasLayer(APP.overlays.flat_roofs.casing),
  layer: APP.map.hasLayer(APP.overlays.flat_roofs.layer),
}));

test("every roof is a Polygon or MultiPolygon (the tooltip reads only those)", async ({ mapPage: page, check }) => {
  const types = await page.evaluate(() => [...new Set(APP.data.flat_roofs.features.map((f) => f.geometry.type))].sort());
  check(types.every((t) => t === "Polygon" || t === "MultiPolygon"), "geometry types: " + types.join());
});

test("row, ⓘ, off at start", async ({ mapPage: page, check }) => {
  await page.evaluate(() => APP.openTab("city"));
  const row = await page.evaluate(() => {
    const c = document.querySelector('#tab-city input[data-overlay="flat_roofs"]');
    if (!c) return null;
    const r = c.closest(".layer-row"), b = r.querySelector(".info-button");
    b.click();
    const info = document.getElementById("info-overlay-flat_roofs");
    return { title: APP.meta.ROOF_FLAT.title, label: r.textContent.trim(), checked: c.checked, open: !info.hidden, text: protocolText(info) };
  });
  check(row && row.label.startsWith(row.title), "overlay row: " + row?.label);
  check(row && !row.checked, "off at start");
  check(row && row.open && /Quelle/.test(row.text) && /Stand/.test(row.text) && /Regel/.test(row.text), "ⓘ holds Quelle, Stand, Regel: " + row?.text);
});

test("minimum zoom 15, tooltip, two key rows", async ({ mapPage: page, check }) => {
  await page.evaluate(() => APP.setIndicator("OWN_PUBLIC"));
  const note = await page.evaluate(() => APP.overlays.flat_roofs.zoomNote);
  check(note, "the overlay has a zoom note");
  await setOn(page, true);
  await view(page, 14);
  const low = await roofPaths(page);
  check(low.lines === 0 && !low.layer && !low.casing, "zoom 14: no roof path, no layer: " + JSON.stringify(low));
  const key14 = await page.evaluate(() => document.querySelector(".legend-overlays").textContent);
  check(key14.includes(note), "zoom 14: key asks to zoom: " + key14);

  const counted = await pointIn(page, 1), not = await pointIn(page, 0);
  check(counted && not, "test points found");
  const tip = await page.evaluate(() => APP.data.overlays.flat_roofs.tip);
  for (const [kind, p] of [["counted", counted], ["not counted", not]]) {
    await view(page, 15, p.point);
    const rows = await hoverAt(page, p.point);
    check(rows.some((t) => t.includes(tip) && t.includes(p.text)), `${kind}: tooltip holds "${tip}" and the text: ${rows.join(" | ")}`);
    if (kind === "not counted") check(p.text.includes("Zählt nicht:"), "not counted text contains Zählt nicht: " + p.text);
    const on = await roofPaths(page);
    check(on.lines > 0 && on.casing && on.layer, `${kind}: zoom 15 draws roofs: ` + JSON.stringify(on));
  }
  const keys = await page.evaluate(() => ({ rows: [...document.querySelectorAll(".legend-overlays .key-row")].map((r) => r.textContent.trim()),
    swatches: document.querySelectorAll(".legend-overlays .key-row .key-swatch").length,
    keys: [APP.data.overlays.flat_roofs.key, APP.data.overlays.flat_roofs.key_not_counted] }));
  check(keys.keys.every((k) => k && keys.rows.includes(k)) && keys.swatches >= 2, "two key rows with the payload keys: " + keys.rows.join(" | "));
  check(!keys.rows.some((r) => r === note), "no zoom note at 15");

  await view(page, 14, counted.point);
  const back = await roofPaths(page);
  check(back.lines === 0 && !back.layer && !back.casing, "back at 14: paths and casing leave: " + JSON.stringify(back));
  const rows = await hoverAt(page, counted.point);
  check(!rows.some((t) => t.includes(tip)), "back at 14: no roof row in the tooltip: " + rows.join(" | "));
});

test("layer ROOF_FLAT: legend note, city value, sum", async ({ mapPage: page, check }) => {
  await page.evaluate(() => { APP.setLevel("district"); APP.openTab("city"); APP.setIndicator("ROOF_FLAT"); });
  const got = await page.evaluate(() => {
    const m = APP.meta.ROOF_FLAT;
    const title = m.title;
    const label = document.querySelector('label[data-id="ROOF_FLAT"]');
    document.querySelector('.info-button[data-info="ROOF_FLAT"]').click();
    const info = document.getElementById("info-ROOF_FLAT");
    const out = { title, row: label && label.textContent.trim(), note: (APP.legendDiv.querySelector(".legend-note") || {}).textContent,
      expectedNote: m.legend_note, legend: APP.legendDiv.textContent, city: APP.valueText("ROOF_FLAT", APP.data.city_values.ROOF_FLAT),
      info: protocolText(info), dts: [...info.querySelectorAll("dt")].map((d) => d.textContent), calc: Object.fromEntries(APP.PROTOCOL).calc,
      area: m.calc_example && m.calc_example.area, sources: m.source.split(" · "), dates: m.as_of.split(" · ") };
    // the sum stands in the <dd> under its own label; its text ends with the last row: "~" + number, then the text
    const ex = m.calc_example, last = ex && ex.rows.at(-1);
    const dt = ex && [...info.querySelectorAll("dt")].find((d) => d.textContent === ex.label);
    out.sum = dt ? dt.nextElementSibling.textContent.trim() : "";
    out.lastRow = last ? (last.estimate ? "~" : "") + APP.format(last.number, last.decimals) + last.text : null;
    return out;
  });
  check(got.row && got.row.startsWith(got.title), "layer row in Stadt: " + got.row);
  check(got.expectedNote && got.note === got.expectedNote, "legend note: " + got.note);
  check(got.legend.includes("Ganz Frankfurt: " + got.city), "legend shows Ganz Frankfurt with the city value: " + got.legend);
  check(got.sources.length === 3 && got.sources.every((s) => got.info.includes(s)) && got.dates.every((d) => got.info.includes(d)),
    "ⓘ names the three sources and both dates: " + got.info);
  check(got.area && got.dts.some((d) => d.startsWith(got.calc + " ") && d.includes(got.area)), "ⓘ labels the sum with the area: " + got.dts.join(" | "));
  check(got.lastRow && got.sum.endsWith(got.lastRow), `the sum ends in its last row "${got.lastRow}": ` + got.sum);
});
