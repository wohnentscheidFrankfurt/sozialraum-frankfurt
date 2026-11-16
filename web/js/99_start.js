"use strict";
APP.buildLayers();
if (APP.buildOverlays) APP.buildOverlays();
if (APP.buildCandidates) APP.buildCandidates();
APP.footer();
APP.renderProfile(); // the note, until a profile is chosen
// The map changes size even without a window change (footer, fonts loaded later): let Leaflet measure again
APP.map.invalidateSize();
new ResizeObserver(() => { APP.map.invalidateSize(); APP.updatePanel(); }).observe(APP.map.getContainer());
// the closed panel shows exactly its tab bar (--tabs), also when the bar changes height later (fonts)
const panelObserver = new ResizeObserver(APP.updatePanel);
panelObserver.observe(APP.sidebar);
panelObserver.observe(document.getElementById("tabs"));
document.querySelectorAll("#tabs button[data-tab]").forEach((b) => b.addEventListener("click", () => APP.openTab(b.dataset.tab)));
document.getElementById("panel-toggle").addEventListener("click", () => APP.setPanel(APP.sidebar.classList.contains("closed")));
document.querySelectorAll("#views button").forEach((b) => b.addEventListener("click", () => APP.openView(b.dataset.view)));
APP.draw();
// the phone starts with the panel closed: all of Frankfurt above the tab bar. Without animation: an animated fit would
// end after a map link has set its view, and take it back.
APP.setPanel(!APP.phone());
APP.fitCity(false);
// the start state, as a link: while the map equals it, a page without a map link gets none (APP.writeMapLink)
APP.startLink = APP.mapLink();
APP.map.on("moveend", APP.writeMapLink);
// a direct link opens its view and chart (docs/design.md, Direct links)
APP.followLink();
window.addEventListener("hashchange", APP.followLink);
APP.ready = true;
