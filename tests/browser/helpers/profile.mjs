// Helpers of the profile, explore and help tests (desktop): points on the map, the end of a zoom, the state of the
// explored map and of the profile rows.
import { settle } from "./common.mjs";

// Leaflet sets _animatingZoom only in the next animation frame: let the frames pass first, then wait for the end
export const zoomDone = async (page) => {
  await settle(page);
  await page.waitForFunction(() => !APP.map._animatingZoom);
};

// wait until the map has stopped moving: no zoom animation and the same view over three polls
export const settleView = (page) => page.evaluate(async () => {
  let last = "", same = 0;
  while (same < 3) {
    await new Promise((r) => setTimeout(r, 120));
    const c = APP.map.getCenter(), now = `${c.lat.toFixed(6)},${c.lng.toFixed(6)},${APP.map.getZoom()}`;
    same = now === last && !APP.map._animatingZoom ? same + 1 : 0;
    last = now;
  }
});

// Page coordinates of a point in district districtId under the overlay (land_value, grid, townscape), on the tab
// Stadt with only that overlay on; null if there is none that no control covers. The profile is cleared, so a click
// there opens it fresh.
export const clickPoint = (page, overlay, zoom, districtId = "213") => page.evaluate(([u, z, did]) => {
  APP.openTab("city"); // first: it ends an exploring and with it moves the view back
  APP.setLevel("district");
  APP.overlays.land_value.on = u === "land_value";
  APP.overlays.grid.on = u === "grid";
  if (APP.overlays.townscape) APP.overlays.townscape.on = u === "townscape";
  const district = Object.values(APP.layers.district._layers).find((l) => l.feature.properties.id === did);
  APP.map.fitBounds(district.getBounds(), { animate: false });
  if (z) APP.map.setZoom(z, { animate: false });
  APP.updateOverlays();
  const inside = (l, pt) => l._containsPoint(APP.map.latLngToLayerPoint(pt));
  const above = Object.values(APP.overlays[u].layer._layers).flatMap((l) => (l._layers ? Object.values(l._layers) : [l]));
  const b = district.getBounds();
  for (let i = 1; i < 40; i++) for (let j = 1; j < 40; j++) {
    const pt = L.latLng(b.getSouth() + (b.getNorth() - b.getSouth()) * i / 40, b.getWest() + (b.getEast() - b.getWest()) * j / 40);
    if (inside(district, pt) && above.some((l) => inside(l, pt))) {
      const c = APP.map.latLngToContainerPoint(pt), r = APP.map.getContainer().getBoundingClientRect();
      const top = document.elementFromPoint(r.left + c.x, r.top + c.y);
      if (!top || !APP.map.getContainer().contains(top) || top.closest(".leaflet-control")) continue; // point outside the map or covered by the legend or zoom buttons
      APP.setState({ profile: null }, false);
      return { x: r.left + c.x, y: r.top + c.y };
    }
  }
  return null;
}, [overlay, zoom, districtId]);

// page coordinates of a point well inside the area that no control or panel covers, or null
export const pointIn = (page, level, id) => page.evaluate(([lv, aid]) => {
  const layer = APP.layers[lv];
  let found = null;
  layer.eachLayer((l) => { if (l.feature.properties.id === aid) found = l; });
  const b = found.getBounds(), box = APP.map.getContainer().getBoundingClientRect();
  for (let i = 1; i < 25; i++) for (let j = 1; j < 25; j++) {
    const ll = L.latLng(b.getSouth() + ((b.getNorth() - b.getSouth()) * i) / 25, b.getWest() + ((b.getEast() - b.getWest()) * j) / 25);
    // well inside: a point on the edge may hit the neighbour that Leaflet draws on top
    const c0 = APP.map.latLngToContainerPoint(ll);
    const solid = [[0, 0], [8, 0], [-8, 0], [0, 8], [0, -8]].every(([dx, dy]) => { const q = APP.map.containerPointToLatLng([c0.x + dx, c0.y + dy]); return APP.inPolygon(found.feature.geometry, q.lng, q.lat); });
    if (!solid) continue;
    const c = c0, x = box.left + c.x, y = box.top + c.y;
    if (c.x < 0 || c.y < 0 || c.x > box.width || c.y > box.height) continue;
    const el = document.elementFromPoint(x, y);
    if (!el || el.closest(".leaflet-control")) continue;
    return { x, y };
  }
  return null;
}, [level, id]);

// the view of the map: centre and zoom
export const view = (page) => page.evaluate(() => ({ lat: APP.map.getCenter().lat, lng: APP.map.getCenter().lng, zoom: APP.map.getZoom() }));

// the same view as v, to a millionth of a degree
export const sameView = (s, v) => Math.abs(s.center.lat - v.lat) < 1e-6 && Math.abs(s.center.lng - v.lng) < 1e-6 && s.zoom === v.zoom;

// Click or focus the profile row of a layer (its data-layer). false if the profile has no such row.
export const rowDo = (page, id, how) => page.evaluate(([k, h]) => {
  const r = document.querySelector(`#tab-area [data-layer="${k}"]`);
  if (!r) return false;
  if (h === "click") r.click(); else r.focus();
  return true;
}, [id, how]);

// The blocks of the profile shown in the tab Gebiet, by the catalog section of their heading (a heading is the group
// of its section in the catalog; the election heading adds its year). A block lists its items: the catalog id of a
// row (data-layer, or the entry whose title the row shows; null for a row of no entry), "note" for a note,
// "breakdown" for breakdown bars; and the texts of its notes. A heading of no group is listed by its text.
export const profileBlocks = (page) => page.evaluate(() => {
  const sectionOf = (h) => APP.data.catalog.find((m) => m.group === h || h.startsWith(m.group + " "))?.section ?? null;
  const idOf = (row) => row.dataset.layer || APP.data.catalog.find((m) => m.title === row.querySelector("span").firstChild.textContent.trim())?.id || null;
  const blocks = {};
  let cur = null;
  for (const e of document.getElementById("tab-area").children) {
    if (e.tagName === "H3") {
      const head = e.firstChild.textContent.trim();
      cur = sectionOf(head) ?? head;
      blocks[cur] = { head, date: e.querySelector(".as-of")?.textContent ?? null, items: [], notes: [], strong: [] };
    } else if (cur && e.matches("p.note")) { blocks[cur].items.push("note"); blocks[cur].notes.push(e.textContent); }
    else if (cur && e.matches(".row")) { blocks[cur].items.push(idOf(e)); blocks[cur].strong.push(e.querySelector("strong")?.textContent ?? ""); }
    else if (cur && e.matches(".breakdown")) blocks[cur].items.push("breakdown");
  }
  return { sections: Object.keys(blocks), blocks };
});

// The dates a group heading names: every date of the catalog entries of the section that the area shows, once, in
// catalog order (docs/texts.md, Map: profile)
export const sectionDates = (page, section, id, level) => page.evaluate(([s, aid, lv]) => {
  const p = APP.properties(lv).find((x) => x.id === aid);
  const all = APP.data.catalog.filter((m) => m.section === s && (m.type === "number" || m.type === "classes") && APP.valueSource(m, p, lv));
  return [...new Set(all.flatMap((m) => String(m.as_of).split(" · ")))].join(", ");
}, [section, id, level]);

// the length of the common start of two texts
export const commonStart = (a, b) => { let i = 0; while (i < a.length && a[i] === b[i]) i++; return i; };
