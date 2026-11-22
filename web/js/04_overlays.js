"use strict";
APP.map.createPane("overlays-top").style.zIndex = 450;
APP.svg = L.svg({ pane: "overlays-top" });

// Overlays must stay visible on every layer colour: dark lines, a white casing and a pattern instead of a flat fill.
APP.MILIEU = "#1a1a1a";
APP.TOWNSCAPE = "#1d4f91";
APP.ROOF = "#5a3210";
APP.GAP = "#c51b7d"; // same tone as the ramp of GAP_AREA (pipeline/use_cases/building_gaps/catalog.py)
APP.insertPattern = function () {
  const svg = APP.svg._container;
  if (!svg || svg.querySelector("#hatch")) return;
  const defs = document.createElementNS("http://www.w3.org/2000/svg", "defs");
  defs.innerHTML = '<pattern id="hatch" patternUnits="userSpaceOnUse" width="8" height="8" patternTransform="rotate(45)">' +
    '<line x1="0" y1="0" x2="0" y2="8" stroke="#3a3a3a" stroke-width="2"/></pattern>' +
    `<pattern id="dots" patternUnits="userSpaceOnUse" width="11" height="11"><circle cx="5.5" cy="5.5" r="1.3" fill="${APP.TOWNSCAPE}"/></pattern>` +
    `<pattern id="roofs" patternUnits="userSpaceOnUse" width="5" height="5"><path d="M0 0L5 5M5 0L0 5" stroke="${APP.ROOF}" stroke-width="0.8" fill="none"/></pattern>`;
  svg.insertBefore(defs, svg.firstChild);
};
// Outline layer: SVG renderer (patterns need SVG), no mouse events; a white casing below it (u.casing).
APP.outline = (data, style) => L.geoJSON(data, { renderer: APP.svg, interactive: false, style });
APP.casing = (data, weight, dashArray) => APP.outline(data, { color: "#ffffff", weight: weight + 3, opacity: 0.9, fill: false, dashArray });

// Low flat roofs: a counted roof has a heavy dark brown outline and a brown cross-hatch, a roof that does not count only a
// thin brown outline. No flat fill and no dashes (dashes mean "im Verfahren"). Casing and line share the weights.
APP.roofWeight = (f) => (f.properties.counts ? 2 : 1);
APP.roofLayers = function () {
  const data = APP.data.flat_roofs;
  return {
    layer: L.geoJSON(data, { renderer: APP.svg, interactive: false,
      style: (f) => ({ color: APP.ROOF, weight: APP.roofWeight(f), opacity: 1, fill: f.properties.counts === 1, fillOpacity: 1, className: f.properties.counts ? "flat-roof" : "flat-roof-not" }) }),
    casing: L.geoJSON(data, { renderer: APP.svg, interactive: false,
      style: (f) => ({ color: "#ffffff", weight: APP.roofWeight(f) + 3, opacity: 0.9, fill: false }) }),
  };
};

// Overlays catch no mouse events (interactive: false): clicks reach the area below; 05_tooltip.js builds the tooltip.
APP.inRing = function (ring, lng, lat) {
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [xi, yi] = ring[i], [xj, yj] = ring[j];
    if ((yi > lat) !== (yj > lat) && lng < ((xj - xi) * (lat - yi)) / (yj - yi) + xi) inside = !inside;
  }
  return inside;
};

APP.roofs = APP.roofLayers();
// Building gaps: one look for every drawn parcel (counted and to check on site): a magenta outline on a white casing, no fill.
APP.gaps = { layer: APP.outline(APP.data.building_gaps, { color: APP.GAP, weight: 2.5, opacity: 1, fill: false, className: "building-gap" }),
  casing: APP.casing(APP.data.building_gaps, 2.5) };

APP.gridLayer = function () {
  const group = L.featureGroup();
  const k = APP.data.grid_cells.scale;
  for (const [s, w, dn, de, largest] of APP.data.grid_cells.rows) {
    const color = APP.ownershipById[APP.data.grid_groups[largest]].color;
    group.addLayer(L.rectangle([[s / k, w / k], [(s + dn) / k, (w + de) / k]], { stroke: false, fillColor: color, fillOpacity: 0.75, interactive: false }));
  }
  return group;
};

APP.townscapeTip = (p, info) => APP.t("overlays.townscape_tip", { tip: info.tip, title: APP.escape(p.title), since: info.since,
  date: APP.escape(p.date || APP.t("overlays.unknown_date")) });
// Grid tooltip (docs/data-rules.md, Level): the group with most dwellings (estimated, in the dative), then counted buildings 2022 per
// group, or counted dwellings 2011 where the cell has no owner in 2022 (flag 1); only the group is estimated
APP.gridTip = ([largest, flag, ...counts]) => `<div>${APP.escape(APP.t("overlays.grid_largest", { group: APP.data.grid_dative[APP.data.grid_groups[largest]] }))}</div>` +
  APP.escape(flag ? APP.t("overlays.grid_dwellings_2011") : APP.t("overlays.grid_buildings_2022")) + APP.data.grid_groups.map((g, i) =>
  (counts[i] > 0 ? `<div class="tip-indent">${APP.escape(APP.ownershipById[g].title)} ${APP.format(counts[i], 0)}</div>` : "")).join("");

// Title and tip prefix of each overlay come from the payload (pipeline/use_cases/protection and land catalog.py); the grid
// tip is built above, from the counts of the cell
APP.overlayInfo = APP.data.overlays;
APP.overlays = {
  social_preservation: { on: true,
    layer: APP.outline(APP.data.social_preservation, { color: APP.MILIEU, weight: 2.5, fillOpacity: 1, className: "social-preservation" }),
    casing: APP.casing(APP.data.social_preservation, 2.5), tip: (p) => APP.overlayInfo.social_preservation.tip + " " + APP.escape(p.title) },
  social_preservation_pending: { on: true,
    layer: APP.outline(APP.data.social_preservation_pending, { color: APP.MILIEU, weight: 2.5, dashArray: "6 4", fill: false }),
    casing: APP.casing(APP.data.social_preservation_pending, 2.5, "6 4"), tip: (p) => APP.overlayInfo.social_preservation_pending.tip + " " + APP.escape(p.title) },
  townscape: { on: false,
    layer: APP.outline(APP.data.townscape, { color: APP.TOWNSCAPE, weight: 3, fillOpacity: 1, className: "townscape" }),
    casing: APP.casing(APP.data.townscape, 3), tip: (p) => APP.townscapeTip(p, APP.overlayInfo.townscape) },
  townscape_pending: { on: false,
    layer: APP.outline(APP.data.townscape_pending, { color: APP.TOWNSCAPE, weight: 3, dashArray: "6 4", fill: false }),
    casing: APP.casing(APP.data.townscape_pending, 3, "6 4"), tip: (p) => APP.townscapeTip(p, APP.overlayInfo.townscape_pending) },
  pending_plans: { on: false, layer: L.geoJSON(APP.data.pending_plans, { renderer: APP.svg, interactive: false, style: { color: "#6a3d9a", weight: 2, fill: false } }),
    tip: (p) => APP.overlayInfo.pending_plans.tip + " " + APP.escape(p.title) },
  land_value: { on: false, layer: L.geoJSON(APP.data.land_value, {
    interactive: false, style: { color: "#7f7f7f", weight: 0.6, fillOpacity: 0 },
  }), tip: (p) => APP.t("overlays.land_value_tip", { tip: APP.overlayInfo.land_value.tip, value: APP.format(p.land_value, 0), use: APP.escape(p.use) }) },
  flat_roofs: { on: false, layer: APP.roofs.layer, casing: APP.roofs.casing, minZoom: 15, zoomNote: APP.t("overlays.zoom_flat_roofs"),
    tip: (p) => APP.overlayInfo.flat_roofs.tip + " " + APP.escape(p.text) },
  building_gaps: { on: false, layer: APP.gaps.layer, casing: APP.gaps.casing,
    tip: (p) => APP.overlayInfo.building_gaps.tip + " " + APP.escape(p.text) },
  grid: { on: false, layer: APP.gridLayer(), tip: APP.gridTip, minZoom: 14, zoomNote: APP.t("overlays.zoom_grid") },
};
for (const [name, u] of Object.entries(APP.overlays)) u.title = APP.overlayInfo[name].title;
// An overlay without features (no area, no grid row) has no checkbox, no ⓘ and no key row.
for (const [name, u] of Object.entries(APP.overlays)) {
  u.empty = name === "grid" ? APP.data.grid_cells.rows.length === 0 : APP.data[name].features.length === 0;
}
// minZoom: an overlay is drawn and keyed only from that zoom (the grid and the roofs are too dense below it).

// Swatches of the key: the same look as the lines on the map, on a 16 x 12 px box (.key-swatch).
APP.SWATCHES = {
  social_preservation: `border:1.5px solid ${APP.MILIEU};background:repeating-linear-gradient(45deg,#3a3a3a 0 2px,transparent 2px 5px)`,
  social_preservation_pending: `border:2px dashed ${APP.MILIEU}`,
  townscape: `border:2px dotted ${APP.TOWNSCAPE};background:radial-gradient(${APP.TOWNSCAPE} 1px,transparent 1.5px) 0 0/5px 5px`,
  townscape_pending: `border:2px dashed ${APP.TOWNSCAPE}`,
  pending_plans: "border:2px solid #6a3d9a",
  land_value: "border:1px solid #7f7f7f",
  flat_roofs: `border:2px solid ${APP.ROOF};background:repeating-linear-gradient(45deg,${APP.ROOF} 0 1px,transparent 1px 3px),repeating-linear-gradient(-45deg,${APP.ROOF} 0 1px,transparent 1px 3px)`,
  building_gaps: `border:2px solid ${APP.GAP}`,
  flat_roofs_not_counted: `border:1px solid ${APP.ROOF}`,
};
APP.overlayKey = function () {
  const swatch = (css) => `<span class="key-swatch" style="${css}"></span>`;
  return Object.entries(APP.overlays).filter(([, u]) => u.on && !u.empty).map(([name]) => {
    const u = APP.overlays[name];
    if (u.minZoom && APP.map.getZoom() < u.minZoom) return `<div class="key-row note">${APP.escape(u.zoomNote)}</div>`;
    if (name === "flat_roofs") return [["flat_roofs", "key"], ["flat_roofs_not_counted", "key_not_counted"]].map(([sw, k]) =>
      `<div class="key-row">${swatch(APP.SWATCHES[sw])}${APP.escape(APP.overlayInfo.flat_roofs[k])}</div>`).join("");
    if (name !== "grid") return `<div class="key-row">${swatch(APP.SWATCHES[name])}${APP.escape(APP.overlayInfo[name].key)}</div>`;
    return `<div class="key-row">` + APP.data.grid_groups.map((g) => `<span class="key-group">${swatch(`background:${APP.ownershipById[g].color}`)}` +
      `${APP.escape(APP.ownershipById[g].title)}</span>`).join(" ") + `</div>`;
  }).join("");
};

// Order to the front: last = on top. Only for the picture; overlays catch no pointer. The outlines lie in
// their own SVG pane above land values and grid; Milieuschutz lies above Ortsbild.
APP.FRONT = ["land_value", "grid", "flat_roofs", "building_gaps", "townscape", "townscape_pending", "pending_plans", "social_preservation", "social_preservation_pending"];

APP.updateOverlays = function () {
  for (const [name, u] of Object.entries(APP.overlays)) {
    const visible = u.on && APP.map.getZoom() >= (u.minZoom || 0);
    for (const layer of [u.casing, u.layer].filter(Boolean)) {
      if (visible && !APP.map.hasLayer(layer)) layer.addTo(APP.map);
      if (!visible && APP.map.hasLayer(layer)) APP.map.removeLayer(layer);
    }
  }
  for (const name of APP.FRONT) {
    const u = APP.overlays[name];
    if (!APP.map.hasLayer(u.layer)) continue;
    if (u.casing) u.casing.bringToFront();
    u.layer.bringToFront();
  }
  APP.insertPattern();
  const key = document.querySelector(".legend-overlays");
  if (key) key.innerHTML = APP.overlayKey();
};

// The one writer of `on`: the overlay, every checkbox of it, the key and the names of the details line follow
APP.setOverlay = function (name, on) {
  const u = APP.overlays[name];
  if (!u) return;
  u.on = on;
  document.querySelectorAll(`input[data-overlay="${name}"]`).forEach((box) => { box.checked = on; });
  APP.syncDetails();
  APP.updateOverlays();
  APP.writeMapLink();
};

// The short names of the overlays that are on and have features, in the order of APP.overlays: the title without a
// final look in brackets, so no text stands twice (docs/texts.md, Map: profile). Below its minimum zoom an overlay counts.
APP.overlayNames = () => Object.values(APP.overlays).filter((u) => u.on && !u.empty).map((u) => u.title.replace(/ \([^()]*\)$/, ""));

// The details line in „Gebiet“ (03_profile.js): its names follow every change without a redraw of the profile.
APP.syncDetails = function () {
  const names = document.querySelector("#tab-area .details-names");
  if (names) names.textContent = APP.overlayNames().join(", ");
};

APP.gridLegend = () => `<div class="grid-legend">` + APP.data.grid_groups.map((g) =>
  `<span><i style="background:${APP.ownershipById[g].color}"></i>${APP.escape(APP.ownershipById[g].title)}</span>`).join("") + `</div>`;

// The one builder of the overlay rows (no events): „Stadt“ uses the prefix "overlay-", the line in „Gebiet“
// "area-overlay-", so ⓘ ids stay unique.
APP.overlayRows = (prefix) => Object.entries(APP.overlays).filter(([, u]) => !u.empty).map(([name, u]) =>
  `<div class="layer-row"><label><input type="checkbox" data-overlay="${name}" ${u.on ? "checked" : ""}> ${APP.escape(u.title)}</label>` +
  `${APP.infoButton(prefix + name)}</div>` + APP.infoBlock(APP.data.overlays[name], prefix + name) +
  (name === "grid" ? APP.gridLegend() : "")).join("");

// One delegated listener on the sidebar serves every overlay checkbox, also those drawn later (the tab Gebiet).
APP.buildOverlays = function () {
  const el = document.getElementById("overlays");
  el.innerHTML = APP.overlayRows("overlay-");
  APP.sidebar.addEventListener("change", (e) => {
    const box = e.target.closest("input[data-overlay]");
    if (box) APP.setOverlay(box.dataset.overlay, box.checked);
  });
  APP.map.on("zoomend", APP.updateOverlays);
  APP.bindInfo(el); // buildLayers ran before, when the container was still empty: no double binding
};
