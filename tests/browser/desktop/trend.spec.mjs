// View Trend: ownership 2011–2022 (pipeline/use_cases/ownership_history/README.md), its charts, tooltips, the narrow
// drawing, and the texts of the view (docs/texts.md, Trend).
import { test } from "../fixtures.mjs";
import { frames } from "../helpers/common.mjs";
import { historyDrawnAt, openTrend, tipText } from "../helpers/views.mjs";

test("the switch opens the view Trend with four charts", async ({ mapPage: page, check }) => {
  await openTrend(page);
  const history = await page.evaluate(() => ({
    mainHidden: document.querySelector("main").hidden, viewHidden: document.getElementById("view-history").hidden,
    svgs: [...document.querySelectorAll("#view-history svg")].map((s) => s.getAttribute("class")),
    text: document.getElementById("view-history").textContent,
    pressed: document.querySelector('#views button[data-view="history"]').getAttribute("aria-pressed"),
    headings: [...document.querySelectorAll("#view-history figure > h2")].map((e) => e.textContent),
    titles: Object.values(APP.data.history.charts).map((c) => APP.keepUnits(c.title)),
    // what the view shows, from the payload: the texts of each chart, the groups with the dwellings of the companies,
    // the sectors with their share 2022, the dwellings of companies in large buildings, the source, the row labels
    want: (() => {
      const h = APP.data.history, f = APP.format;
      return [...Object.values(h.charts).flatMap((c) => [c.title, c.lead, c.caveat].filter(Boolean).map(APP.keepUnits)),
        ...h.groups.map((g) => g.title), ...h.groups.filter((g) => g.company).map((g) => f(g.values["2022"], 0)),
        ...h.sectors.map((s) => `${s.title} ${f(s.share.values["2022"], 1)} %`), f(h.sizes.at(-1).company["2022"], 0),
        h.source, ...h.decades.map((d) => d.label), ...h.sizes.map((s) => s.label)];
    })(),
  }));
  check(history.mainHidden && !history.viewHidden && history.pressed === "true", "the switch opens the chart view");
  check(JSON.stringify(history.svgs) === JSON.stringify(["houses", "decades", "arrows", "sizes"]), "four charts: " + JSON.stringify(history.svgs));
  check(JSON.stringify(history.headings) === JSON.stringify(history.titles), "the chart of the company classes is gone: " + JSON.stringify(history.headings));
  for (const t of history.want) {
    check(t && history.text.includes(t), "chart view shows " + t);
  }
  // a number and its "%" never break apart in the texts of the charts (iPhone SE broke "19 %" in the lead line)
  const looseUnits = await page.evaluate(() => [...document.querySelectorAll("#view-history figure > h2, #view-history figure > p, #view-history .history > p")]
    .map((e) => e.textContent).filter((t) => /\d %/.test(t)));
  check(looseUnits.length === 0, "chart texts keep a number and % together: " + JSON.stringify(looseUnits));
});

test("chart 1: tooltips of the groups, the sector boundary and its labels", async ({ mapPage: page, check }) => {
  await openTrend(page);
  // every tooltip of a group describes it, examples only in 2022. The tooltips of the payload: per year and bar
  // (buildings, dwellings) and group the title, the year, the count and the share, then the note of the group
  const tips = await page.evaluate(() => {
    const h = APP.data.history, f = APP.format;
    const want = ["2011", "2022"].flatMap((year) => ["buildings", "values"].flatMap((key) => APP.groupsInOrder(h).map((g) => ({
      head: `${g.title} ${year}: ${f(g[key][year], 0)} `, tail: `(${f(g.share[key][year], 1)} %).` + APP.groupNote(g, year === "2022") }))));
    return { shown: [...document.querySelectorAll("svg.houses rect[data-tip]")].map((r) => r.dataset.tip), want,
      examples: h.groups.map((g) => g.example).filter(Boolean) };
  });
  const houseTips = tips.shown;
  for (const { head, tail } of tips.want) {
    check(houseTips.some((t) => t.startsWith(head) && t.endsWith(tail)), "houses tooltip: " + head + "… " + tail);
  }
  check(houseTips.length === 28 && tips.examples.length > 0 && houseTips.filter((t) => t.includes(" 2011: ")).every((t) => !tips.examples.some((e) => t.includes(e))),
    "houses: 28 tooltips, no examples in 2011: " + houseTips.filter((t) => t.includes(" 2011: ") && tips.examples.some((e) => t.includes(e))));
  // docs/design.md, Sector boundary: per year a black line follows the boundary of the sectors; the
  // labels face each other at its foot in the main colours; in 2022 a dashed line marks the boundary of 2011
  const sectorMarks = await page.evaluate(() => {
    const svg = document.querySelector("svg.houses"), vb = svg.viewBox.baseVal;
    const inside = (b) => b.x >= 0 && b.x + b.width <= vb.width && b.y >= 0 && b.y + b.height <= vb.height;
    const h = APP.data.history, f = APP.format, [first, second] = h.sectors;
    // the right edge of the last group of the first sector in the bar of the buildings or of the dwellings; the rect is
    // found by the head of its tooltip (title, year, count of the payload)
    const last = h.groups.find((g) => g.id === first.groups.at(-1));
    const edge = (year, key) => { const r = [...svg.querySelectorAll("rect[data-tip]")].find((e) =>
      e.dataset.tip.startsWith(`${last.title} ${year}: ${f(last[key][year], 0)} `)); return r.x.baseVal.value + r.width.baseVal.value; };
    return {
      first: first.title,
      // the tooltip of the second sector in 2022: title, year, count, share, then the titles of its groups
      sectorTip: { head: `${second.title} 2022: ${f(second.count.values["2022"], 0)} `, share: `(${f(second.share.values["2022"], 1)} %)`,
        tail: second.groups.map((id) => h.groups.find((g) => g.id === id).title).join(", ") + "." },
      // the boundary of 2011: both sectors with their share of the dwellings 2011
      before: h.sectors.map((sec) => `${sec.title} ${f(sec.share.values["2011"], 1)} %`).join(", "),
      lines: [...svg.querySelectorAll("path.boundary")].map((p, i) => ({ top: p.getPointAtLength(0).x, x: p.getPointAtLength(p.getTotalLength()).x,
        houses: edge(["2011", "2022"][i], "buildings"), dwellings: edge(["2011", "2022"][i], "values"), stroke: p.getAttribute("stroke"),
        pointer: p.getAttribute("pointer-events"), inside: inside(p.getBBox()) })),
      labels: [...svg.querySelectorAll(".sector text")].map((t) => {
        const b = t.getBBox();
        return { text: t.textContent, fill: getComputedStyle(t).fill, left: b.x, right: b.x + b.width,
          inside: inside(b) };
      }),
      tips: [...svg.querySelectorAll(".sector")].map((g) => g.dataset.tip),
      visibleRects: svg.querySelectorAll(".sector rect:not([fill-opacity='0'])").length,
      previous: [...svg.querySelectorAll(".previous-boundary")].map((g) => ({ x: g.querySelector("line").x1.baseVal.value,
        text: g.querySelector("text").textContent, tip: g.dataset.tip, inside: inside(g.getBBox()) })),
    };
  });
  const [b11, b22] = sectorMarks.lines.map((l) => l.x);
  check(sectorMarks.lines.length === 2 && sectorMarks.lines.every((l) => l.stroke === "#1a1a1a" && l.pointer === "none" && l.inside
    && Math.abs(l.top - l.houses) < 0.5 && Math.abs(l.x - l.dwellings) < 0.5),
  "one boundary line per year, at the edge of „Privat“ in both bars: " + JSON.stringify(sectorMarks.lines));
  check(sectorMarks.labels.length === 4 && sectorMarks.labels.every((l, i) => l.inside && (l.text.startsWith(sectorMarks.first + " ")
    ? l.fill === "rgb(38, 38, 38)" && Math.abs(l.right - [b11, b22][i >> 1] + 8) < 1.5
    : l.fill === "rgb(212, 0, 0)" && Math.abs(l.left - [b11, b22][i >> 1] - 8) < 1.5)),
  "sector labels face each other at the boundary, in the main colours: " + JSON.stringify(sectorMarks));
  const { head, share, tail } = sectorMarks.sectorTip;
  check(sectorMarks.tips.some((t) => t.startsWith(head) && t.includes(share) && t.endsWith(tail)),
    "sector tooltip: " + JSON.stringify(sectorMarks.tips));
  check(sectorMarks.visibleRects === 0, "no rule per sector any more");
  check(sectorMarks.previous.length === 1 && Math.abs(sectorMarks.previous[0].x - b11) < 0.5 && sectorMarks.previous[0].text.includes("2011")
    && sectorMarks.previous[0].inside && sectorMarks.previous[0].tip.startsWith(sectorMarks.previous[0].text + ": ")
    && sectorMarks.previous[0].tip.includes(": " + sectorMarks.before + " "),
  "in 2022 the boundary of 2011: " + JSON.stringify(sectorMarks.previous));
});

test("labels in bars and at the arrows: contrast, room, no overlap", async ({ mapPage: page, check }) => {
  await openTrend(page);
  // pipeline/use_cases/ownership_history/README.md: text inside a bar reaches 4.5:1 and fits into its bar
  const inBar = await page.evaluate(() => {
    const rgb = (s) => s.startsWith("#") ? [1, 3, 5].map((i) => parseInt(s.slice(i, i + 2), 16)) : s.match(/\d+/g).slice(0, 3).map(Number);
    const lum = (c) => { const v = c.map((x) => x / 255).map((x) => (x <= 0.03928 ? x / 12.92 : ((x + 0.055) / 1.055) ** 2.4)); return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2]; };
    return [...document.querySelectorAll("#view-history text.in-bar")].map((t) => {
      const r = t.previousElementSibling, a = lum(rgb(r.getAttribute("fill"))), b = lum(rgb(getComputedStyle(t).fill));
      const tb = t.getBBox(), rb = r.getBBox();
      return { text: t.textContent, ratio: (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05),
        fits: r.tagName === "rect" && tb.x >= rb.x + 2 && tb.x + tb.width <= rb.x + rb.width - 2 };
    });
  });
  check(inBar.length >= 8 && inBar.every((t) => t.ratio >= 4.5 && t.fits), "text in bars: contrast ≥ 4.5 and fits: " + JSON.stringify(inBar.filter((t) => t.ratio < 4.5 || !t.fits)));
  const arrowLabels = await page.evaluate(() => {
    const boxes = [...document.querySelectorAll("svg.arrows .arrow-label")].map((t) => t.getBBox());
    const out = [];
    for (let i = 0; i < boxes.length; i++) for (let j = i + 1; j < boxes.length; j++) {
      const a = boxes[i], c = boxes[j];
      if (a.y < c.y + c.height && c.y < a.y + a.height && a.x < c.x + c.width && c.x < a.x + a.width) out.push(i + "/" + j);
    }
    return { n: boxes.length, out, inside: boxes.every((b) => b.x >= 0 && b.x + b.width <= 760) };
  });
  check(arrowLabels.n === 14 && arrowLabels.out.length === 0 && arrowLabels.inside, "arrow labels: 14, no overlap, inside the chart: " + JSON.stringify(arrowLabels));
  // row labels of the arrows stay inside the chart; long titles break into two lines (the lines of the group in the payload)
  const rows = await page.evaluate(() => ({ shown: [...document.querySelectorAll("svg.arrows text.row-label")].map((t) => ({ text: t.textContent, x: t.getBBox().x })),
    want: APP.groupsInOrder(APP.data.history).flatMap((g) => g.lines || [g.title]),
    broken: APP.data.history.groups.filter((g) => g.company).every((g) => g.lines && g.lines.length === 2) }));
  const rowLabels = rows.shown;
  check(rowLabels.length === 9 && rowLabels.every((l) => l.x >= 0) && rows.broken && JSON.stringify(rowLabels.map((l) => l.text)) === JSON.stringify(rows.want),
    "arrow row labels inside the chart, two lines for the company classes: " + JSON.stringify(rowLabels));
  // a thick arrow keeps 3:1 against white (WCAG non-text contrast)
  const arrowContrast = await page.evaluate(() => {
    const lum = (hex) => { const v = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255).map((x) => (x <= 0.03928 ? x / 12.92 : ((x + 0.055) / 1.055) ** 2.4)); return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2]; };
    return [...document.querySelectorAll("svg.arrows line[stroke-width='4']")]
      .map((l) => ({ c: l.getAttribute("stroke"), r: 1.05 / (lum(l.getAttribute("stroke")) + 0.05) })).filter((x) => x.r < 3);
  });
  check(arrowContrast.length === 0, "thick arrows reach 3:1: " + JSON.stringify(arrowContrast));
});

test("chart tooltips: hover shows, scrolling and leaving hide", async ({ mapPage: page, check, saveScreenshot }) => {
  await openTrend(page);
  // tooltips: hover shows, German numbers, leaving the view hides. Each element is found by the head of its tooltip,
  // built from the payload; the tooltip shown is its data-tip, and the data-tip holds the numbers of the payload.
  const want = await page.evaluate(() => {
    const h = APP.data.history, f = APP.format, g = h.groups.find((x) => x.id === "housing_company"), c = h.company;
    const large = h.sizes.find((x) => x.size === "13_plus"), decade = h.decades[0];
    return {
      company: { head: `${g.title} 2022: ${f(g.buildings["2022"], 0)} `, parts: [`(${f(g.share.buildings["2022"], 1)} %).`], tail: APP.groupNote(g, true) },
      large: { head: `${c.title} 2022: ${f(large.company["2022"], 0)} `, parts: [large.long, `${f(large.company_share["2022"], 1)} %`], tail: " " + h.charts.sizes.tip_large_text },
      decade: { head: `${c.title} 2022: ${f(decade.values["2022"], 0)} `, parts: [], tail: `(2011: ${f(decade.values["2011"], 0)})` },
      arrow: { head: `${g.title}, `, parts: [`${f(g.values["2011"], 0)} → ${f(g.values["2022"], 0)} (${g.change.values})`,
        `${f(g.share.values["2011"], 1)} → ${f(g.share.values["2022"], 1)} %`], tail: APP.groupNote(g, true) },
    };
  });
  // nth(-1) would take the last element, so a head that no element has is a failed check
  const byHead = async (selector, head) => {
    const i = await page.evaluate(([s, p]) => [...document.querySelectorAll(s)].findIndex((e) => e.dataset.tip.startsWith(p)), [selector, head]);
    check(i >= 0, `${selector}: an element whose tooltip starts with ${head}`);
    return page.locator(selector).nth(i);
  };
  const hover = async (selector, w) => {
    const target = await byHead(selector, w.head);
    const shown = await tipText(page, target);
    const tip = await target.getAttribute("data-tip");
    return { shown, ok: shown === tip && tip.startsWith(w.head) && w.parts.every((p) => tip.includes(p)) && tip.endsWith(w.tail) };
  };
  const companyTip = await hover("svg.houses rect[data-tip]", want.company);
  check(companyTip.ok, "tooltip on the company segment: " + companyTip.shown);
  // every bar tooltip starts with group and year, as in chart 1
  const largeTip = await hover("svg.sizes rect[data-tip]", want.large);
  check(largeTip.ok, "tooltip of large buildings 2022: " + largeTip.shown);
  const decadeTip = await hover("svg.decades rect[data-tip]", want.decade);
  check(decadeTip.ok, "tooltip of a decade 2022: " + decadeTip.shown);
  // the arrow of the dwellings: the second group of the company with this head
  const arrowIndex = await page.evaluate((w) => [...document.querySelectorAll("svg.arrows g[data-tip]")]
    .findIndex((e) => e.dataset.tip.startsWith(w.head) && w.parts.every((p) => e.dataset.tip.includes(p))), want.arrow);
  check(arrowIndex >= 0, "an arrow with the head and the numbers of the company dwellings");
  const arrowTarget = page.locator("svg.arrows g[data-tip]").nth(arrowIndex);
  const arrowShown = await tipText(page, arrowTarget), arrowData = await arrowTarget.getAttribute("data-tip");
  check(arrowShown === arrowData && arrowData.startsWith(want.arrow.head) && arrowData.endsWith(want.arrow.tail), "tooltip of the company arrow: " + arrowShown);
  // scrolling the view hides the tooltip, it would no longer point at its bar (the charts never scroll sideways)
  for (const [what, scroll] of [["view", 'document.getElementById("view-history").scrollBy(0, 200)']]) {
    await tipText(page, await byHead("svg.houses rect[data-tip]", want.company.head));
    await page.evaluate(scroll);
    await page.evaluate(() => new Promise((r) => requestAnimationFrame(() => r())));
    check(await page.evaluate(() => document.querySelector(".chart-tip").hidden), "scrolling the " + what + " hides the tooltip");
  }
  await page.mouse.move(5, 5);
  check(await page.evaluate(() => document.querySelector(".chart-tip").hidden), "leaving the view hides the tooltip");
  const charts = page.locator("#view-history .chart");
  for (let i = 0; i < await charts.count(); i++) await saveScreenshot(`history_${i + 1}`, { element: charts.nth(i) });
});

test("narrow window: drawn at its width; back on the map", async ({ mapPage: page, check, saveScreenshot }) => {
  await openTrend(page);
  // docs/design.md, Phone and tablet: below 600 px of room every chart is drawn at its width in px, so its
  // text keeps its size; a resize redraws it (debounced), back on a wide window it is the drawing of 760 units again
  await page.setViewportSize({ width: 420, height: 900 });
  check(await historyDrawnAt(page, 0), "narrow window: every chart is drawn at its width, text at its real size");
  await saveScreenshot("history_narrow", { element: page.locator("#view-history .chart").first() });
  check(await page.evaluate(() => { const v = document.getElementById("view-history"); return v.scrollWidth <= v.clientWidth + 1; }),
    "narrow window: the view does not overflow");
  await page.setViewportSize({ width: 1400, height: 900 });
  check(await historyDrawnAt(page, 760), "wide window again: the drawing of 760 units");
  await page.click('#views button[data-view="map"]');
  await frames(page);
  check(await page.evaluate(() => { const c = APP.map.getContainer(), s = APP.map.getSize(); return !document.querySelector("main").hidden && s.x === c.clientWidth && s.y === c.clientHeight && s.x > 0; }),
    "back on the map, Leaflet knows its size");
  const backProfile = await page.evaluate(() => { APP.setLevel("district"); APP.showProfile("10"); return document.getElementById("tab-area").textContent.length; });
  check(backProfile > 100, "the map still works after the chart view");
});

// docs/texts.md, Trend: no intro line, one source line, clear keys
test("texts 4.1-4.6: no intro line, one source line, clear keys", async ({ mapPage: page, check }) => {
  await page.evaluate(() => APP.openView("history"));
  const t = await page.evaluate(() => {
    const h = document.querySelector("#view-history .history"), figs = [...h.querySelectorAll("figure")];
    const keys = (cls) => [...document.querySelectorAll(`svg.${cls}`)].map((s) => [...s.parentElement.querySelectorAll(".key span")].map((e) => e.textContent))[0];
    const tipRow = document.querySelector("svg.decades rect[data-tip]");
    return { figureFirst: h.firstElementChild === figs[0] && !h.querySelector("p.intro"), sources: [...document.querySelectorAll("#view-history p.source")].map((p) => p.textContent),
      sourceLast: h.lastElementChild.matches("p.source"), figSources: figs.filter((f) => f.querySelector(".source")).length,
      caveat: figs[0].querySelector(".caveat")?.textContent, arrowsKey: document.querySelector("svg.arrows").parentElement.querySelector(".key").textContent,
      sizesKey: keys("sizes"), decadesKey: keys("decades"), tip: tipRow.dataset.tip,
      label: tipRow.parentElement.querySelector("text").textContent, heading: figs[3].querySelector("h2").textContent,
      inBar: [...document.querySelectorAll("#view-history text.in-bar")].map((e) => e.textContent), source: APP.keepUnits(APP.data.history.source),
      charts: APP.data.history.charts, wantCaveat: APP.keepUnits(APP.data.history.charts.houses.caveat), wantHeading: APP.keepUnits(APP.data.history.charts.sizes.title),
      // the tooltips of a chart, to find its unit in them
      sizesTips: [...document.querySelectorAll("svg.sizes rect[data-tip]")].map((r) => r.dataset.tip),
      decadesTips: [...document.querySelectorAll("svg.decades rect[data-tip]")].map((r) => r.dataset.tip),
      decade: APP.data.history.decades[0], company: APP.data.history.company.title, decadeCount: APP.format(APP.data.history.decades[0].values["2011"], 0) };
  });
  check(t.figureFirst, "10 4.1: the first chart opens the view, no intro line");
  check(t.sources.length === 1 && t.sourceLast && t.sources[0].endsWith(t.source) && t.sources[0].length > t.source.length && t.figSources === 0,
    "10 4.2: one source line, last: " + JSON.stringify(t.sources));
  check(t.caveat && t.caveat === t.wantCaveat, "10 4.3: caveat of chart 1");
  check(t.charts.arrows.key && t.arrowsKey === t.charts.arrows.key, "10 4.5: key of chart 3");
  // a key names the unit: "<unit> 2011", "<unit> 2022", and the tooltips of its chart count in that unit
  const unitOf = (key, tips) => { const u = key?.length === 2 && key[0].endsWith(" 2011") && key[1].endsWith(" 2022") && key[0].slice(0, -5);
    return u && key[1] === u + " 2022" && tips.length > 0 && tips.every((tip) => new RegExp("\\d " + u + "\\b").test(tip)) ? u : null; };
  check(unitOf(t.sizesKey, t.sizesTips) && unitOf(t.decadesKey, t.decadesTips) && unitOf(t.sizesKey, t.sizesTips) !== unitOf(t.decadesKey, t.decadesTips), "10 4.4: keys name the unit: " + JSON.stringify([t.sizesKey, t.decadesKey]));
  // the first decade in the 2011 tooltip, its label with a lower-case first letter; the row label as in the payload
  const lowered = t.decade.label[0].toLowerCase() + t.decade.label.slice(1);
  check(t.tip.startsWith(`${t.company} 2011: ${t.decadeCount} `) && t.tip.endsWith(" " + lowered) && lowered !== t.decade.label && t.label === t.decade.label,
    "10 4.4: decades tooltip lowers the label: " + t.tip);
  check(t.heading && t.heading === t.wantHeading, "10 4.6: chart 4 heading");
  check(t.inBar.length >= 8 && t.inBar.every((x) => /^\d{1,2},\d\u00a0%$/.test(x)), "10 4.5: numbers in bars carry %: " + JSON.stringify(t.inBar));
});
