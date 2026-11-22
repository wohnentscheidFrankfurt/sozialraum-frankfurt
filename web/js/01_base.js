"use strict";
const APP = (window.APP = {});
APP.data = JSON.parse(document.getElementById("data").textContent);
APP.meta = Object.fromEntries(APP.data.catalog.map((m) => [m.id, m]));
APP.listByName = Object.fromEntries(APP.data.lists.map((l) => [l.name, l]));
// Start: ABG and Nassauische Heimstätte per Stadtteil (pipeline/use_cases/public_housing/README.md)
// area: the explored area (09_explore.js), an id of the current level, or null
APP.state = { level: "quarter", indicator: "OWN_PUBLIC", mode: "layer", area: null, profile: null }; // profile: { id, level } of the area the user chose
APP.breaks = [];
// Ramp of an indicator: five colours from almost white to its colour, finished in Python (pipeline/shared/core/colours.py).
APP.rampFor = (m) => m.colors;

// The texts of the map in its language (pipeline/map/html/texts.<lang>.yaml, section ui): APP.t("legend.city", { value })
// fills {value}. A missing key or a missing value throws, so a browser test finds it.
APP.t = function (key, values = {}) {
  const text = key.split(".").reduce((node, part) => (node == null ? undefined : node[part]), APP.data.ui);
  if (typeof text !== "string") throw new Error(`no text ui.${key} (${APP.data.lang})`);
  return text.replace(/\{(\w+)\}/g, (_, name) => {
    if (!(name in values)) throw new Error(`no value {${name}} for the text ui.${key}`);
    return String(values[name]);
  });
};

APP.LOCALES = { de: "de-DE", en: "en-GB" };
APP.format = function (value, decimals) {
  if (value == null || Number.isNaN(value)) return APP.t("no_data");
  return Number(value).toLocaleString(APP.LOCALES[APP.data.lang], { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
};
// A number text and its unit as format_number writes them (pipeline/shared/core/numbers.py): de „18,4 %“ and
// „1.200 €“, en „18.4%“ and „€1,200“; other units follow the number after a space. Without a unit the text stays.
APP.attachUnit = function (text, unit) {
  if (!unit) return text;
  if (APP.data.lang !== "de" && unit === "%") return `${text}%`;
  if (APP.data.lang !== "de" && unit === "€") return `€${text}`;
  return `${text} ${unit}`;
};
// A number and its "%" stay on one line: a no-break space between them (an iPhone SE broke "19 %").
// It is tied to the number format of the language (APP.attachUnit, format_number in pipeline/shared/core/numbers.py):
// German writes "19 %", so the space turns into a no-break space; English writes "19%" and "€1,200" with no space,
// so nothing changes. A language with a space before another unit needs that unit here too.
APP.keepUnits = (text) => text.replace(/(\d) %/g, "$1\u00a0%");
// With the properties p of an area: a printed class shows as in the report ("64–70 %"; "29–29" as "29 %").
// No range at an estimate (docs/texts.md, Numbers); the tilde comes from APP.valueText.
APP.withUnit = function (id, value, p) {
  const m = APP.meta[id];
  const lower = p ? p[id + "_LOWER"] : null;
  if (m && lower != null && value != null && lower !== value) return `${APP.format(lower, m.decimals)}–${APP.withUnit(id, value)}`;
  if (!m) return APP.format(value, 1);
  if (m.type === "yes_no") return value === 1 ? APP.t("answer_yes") : value === 0 ? APP.t("answer_no") : APP.t("no_data");
  if (m.type === "category") return value || APP.t("no_data");
  const text = APP.format(value, m.decimals);
  return value == null ? text : APP.attachUnit(text, m.unit);
};
// A single value as the reader sees it: an estimate starts with a tilde ("~17,8 %"). Legend classes, the CSV and the
// thresholds of the candidates use withUnit without it.
APP.valueText = function (id, value, p) {
  const m = APP.meta[id], text = APP.withUnit(id, value, p);
  return m && m.estimate && value != null ? "~" + text : text;
};
// The value as the map shows it, rounded half up to the decimals of the indicator. Colour, legend, tooltip, candidates and
// histogram all compare this value, so what the reader sees is what counts (pipeline/use_cases/candidates/model.py `shown`
// does the same). A rank (m.rank > 0) is not rounded: a tie keeps its .5.
// Math.round rounds half up, like Python's `shown`. Intl formatting (APP.format) may differ on exact decimal halves only;
// the stored values never sit on one (they carry more decimals than the map shows).
APP.shown = (x, decimals) => (x == null || Number.isNaN(x) || typeof decimals !== "number" ? x : Math.round(x * 10 ** decimals) / 10 ** decimals);
APP.shownOf = function (id, x) {
  const m = APP.meta[id];
  return m && !(m.rank > 0) && (m.type === "number" || m.type === "yes_no") ? APP.shown(x, m.decimals) : x;
};
// A threshold or value as text without unit, at the decimals the map shows. A rank is not rounded: it reads „44“ or „44,5“.
APP.shownText = function (id, x) {
  const m = APP.meta[id];
  if (m && m.rank > 0) return APP.format(x, Number.isInteger(x) ? 0 : 1);
  return APP.format(APP.shownOf(id, x), m ? m.decimals : 1);
};
// The slider of a rank moves in steps of 0.5 (a tie keeps its .5), so label and comparison agree
APP.snapThreshold = (id, x) => (x != null && APP.meta[id]?.rank > 0 ? Math.round(x * 2) / 2 : x);
// The label of a threshold in the own query
APP.thresholdLabel = (id, x) => (APP.meta[id]?.rank > 0 ? APP.shownText(id, x) : APP.withUnit(id, x));
// The districts that share the value of the area p for the indicator id, as „202, 203 und 213“; null if it is its own
APP.sharedList = (p, id) => p[id + "_SHARED"] || null;
APP.escape = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
// Class breaks as quantiles. Empty classes are dropped, breaks with the same display text are merged.
// If the first quantile break is already 0 (more than every fifth value is 0), 0 gets its own class
// (zeroClass): breaks[0] is then the smallest value above 0, the class before it holds only 0.
APP.classify = function (values, n = 5, decimals = 1) {
  const v = values.filter((x) => x != null && !Number.isNaN(x)).sort((a, b) => a - b);
  if (!v.length) return { breaks: [], zeroClass: false };
  const cuts = (w, k, before) => {
    const raw = [];
    for (let i = 1; i < k; i++) raw.push(w[Math.min(w.length - 1, Math.floor((i * w.length) / k))]);
    const out = [];
    let last = before;
    for (const g of raw) {
      const text = APP.format(g, decimals);
      if (g <= w[0] || text === last) continue;
      out.push(g);
      last = text;
    }
    return out;
  };
  const zeroClass = v[Math.floor(v.length / n)] === 0;
  if (!zeroClass) return { breaks: cuts(v, n, null), zeroClass };
  const positive = v.filter((x) => x > 0);
  if (!positive.length) return { breaks: [], zeroClass: false };
  return { breaks: [positive[0], ...cuts(positive, n - 1, APP.format(0, decimals))], zeroClass };
};
// Rank legend: a class names the ranks it holds, „Rang 1 bis 23“; a tie x,5 widens to its neighbours, one rank reads „Rang 7“
APP.rankClassText = function (i) {
  const inClass = APP.classValues.filter((x) => x != null && APP.classOf(x, APP.breaks) === i);
  const a = Math.floor(Math.min(...inClass)), b = Math.ceil(Math.max(...inClass));
  return a === b ? APP.t("rank.one", { rank: a }) : APP.t("rank.range", { from: a, to: b });
};
// Printed classes (at most 4) skip the lightest step, so the first class stays apart from the white of no data
APP.rampOffset = () => (APP.upperClosed ? 1 : 0);

// upperClosed: printed classes of a report (type classes); the upper end of a class belongs to it
APP.classOf = function (x, breaks, upperClosed = false) {
  let i = 0;
  while (i < breaks.length && (upperClosed ? x > breaks[i] : x >= breaks[i])) i++;
  return i;
};
APP.COLLECTIONS = { district: "districts", quarter: "quarters" };
APP.LEVEL_NAMES = { district: APP.t("levels.districts"), quarter: APP.t("levels.quarters") };
APP.LEVEL_SINGULAR = { district: APP.t("levels.district"), quarter: APP.t("levels.quarter") };
// the labels of the level choice; the words above stand inside sentences, where English writes them in lower case
APP.LEVEL_CHOICE = { district: APP.t("levels.choice.district"), quarter: APP.t("levels.choice.quarter") };
APP.properties = (level) => APP.data[APP.COLLECTIONS[level]].features.map((f) => f.properties);
// First layer of a level in catalog order: OWN_PUBLIC for quarters, SOC_MIN_INCOME for districts
APP.firstIndicator = (level) => APP.data.catalog.find((m) => m.layer && m.levels.includes(level)).id;

APP.map = L.map("map", { preferCanvas: true, zoomSnap: 0.5 }).setView([50.12, 8.68], 11);
// All of Frankfurt above the phone panel. The start fit does not animate (99_start.js), the button does.
APP.fitCity = (animate = true) => APP.map.fitBounds(APP.layers.district.getBounds(), { paddingBottomRight: [0, APP.panelHeight()], animate });
// Third button of the zoom control, between + and −: a button, not a link, so the address bar keeps the map link
(() => {
  const reset = L.DomUtil.create("button", "zoom-reset");
  reset.type = "button";
  reset.setAttribute("aria-label", APP.t("zoom_reset"));
  reset.title = APP.t("zoom_reset");
  reset.innerHTML = '<svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 5V1h4M11 1h4v4M15 11v4h-4M5 15H1v-4"/></svg>';
  L.DomEvent.disableClickPropagation(reset);
  L.DomEvent.on(reset, "click", () => APP.fitCity());
  APP.map.zoomControl._container.insertBefore(reset, APP.map.zoomControl._zoomOutButton);
})();
// basemap.de grey (BKG, CC BY 4.0, no key). Note the order {z}/{y}/{x}
// Over http(s) the website proxies the tiles, so the BKG sees no visitor (docs/architecture.md). The file keeps BKG.
APP.tileUrl = (protocol) => protocol === "file:"
  ? "https://sgx.geodatenzentrum.de/wmts_basemapde/tile/1.0.0/de_basemapde_web_raster_grau/default/GLOBAL_WEBMERCATOR/{z}/{y}/{x}.png"
  : "/sozialraum-frankfurt/kacheln/{z}/{y}/{x}.png";
APP.background = L.tileLayer(APP.tileUrl(location.protocol), {
  maxZoom: 19, maxNativeZoom: 18, attribution: '© <a href="https://basemap.de">basemap.de</a> / BKG (CC BY 4.0)',
}).addTo(APP.map);

// Style of an area; while one is explored, the others turn grey (09_explore.js)
APP.style = function (feature) {
  const style = APP.styleBase(feature);
  return APP.state.area && APP.styleExplore ? APP.styleExplore(feature.properties, style) : style;
};
APP.styleBase = function (feature) {
  const p = feature.properties;
  const base = { weight: 0.8, color: "#555", opacity: 1, fillOpacity: 0.75, dashArray: null };
  // Small districts: shares are unsure. A survey class belongs to the whole survey area and stays coloured.
  if (APP.state.level === "district" && p.small && APP.meta[APP.state.indicator].type !== "classes") return { ...base, fillColor: "#d0d0d0", dashArray: "2 3" };
  if (APP.state.mode === "candidates" && APP.styleCandidates) return APP.styleCandidates(p, base);
  const id = APP.state.indicator;
  const m = APP.meta[id];
  if (m.type === "category") {
    const list = APP.listByName[p[id]];
    return { ...base, fillColor: list ? list.color : "#cccccc" };
  }
  const x = m.type === "number" ? APP.shownOf(id, p[id]) : p[id];
  if (x == null) return { ...base, fillColor: "#ffffff", fillOpacity: 0.3 };
  const ramp = APP.rampFor(m);
  return { ...base, fillColor: ramp[Math.min(ramp.length - 1, APP.classOf(x, APP.breaks, APP.upperClosed) + APP.rampOffset())] };
};

// 13 district names stand for 55 districts. The label of a district carries its number: "Bockenheim (Bezirk 343)".
// With withQuarter it names the quarter too, where the name does not contain it: "Osthafen (Bezirk 70, Ostend)"
// (docs/texts.md, Area names). Quarters stay as they are. The one place for this label.
APP.areaLabel = function (p, level, withQuarter = false) {
  if (level !== "district") return APP.escape(p.name);
  const parts = [APP.escape(APP.t("district_number", { id: p.id }))];
  if (withQuarter && p.quarter && !p.name.includes(p.quarter)) parts.push(APP.escape(p.quarter));
  return `${APP.escape(p.name)} (${parts.join(", ")})`;
};
// Local council election on the same day: legend and tooltip name the election shown
APP.titleWithElection = (m) => (m.section === "election" ? APP.t("election_title", { title: m.title }) : m.title);

// Dwellings per owner group and Stadtteil (pipeline/use_cases/ownership_shares/README.md), an estimate with a tilde
// (docs/data-rules.md, Counts of an estimate). The pipeline gives them unrounded; rounding happens only here: under 200
// without a number, else to 50. Where the upper end lies more than a third above the value, no number is shown.
APP.roundTo50 = (x) => 50 * Math.round(x / 50);
APP.dwellingsText = function (value, high) {
  if (value == null || high == null) return APP.t("no_data");
  if (high < 200) return APP.t("count.under", { count: 200 });
  if (high - value <= value / 3) return "~" + APP.format(APP.roundTo50(value), 0);
  return APP.t("count.uncertain");
};

// Head of the shared tooltip (05_tooltip.js): area in bold, below it the indicator with its value or the criteria met.
// An owner group adds its count of dwellings (docs/texts.md, Map: tooltip): hover and tap both show it.
// On touch, the button below explores the area (05_tooltip.js listens); the explored area has none.
APP.tooltipHead = function (p) {
  const button = APP.touch() && p.id !== APP.state.area ? `<button type="button" class="tip-explore" data-explore="${APP.escape(p.id)}">${APP.escape(APP.t("tooltip.explore"))}</button>` : "";
  return APP.tooltipText(p) + button;
};
// A rank reads „Rang 46 von 114“; a tie (x,5) reads „Rang 23 bis 24 von 114“. The total is the number of ranks of the
// indicator (catalog `rank`); without it the areas of `level` with a value are counted (the profile can show an area of
// another level than the map).
APP.rankText = function (id, value, level = APP.state.level) {
  const ranks = APP.meta[id]?.rank;
  const total = ranks > 1 ? ranks : APP.properties(level).filter((p) => p[id] != null).length;
  return Number.isInteger(value) ? APP.t("rank.one_of", { rank: value, count: total })
    : APP.t("rank.range_of", { from: value - 0.5, to: value + 0.5, count: total });
};
// The coverage only where it matters (under 90 %); used by the tooltip and the profile
APP.coverageText = (p) => p.COV_OWN != null && Math.round(p.COV_OWN) < 90 ? APP.t("tooltip.coverage", { share: APP.attachUnit(APP.format(p.COV_OWN, 0), "%") }) : "";
// A count without a layer stands in the tooltip of its share, in a line of its own (catalog: count_of;
// docs/texts.md, Map: tooltip)
APP.countFor = (m) => APP.data.catalog.find((c) => c.count_of === m.id);
// Counts with a step in the catalog (round_to): small exact numbers would look more exact than the grid, which changes
// them for secrecy (pipeline/use_cases/construction_year/README.md). The pipeline keeps the exact value.
// A count of an estimate carries the tilde like its share ("~1.240"); "unter 10" has none.
APP.roundedCount = (x, step, estimate = false) => (x == null ? APP.t("no_data") : x < step ? APP.t("count.under", { count: step }) : (estimate ? "~" : "") + APP.format(step * Math.round(x / step), 0));
// „Wohnungen: 1.754“, „Wählende: 1.343 von 2.871“ (count_total); "" without the share or the count
APP.countLine = function (m, p) {
  const c = APP.countFor(m), x = c ? p[c.id] : null;
  if (x == null || p[m.id] == null) return "";
  const number = c.round_to ? APP.roundedCount(x, c.round_to, !!c.estimate) : (c.estimate ? "~" : "") + APP.format(x, 0);
  if (c.count_total && p[c.count_total] != null) return APP.t("count.line_of", { unit: c.unit, number, total: APP.format(p[c.count_total], 0) });
  return APP.t("count.line", { unit: c.unit, number });
};
// The values of a layer that has no layer of its own (catalog: breakdown_of), in catalog order
APP.breakdownFor = (m) => APP.data.catalog.filter((c) => c.breakdown_of === m.id);
// „<br>Nach Haushaltsnettoeinkommen:“ and a line „<br>unter 2.000 €: ~55 %“ per value; "" without values
APP.breakdownLines = function (m, p) {
  const entries = APP.breakdownFor(m);
  return entries.length ? `<br>${APP.escape(m.breakdown_lead)}:` + entries.map((c) => `<br>${APP.escape(c.title)}: ${APP.escape(APP.valueText(c.id, p[c.id], p))}`).join("") : "";
};
APP.tooltipText = function (p) {
  const name = APP.areaLabel(p, APP.state.level);
  if (APP.state.mode === "candidates" && APP.evaluationById) {
    const b = APP.evaluationById[p.id];
    const line = APP.candidateLine(b, APP.activeCriteria().length);
    return `<strong>${name}</strong>${line ? "<br>" + APP.escape(line) : ""}`;
  }
  const id = APP.state.indicator;
  // only owner groups: the construction-year and vacancy layers carry a _DWELLINGS count of their own
  const count = APP.meta[id].section === "ownership" && id + "_DWELLINGS" in p ? `<br>${APP.escape(APP.t("tooltip.dwellings", { count: APP.dwellingsText(p[id + "_DWELLINGS"], p[id + "_DWELLINGS_HIGH"]) }))}` : "";
  const coverage = APP.meta[id].section === "ownership" && APP.coverageText(p) ? `<br>${APP.coverageText(p)}` : "";
  const m = APP.meta[id];
  const value = m.rank && p[id] != null ? APP.rankText(id, p[id]) : APP.valueText(id, p[id], p);
  const area = m.survey_area && p.survey_area ? " " + APP.escape(APP.t("tooltip.survey_area", { name: p.survey_area })) : "";
  // a value the Monitoring publishes for several districts says so (the value is not that of this district alone)
  const list = p[id] != null ? APP.sharedList(p, id) : null;
  const shared = list ? " " + APP.escape(APP.t("tooltip.shared", { list })) : "";
  // the count of the indicator in a line of its own, under the value (catalog: count_of)
  const line = APP.countLine(m, p), counted = line ? `<br>${APP.escape(line)}` : "";
  return `<strong>${name}</strong><br>${APP.escape(APP.titleWithElection(m))}: ${APP.escape(value)}${shared}${area}${counted}${count}${coverage}${APP.breakdownLines(m, p)}`;
};

APP.layers = {};
for (const level of Object.keys(APP.COLLECTIONS)) {
  APP.layers[level] = L.geoJSON(APP.data[APP.COLLECTIONS[level]], {
    style: (f) => APP.style(f),
    onEachFeature: (f, layer) => {
      // mouse: a click explores the area. Touch: a tap shows the tooltip, with the button that explores. Until then the
      // profile follows the tap; while exploring, profile and focus stay on the explored area.
      layer.on("click", () => {
        if (!APP.touch()) APP.explore(f.properties.id);
        else if (!APP.state.area) APP.showProfile(f.properties.id, false);
      });
    },
  });
}

APP.draw = function () {
  const level = APP.state.level;
  const id = APP.state.indicator, m = APP.meta[id];
  // the classes are made of the values as shown (decimals of the indicator), so a legend limit and a tooltip agree.
  // A rank has ties of .5 and is not rounded; one decimal keeps them apart in the classes.
  const values = APP.properties(level).filter((p) => !(level === "district" && p.small)).map((p) => APP.shownOf(id, p[id]));
  APP.classValues = values;
  const classes = m.type === "number" ? APP.classify(values, 5, m.rank > 0 ? 1 : m.decimals) : { breaks: [], zeroClass: false };
  // Printed classes of a report (type classes): taken from the data, the upper end decides the colour
  APP.upperClosed = APP.meta[id].type === "classes";
  APP.printedClasses = APP.upperClosed ? [...new Map(APP.properties(level).filter((p) => p[id] != null)
    .map((p) => [p[id], p[id + "_LOWER"]])).entries()].sort((a, b) => a[0] - b[0]).map(([upper, lower]) => [lower, upper]) : [];
  APP.breaks = APP.upperClosed ? APP.printedClasses.slice(0, -1).map((c) => c[1]) : classes.breaks;
  APP.zeroClass = APP.upperClosed ? false : classes.zeroClass;
  for (const [e, layer] of Object.entries(APP.layers)) {
    if (e === level) {
      if (!APP.map.hasLayer(layer)) layer.addTo(APP.map);
      layer.setStyle((f) => APP.style(f));
      // the explored area lies on top, so its outline is not covered by the grey neighbours
      if (APP.state.area) layer.eachLayer((l) => { if (l.feature.properties.id === APP.state.area) l.bringToFront(); });
    } else if (APP.map.hasLayer(layer)) {
      APP.map.removeLayer(layer);
    }
  }
  APP.legend();
  APP.syncSwitch();
  if (APP.updateOverlays) APP.updateOverlays();
  // the bar of the pressed row takes the class of the new breaks (03_profile.js)
  if (APP.syncProfile) APP.syncProfile();
};

APP.legendControl = L.control({ position: "bottomright" });
// On the phone the legend starts collapsed; a tap opens and closes it (CSS shows the body only with .open)
APP.legendControl.onAdd = () => {
  const div = (APP.legendDiv = L.DomUtil.create("div", "legend"));
  L.DomEvent.disableClickPropagation(div);
  L.DomEvent.disableScrollPropagation(div);
  div.addEventListener("click", () => div.classList.toggle("open"));
  return div;
};
APP.legendControl.addTo(APP.map);
// The silent change of the layer after a click on the level: one line above the legend (added second, so it stands on top)
APP.switchNote = null;
APP.switchControl = L.control({ position: "bottomright" });
APP.switchControl.onAdd = () => {
  const div = (APP.switchDiv = L.DomUtil.create("div", "legend-switch"));
  div.setAttribute("role", "status");
  L.DomEvent.disableClickPropagation(div);
  return div;
};
APP.switchControl.addTo(APP.map);
APP.syncSwitch = function () {
  const note = APP.state.mode === "candidates" ? null : APP.switchNote;
  APP.switchDiv.textContent = note || "";
  APP.switchDiv.hidden = !note;
  if (APP.updatePanel) APP.updatePanel();
};
// Title, note and body apart: the phone layout collapses the body, the note stays under the title (no note: no line).
// The second note line (detail) is the first child of the body, so the collapsed legend stays title plus note.
APP.legendHtml = (title, body, note = "", detail = "") => `<strong class="legend-title">${APP.escape(title)}</strong>` +
  (note ? `<span class="legend-note">${APP.escape(note)}</span>` : "") +
  `<div class="legend-body">${detail ? `<span class="legend-detail">${APP.escape(detail)}</span>` : ""}${body}</div>`;
// What the current map shows, so the legend lists only rows that exist: a white area, the strongest lists, a small district
APP.anyWhite = () => APP.layers[APP.state.level].getLayers().some((l) => APP.styleBase(l.feature).fillColor === "#ffffff");
APP.strongestLists = () => APP.data.lists.filter((l) => l.position > 0 && APP.properties(APP.state.level).some((p) => p.ELEC_STRONGEST === l.name));
APP.anySmall = () => APP.properties("district").some((p) => p.small);
// The key of the visible overlays closes the body of the legend; 04_overlays.js fills it and refreshes it on zoom and checkboxes
APP.overlayKeyHtml = () => `<div class="legend-overlays">${APP.overlayKey ? APP.overlayKey() : ""}</div>`;
APP.legend = function () {
  const div = APP.legendDiv;
  if (APP.state.mode === "candidates" && APP.legendCandidates) return APP.legendCandidates(div);
  const id = APP.state.indicator;
  const m = APP.meta[id];
  let h = "";
  if (m.type === "category") {
    h += APP.strongestLists().map((l) => `<i style="background:${l.color}"></i>${APP.escape(l.name)}`).join("<br>") + "<br>";
  } else {
    const ramp = APP.rampFor(m);
    const g = APP.breaks;
    // a count layer names its unit once per class, after the upper bound
    const count = m.criterion === false;
    const lower = (x) => APP.format(x, m.decimals);
    const bound = (x) => count ? APP.attachUnit(lower(x), m.unit) : APP.withUnit(id, x);
    const zero = APP.attachUnit("0", m.unit);
    const zeroLabel = m.unit === "%" ? APP.t("legend.none", { value: zero }) : zero;
    for (let i = 0; i <= g.length; i++) {
      let text;
      if (!g.length && !APP.upperClosed) text = APP.t("legend.all_values");
      else if (m.rank > 0) text = APP.rankClassText(i);
      else if (APP.upperClosed) text = APP.withUnit(id, APP.printedClasses[i][1], { [id + "_LOWER"]: APP.printedClasses[i][0] });
      else if (APP.zeroClass && i === 0) text = zeroLabel;
      else if (APP.zeroClass && i === 1) {
        text = g.length > 1 ? APP.t("legend.above_zero_below", { zero: count ? "0" : zero, to: bound(g[1]) }) : APP.t("legend.above_zero", { zero });
      } else if (i === 0) text = APP.t("legend.below", { to: bound(g[0]) });
      else if (i === g.length) text = APP.t("legend.from", { from: bound(g[i - 1]) });
      else text = APP.t("legend.range", { from: count ? lower(g[i - 1]) : APP.withUnit(id, g[i - 1]), to: bound(g[i]) });
      h += `<i style="background:${ramp[i + APP.rampOffset()]}"></i>${APP.escape(text)}<br>`;
    }
    if (APP.anyWhite()) h += `<i style="background:#ffffff"></i>${APP.escape(APP.t("no_data"))}<br>`;
    const cityValue = APP.data.city_values[id];
    // Counts (criterion false) and the rank SOC_INDEX have no city value
    if (m.criterion !== false && cityValue != null) h += `${APP.escape(APP.t("legend.city", { value: APP.valueText(id, cityValue) }))}<br>`;
  }
  if (m.section === "election") h += `<strong>${APP.escape(APP.t("areas_not_people"))}</strong>`;
  div.innerHTML = APP.legendHtml(APP.titleWithElection(m), h + APP.overlayKeyHtml(), m.legend_note, m.legend_detail);
};

// ⓘ of an indicator or overlay: button and collapsible result protocol (docs/texts.md, ⓘ protocol). Lines without
// text are left out. The key makes the id unique. Each label stands above its value; in Quelle and Stand, parts joined
// by " · " (several sources or dates) get a line each (docs/texts.md, ⓘ protocol).
APP.SPLIT_PARTS = ["source", "as_of"];
APP.infoButton = (key) => `<button class="info-button" data-info="${key}" aria-expanded="false" aria-controls="info-${key}" ` +
  `title="${APP.escape(APP.t("info.button"))}" aria-label="${APP.escape(APP.t("info.button"))}">ⓘ</button>`;
APP.PROTOCOL = [["source", APP.t("info.source")], ["as_of", APP.t("info.as_of")], ["calc", APP.t("info.calc")],
  ["rule", APP.t("info.rule")], ["uncertainty", APP.t("info.uncertainty")]];
// Worked example (ex: m.calc_example, or one of m.calc_examples): a written sum, one row per step. A row with `total`
// stands under a line. Its label is „Rechnung am Beispiel <area>“, or its own `label` where an ⓘ has several sums.
APP.calcExampleHtml = function (ex) {
  const label = ex.label || APP.t("info.example", { area: ex.area });
  const rows = ex.rows.map((r, i) => {
    const number = (r.estimate ? "~" : "") + APP.attachUnit(APP.format(r.number, r.decimals), r.unit);
    const shown = i === ex.rows.length - 1 ? `<span class="result">${APP.escape(number)}</span>` : APP.escape(number);
    return (r.total ? `<span class="rule"></span><span></span>` : "") + `<span class="op">${APP.escape(r.op)}</span><span class="n">${shown}</span>` +
      `<span class="what${r.total && r.text ? " sub" : ""}">${APP.escape(r.text)}</span>`;
  }).join("");
  return { label, html: `<div class="sum" role="group" aria-label="${APP.escape(label)}">${rows}</div>` };
};
// The entries of the protocol as [label, html]. An indicator with a prose calc and a worked example gets both:
// "Rechnung" with the prose, then the sum under its own label. With only the example, it is the whole Rechnung. The
// ⓘ of a chart view may carry several sums (m.calc_examples), each under its label.
APP.infoEntries = (m) => APP.PROTOCOL.flatMap(([k, label]) => {
  const prose = m[k] ? [[label, (APP.SPLIT_PARTS.includes(k) ? String(m[k]).split(" · ") : [String(m[k])]).map((part) => `<span>${APP.escape(part)}</span>`).join("")]] : [];
  const examples = m.calc_examples || (m.calc_example ? [m.calc_example] : []);
  if (k !== "calc") return prose;
  return [...prose, ...examples.map((ex) => { const e = APP.calcExampleHtml(ex); return [e.label, e.html]; })];
});
APP.infoBlock = (m, key) => `<div class="info" id="info-${key}" hidden><dl>` +
  APP.infoEntries(m).map(([label, html]) => `<dt>${APP.escape(label)}</dt><dd>${html}</dd>`).join("") + `</dl></div>`;
APP.bindInfo = function (el) {
  el.querySelectorAll(".info-button").forEach((b) => b.addEventListener("click", () => {
    const info = document.getElementById("info-" + b.dataset.info);
    info.hidden = !info.hidden;
    b.setAttribute("aria-expanded", String(!info.hidden));
  }));
};

APP.layerRow = function (m) {
  return `<div class="layer-row"><label data-id="${m.id}"><input type="radio" name="indicator" value="${m.id}"> ${APP.escape(m.title)}<span class="only-level"></span></label>` +
    `${APP.infoButton(m.id)}</div>` + APP.infoBlock(m, m.id);
};

// the heading of the overlays in „Stadt“ and of the details line in „Gebiet“ (03_profile.js)
APP.OVERLAY_HEADING = APP.t("layers.details");

APP.buildLayers = function () {
  const el = document.getElementById("tab-city");
  const groups = []; // the first layer of each group stands for it: heading `group`, logic `section`
  for (const m of APP.data.catalog) if (m.layer && !groups.some((x) => x.section === m.section)) groups.push(m);
  let h = `<h3>${APP.escape(APP.t("layers.level"))}</h3><div class="choice">` + Object.keys(APP.COLLECTIONS).map((e) =>
    `<label><input type="radio" name="level" value="${e}"> ${APP.LEVEL_CHOICE[e]} (${APP.properties(e).length})</label>`).join("") + `</div>`;
  for (const g of groups) {
    h += `<h3>${APP.escape(g.group)}</h3><div class="choice">`;
    if (g.section === "election") {
      h += APP.data.election_layers.map((id) => APP.layerRow(APP.meta[id])).join("");
      h += `<div class="layer-row"><label data-id="ELEC_LIST"><input type="radio" name="indicator" value="ELEC_LIST"> ${APP.escape(APP.t("layers.list_share"))}<span class="only-level"></span></label>` +
        `<select id="list-choice">${APP.data.lists.map((l) => `<option value="${l.key}">${APP.escape(l.name)}</option>`).join("")}</select></div>`;
    } else {
      h += APP.data.catalog.filter((m) => m.layer && m.section === g.section).map(APP.layerRow).join("");
    }
    h += "</div>";
  }
  h += `<h3>${APP.OVERLAY_HEADING}</h3><div id="overlays" class="choice"></div>`;
  el.innerHTML = h;
  el.querySelectorAll('input[name="level"]').forEach((r) => r.addEventListener("change", () => APP.setLevel(r.value)));
  el.querySelectorAll('input[name="indicator"]').forEach((r) => r.addEventListener("change", () => APP.setIndicator(r.value === "ELEC_LIST" ? document.getElementById("list-choice").value : r.value)));
  document.getElementById("list-choice").addEventListener("change", (e) => APP.setIndicator(e.target.value));
  APP.bindInfo(el);
  APP.syncLayers();
};

APP.syncLayers = function () {
  const el = document.getElementById("tab-city");
  if (!el) return;
  el.querySelectorAll('input[name="level"]').forEach((r) => (r.checked = r.value === APP.state.level));
  const listChoice = APP.state.indicator.startsWith("ELEC_") && !APP.data.election_layers.includes(APP.state.indicator);
  el.querySelectorAll('input[name="indicator"]').forEach((r) => {
    r.checked = listChoice ? r.value === "ELEC_LIST" : r.value === APP.state.indicator;
    // the row of the list share takes the meta of the chosen list, so it greys like the other election rows
    const m = APP.meta[r.value === "ELEC_LIST" ? document.getElementById("list-choice").value : r.value];
    const off = Boolean(m) && !m.levels.includes(APP.state.level);
    const label = r.closest("label");
    label.classList.toggle("off", off);
    label.querySelector(".only-level").textContent = off ? " " + APP.t("layers.only", { levels: APP.LEVEL_NAMES[m.levels[0]] }) : "";
  });
  if (listChoice) document.getElementById("list-choice").value = APP.state.indicator;
};

// The one place that changes level, indicator and mode. A patch holds what the user changed. When the indicator is not
// on the level, what the user changed wins: a new level takes its first layer, a new indicator its first level.
// The candidates show the level of their template and keep the layer, even one their level lacks. Back in the city tab,
// a layer gets its own level again, or the first level of the layer.
// The area whose profile the tab Gebiet shows: the chosen area on the current level; null if none fits
APP.profileId = () => (APP.state.profile ? APP.areaFor(APP.state.profile.id, APP.state.profile.level, APP.state.level) : null);

APP.setState = function (patch, draw = true) {
  const s = APP.state, oldLevel = s.level, oldIndicator = s.indicator;
  if ("level" in patch || "indicator" in patch || "mode" in patch) APP.switchNote = null;
  if ("mode" in patch && patch.mode !== s.mode) {
    if (patch.mode === "candidates") APP.layerLevel = s.level;
    else if (APP.layerLevel && !("area" in patch ? patch.area : s.area)) s.level = APP.layerLevel; // an explored area keeps its level
  }
  const oldShown = APP.profileId();
  Object.assign(s, patch);
  if (s.mode === "candidates" && !("indicator" in patch)) s.level = APP.candidateLevel();
  const m = APP.meta[s.indicator];
  if (!m.levels.includes(s.level)) {
    if ("level" in patch) {
      s.indicator = APP.firstIndicator(s.level);
      APP.switchNote = APP.t("layers.switch_note", { title: APP.meta[oldIndicator].title, level: APP.LEVEL_SINGULAR[APP.meta[oldIndicator].levels[0]] });
    }
    else if ("indicator" in patch || s.mode === "layer") s.level = m.levels[0];
  }
  // a new level takes the area along: a district becomes its Stadtteil, a Stadtteil has no district
  if (s.area && s.level !== oldLevel && !("area" in patch)) s.area = APP.areaFor(s.area, oldLevel, s.level);
  // an explored area is the profile shown; only showProfile (a list, a candidate) may show another one meanwhile
  if (s.area && !("profile" in patch)) s.profile = { id: s.area, level: s.level };
  APP.syncLayers();
  // the tab Gebiet follows the state; before 03_profile.js has run there is nothing to draw
  if (APP.renderProfile && (APP.profileId() !== oldShown || s.level !== oldLevel)) APP.renderProfile();
  else if (APP.syncProfile) APP.syncProfile();
  if (draw) APP.draw();
  APP.writeMapLink();
};
APP.setLevel = (level) => APP.setState({ level });
APP.setIndicator = (id) => APP.meta[id] && APP.setState({ indicator: id });

// Navigation (docs/design.md, Views and tabs): views in the header, map tabs on top of the sidebar
APP.press = function (buttons, on) {
  buttons.forEach((b) => {
    b.classList.toggle("active", on(b));
    b.setAttribute("aria-pressed", String(on(b)));
  });
};

// Four views: the map, „Trend“, „Neubau“ and „Miete“. A chart view is drawn on first open; a resize while it was hidden
// redraws it on the next open.
APP.VIEWS = { history: "view-history", new_construction: "view-new-construction", rent_burden: "view-rent-burden" };
APP.openView = function (name) {
  APP.press(document.querySelectorAll("#views button"), (b) => b.dataset.view === name);
  document.querySelector("main").hidden = name !== "map";
  for (const [view, id] of Object.entries(APP.VIEWS)) document.getElementById(id).hidden = name !== view;
  if (name === "history") { if (APP.historyDrawn) APP.layoutHistory(); else APP.drawHistory(); }
  if (name === "new_construction") { if (APP.newConstructionDrawn) APP.layoutNewConstruction(); else APP.drawNewConstruction(); }
  if (name === "rent_burden") { if (APP.rentBurdenDrawn) APP.layoutRentBurden(); else APP.drawRentBurden(); }
  if (name === "map") APP.map.invalidateSize();
  APP.showLink(name);
};

// Direct links (docs/design.md, Direct links): the fragment #<view> or #<view>/<chart> opens a view and scrolls to the
// figure of the chart. The view slugs stand as data-link on the view buttons, the chart slugs as link in the payload;
// a figure has the id <view>-<chart>. No fragment is the map; an unknown view changes nothing.
APP.viewLink = (name) => document.querySelector(`#views button[data-view="${name}"]`).dataset.link;
// The fragment splits at its first "/" only: the rest of a map link may hold an area like 40/50/60
APP.followLink = function () {
  const fragment = location.hash.slice(1), cut = fragment.indexOf("/");
  const link = cut < 0 ? fragment : fragment.slice(0, cut), chart = cut < 0 ? undefined : fragment.slice(cut + 1);
  const button = [...document.querySelectorAll("#views button")].find((b) => b.dataset.link === (link || APP.viewLink("map")));
  if (!button) return;
  APP.openView(button.dataset.view);
  // a map link: the address bar then holds the clean link of the map shown
  if (button.dataset.view === "map" && chart) {
    APP.applyMapLink(APP.parseMapLink(chart));
    history.replaceState(null, "", "#" + APP.mapLink());
    return;
  }
  const fig = chart ? document.getElementById(`${link}-${chart}`) : null, view = document.getElementById(APP.VIEWS[button.dataset.view]);
  if (!fig) {
    if (view) view.scrollTop = 0;
    // an unknown chart: the address bar names only its view, so nobody copies a dead link
    if (chart !== undefined) history.replaceState(null, "", "#" + link);
    return;
  }
  fig.scrollIntoView({ block: "start" });
  // fonts loaded later change the height of the view: scroll again, unless the reader has followed another link
  // meanwhile. The fonts are embedded, so the reader has no time to scroll before.
  const hash = location.hash;
  document.fonts.ready.then(() => { if (location.hash === hash) fig.scrollIntoView({ block: "start" }); });
};
// Map links (docs/design.md, Direct links): #karte/zoom=…&center=…&level=…&area=…&layer=…&overlays=…. The keys, the
// levels, the layer ids and the overlay names are addresses: they never change.
APP.MAP_LINK_KEYS = ["zoom", "center", "level", "area", "layer", "overlays"];
// The rest of a map link (after "karte/") as { zoom, center, level, area, indicator, overlays }; a key stays absent
// when the link lacks it or its value is unknown. Messengers encode parts (%2C, %3D) and glue punctuation to the end.
APP.parseMapLink = function (text) {
  const values = {};
  for (const part of text.replace(/[.,)!?]+$/, "").split("&")) {
    let decoded;
    try { decoded = decodeURIComponent(part); } catch { continue; } // a broken escape drops its key
    const cut = decoded.indexOf("=");
    if (cut > 0 && APP.MAP_LINK_KEYS.includes(decoded.slice(0, cut))) values[decoded.slice(0, cut)] = decoded.slice(cut + 1);
  }
  const number = (v) => (v.trim() === "" ? NaN : Number(v));
  const out = {};
  if ("zoom" in values && Number.isFinite(number(values.zoom))) out.zoom = Math.min(19, Math.max(10, number(values.zoom)));
  if ("center" in values) {
    const c = values.center.split(",").map(number);
    if (c.length === 2 && c.every(Number.isFinite) && APP.layers.district.getBounds().pad(0.5).contains(c)) out.center = c;
  }
  if (Object.hasOwn(APP.COLLECTIONS, values.level ?? "")) out.level = values.level;
  const layer = APP.meta[values.layer]?.layer ? values.layer : null;
  // the area must lie on the level shown in the city tab: the layer wins over the level (APP.applyMapLink); the candidates
  // give back the level of the city tab (APP.setState)
  const m = APP.meta[layer ?? APP.state.indicator];
  const wanted = out.level ?? (APP.state.mode === "candidates" && APP.layerLevel ? APP.layerLevel : APP.state.level);
  const level = m.levels.includes(wanted) ? wanted : m.levels[0];
  // an area of the level shown stays; a Bezirk on a layer of Stadtteile only goes to its Stadtteil, as a switch of the
  // level would (APP.setState). Stadtteil and Bezirk ids never overlap.
  const shown = (id) => APP.properties(level).some((p) => p.id === id);
  const area = !("area" in values) ? null : shown(values.area) ? values.area : APP.areaFor(values.area, wanted, level);
  if (area && shown(area)) out.area = area;
  if (layer) out.indicator = layer;
  if ("overlays" in values) {
    const names = values.overlays.split(",");
    out.overlays = Object.keys(APP.overlays).filter((n) => names.includes(n));
  }
  return out;
};
// Shows a parsed map link. It ends the candidates; without an area it ends exploring and shows „Stadt“. The phone
// panel stays as it is. Absent keys keep what the map shows. The centre of the link goes to the visible centre.
APP.applyMapLink = function (link) {
  if (link.overlays) for (const name of Object.keys(APP.overlays)) APP.setOverlay(name, link.overlays.includes(name));
  // as a click on „Stadt“: the level of the city tab comes back, also from candidates on another level
  APP.endExplore();
  const indicator = link.indicator ?? APP.state.indicator;
  // a level the layer lacks is dropped, so setState switches nothing and writes no note
  const patch = { indicator, mode: "layer" };
  if (link.level && APP.meta[indicator].levels.includes(link.level)) patch.level = link.level;
  APP.setState(patch);
  // explore keeps the view before the link (APP.overview); on a fresh load that is the fit of the city. Without both
  // zoom and centre it flies to the area, as a click would.
  const fly = Boolean(link.area) && !(link.zoom && link.center);
  if (link.area && APP.state.area !== link.area) APP.explore(link.area, { fly, panel: false });
  // „Gebiet“ also when the area was explored before; „Stadt“ ends exploring
  APP.openTab(link.area && APP.state.area === link.area ? "area" : "city", { panel: false });
  if (!fly && (link.zoom || link.center)) APP.centerAt(link.center ?? APP.visibleCenter(), link.zoom ?? APP.map.getZoom());
};
// The centre of the visible map: on the phone the part above the panel (APP.panelHeight), else the container. A link
// names this centre, so a phone with the panel open and a desktop show the same place. From getCenter, which keeps the
// exact centre of setView: a container point would round to the pixel origin of Leaflet.
APP.visibleCenter = function (panel = APP.panelHeight()) {
  const zoom = APP.map.getZoom();
  return APP.map.unproject(APP.map.project(APP.map.getCenter(), zoom).subtract([0, panel / 2]), zoom);
};
// Shows `center` at the visible centre, without animation. The anchor of the link comes first: setView fires moveend
// at once, and that writes the link. On a loaded map setView pans by truncated pixels and may land up to 1 px off.
// The 2 px of APP.linkedCenter absorb this, so do not tighten them.
APP.centerAt = function (center, zoom) {
  const point = APP.map.project(center, zoom).add([0, APP.panelHeight() / 2]);
  APP.linkCenter = { center: L.latLng(center), zoom };
  APP.map.setView(APP.map.unproject(point, zoom), zoom, { animate: false });
};
// The centre a link names. Leaflet rounds the centre to a pixel once the map pane moves (a resize, the fonts), so the
// last 5 decimals would change without a move. The centre of before stays while the map is less than 2 px from it.
// panel: the panel height the visible centre is measured above (default: the panel shown now).
APP.linkCenter = null; // { center, zoom }
APP.linkedCenter = function (panel = APP.panelHeight()) {
  const c = APP.visibleCenter(panel), zoom = APP.map.getZoom(), last = APP.linkCenter;
  if (last && last.zoom === zoom && APP.map.project(c, zoom).distanceTo(APP.map.project(last.center, zoom)) < 2) return last.center;
  APP.linkCenter = { center: c, zoom };
  return c;
};
// The map link of the map shown, keys in the order of APP.MAP_LINK_KEYS; area only while exploring
APP.mapLink = function () {
  const c = APP.linkedCenter(), s = APP.state;
  const parts = [`zoom=${Math.round(APP.map.getZoom() * 10) / 10}`, `center=${c.lat.toFixed(5)},${c.lng.toFixed(5)}`, `level=${s.level}`];
  if (s.area) parts.push(`area=${encodeURIComponent(s.area)}`);
  parts.push(`layer=${s.indicator}`, `overlays=${Object.keys(APP.overlays).filter((n) => APP.overlays[n].on).join(",")}`);
  return APP.viewLink("map") + "/" + parts.join("&");
};

// The address bar holds the link of the map shown (after every moveend, setState and overlay), while the map is shown.
// Without a map link in the fragment it writes nothing while the map is as at the start (APP.startLink): a resize or
// the fonts must not put a link into a fresh page, and #karte stays #karte. Safari throws on too many replaceState
// calls in a short time: the map goes on, the address bar keeps the last link.
APP.writeMapLink = function () {
  if (!APP.ready || document.querySelector("main").hidden) return;
  const link = APP.mapLink(), hash = "#" + link;
  if (!location.hash.startsWith("#" + APP.viewLink("map") + "/") && link === APP.startLink) return;
  if (hash === location.hash) return;
  try { history.replaceState(null, "", hash); } catch { /* keeps the last link */ }
};

// The address bar names the view shown, so it can be copied as a link. A fragment of the same view stays, with its
// chart. replaceState adds no history entry: „Zurück“ leaves the page as before. The map writes its link once it
// differs from the start; else it clears any other fragment and keeps only #karte.
APP.showLink = function (name) {
  if (name === "map" && APP.startLink && APP.mapLink() !== APP.startLink) return APP.writeMapLink();
  const link = APP.viewLink(name), current = location.hash.slice(1).split("/")[0];
  if (current === link || (name === "map" && !location.hash)) return;
  history.replaceState(null, "", name === "map" ? location.pathname + location.search : "#" + link);
};

// A map tab always shows the map view. It opens the phone panel, except for a map link (panel: false).
APP.openTab = function (name, { panel = true } = {}) {
  if (!document.getElementById("tab-" + name)) return;
  APP.press(document.querySelectorAll("#tabs button[data-tab]"), (b) => b.dataset.tab === name);
  document.querySelectorAll(".tab").forEach((s) => s.classList.toggle("active", s.id === "tab-" + name));
  if (panel) APP.setPanel(true);
  APP.openView("map");
  // Stadt and Kandidaten work on the whole city; Gebiet explores the area of the profile
  if (name === "city" || name === "candidates") APP.endExplore();
  if (name === "area" && !APP.state.area && APP.profileId()) return APP.explore(APP.profileId());
  const mode = name === "city" ? "layer" : name === "candidates" ? "candidates" : APP.state.mode;
  if (mode !== APP.state.mode) APP.setState({ mode });
};

// One line; a tap or click opens the source list
APP.footer = function () {
  // a source with a page links its title (docs/design.md, Layouts)
  const title = (q) => (q.url ? `<a href="${APP.escape(q.url)}" target="_blank" rel="noopener">${APP.escape(q.title)}</a>` : APP.escape(q.title));
  const sources = APP.data.sources.map((q) => `${title(q)} (${APP.escape(q.as_of)}; ${APP.escape(q.license)})`).join(" · ");
  document.getElementById("footer").innerHTML = `<details><summary>${APP.escape(APP.t("footer", { created: APP.data.created }))}</summary><p>${sources}</p></details>`;
};
// Print the full source list, then restore the footer
window.addEventListener("beforeprint", () => {
  const d = document.querySelector("#footer details");
  APP.footerOpen = d.open;
  d.open = true;
});
window.addEventListener("afterprint", () => { document.querySelector("#footer details").open = APP.footerOpen; });

// Phone layout (docs/design.md, Phone panel): the sidebar is a panel at the bottom of the map, always
// 60 % high. Closed (class "closed") it is moved down until only its tab bar shows; the arrow or a swipe
// (07_swipe.js) opens and closes it. CSS uses "closed", --tabs and --panel only on the phone.
APP.phoneQuery = window.matchMedia("(max-width: 700px)");
APP.phone = () => APP.phoneQuery.matches;
APP.sidebar = document.getElementById("sidebar");
// visible height of the closed panel: its top border and the tab bar
APP.tabsHeight = () => APP.sidebar.offsetHeight - APP.sidebar.clientHeight + document.getElementById("tabs").offsetHeight;
APP.closedShift = () => APP.sidebar.offsetHeight - APP.tabsHeight();
// visible height of the panel once it has settled (not the moment of a slide)
APP.panelHeight = () => (!APP.phone() ? 0 : APP.sidebar.classList.contains("closed") ? APP.tabsHeight() : APP.sidebar.offsetHeight);
// --panel lifts the bottom controls above the panel; --legend-max keeps an open legend below the top of the map
APP.updatePanel = function () {
  const style = APP.map.getContainer().style;
  APP.sidebar.style.setProperty("--tabs", APP.tabsHeight() + "px");
  APP.shownPanel = APP.panelHeight(); // the panel of before, when the phone layout turns on or off
  style.setProperty("--panel", APP.shownPanel + "px");
  const switchHeight = APP.switchDiv && !APP.switchDiv.hidden ? APP.switchDiv.offsetHeight + 10 : 0;
  style.setProperty("--legend-max", Math.max(60, APP.map.getContainer().clientHeight - APP.panelHeight() - 40 - switchHeight) + "px");
};
APP.setPanel = function (open) {
  const arrow = document.getElementById("panel-toggle");
  APP.sidebar.classList.toggle("closed", !open);
  // out of view, the content must not take focus; beside the map (medium layout) it is always usable
  APP.sidebar.querySelectorAll(".tab").forEach((t) => { t.inert = !open && APP.phone(); });
  arrow.textContent = open ? "▼" : "▲";
  arrow.setAttribute("aria-expanded", String(open));
  arrow.setAttribute("aria-label", open ? APP.t("panel.close") : APP.t("panel.open"));
  APP.updatePanel();
  // the panel covers another part of the map: a map link follows the visible centre; a fragment without one stays
  if (location.hash.startsWith("#" + APP.viewLink("map") + "/")) APP.writeMapLink();
};
// turning the phone keeps the state; the medium layout frees the content. The map keeps its visible centre, now above
// another panel. Here Leaflet still knows the size of before and APP.shownPanel the panel of before; the new size
// comes with the next frame. The sticky centre of the link (APP.linkedCenter) goes over, so a turn and back keeps the
// link and a fresh page stays at its start.
APP.phoneQuery.addEventListener("change", () => {
  const center = !document.querySelector("main").hidden && APP.linkedCenter(APP.shownPanel ?? 0), zoom = APP.map.getZoom();
  APP.setPanel(!APP.sidebar.classList.contains("closed"));
  if (center) requestAnimationFrame(() => { APP.map.invalidateSize(); APP.centerAt(center, zoom); });
});
