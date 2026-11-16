"use strict";
APP.template = null;
APP.criteria = [];
APP.evaluation = [];
APP.evaluationById = {};

APP.threshold = (k, cityValues) => (k.threshold === "city_value" ? cityValues[k.city ?? k.indicator] ?? null : k.threshold);
// A criterion on the end of a range (OWN_PUBLIC_HIGH) takes unit and ⓘ from its indicator (k.city) and has its own label
APP.criterionMeta = (k) => APP.meta[k.indicator] ?? APP.meta[k.city];
APP.criterionTitle = (k) => k.label ?? APP.criterionMeta(k).title;
APP.unitId = (k) => k.city ?? k.indicator;
// Compared on the shown values: value and threshold are rounded to the decimals of the indicator `id` (`shownOf`; a rank is
// not rounded), the same rule as the Python evaluation (pipeline/use_cases/candidates/model.py)
APP.meets = function (x, op, s, id = null) {
  if (x == null || s == null || Number.isNaN(x)) return false;
  if (id) { x = APP.shownOf(id, x); s = APP.shownOf(id, s); }
  if (op === ">=") return x >= s;
  if (op === "<") return x < s;
  if (op === "==") return x === s;
  return false;
};
// Small districts (under 1,000 residents) do not count; Stadtteile have no such rule
APP.counts = (p) => APP.candidateLevel() !== "district" || !p.small;
APP.evaluate = function (properties, criteria, cityValues) {
  const active = criteria.filter((k) => k.active !== false);
  return properties.filter(APP.counts).map((p) => {
    // a criterion without a value for this area is unknown, not missed: the tooltip says „k. A.“ for it
    const unknownValue = (k) => p[k.indicator] == null || Number.isNaN(p[k.indicator]);
    const failed = active.filter((k) => !APP.meets(p[k.indicator], k.op, APP.threshold(k, cityValues), APP.unitId(k)));
    const missing = failed.filter((k) => !unknownValue(k)).map(APP.criterionTitle), unknown = failed.filter(unknownValue).map(APP.criterionTitle);
    const n = active.length - failed.length;
    return { id: p.id, name: p.name, quarter: p.quarter, met: n, full: active.length > 0 && n === active.length, missing, unknown };
  });
};
APP.activeCriteria = () => APP.criteria.filter((k) => k.active);
// Level of the chosen template (pipeline/use_cases/candidates/README.md); the own query works on districts
APP.candidateLevel = () => APP.data.templates.find((x) => x.id === APP.template)?.level ?? "district";
APP.matches = () => APP.evaluation.map((b) => ({ id: b.id, met: b.met, full: b.full }));
// The values of the areas as shown; `unit` is the indicator whose decimals count (a criterion on a range end takes its city indicator)
APP.areaValues = (id, unit = id) => APP.properties(APP.candidateLevel()).filter(APP.counts).map((p) => APP.shownOf(unit, p[id])).filter((x) => x != null);
APP.median = function (values) {
  const s = [...values].sort((a, b) => a - b);
  return s.length ? s[Math.floor((s.length - 1) / 2)] : null;
};

APP.setTemplate = function (id) {
  const v = APP.data.templates.find((x) => x.id === id);
  APP.template = id;
  APP.criteria = v ? v.criteria.map((k) => ({ ...k, active: true, threshold: APP.snapThreshold(APP.unitId(k), APP.threshold(k, APP.data.city_values)) })) : [];
  const select = document.getElementById("template");
  if (select) select.value = v ? id : "custom";
  // the new template may have another level; updateCandidates draws
  if (APP.state.mode === "candidates" && APP.state.level !== APP.candidateLevel()) APP.setState({}, false);
  const lead = document.getElementById("template-lead");
  if (lead) { lead.textContent = v?.lead ?? ""; lead.hidden = !v; }
  APP.buildCriteria();
  APP.updateCandidates();
};

APP.updateCandidates = function () {
  APP.evaluation = APP.evaluate(APP.properties(APP.candidateLevel()), APP.activeCriteria(), APP.data.city_values);
  APP.evaluationById = Object.fromEntries(APP.evaluation.map((b) => [b.id, b]));
  APP.buildMatches();
  if (APP.state.mode === "candidates") APP.draw();
};

APP.styleCandidates = function (p, base) {
  const b = APP.evaluationById[p.id];
  const n = APP.activeCriteria().length;
  if (!b || n === 0 || b.met === 0) return { ...base, fillColor: "#ffffff", fillOpacity: 0.5 };
  const ramp = APP.data.ramp_teal;
  const step = Math.max(1, Math.round((b.met / n) * (ramp.length - 1)));
  return { ...base, fillColor: ramp[step], weight: b.full ? 3.5 : base.weight, color: b.full ? APP.data.hit_border : base.color };
};

APP.legendCandidates = function (div) {
  const n = APP.activeCriteria().length;
  const ramp = APP.data.ramp_teal;
  const step = (i) => ramp[Math.max(1, Math.round((i / n) * (ramp.length - 1)))];
  let h = `<i style="background:#ffffff"></i>keins<br>`;
  for (let i = 1; i < n; i++) h += `<i style="background:${step(i)}"></i>${i} von ${n}<br>`;
  if (n > 0) h += `<i style="background:${step(n)};border:3px solid ${APP.data.hit_border}"></i>alle erfüllt<br>`;
  if (APP.candidateLevel() === "district" && APP.anySmall()) h += `<i style="background:#d0d0d0"></i>unter 1.000 Einwohner*innen<br>`;
  div.innerHTML = APP.legendHtml("Kriterien erfüllt", h + APP.overlayKeyHtml());
};

APP.histogram = function (values, threshold, cityValue, min, max, i) {
  const n = 20, width = 300, height = 46, bins = new Array(n).fill(0), span = max - min || 1;
  for (const x of values) bins[Math.min(n - 1, Math.floor(((x - min) / span) * n))]++;
  const peak = Math.max(...bins, 1), binWidth = width / n, pos = (x) => ((x - min) / span) * width;
  let svg = `<svg id="hist-${i}" viewBox="0 0 ${width} ${height + 4}" width="100%" height="${height + 4}" role="img" aria-label="Verteilung der ${APP.LEVEL_NAMES[APP.candidateLevel()]}">`;
  bins.forEach((c, j) => {
    const h = (c / peak) * height;
    svg += `<rect x="${j * binWidth + 0.5}" y="${height - h}" width="${binWidth - 1}" height="${h}" fill="#b3eeee"/>`;
  });
  if (cityValue != null) svg += `<line x1="${pos(cityValue)}" x2="${pos(cityValue)}" y1="0" y2="${height}" stroke="#0e8080" stroke-width="2" stroke-dasharray="3 2"/>`;
  if (threshold != null) svg += `<line x1="${pos(threshold)}" x2="${pos(threshold)}" y1="0" y2="${height + 4}" stroke="#000" stroke-width="2"/>`;
  return svg + "</svg>";
};

APP.criterionHtml = function (k, i) {
  const m = APP.criterionMeta(k);
  const head = `<div class="head-row"><input type="checkbox" data-i="${i}" data-field="active" ${k.active ? "checked" : ""}><strong>${APP.escape(APP.criterionTitle(k))}</strong>${APP.infoButton("k" + i)}`;
  const remove = `<button data-i="${i}" data-field="remove" title="Kriterium entfernen">×</button></div>` + APP.infoBlock(m, "k" + i);
  if (m.type === "yes_no") {
    return `<div class="criterion">${head}<select data-i="${i}" data-field="threshold"><option value="1" ${k.threshold === 1 ? "selected" : ""}>ja</option>` +
      `<option value="0" ${k.threshold === 0 ? "selected" : ""}>nein</option></select>${remove}</div>`;
  }
  const values = APP.areaValues(k.indicator, APP.unitId(k));
  const min = Math.min(...values), max = Math.max(...values), stepSize = m.rank > 0 ? 0.5 : (max - min) / 200 || 1;
  const cityValue = APP.shownOf(APP.unitId(k), APP.data.city_values[APP.unitId(k)]);
  return `<div class="criterion">${head}<button data-i="${i}" data-field="op" title="Vergleich umschalten">${k.op === ">=" ? "≥" : "&lt;"}</button>` +
    `<span id="value-${i}">${APP.escape(APP.thresholdLabel(APP.unitId(k), k.threshold))}</span>${remove}` +
    APP.histogram(values, APP.shownOf(APP.unitId(k), k.threshold), cityValue, min, max, i) +
    `<input type="range" data-i="${i}" data-field="threshold" min="${min}" max="${max}" step="${stepSize}" value="${k.threshold ?? min}">` +
    (cityValue == null ? "" : `<div class="note">Stadt ${APP.escape(APP.valueText(APP.unitId(k), cityValue))}</div>`) +
    (k.note && k.op === "<" ? `<div class="note criterion-note">${APP.escape(k.note)}</div>` : "") + `</div>`;
};

APP.buildCriteria = function () {
  const el = document.getElementById("criteria");
  if (!el) return;
  el.innerHTML = APP.criteria.map(APP.criterionHtml).join("") || `<p class="note">Noch gibt es kein Kriterium. Unten lässt sich eins hinzufügen.</p>`;
  el.querySelectorAll("[data-i]").forEach((e) => {
    const eventName = e.tagName === "BUTTON" ? "click" : e.type === "range" ? "input" : "change";
    e.addEventListener(eventName, APP.criterionChanged);
  });
  APP.bindInfo(el);
  const custom = document.getElementById("custom-note"), words = APP.LEVEL_NAMES[APP.candidateLevel()];
  if (custom) custom.hidden = APP.template !== "custom";
  const explain = document.getElementById("candidates-note");
  if (explain) explain.textContent = APP.candidatesNote(words);
  const choosable = APP.data.catalog.filter((m) => m.levels.includes(APP.candidateLevel()) && m.criterion !== false && (m.type === "number" || m.type === "yes_no"));
  document.getElementById("new-criterion").innerHTML = `<select id="criterion-new"><option value="">+ Kriterium hinzufügen</option>` +
    choosable.map((m) => `<option value="${m.id}">${APP.escape(m.group)}: ${APP.escape(m.title)}</option>`).join("") + `</select>`;
  document.getElementById("criterion-new").addEventListener("change", (e) => {
    const m = APP.meta[e.target.value];
    if (!m) return;
    const yesNo = m.type === "yes_no";
    APP.criteria.push({ indicator: m.id, op: yesNo ? "==" : ">=", active: true,
      threshold: yesNo ? 1 : APP.snapThreshold(m.id, APP.data.city_values[m.id] ?? APP.median(APP.areaValues(m.id))) });
    APP.buildCriteria();
    APP.updateCandidates();
  });
};

APP.criterionChanged = function (ev) {
  const el = ev.currentTarget, i = Number(el.dataset.i), k = APP.criteria[i];
  if (el.dataset.field === "active") k.active = el.checked;
  if (el.dataset.field === "threshold") {
    k.threshold = APP.snapThreshold(APP.unitId(k), Number(el.value));
    const display = document.getElementById("value-" + i);
    if (display) display.textContent = APP.thresholdLabel(APP.unitId(k), k.threshold);
    const hist = document.getElementById("hist-" + i);
    if (hist) {
      const values = APP.areaValues(k.indicator, APP.unitId(k)), unit = APP.unitId(k);
      hist.outerHTML = APP.histogram(values, APP.shownOf(unit, k.threshold), APP.shownOf(unit, APP.data.city_values[unit]), Math.min(...values), Math.max(...values), i);
    }
  }
  if (el.dataset.field === "op") { k.op = k.op === ">=" ? "<" : ">="; APP.buildCriteria(); }
  if (el.dataset.field === "remove") { APP.criteria.splice(i, 1); APP.buildCriteria(); }
  APP.updateCandidates();
};

// „A“, „A und B“, „A, B und C“
APP.missingText = (names) => (names.length > 1 ? `${names.slice(0, -1).join(", ")} und ${names.at(-1)}` : names[0] ?? "");
// The line of a tooltip and of the second hit group: how many criteria an area meets, which ones it misses and for which
// the value is unknown („k. A. bei …“; such a criterion counts as not met)
APP.candidateLine = function (b, n) {
  if (!b || n === 0) return "";
  const unknown = b.unknown ?? [];
  if (b.missing.length === 0 && unknown.length === 0) return `Alle ${n} Kriterien erfüllt.`;
  const missing = b.missing.length ? `Es ${b.missing.length === 1 ? "fehlt" : "fehlen"} ${APP.missingText(b.missing)}` : "";
  const none = unknown.length ? `k. A. bei ${APP.missingText(unknown)}` : "";
  return `${b.met} von ${n} Kriterien erfüllt. ${[missing, none].filter(Boolean).join(", ")}.`;
};
// What the second hit group says after the name: the first criterion that is missing or unknown
APP.nearText = (b) => (b.missing.length ? `es fehlt ${b.missing[0]}` : `k. A. bei ${(b.unknown ?? [])[0]}`);
APP.matchCountText = function (full, near, n, level) {
  if (n === 0) return "";
  const one = full === 1;
  const first = `${full} ${one ? APP.LEVEL_SINGULAR[level] : APP.LEVEL_NAMES[level]} ${one ? "erfüllt" : "erfüllen"} alle Kriterien`;
  return n === 1 ? first + "." : `${first}, ${near} alle bis auf eins.`;
};

APP.buildMatches = function () {
  const el = document.getElementById("matches");
  if (!el) return;
  const n = APP.activeCriteria().length, level = APP.candidateLevel();
  const byName = (a, b) => a.name.localeCompare(b.name, "de");
  const full = APP.evaluation.filter((b) => b.full).sort(byName);
  const near = n > 1 ? APP.evaluation.filter((b) => b.met === n - 1).sort(byName) : [];
  const group = (title, list, text) => (list.length
    ? `<h3>${title} (${list.length})</h3><ol class="matches">${list.map((b) => `<li data-id="${APP.escape(b.id)}"${b.full ? ` class="full"` : ""}>${text(b)}</li>`).join("")}</ol>` : "");
  el.innerHTML = full.length + near.length
    ? group("Alle Kriterien erfüllt", full, (b) => APP.areaLabel(b, level, true)) +
      group("Ein Kriterium fehlt", near, (b) => `${APP.areaLabel(b, level, true)} <span class="note">· ${APP.escape(APP.nearText(b))}</span>`)
    : `<p class="note">keine Treffer</p>`;
  el.querySelectorAll("li[data-id]").forEach((li) => li.addEventListener("click", () => APP.zoomTo(li.dataset.id)));
  const count = document.getElementById("match-count");
  if (count) { count.textContent = APP.matchCountText(full.length, near.length, n, level); count.hidden = !count.textContent; }
};

APP.zoomTo = function (id) {
  APP.layers[APP.candidateLevel()].eachLayer((l) => { if (l.feature.properties.id === id) APP.map.fitBounds(l.getBounds(), { maxZoom: 15, paddingBottomRight: [0, APP.panelHeight()] }); });
  if (APP.showProfile) APP.showProfile(id, false);
};

APP.csvRow = (fields) => fields.map((f) => {
  const s = String(f ?? "");
  return /[;"\r\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}).join(";");

APP.csvText = function () {
  const chosen = APP.activeCriteria();
  const districts = APP.candidateLevel() === "district";
  const props = Object.fromEntries(APP.properties(APP.candidateLevel()).map((p) => [p.id, p]));
  // the values and thresholds as the map shows them: the file agrees with the "erfüllt" column (a rank is not rounded)
  const text = (k, x) => (APP.criterionMeta(k).type === "yes_no" ? APP.withUnit(APP.unitId(k), x) : APP.shownText(APP.unitId(k), x));
  const value = (k, p) => text(k, p[k.indicator]);
  const area = (p) => (districts ? [p.id, p.name, p.quarter] : [p.name]);
  const rows = [APP.csvRow([...(districts ? ["Bezirk-Nr.", "Bezirk", "Stadtteil"] : ["Stadtteil"]),
    ...chosen.map((k) => `${APP.criterionTitle(k)} (${k.op === "<" ? "<" : k.op === "==" ? "=" : "≥"} ${text(k, k.threshold)})`), "erfüllt", "von"])];
  for (const b of [...APP.evaluation].sort((a, c) => c.met - a.met || a.name.localeCompare(c.name, "de"))) {
    const p = props[b.id];
    rows.push(APP.csvRow([...area(p), ...chosen.map((k) => value(k, p)), b.met, chosen.length]));
  }
  return "\uFEFF" + rows.join("\r\n");
};

// The file name is visible and stays German (pipeline/use_cases/candidates/README.md).
APP.DOWNLOAD_SLUGS = { social_preservation: "milieuschutz", coop: "geno", public_company: "oeffentliche_gesellschaften", custom: "eigene" };
APP.downloadName = (id) => `kandidaten_${APP.DOWNLOAD_SLUGS[id] ?? id}.csv`;

APP.saveCsv = function () {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([APP.csvText()], { type: "text/csv;charset=utf-8" }));
  a.download = APP.downloadName(APP.template);
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
};

// The tab note: black and dashed line, the colour, and what a bar of the histograms counts (Bezirke or Stadtteile)
APP.candidatesNote = (areas) => "Der schwarze Strich ist die Schwelle. Der gestrichelte Strich ist der Wert für ganz Frankfurt. " +
  `Je dunkler ein Gebiet, desto mehr Kriterien erfüllt es. Jeder Balken zählt die ${areas} in diesem Bereich.`;

APP.buildCandidates = function () {
  const el = document.getElementById("tab-candidates");
  el.innerHTML = `<h3>Vorlage</h3><select id="template">${APP.data.templates.map((v) => `<option value="${v.id}">${APP.escape(v.title)}</option>`).join("")}` +
    `<option value="custom">Eigene Abfrage</option></select>` +
    `<p id="template-lead" class="note"></p>` +
    `<button type="button" id="match-count" class="link"></button>` +
    `<p id="candidates-note" class="note"></p>` +
    `<div id="criteria"></div><div id="new-criterion"></div><p id="custom-note" class="note" hidden>${APP.escape(APP.data.custom_note)}</p>` +
    `<button id="csv">Als CSV speichern</button><div id="matches"></div>`;
  document.getElementById("template").addEventListener("change", (e) => APP.setTemplate(e.target.value));
  document.getElementById("csv").addEventListener("click", APP.saveCsv);
  document.getElementById("match-count").addEventListener("click", () => document.getElementById("matches").scrollIntoView({ block: "start" }));
  APP.setTemplate(APP.data.templates[0].id);
};
