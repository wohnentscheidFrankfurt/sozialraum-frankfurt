"use strict";
APP.OWNERSHIP = APP.data.grid_groups.map((id) => APP.meta[id]); // the owner groups in the order of the grid; title and colour from the catalog
APP.ownershipById = Object.fromEntries(APP.OWNERSHIP.map((e) => [e.id, e]));

// The Stadtteil of an area: a district names it in p.quarter, a Stadtteil is its own
APP.quarterOf = (p) => (p.quarter === undefined ? p : APP.properties("quarter").find((s) => s.id === p.quarter));

// Where the value of an indicator for the area p comes from: its own level, or for a district and a Stadtteil-only
// indicator the Stadtteil of the district (ownership is only known per Stadtteil); null if there is none
APP.valueSource = function (m, p, level) {
  if (m.levels.includes(level)) return { p, level };
  if (level === "district" && m.levels.includes("quarter")) return { p: APP.quarterOf(p), level: "quarter" };
  return null;
};

// A row whose indicator is a layer is a button: it shows that layer on the map (APP.chooseLayer, 09_explore.js)
APP.layerAttrs = (m) => (m && m.layer === true ? ` data-layer="${m.id}" role="button" tabindex="0" aria-pressed="false"` : "");

APP.profileOwnership = function (area, level) {
  // Ownership only per Stadtteil (docs/data-rules.md, Level); a district shows the values of its Stadtteil. Every share is estimated (~)
  const source = APP.valueSource(APP.OWNERSHIP[0], area, level);
  if (!source) return "";
  const p = source.p;
  const from = p !== area ? APP.escape(APP.t("profile.ownership.from_quarter", { name: p.name })) + " " : "";
  const parts = APP.OWNERSHIP.map((e) => ({ ...e, value: p[e.id] ?? 0 }));
  const coverage = APP.coverageText(p) ? " " + APP.coverageText(p) : "";
  // only the year of the estimate; how 2011 is used says the ⓘ of each layer
  let h = `<h3>${APP.escape(APP.t("profile.ownership.heading"))} <span class="as-of">${APP.escape(APP.meta.OWN_COMPANY.as_of.split(" · ")[0])}</span></h3>` +
    `<p class="note">${from}${APP.escape(APP.t("profile.ownership.estimated"))}${coverage}</p><div class="stack">`;
  h += parts.map((t) => `<span style="width:${t.value}%;background:${t.color}" title="${APP.escape(t.title)}: ${APP.escape(APP.valueText(t.id, p[t.id]))}"></span>`).join("") + "</div>";
  // shares only; the count of a group stands in the map tooltip (docs/texts.md, Map: profile)
  h += `<table class="table"><tr><th></th><th>${APP.escape(APP.t("profile.ownership.area"))}</th><th>${APP.escape(APP.t("profile.ownership.city"))}</th></tr>`;
  h += parts.map((t) => `<tr${APP.layerAttrs(t)}><td><i style="background:${t.color}"></i>${APP.escape(t.title)}${t.layer === false ? " " + APP.infoButton("profile-" + t.id) : ""}</td>` +
    `<td>${APP.escape(APP.valueText(t.id, p[t.id], p))}</td>` +
    `<td>${APP.escape(APP.valueText(t.id, APP.data.city_values[t.id]))}</td></tr>`).join("");
  // a group without its own layer carries its ⓘ here, below the table
  return h + `</table>` + parts.filter((t) => t.layer === false).map((t) => APP.infoBlock(t, "profile-" + t.id)).join("");
};

APP.profileRow = function (m, area, level) {
  const source = APP.valueSource(m, area, level);
  if (!source) return "";
  const p = source.p;
  const allValues = APP.properties(source.level).map((x) => x[m.id]).filter((x) => x != null);
  const x = p[m.id];
  const cityValue = APP.data.city_values[m.id];
  const max = Math.max(...allValues, cityValue ?? 0, 0) || 1;
  const bar = Math.min(...allValues) < 0 || m.type === "classes" ? "" :
    `<div class="bar"><span style="width:${x == null ? 0 : (x / max) * 100}%"></span>` +
    (cityValue == null ? "" : `<i class="city" style="left:${(cityValue / max) * 100}%"></i>`) + `</div>`;
  // one value per row; its count stands in the tooltip of the layer (docs/texts.md, Map: profile)
  const value = m.rank && x != null ? APP.rankText(m.id, x, source.level) : APP.valueText(m.id, x, p);
  // a row without its own layer carries the ⓘ itself
  const key = `profile-${m.id}`, own = m.layer === false;
  const note = cityValue == null ? "" : APP.escape(APP.t("city_value", { value: APP.valueText(m.id, cityValue) }));
  // a value the Monitoring publishes for several districts says so under the value
  const list = x != null ? APP.sharedList(p, m.id) : null;
  const shared = list ? `<span class="note shared">${APP.escape(APP.t("profile.shared", { list }))}</span>` : "";
  return `<div class="row"${APP.layerAttrs(m)}><span>${APP.escape(m.title)}${own ? " " + APP.infoButton(key) : ""}</span><strong>${APP.escape(value)}</strong>` +
    `${shared}${bar}${m.criterion === false || !note ? "" : `<span class="note">${note}</span>`}</div>` +
    (own ? APP.infoBlock(m, key) : "");
};

// Statutes and plans: only what exists; without any Milieuschutz one short line. No date (docs/texts.md, Map: profile)
APP.profilePlanning = function (p) {
  const row = (label, value) => (value ? `<div class="row"><span>${APP.escape(label)}</span><strong>${APP.escape(value)}</strong></div>` : "");
  let h = `<h3>${APP.escape(APP.t("profile.planning.heading"))}</h3>`;
  if (!p.social_preservation_names && !p.social_preservation_pending_names) h += `<p class="note">${APP.escape(APP.t("no_social_preservation"))}</p>`;
  h += row(APP.t("profile.planning.social_preservation"), p.social_preservation_names);
  if (p.PROT_SOCIAL > 0) h += row(APP.t("profile.planning.coverage"), APP.withUnit("PROT_SOCIAL", p.PROT_SOCIAL));
  h += row(APP.t("profile.planning.social_preservation_pending"), p.social_preservation_pending_names);
  h += row(APP.t("profile.planning.townscape"), p.townscape_names);
  h += row(APP.t("profile.planning.townscape_pending"), p.townscape_pending_names);
  return h + row(APP.t("profile.planning.pending_plans"), p.pending_plan_names);
};

// The breakdown of a layer (catalog: breakdown_of) as bars under its row: no layer, no ⓘ (the ⓘ of the layer explains
// them). One scale for all bars, 0 to the next multiple of 10 above the largest value; the ramp of the layer from its
// darkest step on, the darkest for the first entry (docs/design.md, Profile and pressed row).
APP.profileBreakdown = function (m, p) {
  const entries = APP.breakdownFor(m), ramp = APP.rampFor(m);
  if (!entries.length) return "";
  const values = [...APP.properties("district").flatMap((d) => entries.map((c) => d[c.id])), ...entries.map((c) => APP.data.city_values[c.id])].filter((v) => v != null);
  const scale = Math.floor(Math.max(...values, 0) / 10) * 10 + 10;
  return `<div class="breakdown"><p class="note">${APP.escape(m.breakdown_lead)}:</p>` + entries.map((c, i) => {
    const x = p[c.id], city = APP.data.city_values[c.id];
    return `<div class="row"><span>${APP.escape(c.title)}</span><strong>${APP.escape(APP.valueText(c.id, x, p))}</strong>` +
      `<div class="bar"><span style="width:${x == null ? 0 : (x / scale) * 100}%;--bar:${ramp[ramp.length - 1 - i]}"></span>` +
      (city == null ? "" : `<i class="city" style="left:${(city / scale) * 100}%"></i>`) + `</div>` +
      (city == null ? "" : `<span class="note">${APP.escape(APP.t("city_value", { value: APP.valueText(c.id, city) }))}</span>`) + `</div>`;
  }).join("") + `</div>`;
};

// The note before rows of another area: the singular for one value, the plural for more; a row with breakdown bars
// counts as more (docs/texts.md, Map: profile). `what` is HTML.
APP.otherAreaNote = (ms, what) => (ms.length === 1 && !APP.breakdownFor(ms[0]).length
  ? APP.t("profile.other_area.one", { area: what }) : APP.t("profile.other_area.many", { area: what }));

// The block of one topic: the rows of the area, then the rows of its Umfragebezirk (only a district has them), then
// the rows that a district takes from its Stadtteil, each group after its note. A count has no row; it stands in the
// tooltip of its share. A breakdown entry is a bar under the row of its layer.
APP.profileSection = function (section, p, level) {
  const all = APP.data.catalog.filter((m) => m.section === section && (m.type === "number" || m.type === "classes") && APP.valueSource(m, p, level));
  const rows = all.filter((m) => !m.count_of && !m.breakdown_of);
  if (!rows.length) return "";
  const own = rows.filter((m) => m.levels.includes(level) && !m.survey_area), survey = rows.filter((m) => m.levels.includes(level) && m.survey_area);
  const fromQuarter = rows.filter((m) => !m.levels.includes(level));
  const draw = (ms) => ms.map((m) => APP.profileRow(m, p, level) + (m.breakdown_lead ? APP.profileBreakdown(m, APP.valueSource(m, p, level).p) : "")).join("");
  // each date once beside the heading; "9.5.2011 · 15.5.2022" gives two dates (pipeline/use_cases/construction_year/README.md)
  const dates = [...new Set(all.flatMap((m) => String(m.as_of).split(" · ")))].join(", ");
  let h = `<h3>${APP.escape(rows[0].group)} <span class="as-of">${APP.escape(dates)}</span></h3>` + draw(own);
  if (survey.length) h += `<p class="note">${APP.otherAreaNote(survey, APP.escape(APP.t("profile.other_area.survey_area", { name: p.survey_area })))}</p>` + draw(survey);
  if (fromQuarter.length) h += `<p class="note">${APP.otherAreaNote(fromQuarter, APP.escape(APP.t("profile.other_area.quarter", { name: APP.quarterOf(p).name })))}</p>` + draw(fromQuarter);
  return h;
};

APP.profileElection = function (s, fromQuarter) {
  if (!s) return "";
  const note = fromQuarter ? APP.t("profile.election.note_quarter", { name: s.name }) : APP.t("profile.election.note");
  let h = `<h3>${APP.escape(APP.t("profile.election.heading"))}</h3><p class="note">${APP.escape(note)}</p>`;
  const max = Math.max(...APP.data.lists.map((l) => s[l.key] || 0), 1);
  for (const l of APP.data.lists) {
    h += `<div class="row"${APP.layerAttrs(APP.meta[l.key])}><span>${APP.escape(l.name)}</span><strong>${APP.escape(APP.attachUnit(APP.format(s[l.key], 1), "%"))}</strong>` +
      `<div class="bar"><span style="width:${((s[l.key] || 0) / max) * 100}%;--bar:${l.color}"></span></div>` +
      `<span class="note">${APP.escape(APP.t("city_value", { value: APP.attachUnit(APP.format(l.city_share, 1), "%") }))}</span></div>`;
  }
  h += `<div class="row"${APP.layerAttrs(APP.meta.ELEC_TURNOUT)}><span>${APP.escape(APP.t("profile.election.turnout"))}</span>` +
    `<strong>${APP.escape(APP.attachUnit(APP.format(s.ELEC_TURNOUT, 1), "%"))}</strong></div>`;
  return h + `<p class="note"><strong>${APP.escape(APP.t("areas_not_people"))}</strong></p>`;
};

// The details line under the head (docs/design.md, Profile and pressed row): closed, it names the overlays that are on
// (APP.syncDetails); open, it holds the rows of „Stadt“. It stays open or closed through every redraw (APP.detailsOpen).
// Before 04_overlays.js has run there are no rows and no line.
APP.profileDetails = () => (!APP.overlayRows ? "" :
  `<details class="area-details"${APP.detailsOpen ? " open" : ""}><summary><h3>${APP.OVERLAY_HEADING} <span class="as-of details-names"></span></h3></summary>` +
  `<div class="choice">${APP.overlayRows("area-overlay-")}</div></details>`);

APP.PROFILE_NOTE = `<p class="note">${APP.escape(APP.t("profile.empty"))}</p>`;

// The one writer of the tab Gebiet: the profile of the profile, or the note
APP.renderProfile = function () {
  const level = APP.state.level;
  const tab = document.getElementById("tab-area");
  const id = APP.profileId();
  const p = id && APP.properties(level).find((x) => x.id === id);
  if (!p) {
    document.getElementById("tab-area").innerHTML = APP.PROFILE_NOTE;
    APP.syncProfile();
    return;
  }
  const quarterName = level === "district" && !p.name.includes(p.quarter) ? ` · ${APP.escape(p.quarter)}` : "";
  const number = level === "district" ? `${APP.escape(APP.t("district_number", { id: p.id }))} · ` : "";
  let h = `<h2>${APP.escape(p.name)}</h2><p class="note">${number}${APP.escape(APP.t("profile.residents", { count: APP.format(p.POP, 0) }))}${quarterName}</p>`;
  if (p.small) h += `<p class="warning">${APP.escape(APP.t("profile.small"))}</p>`;
  h += APP.profileDetails();
  h += APP.profileOwnership(p, level);
  // the topics in the order of the catalog (docs/texts.md, Map: profile)
  for (const section of ["situation", "rent", "stock", "land"]) h += APP.profileSection(section, p, level);
  h += APP.profilePlanning(p);
  h += APP.profileElection(APP.quarterOf(p), level === "district");
  document.getElementById("tab-area").innerHTML = h;
  APP.bindInfo(tab);
  if (APP.syncDetails) APP.syncDetails();
  APP.syncProfile();
};

// The profile of an area of the current level; the tab opens when `open`
APP.showProfile = function (id, open = true) {
  if (!APP.properties(APP.state.level).some((x) => x.id === id)) return;
  APP.setState({ profile: { id, level: APP.state.level } }, false);
  if (open) APP.openTab("area");
};

// The colour of the area p on the map, if it is a class of the layer m; null for no data, a small Bezirk in grey
// and a list colour. From APP.styleBase, not from the map: while exploring, the other areas are grey.
APP.classColour = function (m, p) {
  const fill = APP.styleBase({ properties: p }).fillColor;
  return APP.rampFor(m)?.includes(fill) ? fill : null;
};

// The row of the layer on the map is pressed. Its bar takes the colour of the area on the map; the classes come from
// APP.draw, which calls this again at its end.
APP.syncProfile = function () {
  const on = APP.state.mode === "layer" ? APP.state.indicator : null;
  const id = APP.profileId(), p = on && id && APP.properties(APP.state.level).find((x) => x.id === id);
  const colour = p ? APP.classColour(APP.meta[on], p) : null;
  document.querySelectorAll("#tab-area [data-layer]").forEach((r) => {
    const pressed = r.dataset.layer === on;
    r.classList.toggle("active", pressed);
    r.setAttribute("aria-pressed", String(pressed));
    if (pressed && colour) r.style.setProperty("--map", colour);
    else r.style.removeProperty("--map");
  });
};

// The details line stays open or closed while the page is open. toggle does not bubble, so the tab listens in the
// capture phase.
APP.detailsOpen = false;
document.getElementById("tab-area").addEventListener("toggle", (e) => {
  if (e.target.matches("details.area-details")) APP.detailsOpen = e.target.open;
}, true);

// One listener for all rows: click, Enter and Space
(() => {
  const area = document.getElementById("tab-area");
  const rowOf = (e) => (e.target.closest(".info-button") ? null : e.target.closest("[data-layer]"));
  area.addEventListener("click", (e) => { const r = rowOf(e); if (r) APP.chooseLayer(r.dataset.layer); });
  area.addEventListener("keydown", (e) => {
    const r = rowOf(e);
    if (!r || r !== e.target || (e.key !== "Enter" && e.key !== " ")) return;
    e.preventDefault();
    APP.chooseLayer(r.dataset.layer);
  });
})();
