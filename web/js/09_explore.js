"use strict";
// Explore an area (docs/design.md, Exploring an area): a click focuses one area, the others turn grey. Legend
// and classes stay those of the whole city. The tab Stadt returns to the view before.
APP.overview = null; // { center, zoom } before exploring

// Touch input has no hover: a tap shows the tooltip, it does not explore
APP.touch = () => window.matchMedia("(hover: none), (pointer: coarse)").matches;

// The area of the level `toLevel` that stands for the area `id` of the level `fromLevel`; null if there is none
APP.areaFor = function (id, fromLevel, toLevel) {
  if (fromLevel === toLevel) return id;
  if (fromLevel === "district" && toLevel === "quarter") return APP.properties("district").find((p) => p.id === id)?.quarter ?? null;
  return null;
};

APP.styleExplore = function (p, style) {
  // the border of a full candidate hit stays, only heavier
  if (p.id === APP.state.area) return { ...style, weight: Math.max(3, style.weight), color: style.color === APP.data.hit_border ? style.color : "#000000" };
  return { ...style, fillColor: "#e8e8e8", fillOpacity: 0.6, color: "#bbbbbb", weight: 0.5, dashArray: null };
};

// The map flies to the area of the current level
APP.flyToArea = function (id) {
  let layer;
  APP.layers[APP.state.level].eachLayer((l) => { if (l.feature.properties.id === id) layer = l; });
  if (layer) APP.map.flyToBounds(layer.getBounds(), { maxZoom: 15, paddingBottomRight: [0, APP.panelHeight()], duration: 0.5 });
  return Boolean(layer);
};

// Also called while exploring (another area, or the same area on another level): then the view of before stays.
// A map link explores without the flight (fly: false keeps its own view) and leaves the phone panel as it is (panel: false).
APP.explore = function (id, { fly = true, panel = true } = {}) {
  if (APP.state.area === id) return;
  if (!APP.properties(APP.state.level).some((p) => p.id === id)) return;
  if (!APP.state.area) APP.overview = { center: APP.map.getCenter(), zoom: APP.map.getZoom() };
  APP.setState({ area: id });
  APP.openTab("area", { panel });
  if (fly) APP.flyToArea(id);
};

// A row of the profile shows its layer. A district row without the layer on its level moves to the Stadtteil (setState).
APP.chooseLayer = function (id) {
  const level = APP.state.level;
  APP.setState({ indicator: id, mode: "layer" });
  if (APP.state.area && APP.state.level !== level) {
    APP.flyToArea(APP.state.area);
    document.querySelector(`#tab-area [data-layer="${id}"]`)?.focus(); // the profile was drawn again
  }
};

APP.endExplore = function () {
  if (!APP.state.area) return;
  APP.setState({ area: null });
  if (APP.overview) APP.map.setView(APP.overview.center, APP.overview.zoom, { animate: false });
  APP.overview = null;
};
