// Help and the review of the texts: the help tab, the final review fixes of the self-explaining texts, and the QA
// of Lage and Belastung (shown values decide, shared and missing values are named, the CSV agrees with the map).
// Texts of the map are compared with what the page holds (payload, catalog, APP), never with a literal.
import { test } from "../fixtures.mjs";
import { integers } from "../helpers/common.mjs";

// 5.2 help: the Handy paragraph shows only on the phone
test("help: the Handy paragraph is hidden on the desktop", async ({ mapPage: page, check }) => {
  await page.evaluate(() => APP.openTab("help"));
  check(await page.evaluate(() => document.querySelector("#tab-help .phone-only").offsetHeight === 0), "10 5.2: the Handy paragraph is hidden at 1400 px");
});

// Final review fixes of the self-explaining texts (docs/texts.md, Texts per view)
test.describe("final review fixes of the texts", () => {
  test("Neubau shows the source line of each chart", async ({ mapPage: page, check }) => {
    // 1: the Neubau view keeps the source line of the columns, the rents below have their own; Trend has exactly one, last
    const nc = await page.evaluate(() => { APP.openView("new_construction");
      const v = document.getElementById("view-new-construction"), p = [...v.querySelectorAll("p.source")].map((e) => e.textContent);
      return { p, want: [APP.data.new_construction.source, APP.data.new_construction.rents.source] }; });
    // the columns: a label, a colon and the source; the rents: their source line as the payload holds it
    check(nc.p.length === 2 && /^\S+: /.test(nc.p[0]) && nc.p[0].endsWith(": " + nc.want[0]) && nc.p[1] === nc.want[1], "10 Neubau shows the source line of each chart: " + JSON.stringify(nc));
  });

  test("candidates tab: headings and the upper-end note", async ({ mapPage: page, check }) => {
    // 2: no heading „Treffer“ in the candidates tab
    check(await page.evaluate(() => ![...document.querySelectorAll("#tab-candidates h3")].some((h) => h.textContent.includes("Treffer"))),
      "10 3.3: no heading Treffer");
    // 5: the upper-end note renders only while the criterion checks „unter“
    const flip = await page.evaluate(() => { APP.openTab("candidates"); APP.setTemplate("coop");
      const notes = () => document.querySelectorAll("#criteria .criterion-note").length;
      const idx = [...document.querySelectorAll("#criteria .criterion")].findIndex((c) => c.querySelector(".criterion-note"));
      const toggle = () => document.querySelector(`#criteria button[data-i="${idx}"][data-field="op"]`).click();
      const before = notes(); toggle(); const flipped = notes(); toggle(); const back = notes();
      APP.openTab("city"); return [before, flipped, back]; });
    check(flip[0] === 1 && flip[1] === 0 && flip[2] === 1, "10 3.2: the note follows the comparison: " + JSON.stringify(flip));
  });

  test("the switch line has role status", async ({ mapPage: page, check }) => {
    check(await page.evaluate(() => document.querySelector(".legend-switch").getAttribute("role") === "status"), "10 5.1: switch line has role status");
  });
});

// QA of Lage and Belastung: shown values decide, shared and missing values are named
test.describe("QA of Lage and Belastung", () => {
  test("shown values decide the class", async ({ mapPage: page, check }) => {
    // a value on a break takes the upper class: on districts of HOU_RENTERS every area whose shown value equals a shown break
    const onBreak = await page.evaluate(() => {
      APP.openTab("city"); APP.setLevel("district"); APP.setIndicator("HOU_RENTERS");
      const m = APP.meta.HOU_RENTERS, ramp = APP.rampFor(m), shown = (x) => Math.round(x * 10 ** m.decimals) / 10 ** m.decimals;
      const breaks = APP.breaks, out = { breaks, decimals: m.decimals, on: 0, wrong: [], roundedBreaks: breaks.every((b) => shown(b) === b) };
      for (const l of APP.layers.district.getLayers()) {
        const p = l.feature.properties;
        if (p.small || p.HOU_RENTERS == null) continue;
        const i = breaks.findIndex((b) => b === shown(p.HOU_RENTERS));
        if (i < 0) continue;
        out.on++;
        if (APP.styleBase(l.feature).fillColor !== ramp[i + 1 + APP.rampOffset()]) out.wrong.push(p.id);
      }
      return out;
    });
    check(onBreak.on > 0 && onBreak.wrong.length === 0 && onBreak.roundedBreaks,
      "an area on a shown break has the colour of the upper class (HOU_RENTERS): " + JSON.stringify(onBreak));
    // the same area never has a legend class and a tooltip that disagree: a shown value below a break is in a lower class
    const sorted = await page.evaluate(() => {
      const m = APP.meta.HOU_RENTERS, shown = (x) => Math.round(x * 10 ** m.decimals) / 10 ** m.decimals, ramp = APP.rampFor(m);
      const ps = APP.properties("district").filter((p) => !p.small && p.HOU_RENTERS != null).sort((a, b) => a.HOU_RENTERS - b.HOU_RENTERS);
      const colour = (p) => APP.styleBase({ properties: p }).fillColor;
      return ps.filter((p, i) => i && shown(p.HOU_RENTERS) === shown(ps[i - 1].HOU_RENTERS) && colour(p) !== colour(ps[i - 1])).map((p) => p.id);
    });
    check(sorted.length === 0, "two areas with the same shown value have the same colour: " + sorted);
  });

  test("a shared value is named", async ({ mapPage: page, check }) => {
    // district 202 shares its value of Arbeitslosendichte with 203 and 213
    const shared = await page.evaluate(() => {
      APP.setLevel("district"); APP.setIndicator("SOC_UNEMPLOYED");
      const p = APP.properties("district").find((x) => x.id === "202"), own = APP.properties("district").find((x) => x.id === "10");
      APP.showProfile("202");
      const row = document.querySelector('#tab-area .row[data-layer="SOC_UNEMPLOYED"]');
      const out = { tip: APP.tooltipText(p), own: APP.tooltipText(own), note: row && row.querySelector(".note.shared")?.textContent,
        list: APP.sharedList(p, "SOC_UNEMPLOYED"), ownList: APP.sharedList(own, "SOC_UNEMPLOYED"), noteOwn: null };
      APP.showProfile("10");
      const row10 = document.querySelector('#tab-area .row[data-layer="SOC_UNEMPLOYED"]');
      out.noteOwn = row10 ? row10.querySelectorAll(".note.shared").length : -1;
      return out;
    });
    // the list of the districts that share the value: 202, 203 and 213; the tooltip ends with it in brackets, after
    // words that say so; the profile row names it in a note
    const paren = (/\(([^()]*)\)$/.exec(shared.tip) || [])[1] ?? "";
    const ids = (shared.list ?? "").match(/\d+/g) ?? [];
    check(JSON.stringify(ids) === JSON.stringify(["202", "203", "213"]) && paren.endsWith(" " + shared.list) && paren.length > shared.list.length + 1,
      "tooltip of district 202 names the shared value: " + shared.tip);
    check(shared.note?.endsWith(" " + shared.list) && shared.note.length > shared.list.length + 1, "profile row of district 202 names the shared value: " + shared.note);
    const words = paren.slice(0, paren.length - shared.list.length).trim();
    check(shared.ownList === null && words !== "" && !shared.own.includes(words) && shared.noteOwn === 0, "a district with its own value has no note: " + JSON.stringify([shared.own, shared.noteOwn]));
  });

  test("the deprivation index reads ranks", async ({ mapPage: page, check }) => {
    // Benachteiligungsindex legend names ranks
    const rank = await page.evaluate(() => {
      APP.setLevel("district"); APP.setIndicator("SOC_INDEX");
      // the classes of the legend body: one line per swatch, before the key of the overlays
      const body = APP.legendDiv.querySelector(".legend-body").cloneNode(true);
      body.querySelector(".legend-overlays")?.remove();
      const rows = body.innerHTML.split("<br>").filter((r) => r.startsWith("<i ")).map((r) => r.replace(/<[^>]*>/g, "").trim());
      const tie = APP.properties("district").find((p) => p.SOC_INDEX != null && !Number.isInteger(p.SOC_INDEX));
      return { rows, tie: APP.tooltipText(tie), v: tie.SOC_INDEX, total: APP.meta.SOC_INDEX.rank,
        tieText: APP.rankText("SOC_INDEX", tie.SOC_INDEX, "district"), fixed: [APP.rankText("SOC_INDEX", 44.5, "quarter"), APP.rankText("SOC_INDEX", 44.5, "district")] };
    });
    // a class names its first and last rank (one rank: that rank); the classes run from 1 to the total, in order
    const ranks = rank.rows.map(integers);
    check(rank.rows.length > 1 && ranks.every((n) => n.length === 1 || (n.length === 2 && n[0] < n[1])) && ranks[0][0] === 1 && ranks.at(-1).at(-1) === rank.total
      && ranks.every((n, i) => i === 0 || n[0] === ranks[i - 1].at(-1) + 1), "legend classes read Rang a bis b: " + JSON.stringify(rank.rows));
    // a tie x,5 names the ranks on both sides and the total
    check(rank.tie.endsWith(rank.tieText) && JSON.stringify(integers(rank.tieText)) === JSON.stringify([rank.v - 0.5, rank.v + 0.5, 114]) && rank.total === 114, "tie reads Rang … bis … von 114: " + rank.tie);
    check(rank.fixed[0] === rank.fixed[1] && JSON.stringify(integers(rank.fixed[0])) === JSON.stringify([44, 45, 114]), "the total is fixed, not counted on the level: " + JSON.stringify(rank.fixed));
  });

  test("a missing value reads k. A. bei", async ({ mapPage: page, check }) => {
    // a missing value reads „k. A. bei“, not „es fehlt“
    const gap = await page.evaluate(() => {
      APP.openTab("candidates"); APP.setTemplate("public_company");
      const q = APP.properties("quarter").find((p) => p.name === "Sachsenhausen-Süd und Flughafen");
      const b = APP.evaluationById[q.id], n = APP.activeCriteria().length;
      const li = [...document.querySelectorAll("#matches li[data-id]")].find((e) => e.dataset.id === q.id);
      const out = { line: APP.candidateLine(b, n), tip: APP.tooltipText(q), li: li && li.textContent.trim(), met: b.met, n,
        missing: b.missing, unknown: b.unknown, title: APP.meta.SOC_MIN_INCOME.title, na: APP.valueText("SOC_MIN_INCOME", null), joined: APP.missingText(["QQ", "ZZ"]),
        lines: [APP.candidateLine({ met: 1, missing: [], unknown: ["WW"] }, 3), APP.candidateLine({ met: 1, missing: ["QQ"], unknown: ["WW"] }, 3),
          APP.candidateLine({ met: 1, missing: ["QQ", "ZZ"], unknown: ["WW"] }, 4), APP.candidateLine({ met: 2, missing: ["QQ"], unknown: [] }, 3)] };
      APP.openTab("city");
      return out;
    });
    // the missing value of Mindestsicherung counts as unknown, not as missing; the line names it after the marker of a
    // missing value (APP.valueText of null), in the same words in tooltip and match list
    const unknownPart = gap.line.includes(gap.na) ? gap.line.slice(gap.line.indexOf(gap.na)).replace(/\.$/, "") : null;
    check(gap.unknown.includes(gap.title) && !gap.missing.includes(gap.title) && unknownPart?.includes(gap.title),
      "Sachsenhausen-Süd reads k. A. bei Mindestsicherung: " + JSON.stringify([gap.line, gap.missing, gap.unknown]));
    check(unknownPart && gap.tip.includes(unknownPart) && (gap.li === null || gap.li.includes(unknownPart)),
      "tooltip and match list agree: " + JSON.stringify([gap.tip, gap.li]));
    // each line: the met and the total criteria, then the missing criteria, then the unknown ones after the marker;
    // one missing criterion reads alike in every line, two read in the plural and joined as APP.missingText joins them
    const nums = (t) => (t.match(/\d+/g) || []).map(Number);
    const order = (t, parts) => parts.every((x, i) => t.indexOf(x) >= 0 && (i === 0 || t.indexOf(x) > t.indexOf(parts[i - 1])));
    // the words between the two numbers and a criterion
    const before = (t, x) => t.slice(0, t.indexOf(x)).replace(/^\d+\D+\d+/, "");
    const [l1, l2, l3, l4] = gap.lines;
    check(JSON.stringify(gap.lines.map(nums)) === JSON.stringify([[1, 3], [1, 3], [1, 4], [2, 3]])
      && order(l1, [gap.na, "WW"]) && !l1.includes("QQ") && order(l2, ["QQ", gap.na, "WW"]) && l3.includes(gap.joined) && order(l3, [gap.joined, gap.na, "WW"])
      && l4.includes("QQ") && !l4.includes(gap.na) && before(l2, "QQ") === before(l4, "QQ") && before(l3, "QQ") !== before(l2, "QQ"),
    "the lines of the candidates: " + gap.lines.join("|"));
  });

  test("shown values in the candidates", async ({ mapPage: page, check }) => {
    // the candidates compare shown values (JS = Python, see the reference above): the half goes up, threshold rounded too
    check(await page.evaluate(() => [APP.shown(2.45, 1), APP.shown(0.5, 0), APP.shown(null, 1), APP.shown(NaN, 1)].map(String).join("|")) === "2.5|1|null|NaN"
      && await page.evaluate(() => APP.meets(17.96, ">=", 18.04, "HOU_RENTERS") && !APP.meets(17.94, ">=", 18.04, "HOU_RENTERS")
        && APP.meets(44.5, ">=", 44.2, "SOC_INDEX") && !APP.meets(44.2, ">=", 44.5, "SOC_INDEX")),
    "APP.shown rounds half up; meets compares shown values, a rank unrounded");
  });

  test("texts of help, profile head and candidates note", async ({ mapPage: page, check }) => {
    // texts: help, profile head, candidates note, no binding end
    // the note says what a bar counts: the areas of the level of the template, on either level
    const notes = await page.evaluate(() => { APP.openTab("candidates");
      return ["social_preservation", "public_company"].map((id) => { APP.setTemplate(id);
        return { level: APP.candidateLevel(), note: document.getElementById("candidates-note").textContent }; }); });
    const levelNames = await page.evaluate(() => APP.LEVEL_NAMES);
    const texts = await page.evaluate(() => { APP.openTab("city");
      APP.setLevel("district"); APP.showProfile("343"); const head = document.querySelector("#tab-area h2 + p").textContent; APP.openTab("city");
      const p = APP.properties("district").find((x) => x.id === "343");
      // the help paragraph of the Bezirke: its keyword is the name of the level, its text the number of Bezirke
      const bezirke = [...document.querySelectorAll("#tab-help p")].find((e) => e.querySelector("strong")?.textContent.replace(":", "").trim() === APP.LEVEL_NAMES.district);
      return { head, pop: APP.format(p.POP, 0), bezirke: bezirke?.textContent ?? null, count: APP.properties("district").length,
        ids: APP.data.catalog.map((m) => m.id) }; });
    // the 114 Bezirke of the payload, the 123 Stadtbezirke and the 16 Ortsbezirke
    check(texts.bezirke && texts.count === 114 && [texts.count, 123, 16].every((n) => new RegExp(`\\b${n}\\b`).test(texts.bezirke)), "the help names the Bezirke: " + texts.bezirke);
    // residents with the gender star, then the census year
    check(texts.head.includes(texts.pop + " ") && /\*innen\b/.test(texts.head) && texts.head.indexOf("2022") > texts.head.indexOf(texts.pop), "profile head names the Zensus 2022: " + texts.head);
    const other = { district: "quarter", quarter: "district" };
    check(JSON.stringify(notes.map((n) => n.level)) === JSON.stringify(["district", "quarter"])
      && notes.every((n) => n.note.includes(levelNames[n.level]) && !n.note.includes(levelNames[other[n.level]])),
    "the candidates note says „in diesem Bereich“: " + JSON.stringify(notes));
    check(!texts.ids.some((id) => id.startsWith("SH_ENDING")), "no layer SH_ENDING_*");
  });
});

// the CSV writes the values the map shows, so every row agrees with its own "erfüllt"
test("the CSV agrees with its met marks", async ({ mapPage: page, check }) => {
  const r = await page.evaluate(() => {
    APP.openTab("candidates");
    const out = {};
    for (const id of ["social_preservation", "coop", "public_company"]) {
      APP.setTemplate(id);
      const rows = APP.csvText().slice(1).split("\r\n").map((l) => l.split(";"));
      const head = rows.shift();
      const num = (t) => Number(t.replace(/\./g, "").replace(",", "."));
      const yes = APP.t("answer_yes"), no = APP.t("answer_no");
      // a table of Bezirke opens with number, name and Stadtteil; one of Stadtteile with the name
      const offset = APP.candidateLevel() === "district" ? 3 : 1;
      const crit = head.slice(offset, -2).map((h) => { const m = /\((<|≥|=) ([^)]*)\)$/.exec(h); return { op: m[1], t: m[2] === yes ? 1 : m[2] === no ? 0 : num(m[2]), text: m[2] }; });
      out[id] = { bad: rows.filter((c) => {
        const met = crit.filter((k, j) => {
          const cell = c[offset + j], x = cell === yes ? 1 : cell === no ? 0 : num(cell);
          if (Number.isNaN(x)) return false;
          return k.op === "≥" ? x >= k.t : k.op === "<" ? x < k.t : x === k.t;
        }).length;
        return met !== Number(c[offset + crit.length]);
      }).map((c) => c.join(";")), n: rows.length };
    }
    APP.setTemplate("social_preservation");
    const rows = APP.csvText().slice(1).split("\r\n").map((l) => l.split(";")), head = rows.shift();
    const j = head.findIndex((h) => h.startsWith(APP.meta.HOU_RENTERS.title + " ("));
    out.rent = { head: head[j], v423: (rows.find((c) => c[0] === "423") || [])[j] };
    APP.openTab("city");
    return out;
  });
  for (const [id, v] of Object.entries(r).filter(([id]) => id !== "rent")) check(v.n > 0 && v.bad.length === 0, `CSV of ${id} agrees with its met marks: ` + JSON.stringify(v.bad.slice(0, 3)));
  check(!!r.rent.head && /\(≥ \d+,\d\)$/.test(r.rent.head) && /^\d+,\d$/.test(r.rent.v423 ?? ""),
    "Mieteranteil threshold and value in the CSV at the one decimal of the map: " + JSON.stringify(r.rent));
});

// a rank threshold moves in steps of 0.5 and its label shows exactly that
test("the rank slider steps by 0.5", async ({ mapPage: page, check }) => {
  const r = await page.evaluate(() => {
    APP.openTab("candidates"); APP.setTemplate("custom");
    const select = document.getElementById("criterion-new");
    select.value = "SOC_INDEX"; select.dispatchEvent(new Event("change"));
    const i = APP.criteria.findIndex((k) => k.indicator === "SOC_INDEX");
    const slider = () => document.querySelector(`input[type=range][data-i="${i}"]`);
    const out = { step: slider().step, start: APP.criteria[i].threshold, labels: [] };
    for (const raw of ["44.07", "63.37", "20.26", "88.9"]) {
      const s = slider(); s.value = raw; s.dispatchEvent(new Event("input"));
      out.labels.push([APP.criteria[i].threshold, document.getElementById("value-" + i).textContent]);
    }
    // a threshold off the grid (a template or a stored value) is snapped; other indicators are left alone
    out.snap = [APP.snapThreshold("SOC_INDEX", 44.07), APP.snapThreshold("SOC_INDEX", 44.3), APP.snapThreshold("SOC_INDEX", null), APP.snapThreshold("HOU_RENTERS", 44.07)];
    APP.setTemplate("social_preservation"); APP.openTab("city");
    return out;
  });
  check(r.step === "0.5" && Number.isInteger(r.start * 2), "the rank slider steps by 0.5: " + JSON.stringify([r.step, r.start]));
  check(r.labels.every(([t, label]) => Number.isInteger(t * 2) && label === t.toLocaleString("de-DE", { maximumFractionDigits: 1 })),
    "the label shows the threshold of the rank slider: " + JSON.stringify(r.labels));
  check(JSON.stringify(r.snap) === "[44,44.5,null,44.07]", "a threshold off the grid is snapped to 0.5: " + JSON.stringify(r.snap));
});

// a count of an estimated share carries a tilde, "unter 10" does not (in the tooltip)
test("tooltip counts carry a tilde", async ({ mapPage: page, check }) => {
  const r = await page.evaluate(() => {
    APP.setLevel("district"); APP.setIndicator("HOU_PRE1919");
    const m = APP.meta.HOU_PRE1919_DWELLINGS;
    return { unit: m.unit, below: APP.roundedCount(0, m.round_to, true), lines: APP.properties("district").filter((p) => p.HOU_PRE1919_DWELLINGS != null && p.HOU_PRE1919 != null)
      .map((p) => [p.HOU_PRE1919_DWELLINGS, APP.tooltipText(p).split("<br>").at(-1)]) };
  });
  // the last line of the tooltip: the unit of the count in the catalog, a colon, the count
  const big = r.lines.filter(([x]) => x >= 10), small = r.lines.filter(([x]) => x < 10);
  check(big.length > 0 && big.every(([, t]) => t.startsWith(r.unit + ": ~") && /: ~[\d.]+$/.test(t)), "tooltip counts carry a tilde: " + JSON.stringify(big.find(([, t]) => !/: ~\d/.test(t))));
  check(!r.below.includes("~") && small.every(([, t]) => t === `${r.unit}: ${r.below}`), "unter 10 without a tilde: " + JSON.stringify([r.below, small[0]]));
});
