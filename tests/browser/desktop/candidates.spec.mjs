// Candidates: JavaScript gives the same matches as the Python pipeline, the criteria, the CSV text, the match list,
// the hit border, the charts of the criteria, the template per Stadtteil, the level of the layers after the
// candidates, and the tooltip line, hit headings and count line.
import { readFileSync } from "node:fs";
import { test } from "../fixtures.mjs";
import { integers, paths } from "../helpers/common.mjs";

// Every test starts on the tab Stadt on the district level (indicator SOC_MIN_INCOME, the fallback of the
// districts), so a template on Stadtteile has to switch the level itself.
test.beforeEach(async ({ mapPage: page }) => {
  await page.evaluate(() => { APP.openTab("city"); APP.setLevel("district"); });
});

test("templates give the matches of the pipeline", async ({ mapPage: page, check }) => {
  const rows = readFileSync(paths.candidatesCsv, "utf8").trim().split(/\r?\n/);
  const head = rows[0].split(",");
  const ref = rows.slice(1).map((line) => Object.fromEntries(line.split(",").map((w, i) => [head[i], w])));
  // pipeline/use_cases/candidates/catalog.py: each template on its level; coop last, the checks below expect it
  for (const template of ["social_preservation", "public_company", "coop"]) {
    const js = await page.evaluate((id) => { APP.openTab("candidates"); APP.setTemplate(id); return { m: APP.matches(), level: APP.state.level }; }, template);
    const expected = ref.filter((r) => r.template === template);
    check(expected.length > 0 && js.level === expected[0].level, `${template}: map on the level of the template (${js.level})`);
    check(js.m.length === expected.length, `${template}: ${js.m.length} instead of ${expected.length} areas`);
    const byId = Object.fromEntries(js.m.map((t) => [t.id, t]));
    for (const r of expected) {
      const t = byId[r.area];
      check(t && t.met === Number(r.met) && Number(t.full) === Number(r.full), `${template}: area ${r.area} differs`);
    }
  }
  // the cooperative gap works on Stadtteile like the template of ABG and NH
  check(await page.evaluate(() => APP.state.level) === "quarter", "the last template (coop) is on Stadtteile");
  check(await page.evaluate(() => APP.state.mode === "candidates" && !document.querySelector(".legend .legend-note")),
    "candidates legend: no note, no line");
});

test("CSV row is escaped", async ({ mapPage: page, check }) => {
  check(await page.evaluate(() => APP.csvRow(["a;b", 'c"d', 3])) === '"a;b";"c""d";3', "CSV row is escaped");
});

test("criteria of the cooperative gap and the ⓘ of LAND_PENDING_PLAN", async ({ mapPage: page, check }) => {
  await page.evaluate(() => { APP.openTab("candidates"); APP.setTemplate("coop"); });
  check(await page.evaluate(() => document.querySelectorAll("#criteria .criterion").length) === 3, "three criteria for the cooperative gap");
  // ⓘ per criterion: indicators without their own layer (LAND_PENDING_PLAN) also show their protocol
  const planInfo = await page.evaluate(() => {
    const i = APP.criteria.findIndex((c) => c.indicator === "LAND_PENDING_PLAN");
    const button = document.querySelector(`#criteria .info-button[data-info="k${i}"]`), info = document.getElementById(`info-k${i}`);
    if (!button || !info) return null;
    const before = info.hidden;
    button.click();
    // the lines Rechnung and Regel of the catalog, under the labels of the ⓘ protocol
    const m = APP.meta.LAND_PENDING_PLAN, line = (key) => m[key] && `${APP.PROTOCOL.find(([k]) => k === key)[1]}: ${m[key]}`;
    return { before, after: info.hidden, text: protocolText(info), calc: line("calc"), rule: line("rule") };
  });
  check(planInfo && planInfo.before && !planInfo.after && planInfo.calc && planInfo.rule && planInfo.text.includes(planInfo.calc)
    && planInfo.text.includes(planInfo.rule), "criterion LAND_PENDING_PLAN has an ⓘ with its protocol: " + JSON.stringify(planInfo));
});

test("criterion on the upper end of the range", async ({ mapPage: page, check }) => {
  // a criterion on the upper end of the range has its own label in the tab and in the CSV
  const upper = await page.evaluate(() => { APP.openTab("candidates"); APP.setTemplate("public_company");
    const titles = [...document.querySelectorAll("#criteria .criterion strong")].map((s) => s.textContent);
    const notes = [...document.querySelectorAll("#criteria .criterion .note")].map((s) => s.textContent);
    const csv = APP.csvText().split("\r\n")[0];
    // the city value of each criterion as the map writes it, and the own label of the criterion on the upper end
    // (catalog of the template) next to the title of its indicator
    const city = (id) => APP.valueText(id, APP.shownOf(id, APP.data.city_values[id]));
    const k = APP.criteria.find((c) => c.city === "OWN_PUBLIC");
    APP.openTab("city");
    return { titles, notes, csv, own: city("OWN_PUBLIC"), income: city("SOC_MIN_INCOME"), label: k?.label, indicatorTitle: k && APP.meta[k.city].title }; });
  // docs/texts.md, Numbers: the city value of an estimate carries its tilde in every place
  check(/^~\d+,\d %$/.test(upper.own) && upper.notes.some((t) => t.endsWith(" " + upper.own))
    && /^\d+,\d+ %$/.test(upper.income) && upper.notes.some((t) => t.endsWith(" " + upper.income)),
  "candidates tab: city value of the ownership criterion with a tilde, Mindestsicherung without: " + JSON.stringify(upper.notes));
  check(upper.label && upper.label !== upper.indicatorTitle && upper.titles.includes(upper.label) && upper.csv.includes(upper.label + " (< "),
    "criterion on the upper end has its label in the tab and the CSV: " + JSON.stringify(upper));
  await page.evaluate(() => APP.openTab("city"));
  check(await page.evaluate(() => APP.state.mode) === "layer", "back in layer mode");
});

test("download names keep the German slug", async ({ mapPage: page, check }) => {
  const DOWNLOAD_NAMES = { social_preservation: "kandidaten_milieuschutz.csv", coop: "kandidaten_geno.csv",
    public_company: "kandidaten_oeffentliche_gesellschaften.csv", custom: "kandidaten_eigene.csv" };
  for (const [id, name] of Object.entries(DOWNLOAD_NAMES)) {
    check(await page.evaluate((i) => APP.downloadName(i), id) === name, `download name of template ${id} keeps the German slug`);
  }
});

test("CSV text and match list on districts", async ({ mapPage: page, check }) => {
  // CSV text and match list: district number visible, BOM as first character
  const csv = await page.evaluate(() => { APP.openTab("candidates"); APP.setTemplate("social_preservation"); return APP.csvText(); });
  check(csv.charCodeAt(0) === 0xfeff, "CSV starts with a BOM");
  // every row starts with the number of its district, then its name and its Stadtteil (data of the page)
  const csvRows = await page.evaluate((text) => {
    const props = Object.fromEntries(APP.properties("district").map((p) => [p.id, p]));
    const [header, ...rows] = text.slice(1).split("\r\n").map((r) => r.split(";"));
    return { header: header.length, rows: rows.length, wrong: rows.filter(([id, name, quarter]) => !props[id] || props[id].name !== name || props[id].quarter !== quarter) };
  }, csv);
  check(csvRows.header > 3 && csvRows.rows > 0 && csvRows.wrong.length === 0, "CSV header has the district number as first column: " + JSON.stringify(csvRows.wrong[0]));
  // docs/texts.md, Area names: on districts every name carries its number, "Name (Bezirk 70) · n von m". Each item is
  // the label of its area (APP.areaLabel with the Stadtteil) and holds its number; an item of the second group adds
  // what is missing (APP.nearText).
  const matchTexts = await page.evaluate(() => {
    const un = (h) => { const d = document.createElement("div"); d.innerHTML = h; return d.textContent; };
    return [...document.querySelectorAll("#matches li[data-id]")].map((li) => {
      const b = APP.evaluationById[li.dataset.id], label = un(APP.areaLabel(b, "district", true));
      return { text: li.textContent.trim(), want: b.full ? label : `${label} · ${APP.nearText(b)}`, number: label.includes(b.id) };
    });
  });
  const wrongMatch = matchTexts.find((t) => t.text !== t.want || !t.number);
  check(matchTexts.length > 0 && !wrongMatch,
    "match list on districts: name (Bezirk n), the second group adds what is missing: " + JSON.stringify(wrongMatch));
  // the label holds the name, then the number, then the Stadtteil where the name lacks it
  const labels = await page.evaluate(() => [APP.areaLabel({ id: "70", name: "Osthafen", quarter: "Ostend" }, "district", true),
    APP.areaLabel({ id: "70", name: "Osthafen", quarter: "Ostend" }, "district"),
    APP.areaLabel({ id: "5", name: "Gallus", quarter: "Gallus" }, "district", true),
    APP.areaLabel({ id: "Gallus", name: "Gallus" }, "quarter", true)]);
  const inOrder = (text, parts) => parts.every((part, i) => text.indexOf(part) >= 0 && (i === 0 || text.indexOf(part) > text.indexOf(parts[i - 1])));
  check(labels[0].startsWith("Osthafen") && inOrder(labels[0], ["Osthafen", "70", "Ostend"])
    && labels[1].startsWith("Osthafen") && labels[1].includes("70") && !labels[1].includes("Ostend")
    && labels[2].startsWith("Gallus") && labels[2].includes("5") && labels[2].split("Gallus").length === 2
    && labels[3] === "Gallus",
  "area label: number on districts only, quarter only where the name lacks it: " + JSON.stringify(labels));
});

test("a hit has the orange border", async ({ mapPage: page, check }) => {
  // docs/design.md, Candidates: a hit has its own border colour, the legend and the notes agree
  const hit = await page.evaluate(() => {
    APP.openTab("candidates"); APP.setTemplate("social_preservation");
    const full = APP.evaluation.find((b) => b.full), none = APP.evaluation.find((b) => !b.full && b.met > 0);
    const layerOf = (id) => Object.values(APP.layers.district._layers).find((l) => l.feature.properties.id === id);
    // the help line of the candidates tab: its <strong> is the label of the tab button
    const tabLabel = document.querySelector('#tabs button[data-tab="candidates"]').textContent.trim();
    const helpLine = [...document.querySelectorAll("#tab-help p")].find((p) => p.querySelector("strong")?.textContent.replace(":", "") === tabLabel);
    return { border: APP.data.hit_border, hit: layerOf(full.id).options.color, hitWeight: layerOf(full.id).options.weight,
      other: layerOf(none.id).options.color, legend: document.querySelector(".legend").innerHTML,
      note: document.getElementById("candidates-note").textContent, want: APP.candidatesNote(APP.LEVEL_NAMES.district),
      help: document.getElementById("tab-help").textContent,
      helpLine: helpLine && helpLine.textContent.slice(helpLine.querySelector("strong").textContent.length).trim() };
  });
  check(hit.border === "#e8590c" && hit.hit === "#e8590c" && hit.hitWeight === 3.5 && hit.other !== "#e8590c", "a hit has the orange border: " + JSON.stringify(hit));
  // the swatch with the orange border has its own label
  const hitKey = hit.legend.match(/border:3px solid #e8590c"><\/i>([^<]*)</);
  check(hitKey && hitKey[1].trim() !== "" && !/#000/.test(hit.legend), "legend shows the orange border: " + hit.legend);
  check(hit.want && hit.note === hit.want, "note of the candidates: " + hit.note);
  // "Schwarzer Rand" is the old wording of the black border, banned since the border is orange
  check(hit.helpLine && !hit.help.includes("Schwarzer Rand"), "help names the orange border: " + JSON.stringify(hit.helpLine));
});

test("every criterion chart: threshold and city value", async ({ mapPage: page, check }) => {
  // the note is true in every criterion chart: the solid black line is the threshold, the dashed line the city value
  const charts = await page.evaluate(() => {
    const out = [];
    for (const t of APP.data.templates) {
      APP.openTab("candidates"); APP.setTemplate(t.id);
      APP.criteria.forEach((k, i) => {
        const svg = document.getElementById("hist-" + i);
        if (!svg) { out.push({ template: t.id, indicator: k.indicator, yesNo: true }); return; }
        const unit = APP.unitId(k), values = APP.areaValues(k.indicator, unit), min = Math.min(...values), max = Math.max(...values), pos = (x) => ((APP.shownOf(unit, x) - min) / ((max - min) || 1)) * 300;
        const lines = [...svg.querySelectorAll("line")].map((l) => ({ x: Number(l.getAttribute("x1")), dashed: l.hasAttribute("stroke-dasharray"), stroke: l.getAttribute("stroke") }));
        const city = APP.data.city_values[APP.unitId(k)];
        out.push({ template: t.id, indicator: k.indicator, lines, threshold: pos(k.threshold), city: city == null ? null : pos(city),
          wrong: lines.filter((l) => l.dashed ? city == null || l.x !== pos(city) : l.stroke !== "#000" || l.x !== pos(k.threshold)).length,
          solid: lines.filter((l) => !l.dashed).length, dashed: lines.filter((l) => l.dashed).length });
      });
    }
    return out;
  });
  check(charts.length >= 9 && charts.filter((c) => !c.yesNo).every((c) => c.wrong === 0 && c.solid === 1 && c.dashed === (c.city == null ? 0 : 1)),
    "every chart: solid black = threshold, dashed = city value: " + JSON.stringify(charts.filter((c) => !c.yesNo && (c.wrong || c.solid !== 1))));
});

test("after the slider moves, the threshold line follows", async ({ mapPage: page, check }) => {
  // after the slider moves, the threshold line follows and the city line stays
  const moved = await page.evaluate(() => {
    APP.openTab("candidates"); APP.setTemplate("social_preservation");
    const i = APP.criteria.findIndex((k) => APP.criterionMeta(k).type === "number");
    const slider = document.querySelector(`input[type="range"][data-i="${i}"]`);
    const before = [...document.querySelectorAll(`#hist-${i} line`)].map((l) => l.getAttribute("x1"));
    slider.value = String(Number(slider.min) + (Number(slider.max) - Number(slider.min)) * 0.8);
    slider.dispatchEvent(new Event("input", { bubbles: true }));
    const after = [...document.querySelectorAll(`#hist-${i} line`)].map((l) => ({ x: l.getAttribute("x1"), dashed: l.hasAttribute("stroke-dasharray") }));
    return { before, after };
  });
  check(moved.after.length === 2 && moved.after.filter((l) => l.dashed).length === 1 && moved.after.find((l) => l.dashed).x === moved.before[0]
    && moved.after.find((l) => !l.dashed).x !== moved.before[1], "after the slider moves, the solid line follows, the dashed one stays: " + JSON.stringify(moved));
});

test("the template per Stadtteil", async ({ mapPage: page, check }) => {
  // the template per Stadtteil (pipeline/use_cases/candidates/README.md); it starts in the tab Kandidaten with the
  // template social_preservation on Stadtbezirke, so the switch to public_company has to change the level
  await page.evaluate(() => { APP.openTab("candidates"); APP.setTemplate("social_preservation"); });
  const perQuarter = await page.evaluate(() => {
    APP.setTemplate("public_company");
    const options = [...document.querySelectorAll("#criterion-new option")].map((o) => o.value);
    const out = { level: APP.state.level, quarterShown: APP.map.hasLayer(APP.layers.quarter), districtShown: APP.map.hasLayer(APP.layers.district),
      csv: APP.csvText().slice(1).split("\r\n"), options, hist: document.querySelector("#criteria svg")?.getAttribute("aria-label"),
      legend: APP.legendDiv.innerHTML, first: document.querySelector("#matches li")?.dataset.id,
      // the column of each criterion: its title, the comparison and the threshold as the map shows it
      area: APP.LEVEL_SINGULAR.quarter, levelName: APP.LEVEL_NAMES.quarter,
      criteria: APP.activeCriteria().map((k) => ({ title: APP.criterionTitle(k), op: k.op === "<" ? "<" : "≥", value: APP.shownText(APP.unitId(k), k.threshold) })) };
    APP.zoomTo(out.first);
    out.profile = document.querySelector("#tab-area h2")?.textContent;
    APP.openTab("candidates");
    APP.setTemplate("social_preservation");
    out.back = APP.state.level;
    return out;
  });
  check(perQuarter.level === "quarter" && perQuarter.quarterShown && !perQuarter.districtShown && perQuarter.back === "district",
    "the template per Stadtteil switches the map to Stadtteile and back: " + JSON.stringify({ level: perQuarter.level, back: perQuarter.back }));
  // header: the Stadtteil, one column per criterion, then two columns (met, of)
  const header = perQuarter.csv[0].split(";"), crit = perQuarter.criteria;
  check(crit.length === 2 && header.length === crit.length + 3 && header[0] === perQuarter.area
    && crit.every((c, i) => /^\d+,\d$/.test(c.value) && header[i + 1] === `${c.title} (${c.op} ${c.value})`)
    && header.slice(-2).every((h) => h !== "") && perQuarter.csv.length === 46, "CSV per Stadtteil: header and 45 rows: " + perQuarter.csv[0]);
  check(perQuarter.options.includes("OWN_PUBLIC") && !perQuarter.options.includes("SOC_INDEX") && perQuarter.hist && perQuarter.hist.endsWith(" " + perQuarter.levelName),
    "criteria and histogram per Stadtteil: " + perQuarter.hist);
  // the grey swatch of the small districts (under 1,000 residents) is missing
  check(!perQuarter.legend.includes("background:#d0d0d0") && perQuarter.profile === perQuarter.first,
    "legend without small districts, a click in the list opens the Stadtteil: " + perQuarter.profile);
});

test("layers keep their own level after the candidates", async ({ mapPage: page, check }) => {
  // back in the tab Stadt, a layer keeps the level it had before the candidates
  const layerLevel = await page.evaluate(() => {
    APP.openTab("city"); APP.setLevel("district"); APP.setIndicator("HOU_RENTERS");
    APP.openTab("candidates"); APP.setTemplate("public_company");
    const inCandidates = APP.state.level;
    APP.openTab("city");
    const back = APP.state.level;
    APP.setLevel("quarter");
    APP.openTab("candidates"); APP.setTemplate("social_preservation");
    APP.openTab("city");
    const back2 = APP.state.level;
    APP.setLevel("district"); APP.openTab("candidates");
    return { inCandidates, back, back2 };
  });
  check(layerLevel.inCandidates === "quarter" && layerLevel.back === "district" && layerLevel.back2 === "quarter",
    "layers keep their own level after the candidates: " + JSON.stringify(layerLevel));
});

test("tooltip line, hit headings and count line", async ({ mapPage: page, check }) => {
  // 2.5, 3.3, 3.4 candidates: tooltip line, two hit headings, count line
  const r = await page.evaluate(() => {
    APP.openTab("candidates"); APP.setTemplate("social_preservation");
    const n = APP.activeCriteria().length, level = APP.candidateLevel();
    const byName = (a, b) => a.name.localeCompare(b.name, "de"), ev = APP.evaluation;
    const full = ev.filter((b) => b.full).sort(byName), near = ev.filter((b) => b.met === n - 1).sort(byName);
    const props = Object.fromEntries(APP.properties(level).map((p) => [p.id, p]));
    const tip = (b) => APP.tooltipText(props[b.id]);
    const un = (h) => { const d = document.createElement("div"); d.innerHTML = h; return d.textContent; };
    const lists = () => [...document.querySelectorAll("#matches ol.matches")].map((o) => [...o.querySelectorAll("li")].map((li) => li.textContent.trim()));
    const heads = () => [...document.querySelectorAll("#matches h3")].map((h) => h.textContent);
    const out = { n, full: full.length, near: near.length, heads: heads(), lists: lists(),
      miss: [APP.missingText(["A"]), APP.missingText(["A", "B"]), APP.missingText(["A", "B", "C"])],
      mt: [APP.matchCountText(APP.evaluation.filter((b) => b.full).length, near.length, n, level), APP.matchCountText(1, 1, 5, "district"),
        APP.matchCountText(6, 27, 3, "quarter"), APP.matchCountText(1, 0, 2, "quarter"), APP.matchCountText(4, 0, 1, "district"), APP.matchCountText(0, 0, 0, "district")],
      count: document.getElementById("match-count").textContent, countTag: document.getElementById("match-count").tagName,
      order: ["template", "template-lead", "match-count", "candidates-note", "criteria", "new-criterion", "custom-note", "csv", "matches"]
        .map((id) => document.getElementById(id)).every((e, i, a) => i === 0 || (a[i - 1].compareDocumentPosition(e) & Node.DOCUMENT_POSITION_FOLLOWING)),
      firstText: full.slice(0, 1).map((b) => un(APP.areaLabel(props[b.id], level, true))),
      secondText: near.slice(0, 1).map((b) => `${un(APP.areaLabel(props[b.id], level, true))} · ${APP.nearText(b)}`),
      // a tooltip of each kind: the name in bold, then a line with the numbers and the names of what is missing
      tips: [full, near, ev.filter((b) => b.met === n - 2)].map((group) => group.slice(0, 1).map((b) => ({ tip: tip(b),
        head: `<strong>${APP.areaLabel(props[b.id], APP.state.level)}</strong><br>`, missing: b.missing.map(APP.escape) }))),
      fullItems: [...document.querySelectorAll("#matches ol.matches")].map((o) => [...o.querySelectorAll("li")].every((li) => li.classList.contains("full"))),
      levelNames: APP.LEVEL_NAMES, singular: APP.LEVEL_SINGULAR };
    out.names = ev.every((b) => b.missing.length + b.unknown.length === n - b.met);
    const boxes = [...document.querySelectorAll("#criteria input[data-field=active]")];
    boxes.forEach((c) => { c.checked = false; c.dispatchEvent(new Event("change", { bubbles: true })); });
    const any = ev[0] && props[APP.evaluation[0].id];
    out.none = { tip: APP.tooltipText(any) === `<strong>${APP.areaLabel(any, APP.state.level)}</strong>`, note: [...document.querySelectorAll("#matches p.note")].map((e) => e.textContent),
      heads: heads(), hidden: document.getElementById("match-count").hidden };
    boxes.forEach((c, i) => { if (i === 0) { c.checked = true; c.dispatchEvent(new Event("change", { bubbles: true })); } });
    out.one = { heads: heads(), count: document.getElementById("match-count").textContent, want: APP.matchCountText(APP.evaluation.filter((b) => b.full).length, 0, 1, level) };
    APP.setTemplate("social_preservation");
    const tab = document.getElementById("tab-candidates"), btn = document.getElementById("match-count");
    tab.scrollTop = 0; btn.click();
    const t = tab.getBoundingClientRect(), m = document.getElementById("matches").getBoundingClientRect();
    out.scrolled = m.top >= t.top - 1 && m.top < t.bottom;
    APP.openTab("city");
    return out;
  });
  const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);
  // „A“, „A und B“, „A, B und C“: the names in order, a comma between the first ones, the same word before the last
  const [m1, m2, m3] = r.miss, joiner = m2.slice(1, -1);
  check(m1 === "A" && m2.startsWith("A ") && m2.endsWith(" B") && !m2.includes(",") && m3 === "A, B" + joiner + "C",
    "10 2.5: missingText: " + JSON.stringify(r.miss));
  // full: the line holds the number of criteria; one or two missing: it starts with the number met, holds the number
  // of criteria and names what is missing, in order
  const [tipFull, tipNear, tip3] = r.tips, rest = (t) => t.tip.slice(t.head.length);
  const inOrder = (text, parts) => parts.every((part, i) => text.indexOf(part) >= 0 && (i === 0 || text.indexOf(part) > text.indexOf(parts[i - 1])));
  check(r.names && [...tipFull, ...tipNear, ...tip3].every((t) => t.tip.startsWith(t.head))
    && tipFull.every((t) => rest(t).includes(` ${r.n} `))
    && tipNear.every((t) => rest(t).startsWith(`${r.n - 1} `) && rest(t).includes(` ${r.n} `) && inOrder(rest(t), t.missing.slice(0, 1)))
    && tip3.every((t) => rest(t).startsWith(`${r.n - 2} `) && rest(t).includes(` ${r.n} `) && inOrder(rest(t), t.missing.slice(0, 2)))
    && tipNear.length + tipFull.length > 0 && tip3.length > 0, "10 2.5: tooltip names the missing criteria: " + JSON.stringify(r.tips));
  check(r.none.tip, "10 2.5: no active criterion, tooltip is the name only");
  // a heading per group with hits, each with its count; the group of full hits first
  const groups = [r.full, r.near].filter((c) => c > 0), title = (h) => h.replace(/ \(\d+\)$/, "");
  check(r.heads.length === groups.length && r.heads.every((h, i) => h.endsWith(` (${groups[i]})`) && title(h).trim() !== "")
    && new Set(r.heads.map(title)).size === r.heads.length && r.lists.length === r.heads.length
    && same(r.fullItems, [r.full > 0, false].slice(0, r.heads.length)), "10 3.3: two hit headings with counts: " + JSON.stringify(r.heads));
  check((r.full === 0 || r.lists[0][0] === r.firstText[0]) && (r.near === 0 || r.lists.at(-1)[0] === r.secondText[0]) && r.lists.every((l) => l.length > 0),
    "10 3.3: hit items: " + JSON.stringify([r.lists.map((l) => l[0]), r.firstText, r.secondText]));
  const fullTitle = r.full > 0 && title(r.heads[0]), nearTitle = r.near > 0 && title(r.heads.at(-1));
  check(r.one.heads.length === 1 && fullTitle && title(r.one.heads[0]) === fullTitle && nearTitle && !r.one.heads.some((h) => title(h) === nearTitle),
    "10 3.3: one active criterion has only the first heading: " + JSON.stringify(r.one.heads));
  check(r.none.heads.length === 0 && r.none.note.length === 1 && r.none.note[0].trim() !== "", "10 3.3: no hits: " + JSON.stringify(r.none));
  // the count line holds the two counts and the name of the level (APP.LEVEL_NAMES, singular for one)
  check(r.countTag === "BUTTON" && same(integers(r.count), [r.full, r.near]) && r.count.includes(r.full === 1 ? r.singular.district : r.levelNames.district)
    && r.count === r.mt[0] && r.order, "10 3.4: count line: " + r.count + " order " + r.order);
  // the variants hold their numbers; one area takes the singular of its level; one criterion has only the first clause
  check(same(integers(r.mt[1]), [1, 1]) && r.mt[1].includes(r.singular.district) && !r.mt[1].includes(r.levelNames.district)
    && same(integers(r.mt[2]), [6, 27]) && r.mt[2].includes(r.levelNames.quarter)
    && same(integers(r.mt[3]), [1, 0]) && r.mt[3].includes(r.singular.quarter) && !r.mt[3].includes(r.levelNames.quarter)
    && same(integers(r.mt[4]), [4]) && r.mt[4].includes(r.levelNames.district) && r.mt[5] === "",
  "10 3.4: count line variants: " + JSON.stringify(r.mt));
  check(r.one.count === r.one.want && r.none.hidden, "10 3.4: one criterion: first clause; none: hidden: " + JSON.stringify([r.one.count, r.none.hidden]));
  check(r.scrolled, "10 3.4: click on the count line scrolls the hits into the tab");
});
