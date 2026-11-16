"use strict";
// Shared tooltip (docs/design.md, Tooltip): area and all visible overlays at the mouse point.

// Point in polygon or multipolygon. Holes: the point must lie in an odd number of rings.
APP.inPolygon = function (geometry, lng, lat) {
  const polygons = geometry.type === "Polygon" ? [geometry.coordinates] : geometry.type === "MultiPolygon" ? geometry.coordinates : [];
  return polygons.some((rings) => rings.reduce((n, r) => n + APP.inRing(r, lng, lat), 0) % 2 === 1);
};
// Properties of all features of a GeoJSON layer at the point. The bounds of each area filter first.
APP.featuresAt = function (layer, latlng) {
  const hits = [];
  layer.eachLayer((l) => {
    if (l.feature && l.getBounds().contains(latlng) && APP.inPolygon(l.feature.geometry, latlng.lng, latlng.lat)) hits.push(l.feature.properties);
  });
  return hits;
};
APP.areaAt = (latlng) => APP.featuresAt(APP.layers[APP.state.level], latlng)[0] || null;
// Grid row: [south, west, height, width, largest group, flag, ...counts per group]; the tooltip reads from the largest group on; the corners are integers (degrees
// x scale). Cells overlap at the edges by 1–2 m (rectangles from rotated EPSG:3035 cells): only the cell drawn last,
// that is the visible one.
APP.gridAt = (latlng) => {
  const k = APP.data.grid_cells.scale;
  return APP.data.grid_cells.rows
    .filter(([s, w, dn, de]) => s / k <= latlng.lat && latlng.lat <= (s + dn) / k && w / k <= latlng.lng && latlng.lng <= (w + de) / k)
    .slice(-1).map((z) => z.slice(4));
};
// One list of rows per visible overlay with a hit. Equal rows (overlapping equal zones) only once.
APP.hitsAt = function (latlng) {
  const list = [];
  for (const [name, u] of Object.entries(APP.overlays)) {
    if (!APP.map.hasLayer(u.layer)) continue;
    const rows = [...new Set((name === "grid" ? APP.gridAt(latlng) : APP.featuresAt(u.layer, latlng)).map(u.tip))];
    if (rows.length) list.push({ name, rows });
  }
  return list;
};

APP.tipHtml = function (latlng) {
  const p = APP.areaAt(latlng);
  const rows = APP.hitsAt(latlng).flatMap((t) => t.rows).map((z) => `<div>${z}</div>`).join("");
  if (!p) return rows || null;
  return APP.tooltipHead(p) + (rows ? `<div class="tip-overlays">${rows}</div>` : "");
};

// One tooltip follows the mouse. It is computed at most once per frame.
APP.tip = L.tooltip({ direction: "right", offset: [14, 0], className: "tip" });
APP.tipPoint = null;
APP.tipFrame = 0;
APP.hideTip = function () {
  APP.tipPoint = null;
  if (APP.map.hasLayer(APP.tip)) APP.map.closeTooltip(APP.tip);
};
// Stay fully inside the map at its edge: flip from right to left, move in vertically at the top and bottom.
// A narrow map (phone) has room on neither side: then the tooltip goes above the point, or below it, without its arrow.
// Leaflet places a "right" tooltip with its left edge at the point and centers it vertically; the offset moves it.
// Size straight from the container, so it is right after later layout changes too.
APP.placeTip = function () {
  const el = APP.tip.getElement(), c = APP.map.getContainer(), p = APP.map.latLngToContainerPoint(APP.tipPoint);
  const w = el.offsetWidth, h = el.offsetHeight, bottom = c.clientHeight - APP.panelHeight();
  // 14 px offset plus the 6 px margin Leaflet's CSS gives .leaflet-tooltip-right and -left
  const right = p.x + 20 + w <= c.clientWidth, left = !right && p.x - 20 - w >= 0;
  let x, top;
  if (right || left) {
    x = right ? 14 : -14;
    top = Math.min(Math.max(p.y - h / 2, 4), bottom - h - 4);
  } else {
    x = Math.min(Math.max(p.x - w / 2, 4), c.clientWidth - w - 4) - p.x - 6;
    top = p.y - 14 - h >= 4 ? p.y - 14 - h : Math.min(p.y + 14, bottom - h - 4);
  }
  el.classList.toggle("tip-free", !right && !left);
  APP.tip.options.direction = left ? "left" : "right";
  APP.tip.options.offset = [x, top - (p.y - h / 2)];
  APP.tip.update();
};
APP.showTip = function () {
  APP.tipFrame = 0;
  const html = APP.tipPoint && APP.tipHtml(APP.tipPoint);
  if (!html) return APP.hideTip();
  APP.tip.setLatLng(APP.tipPoint).setContent(html);
  if (!APP.map.hasLayer(APP.tip)) APP.map.openTooltip(APP.tip);
  APP.placeTip();
};
APP.map.on("mousemove", (e) => {
  if (e.originalEvent.target.closest(".leaflet-control")) return APP.hideTip(); // legend, zoom buttons
  APP.tipPoint = e.latlng;
  if (!APP.tipFrame) APP.tipFrame = requestAnimationFrame(APP.showTip);
});
// mouseleave on the container: the map event mouseout comes only over the canvas and is missing where no area lies.
L.DomEvent.on(APP.map.getContainer(), "mouseleave", APP.hideTip);
// Touch: a tap shows the tooltip at the point. It stays until the next tap or a move of the map.
APP.map.on("click", (e) => {
  APP.tipPoint = e.latlng;
  APP.showTip();
});
APP.map.on("movestart zoomstart", APP.hideTip);
// The button of a touch tooltip explores its area. The event stops here: the map would take it for a tap beside the area.
L.DomEvent.on(APP.map.getPane("tooltipPane"), "click", (e) => {
  const button = e.target.closest("[data-explore]");
  if (!button) return;
  L.DomEvent.stop(e);
  APP.hideTip();
  APP.explore(button.dataset.explore);
});
