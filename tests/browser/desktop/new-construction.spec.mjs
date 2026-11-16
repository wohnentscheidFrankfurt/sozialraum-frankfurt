// View Neubau: new dwellings per year (pipeline/use_cases/new_construction/README.md) and the figure of rents, prices
// and wages below the columns (docs/design.md, View Neubau); the wide and the narrow drawing and the boundary between.
import { test } from "../fixtures.mjs";
import { settle } from "../helpers/common.mjs";
import {
  drawnNc, drawnRents, infoKept, near, openNewConstruction, RENTS_FIG, rentsLayout, rentsShown, rgb, samePath,
  shownRight, wantPaths,
} from "../helpers/views.mjs";

const payload = (page) => page.evaluate(() => APP.data.new_construction);
// an index as the map writes it: one decimal, German format (APP.format(value, 1))
const indexText = (v) => v.toLocaleString("de-DE", { minimumFractionDigits: 1, maximumFractionDigits: 1 });

test("the columns: conversions, key, label, texts, tooltip and ⓘ", async ({ mapPage: page, check, saveScreenshot }) => {
  const n = await payload(page);
  await openNewConstruction(page);
  const nc = await page.evaluate(() => ({
    mainHidden: document.querySelector("main").hidden, historyHidden: document.getElementById("view-history").hidden,
    pressed: document.querySelector('#views button[data-view="new_construction"]').getAttribute("aria-pressed"),
    groups: document.querySelectorAll("#view-new-construction svg.construction g[data-tip]").length,
    last: [...document.querySelectorAll("#view-new-construction svg.construction g.last")].map((g) => g.dataset.tip),
    hatched: document.querySelectorAll('#view-new-construction svg.construction rect[fill="url(#hatch-subsidised)"]').length,
    text: document.getElementById("view-new-construction").textContent,
    shareFill: getComputedStyle(document.querySelector("#view-new-construction svg.construction .last .share")).fill,
  }));
  check(nc.mainHidden && nc.historyHidden && nc.pressed === "true", "the switch opens the view Neubau");
  check(nc.groups === 15 && nc.last.length === 1 && nc.hatched === 3,
    `Neubau: 15 columns, one highlighted, 3 hatched: ${JSON.stringify([nc.groups, nc.last.length, nc.hatched])}`);
  check(nc.last[0] === n.years.at(-1).tip && n.highlight === 2025, "Neubau: the highlighted column is 2025");
  // conversions: a dashed frame per year directly on the solid frame of new construction; the number above is all dwellings
  const cv = await page.evaluate(() => [...document.querySelectorAll("#view-new-construction svg.construction g[data-tip]")].map((g) => {
    const solid = g.querySelector("rect.frame").getBoundingClientRect(), dashed = g.querySelector("rect.conversions");
    const d = dashed && dashed.getBoundingClientRect();
    return { dashed: !!dashed, dash: dashed ? getComputedStyle(dashed).strokeDasharray : "", dashedWidth: dashed ? getComputedStyle(dashed).strokeWidth : "",
      solidWidth: getComputedStyle(g.querySelector("rect.frame")).strokeWidth, gap: d ? Math.abs(solid.top - d.bottom) : null,
      dashedHeight: d ? d.height : 0, solidHeight: solid.height, number: g.querySelector("text.total").textContent, tip: g.dataset.tip,
      numberAbove: g.querySelector("text.total").getBoundingClientRect().bottom <= (d ? d.top : solid.top) + 1 };
  }));
  check(cv.filter((c) => c.dashed && c.dash !== "none").length === 15, "Neubau: 15 dashed frames of conversions");
  check(cv.every((c) => c.gap <= 1), "Neubau: the dashed frame of each year sits on its solid frame: " + cv.map((c) => c.gap?.toFixed(1)).join(" "));
  check(cv.every((c, i) => c.number === n.years[i].all_text && c.numberAbove), "Neubau: the number above each column is all dwellings, above the dashed frame");
  check(cv.every((c, i) => Math.abs(c.dashedHeight / c.solidHeight - n.years[i].conversions / n.years[i].new) < 0.02),
    "Neubau: the dashed frames are drawn to scale of the same axis as the solid frames");
  check(cv.filter((c) => c.solidWidth === "3px").length === 1 && cv.at(-1).solidWidth === "3px" && cv.every((c) => c.dashedWidth !== "3px"),
    "Neubau: only the solid frame of 2025 has stroke-width 3: " + cv.map((c) => c.solidWidth + "/" + c.dashedWidth).join(" "));
  const ncKey = await page.evaluate(() => [...document.querySelectorAll("#view-new-construction figure:first-of-type .key span")].map((s) => s.textContent.trim()));
  check(JSON.stringify(ncKey) === JSON.stringify([n.key.new, n.key.subsidised, n.key.provisional, n.key.conversions])
    && ncKey.every((t) => t !== ""), "Neubau: the key has the four labels in order: " + JSON.stringify(ncKey));
  check(await page.evaluate(() => { const i = document.querySelector("#view-new-construction figure:first-of-type .key span:nth-child(4) i");
    return getComputedStyle(i).borderTopStyle === "dashed"; }), "Neubau: the swatch of conversions has a dashed outline");
  // children of role="img" are hidden from screen readers: the svg label carries every year, the columns have no role
  const ncAria = await page.evaluate(() => ({ label: document.querySelector("#view-new-construction svg.construction").getAttribute("aria-label"),
    roles: document.querySelectorAll('#view-new-construction svg.construction g[role], #view-new-construction svg.construction g[aria-label]').length }));
  check(ncAria.label === [n.title + ".", ...n.years.map((y) => y.tip)].join(" ") && ncAria.label.includes(n.years.at(-1).tip),
    "Neubau: the svg label holds the title and the tooltip of every year");
  check(ncAria.roles === 0, "Neubau: no column has its own role or aria-label");
  const ncText = nc.text.replace(/\u00a0/g, " ");
  check(ncText.includes(n.title) && ncText.includes(n.lead) && ncText.includes(n.years.at(-1).share_text), "Neubau shows title, lead and the share of 2025");
  check(nc.shareFill === "rgb(212, 0, 0)", "Neubau: the share text is red: " + nc.shareFill);
  const looseNc = await page.evaluate(() => [...document.querySelectorAll("#view-new-construction figure > h2, #view-new-construction figure > p")]
    .map((e) => e.textContent).filter((t) => /\d %/.test(t)));
  check(looseNc.length === 0, "Neubau texts keep a number and % together: " + JSON.stringify(looseNc));
  await page.evaluate(() => document.getElementById("view-new-construction").scrollTo(0, 0));
  const lastBox = await page.locator("#view-new-construction svg.construction g.last .frame").boundingBox();
  await page.mouse.move(lastBox.x + lastBox.width / 2, lastBox.y + lastBox.height / 2);
  const ncTip = await page.evaluate(() => { const t = document.querySelector("#view-new-construction .chart-tip"); return t.hidden ? null : t.textContent; });
  check(ncTip === n.years.at(-1).tip, "tooltip of 2025: " + ncTip);
  await page.mouse.move(5, 5);
  const infoNc = async () => page.evaluate(() => ({ hidden: document.getElementById("info-new-construction").hidden,
    expanded: document.querySelector('#view-new-construction .info-button[data-info="new-construction"]').getAttribute("aria-expanded") }));
  await page.click('#view-new-construction .info-button[data-info="new-construction"]');
  const open = await infoNc();
  check(!open.hidden && open.expanded === "true", "Neubau: the ⓘ opens the protocol: " + JSON.stringify(open));
  check(n.info.calc && await page.evaluate((calc) => document.getElementById("info-new-construction").textContent.replace(/\u00a0/g, " ").includes(calc), n.info.calc),
    "Neubau: the protocol has the calculation");
  // two written sums: the column and the share of the last year, each ending with the number of the chart
  const sums = await page.evaluate(() => [...document.querySelectorAll("#info-new-construction .sum")].map((s) => [s.getAttribute("aria-label"), s.querySelector(".result")?.textContent.replace(/\u00a0/g, " ")]));
  const last = n.years.at(-1);
  check(JSON.stringify(sums) === JSON.stringify([[n.info.calc_examples[0].label, last.all_text], [n.info.calc_examples[1].label, last.share_text]]),
    "Neubau: the ⓘ shows the sums of the column and the share, ending with the numbers of the chart: " + JSON.stringify(sums));
  await page.click('#view-new-construction .info-button[data-info="new-construction"]');
  const closed = await infoNc();
  check(closed.hidden && closed.expanded === "false", "Neubau: the ⓘ closes the protocol");
  await page.evaluate(() => document.querySelector("#view-new-construction .chart").scrollIntoView());
  await saveScreenshot("new_construction", { element: page.locator("#view-new-construction figure:first-of-type") });
});

test("rents, wide window: heading, keys, axes, lines, dots, break and end labels", async ({ mapPage: page, check }) => {
  const n = await payload(page);
  await openNewConstruction(page);
  const rents = n.rents;
  const rl = await rentsLayout(page);
  check(rl && rl.charts.length === 2 && !rl.columns, "Rents: its own figure with two charts (svg.rents)");
  check(await infoKept(page), "Neubau, wide window: each ⓘ on the line of the last word of its lead");
  if (!rl) return;
  check(rents.title && rl.title === rents.title && rents.title.includes(String(rents.charts[0].years[0])) && rents.lead && rl.lead.includes(rents.lead) && rl.info,
    `Rents: heading, lead and the ⓘ housing-rents at its end (${rl.title}; ${rl.lead})`);
  check(rl.sources.length === 1 && rents.source && rl.sources[0] === rents.source && rents.source.includes(String(rents.charts[0].years[0])),
    "Rents: one source line under both charts, as in the payload: " + rl.sources.join(" | "));
  // each swatch of a data line or the old base built from its entry with the dot flipped or the dash changed
  const flipped = await page.evaluate((keys) => keys.map((key) => key.filter((e) => e.kind !== "reference").map((e) => {
    const sw = APP.rentsSwatch(e.kind === "old_base" ? { ...e, dash: "2 3" } : { ...e, dot: !e.dot }, false);
    return { kind: e.kind, dash: sw.querySelector("line")?.getAttribute("stroke-dasharray"), dots: sw.querySelectorAll("circle").length }; })),
  rents.charts.map((c) => c.key));
  rents.charts.forEach((c, k) => {
    const d = rl.charts[k], what = `Rents, ${c.id}`, byId = Object.fromEntries(c.series.map((s) => [s.id, s]));
    const [t0, tN] = [c.axis.ticks[0], c.axis.ticks.at(-1)], yOf = (v) => d.grid[0] + (v - t0) * (d.grid.at(-1) - d.grid[0]) / (tN - t0);
    const xOf = (i) => d.groups[i].x;
    check(d.title === c.title && d.explain === c.explain, `${what}: title and the line below (${d.title}; ${d.explain})`);
    // the key serves phones only (APP.CONSTRUCTION_WIDE): in the wide drawing it is hidden, but built in the order of the payload
    check(JSON.stringify(d.key.map((e) => e.text)) === JSON.stringify(c.key.map((e) => e.name)), `${what}: the key names in order: ${d.key.map((e) => e.text)}`);
    check(d.keyBox && d.keyBox.display === "none" && d.keyBox.cls.split(" ").includes("key") && d.keyBox.cls.split(" ").includes("rents-key"),
      `${what}: the key is hidden in the wide drawing: ` + JSON.stringify(d.keyBox));
    check(c.key.every((e, i) => d.key[i].swatch === e.colour && d.key[i].weight === "400" && (e.kind === "reference" ? d.key[i].color === "rgb(107, 107, 107)" : d.key[i].color === "rgb(26, 26, 26)")
      && (e.kind === "reference" ? d.key[i].swatchBand === e.band && d.key[i].swatchEdge === e.edge && d.key[i].swatchDash === e.dash && d.key[i].swatchDots === 0
        : e.kind === "data" ? d.key[i].swatchDots === (e.dot ? 1 : 0) && e.dot === (byId[e.id].dots.length > 0)
          : d.key[i].swatchDots === 1 && d.key[i].swatchDash === e.dash && e.dash === "1 4")),
    `${what}: key swatches: the references a piece of the band with their edge, a dot where the entry says so, the old base dotted with the dash of its entry, names in normal weight, the references grey: ` + JSON.stringify(d.key));
    // the swatch reads the entry and decides nothing itself: a changed dash or dot shows in the drawing
    const entries = c.key.filter((e) => e.kind !== "reference");
    check(flipped[k].length === entries.length && flipped[k].every((f, i) => f.kind === "old_base" ? f.dash === "2 3" : f.dots === (entries[i].dot ? 0 : 1)),
      `${what}: the swatch of a data line follows e.dot, the one of the old base follows e.dash: ` + JSON.stringify(flipped[k]));
    if (c.old_base_note) {
      check(d.note && d.note.text === c.old_base_note && d.note.display !== "none" && d.note.afterSvg && d.note.below && d.note.size === "13px" && d.note.color === "rgb(107, 107, 107)" && d.note.hollow === 1,
        `${what}: one line below the chart explains the hollow dots, 13 px grey with the swatch of the old base: ` + JSON.stringify(d.note));
    } else {
      check(d.note === null, `${what}: no note below the chart`);
    }
    check(d.units === 760 && d.role === "img" && d.roles === 0 && d.label === c.aria_label
      && [...c.tips.map((t) => t.text), ...(c.old_base ? [c.old_base.dwellings.tip, c.old_base.population.tip] : [])].every((t) => d.label.includes(t)),
    `${what}: one image 760 units wide, its label names the chart and holds every tooltip`);
    check(JSON.stringify(d.ticks) === JSON.stringify(c.axis.tick_texts) && d.grid.length === c.axis.ticks.length && d.grid.every((y, i) => i === 0 || y < d.grid[i - 1]),
      `${what}: a grid line per tick, the tick labels of the payload: ${d.ticks}`);
    const gaps = d.groups.slice(1).map((g, i) => g.x - d.groups[i].x);
    check(d.groups.length === c.years.length && d.groups.every((g, i) => g.tip === c.tips[i].text && c.tips[i].year === c.years[i])
      && gaps.every((g) => g > 0 && Math.abs(g - gaps[0]) < 0.01) && d.groups.every((g) => g.fill === "rgba(0, 0, 0, 0)" && g.top <= Math.min(...d.grid) && g.bottom >= Math.max(...d.grid)),
    `${what}: one transparent slot over the full height per year, its tooltip as in the payload (${d.groups.length} of ${c.years.length})`);
    check(JSON.stringify(d.years) === JSON.stringify(c.years.map(String)), `${what}: every year below the chart: ${d.years}`);
    check(d.yearFills.length === c.years.length && d.yearFills.every((t) => t.fill === (c.survey_years.includes(t.year) ? "rgb(26, 26, 26)" : "rgb(107, 107, 107)") && t.weight === "700"),
      `${what}: the survey years ${c.survey_years} in the ink, the other years grey: ` + d.yearFills.map((t) => `${t.year} ${t.fill}`).join(", "));
    // the band is the first thing after the grid; then the references, thin (1.5), the wages dashed; the data lines on them, at most 3 units
    const refs = c.series.filter((s) => s.kind === "reference").map((s) => s.id);
    check(d.bands.length === 1 && d.bands[0].afterGrid && d.bands[0].beforeLines, `${what}: one band path after the grid and before every line, dot and label`);
    check(c.band.between.join() === "wages,prices" && d.bands[0] && d.bands[0].fill === rgb(c.band.colour) && d.bands[0].points.length === 2 * c.years.length
      && c.years.every((y, i) => near(d.bands[0].points[i], [xOf(i), yOf(byId.wages.values[i])]) && near(d.bands[0].points[2 * c.years.length - 1 - i], [xOf(i), yOf(byId.prices.values[i])])),
    `${what}: the band runs through the wages and back through the prices, in ${c.band.colour}: ` + JSON.stringify(d.bands[0] && d.bands[0].points.length));
    check(refs.length === 2 && d.paths.slice(0, 2).map((p) => p.series).join() === refs.join() && d.paths.slice(0, 2).every((p) => p.width === 1.5 && p.join === "round")
      && d.paths.slice(2).every((p) => p.width <= 3 && !refs.includes(p.series)),
    `${what}: the references are the first lines, 1.5 wide, the data lines at most 3: ` + d.paths.map((p) => `${p.series} ${p.width}`).join(", "));
    const dashOf = (p) => (p.dash === "none" ? null : p.dash.replace(/px/g, "").replace(/,\s*/g, " "));
    check(d.paths.filter((p) => refs.includes(p.series)).every((p) => dashOf(p) === byId[p.series].dash && (byId[p.series].dash ? p.cap === "butt" : p.cap === "round"))
      && byId.wages.dash === "5 3" && byId.prices.dash === null,
    `${what}: the wages dashed 5 3 with flat ends, the prices solid: ` + d.paths.slice(0, 2).map((p) => `${p.series} ${p.dash} ${p.cap}`).join(", "));
    for (const s of c.series) {
      const drawn = d.paths.filter((p) => p.series === s.id && !p.old), want = wantPaths(c, s, xOf, yOf);
      check(drawn.length === want.length && drawn.every((p, i) => samePath(p.points, want[i]) && p.stroke === s.colour && p.width === s.width),
        `${what}, ${s.id}: ${want.length} line(s) through the years with a value, colour ${s.colour}, ${s.width} wide (${drawn.map((p) => p.points.length)})`);
      const dots = d.groups.map((g) => g.dots.filter((x) => x.series === s.id));
      check(c.years.every((y, i) => dots[i].length === (s.dots.includes(y) ? 1 : 0)) && c.years.every((y, i) => dots[i].every((x) => near([x.x, x.y], [xOf(i), yOf(s.values[i])]) && x.fill === rgb(s.colour))),
        `${what}, ${s.id}: a dot only in the years ${s.dots}, at its value, in its colour`);
      const dotYears = c.years.filter((y, i) => dots[i].length > 0);
      check(JSON.stringify(dotYears) === JSON.stringify(s.id === "new" || s.id === "old" ? c.survey_years : []),
        `${what}, ${s.id}: dots at ${s.id === "new" || s.id === "old" ? "the survey years" : "no year (no survey day)"}: ${dotYears}`);
      const old = c.old_base?.[s.id], dotted = d.paths.filter((p) => p.series === s.id && p.old);
      if (!old) { check(dotted.length === 0, `${what}, ${s.id}: no dotted segment`); continue; }
      const cut = c.years.indexOf(c.break.year), hollow = d.old.find((o) => o.series === s.id);
      check(hollow && hollow.tip === old.tip && near([hollow.x, hollow.y], [xOf(cut), yOf(old.value)]) && hollow.fill === "rgb(255, 255, 255)" && hollow.stroke === rgb(s.colour),
        `${what}, ${s.id}: a hollow dot at the break year on the old base, white inside, with its own tooltip: ` + JSON.stringify(hollow));
      const oldKey = c.key.find((e) => e.kind === "old_base");
      check(dotted.length === 1 && samePath(dotted[0].points, [[xOf(cut - 1), yOf(s.values[cut - 1])], [xOf(cut), yOf(old.value)]]) && dashOf(dotted[0]) === oldKey.dash && dotted[0].width === oldKey.width,
        `${what}, ${s.id}: one dotted segment from the year before the break to the hollow dot, in the dash and width of the key entry (${oldKey.dash}): ${dotted[0] && dotted[0].dash}`);
    }
    if (c.break) {
      const cut = c.years.indexOf(c.break.year);
      check(d.old.length === 2 && d.breaks.length === 1 && d.breaks[0].x > xOf(cut - 1) && d.breaks[0].x < xOf(cut) && d.breaks[0].dash !== "none"
        && d.notes.length === 1 && d.notes[0] === c.break.note && c.break.note.includes(String(c.break.year)),
      `${what}: two hollow dots, the dashed line of the break between ${c.break.year - 1} and ${c.break.year} with its note (${d.notes})`);
    } else {
      check(d.old.length === 0 && d.breaks.length === 0 && d.notes.length === 0, `${what}: no hollow dots, no break`);
    }
    // end labels right of the last year: in the order of the payload from the top, at least 17 units apart, inside the svg
    const ends = [...d.ends].sort((p, q) => p.y - q.y);
    check(ends.map((e) => e.series).join() === c.end_order.join() && ends.every((e, i) => i === 0 || e.y - ends[i - 1].y >= 17 - 1e-9)
      && d.leaders === c.series.length, `${what}: end labels from the top in the order ${c.end_order}, at least 17 units apart, each with a leader: `
      + ends.map((e) => `${e.series} ${e.y.toFixed(1)}`).join(", "));
    check(ends.every((e) => { const s = byId[e.series]; return e.text === `${s.end_value_text} ${s.end_name}` && e.weight === "700" && e.fill === rgb(s.ink)
      && e.nameWeight === "400"; }),
    `${what}: end labels with the value in bold and the name in regular weight, in the ink of the series (the references grey): ` + ends.map((e) => `${e.text} ${e.fill}`).join(" | "));
    // the key is hidden here, so the end label of the wages says that they are those of Hessen: after the value of
    // the last year it carries the name of the key entry (its head, before a comma that the key adds)
    const wagesEnd = ends.find((e) => e.series === "wages"), wagesKey = c.key.find((e) => e.id === "wages");
    check(wagesEnd && wagesKey && byId.wages.end_name && wagesEnd.text === `${byId.wages.end_value_text} ${byId.wages.end_name}`
      && wagesKey.name.split(",")[0] === byId.wages.end_name && byId.wages.end_value_text === indexText(byId.wages.values.at(-1)),
    `${what}: the end label of the wages carries the name of the key: ${wagesEnd && wagesEnd.text}`);
    check(d.texts.every((t) => t.inside), `${what}: every text inside the svg: ${d.texts.filter((t) => !t.inside).map((t) => t.text)}`);
  });
});

test("rents: tooltips of the years and the ⓘ", async ({ mapPage: page, check, saveScreenshot }) => {
  const n = await payload(page);
  await openNewConstruction(page);
  const rents = n.rents;
  const rl = await rentsLayout(page);
  // the tooltip of a year: its head, a row per series with a swatch in the colour of the line, and the note
  const hoverTip = async (sel, index, dy) => {
    // scrolled into view first: a scroll hides the tooltip, so the pointer moves only after it
    const b = await page.evaluate(async ([sel, index]) => { const e = document.querySelectorAll(sel)[index];
      if (!e) return null;
      e.scrollIntoView({ block: "center" });
      await new Promise((done) => requestAnimationFrame(() => requestAnimationFrame(done)));
      const b = e.getBoundingClientRect(); return { x: b.x, y: b.y, width: b.width, height: b.height }; }, [sel, index]);
    if (!b) return null;
    await page.mouse.move(b.x + b.width / 2, b.y + (dy ?? b.height / 2));
    return page.evaluate(() => { const t = document.querySelector("#view-new-construction .chart-tip");
      return t.hidden ? null : { text: t.textContent, head: t.querySelector(".head")?.textContent, note: t.querySelector(".note")?.textContent,
        rows: [...t.querySelectorAll(".row")].map((r) => [r.querySelector("b")?.textContent, r.querySelector("span")?.textContent, r.querySelector("svg line")?.getAttribute("stroke"),
          r.querySelector("svg line")?.getAttribute("stroke-dasharray"), Number(r.querySelector("svg line")?.getAttribute("stroke-width"))]) }; }); };
  for (const [k, year] of [[0, 2023], [0, 2022], [1, 2025]]) {
    const c = rents.charts[k], i = c.years.indexOf(year), tip = c.tips[i],
      swatchOf = Object.fromEntries(c.series.map((s) => [s.id, [s.colour, s.dash, s.width]]));
    const shown = await hoverTip(`${RENTS_FIG} svg.rents g[data-tip]:not(.old) > rect.hit`, (k ? rents.charts[0].years.length : 0) + i, 30);
    check(shown && shown.head === tip.head && shown.note === tip.note
      && JSON.stringify(shown.rows) === JSON.stringify(tip.rows.map(([v, label, id]) => [v, label, ...swatchOf[id]])),
    `Rents, ${c.id}: tooltip of ${year} as in the payload, swatches in the colour, dash and width of the lines: ` + JSON.stringify(shown));
  }
  // the six agreed rows of 2023: one per series, each with the index of its series in that year
  const c0 = rents.charts[0], i23 = c0.years.indexOf(2023), rows23 = c0.tips[i23].rows;
  check(rows23.length === 6 && JSON.stringify(rows23.map(([, , id]) => id).sort()) === JSON.stringify(c0.series.map((s) => s.id).sort())
    && rows23.every(([v, label, id]) => label && v === indexText(c0.series.find((s) => s.id === id).values[i23])),
  "Rents: the tooltip of 2023 holds the six agreed rows: " + JSON.stringify(rows23));
  const oldTip = await hoverTip(`${RENTS_FIG} svg.rents g.old circle.dot[data-series="dwellings"]`, 0);
  check(oldTip?.text === rents.charts[0].old_base.dwellings.tip, "Rents: the hollow dot of the dwellings has its own tooltip: " + oldTip?.text);
  await page.mouse.move(5, 5);
  const infoRents = () => page.evaluate(() => { const i = document.getElementById("info-housing-rents"), b = document.querySelector('#view-new-construction .info-button[data-info="housing-rents"]');
    return i && b ? { hidden: i.hidden, expanded: b.getAttribute("aria-expanded"), text: i.textContent,
      sums: [...i.querySelectorAll(".sum")].map((s) => [s.getAttribute("aria-label"), s.querySelector(".result")?.textContent]) } : null; });
  if (await infoRents()) await page.click('#view-new-construction .info-button[data-info="housing-rents"]');
  const rentsOpen = await infoRents();
  check(rentsOpen && !rentsOpen.hidden && rentsOpen.expanded === "true" && rentsOpen.text.includes(rents.info.uncertainty) && rentsOpen.text.includes(rents.info.calc),
    "Rents: the ⓘ opens its own protocol: " + JSON.stringify(rentsOpen && [rentsOpen.hidden, rentsOpen.expanded]));
  // the written sum of the new contracts ends with the end value of their line without inflation
  const realNew = rents.charts[1].series.find((s) => s.id === "new").end_value_text;
  check(rentsOpen && JSON.stringify(rentsOpen.sums) === JSON.stringify(rents.info.calc_examples.map((ex) => [ex.label, realNew])),
    "Rents: the ⓘ shows the written sum of the payload, ending with the line without inflation: " + JSON.stringify(rentsOpen?.sums));
  check(await page.evaluate(() => document.getElementById("info-new-construction").hidden && !document.getElementById("info-housing-population")),
    "Rents: its ⓘ leaves the protocol of the columns closed; the ⓘ of the population is gone");
  if (rentsOpen) await page.click('#view-new-construction .info-button[data-info="housing-rents"]');
  check(rentsOpen && (await infoRents()).hidden, "Rents: the ⓘ closes its protocol");
  // the figure is higher than the window, and its view clips what lies below: a high window for the screenshot
  await page.setViewportSize({ width: 1400, height: 1700 });
  await page.evaluate((fig) => document.querySelector(fig)?.scrollIntoView(), RENTS_FIG);
  if (rl) await saveScreenshot("housing_rents", { element: page.locator(RENTS_FIG) });
});

test("narrow window: the columns and the rents drawn at their width", async ({ mapPage: page, check, saveScreenshot }) => {
  const n = await payload(page);
  await openNewConstruction(page);
  const rents = n.rents;
  check(shownRight(await rentsShown(page), true), "Rents, wide window: the keys hidden, the note under chart 1 shown, none under chart 2");
  await page.setViewportSize({ width: 420, height: 900 });
  check(await drawnNc(page, 0), "Neubau, narrow window: drawn at its width");
  check(await page.evaluate(() => document.querySelector("#view-new-construction svg.construction").hasAttribute("width")), "Neubau, narrow window: the svg has a width in px");
  check(await page.evaluate((tip) => document.querySelector("#view-new-construction svg.construction").getAttribute("aria-label").includes(tip)
    && !document.querySelector("#view-new-construction svg.construction g[role]"), n.years.at(-1).tip),
  "Neubau, narrow window: the svg label holds the tooltip of 2025 and no column has a role");
  check(await page.evaluate(() => { const v = document.getElementById("view-new-construction"); return v.scrollWidth <= v.clientWidth + 1; }),
    "Neubau, narrow window: no sideways overflow");
  await saveScreenshot("new_construction_narrow", { element: page.locator("#view-new-construction figure:first-of-type") });
  // rents on a phone: the same orientation as the wide drawing, drawn in px at the room; years only every second
  // year from 2017, the end labels without names, still in the order of the payload and at least 17 px apart
  check(await drawnRents(page, 0), "Rents, narrow window: both charts drawn at their width");
  const rn = await rentsLayout(page);
  check(rn && rn.charts.every((d) => d.width), "Rents, narrow window: each svg has a width in px");
  check(shownRight(await rentsShown(page), false), "Rents, narrow window: the keys shown, no note");
  check(rn && rn.charts.every((d) => d.yearFills.every((t) => t.fill === (t.year === 2019 ? "rgb(107, 107, 107)" : "rgb(26, 26, 26)"))),
    "Rents, narrow window: 2019 grey, the survey years in the ink");
  check(await infoKept(page), "Neubau, narrow window: each ⓘ on the line of the last word of its lead");
  rents.charts.forEach((c, k) => {
    const d = rn?.charts[k], what = `Rents, ${c.id}, narrow window`, byId = Object.fromEntries(c.series.map((s) => [s.id, s]));
    if (!d) { check(false, `${what}: drawn`); return; }
    check(d.years.join() === "2017,2019,2021,2023,2025" && d.groups.length === c.years.length && d.groups.every((g, i) => g.tip === c.tips[i].text),
      `${what}: years at 2017, 2019, 2021, 2023 and 2025, a slot per year: ${d.years}`);
    const ends = [...d.ends].sort((p, q) => p.y - q.y);
    check(ends.map((e) => e.series).join() === c.end_order.join() && ends.every((e, i) => i === 0 || e.y - ends[i - 1].y >= 17 - 1e-9)
      && ends.every((e) => e.text === byId[e.series].end_value_text), `${what}: end labels with the value only, in the order of the payload: ` + ends.map((e) => e.text).join(" "));
    check(d.texts.every((t) => t.inside && t.px >= 11), `${what}: every text inside its svg and at least 11 px: `
      + d.texts.filter((t) => !t.inside || t.px < 11).map((t) => `${t.text} ${t.px}`).join(" | "));
    check(d.old.length === (c.old_base ? 2 : 0) && d.notes.length === (c.break ? 1 : 0), `${what}: the hollow dots and the note of the break`);
  });
  check(await page.evaluate(() => [...document.querySelectorAll("#view-new-construction svg.rents")].filter((svg) => { svg.scrollIntoView();
    return [...svg.querySelectorAll("g[data-tip]:not(.old)")].every((g) => { const b = g.querySelector("rect.hit").getBoundingClientRect(),
      e = document.elementFromPoint(b.left + b.width / 2, b.top + 10); return e && e.closest("[data-tip]") === g; }); }).length === 2),
  "Rents, narrow window: the slot of each year takes the tap");
  await page.setViewportSize({ width: 420, height: 1700 });
  await page.evaluate((fig) => document.querySelector(fig)?.scrollIntoView(), RENTS_FIG);
  if (rn) await saveScreenshot("housing_rents_narrow", { element: page.locator(RENTS_FIG) });
});

test("the boundary of the wide drawing at 700 px of room", async ({ mapPage: page, check }) => {
  await openNewConstruction(page);
  // the wide drawing from 700 px of room (APP.CONSTRUCTION_WIDE): its 12 px labels stay at 11 px; the offset between window and room is measured
  await page.setViewportSize({ width: 800, height: 900 });
  await settle(page);
  const ncOffset = await page.evaluate(() => 800 - APP.newConstructionBody.clientWidth);
  for (const [room, units] of [[650, 0], [699, 0], [700, 760]]) {
    await page.setViewportSize({ width: room + ncOffset, height: 900 });
    check(await drawnNc(page, units) && await page.evaluate(() => APP.newConstructionBody.clientWidth) === room,
      `Neubau, ${room} px of room: ${units ? "the wide drawing" : "rows at the width in px"}`);
    check(await infoKept(page), `Neubau, ${room} px of room: each ⓘ on the line of the last word of its lead`);
    check(shownRight(await rentsShown(page), units === 760), `Rents, ${room} px of room: ${units ? "the keys hidden, the note shown" : "the keys shown, no note"}`);
    if (!units) check(await page.evaluate(() => { const w = APP.newConstructionBody.getBoundingClientRect(), rs = [...document.querySelectorAll("#view-new-construction svg.construction rect.conversions")];
      return rs.length === 15 && rs.every((r) => { const b = r.getBoundingClientRect(); return b.width > 0 && b.left >= w.left - 0.5 && b.right <= w.right + 0.5; }); }),
    `Neubau, ${room} px of room: the dashed bars of conversions lie inside the window`);
  }
  check(await page.evaluate(() => [...document.querySelectorAll("#view-new-construction svg text")].every((t) => {
    const s = t.ownerSVGElement; return parseFloat(getComputedStyle(t).fontSize) * s.getBoundingClientRect().width / s.viewBox.baseVal.width >= 11; })),
  "Neubau, 700 px of room: every text of the charts at least 11 px");
  check(await drawnRents(page, 760), "Rents, 700 px of room: the wide drawing like the columns");
  // the descending boundary: from 700 px of room (wide) down to 699, the key comes back and the note goes
  await page.setViewportSize({ width: 699 + ncOffset, height: 900 });
  check(await drawnNc(page, 0) && await drawnRents(page, 0) && await page.evaluate(() => APP.newConstructionBody.clientWidth) === 699,
    "Rents, 700 down to 699 px of room: the rows and both charts at the width in px");
  check(shownRight(await rentsShown(page), false), "Rents, 700 down to 699 px of room: the keys shown, no note");
  await page.setViewportSize({ width: 1400, height: 900 });
  check(await drawnNc(page, 760) && await drawnRents(page, 760), "Neubau, wide window again: 760 units, every chart");
  check(shownRight(await rentsShown(page), true), "Rents, wide window again: the keys hidden, the note shown");
});

test("resized while hidden: the next opening fits the width", async ({ mapPage: page, check }) => {
  await openNewConstruction(page);
  await page.click('#views button[data-view="map"]');
  await page.setViewportSize({ width: 420, height: 900 });
  // the debounced resize runs while the view is hidden
  await settle(page);
  await page.click('#views button[data-view="new_construction"]');
  check(await drawnNc(page, 0) && await drawnRents(page, 0), "Neubau, resized while hidden: the opening fits the width, every chart");
  check(shownRight(await rentsShown(page), false), "Rents, resized while hidden: the opening shows the keys, no note");
  await page.setViewportSize({ width: 1400, height: 900 });
  check(await drawnNc(page, 760), "Neubau, wide again after the narrow opening");
  check(shownRight(await rentsShown(page), true), "Rents, wide again after the narrow opening: the keys hidden, the note shown");
});
