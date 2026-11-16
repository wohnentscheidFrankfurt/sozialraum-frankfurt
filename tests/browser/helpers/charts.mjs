// Chart checks of the views Trend and Neubau at the width of a phone (docs/design.md, Phone and tablet).
// docs/design.md, Phone and tablet: the charts of the view Trend at the width of the phone. Per chart: no
// sideways overflow, every text inside the window, at least 11 px and free of the others; the boundary of the sectors
// inside the window; per arrow its marks (arrow, or circle and dot) inside the window; numbers in bars inside them.
const trendLayout = (page) => page.evaluate(() => {
  const width = window.innerWidth, view = document.getElementById("view-history");
  const inside = (b) => b.width > 0 && b.height > 0 && b.left >= -0.5 && b.right <= width + 0.5;
  // 2 px of slack: the boxes of SVG text include the line gap
  const meet = (a, c) => a.left + 2 < c.right && c.left + 2 < a.right && a.top + 2 < c.bottom && c.top + 2 < a.bottom;
  const charts = [...view.querySelectorAll(".chart")].map((fig) => {
    const svg = fig.querySelector("svg"), box = svg.getBoundingClientRect(), scale = box.width / svg.viewBox.baseVal.width;
    const texts = [...svg.querySelectorAll("text")].map((t) => ({ text: t.textContent, b: t.getBoundingClientRect(),
      px: parseFloat(getComputedStyle(t).fontSize) * scale }));
    const overlaps = [];
    texts.forEach((a, i) => texts.slice(i + 1).forEach((c) => { if (meet(a.b, c.b)) overlaps.push(a.text + " / " + c.text); }));
    return { chart: svg.getAttribute("class"), overflow: fig.scrollWidth > fig.clientWidth + 1 || !inside(box),
      outside: texts.filter((t) => !inside(t.b)).map((t) => t.text), small: texts.filter((t) => t.px < 11).map((t) => `${t.text} ${t.px}`),
      overlaps };
  });
  const arrows = [...view.querySelectorAll("svg.arrows g[data-tip]")].map((g) => {
    const marks = [...g.querySelectorAll("line, path, circle")].map((e) => e.getBoundingClientRect());
    // the box of a line along the axis is 0 px high
    return marks.length >= 2 && marks.every((b) => b.left >= -0.5 && b.right <= width + 0.5 && b.width + b.height > 0);
  });
  return { charts, viewOverflow: view.scrollWidth > view.clientWidth + 1,
    boundaries: [...view.querySelectorAll("svg.houses path.boundary")].map((p) => inside(p.getBoundingClientRect())),
    sectors: [...view.querySelectorAll("svg.houses .sector text")].map((t) => t.textContent), sectorTitles: APP.data.history.sectors.map((sec) => sec.title),
    rowLabels: view.querySelectorAll("svg.arrows text.row-label").length, arrows,
    inBar: [...view.querySelectorAll("text.in-bar")].filter((t) => { const a = t.getBoundingClientRect(), r = t.previousElementSibling.getBoundingClientRect();
      return a.left < r.left || a.right > r.right; }).map((t) => t.textContent) };
});
export const checkTrend = async (page, check, when) => {
  const t = await trendLayout(page);
  check(!t.viewOverflow && t.charts.length === 4 && t.charts.every((c) => !c.overflow), `${when}: no chart overflows sideways ${JSON.stringify(t.charts.map((c) => c.overflow))}`);
  for (const c of t.charts) {
    check(c.outside.length === 0, `${when}: ${c.chart}: every label inside the window (${c.outside})`);
    check(c.small.length === 0, `${when}: ${c.chart}: no text below 11 px (${c.small})`);
    check(c.overlaps.length === 0, `${when}: ${c.chart}: no text overlaps another (${c.overlaps})`);
  }
  check(t.boundaries.length === 2 && t.boundaries.every(Boolean), `${when}: both boundary lines inside the window`);
  // two years, each label the title of its sector (payload) and its share
  check(t.sectors.length === 4 && t.sectorTitles.length === 2 && t.sectorTitles.every((title) => t.sectors.filter((x) => x.startsWith(title + " ")).length === 2),
    `${when}: four sector labels (${t.sectors})`);
  check(t.rowLabels === 9, `${when}: nine lines of group names in the arrows (${t.rowLabels})`);
  check(t.arrows.length === 14 && t.arrows.every(Boolean), `${when}: every arrow shows its marks in the window (${t.arrows})`);
  check(t.inBar.length === 0, `${when}: numbers in bars stay in their bar (${t.inBar})`);
};

// The view Neubau (docs/design.md, Phone and tablet): no sideways overflow, every text and
// every bar inside the window, texts at least 11 px and free of each other, one group per year.
// The same for the two charts of rents below the columns (svg.rents): every text and dot, hollow dots included.
const constructionLayout = (page) => page.evaluate(() => {
  const width = window.innerWidth, view = document.getElementById("view-new-construction");
  const inside = (b) => b.width > 0 && b.height > 0 && b.left >= -0.5 && b.right <= width + 0.5;
  const meet = (a, c) => a.left + 2 < c.right && c.left + 2 < a.right && a.top + 2 < c.bottom && c.top + 2 < a.bottom;
  const svgTexts = (svg) => {
    const scale = svg.getBoundingClientRect().width / svg.viewBox.baseVal.width;
    const texts = [...svg.querySelectorAll("text")].map((t) => ({ text: t.textContent, b: t.getBoundingClientRect(),
      px: parseFloat(getComputedStyle(t).fontSize) * scale }));
    const overlaps = [];
    texts.forEach((a, i) => texts.slice(i + 1).forEach((c) => { if (meet(a.b, c.b)) overlaps.push(a.text + " / " + c.text); }));
    const frame = svg.getBoundingClientRect(), clipped = (b) => b.left < frame.left - 0.5 || b.right > frame.right + 0.5;
    return { overflow: !inside(frame), outside: texts.filter((t) => !inside(t.b)).map((t) => t.text), clipped: texts.filter((t) => clipped(t.b)).map((t) => t.text),
      small: texts.filter((t) => t.px < 11).map((t) => `${t.text} ${t.px}`), overlaps };
  };
  const svg = view.querySelector("svg.construction"), t = svgTexts(svg);
  // plain text of the view (title, lead, key, source): every leaf inside the window, at least 11 px
  const leaves = [...view.querySelectorAll("*")].filter((e) => !e.closest("svg") && e.offsetParent !== null && e.childElementCount === 0 && e.textContent.trim());
  return { svgs: view.querySelectorAll("svg.construction").length, groups: svg.querySelectorAll("g[data-tip]").length, years: APP.data.new_construction.years.length,
    overflow: view.scrollWidth > view.clientWidth + 1 || t.overflow, outside: t.outside, small: t.small, overlaps: t.overlaps,
    dashed: svg.querySelectorAll("rect.conversions").length,
    bars: [...svg.querySelectorAll("rect")].filter((r) => !r.closest("pattern")).filter((r) => !inside(r.getBoundingClientRect())).length,
    rents: [...view.querySelectorAll("svg.rents")].map((r, k) => { const c = APP.data.new_construction.rents.charts[k];
      const sub = r.closest(".sub"), key = sub.querySelector(".key"), note = sub.querySelector("p.old-base-note"), shown = (e) => !!e && getComputedStyle(e).display !== "none";
      return { ...svgTexts(r), key: key && { cls: key.className, shown: shown(key), entries: [...key.children].map((e) => { const b = e.getBoundingClientRect(), name = e.lastElementChild;
          return { text: e.textContent.trim(), left: b.left, top: b.top, bottom: b.bottom, weight: getComputedStyle(name).fontWeight, color: getComputedStyle(name).color }; }) },
        note: note && { shown: shown(note), text: note.textContent.trim() },
        want: { keyNames: c.key.map((e) => e.name), keyKinds: c.key.map((e) => e.kind),
          endNames: [...c.end_order.map((id) => c.series.find((s) => s.id === id).name), ...c.key.filter((e) => e.kind === "old_base").map((e) => e.name)], noteText: c.old_base_note || null },
        yearFills: [...r.querySelectorAll("text.year")].map((t) => ({ year: Number(t.textContent), fill: getComputedStyle(t).fill, survey: c.survey_years.includes(Number(t.textContent)) })),
        groups: r.querySelectorAll("g[data-tip]:not(.old)").length, years: c.years.length,
        old: r.querySelectorAll("g.old[data-tip]").length, oldWanted: c.old_base ? 2 : 0, units: r.viewBox.baseVal.width, room: r.parentElement.clientWidth,
        dots: r.querySelectorAll("circle.dot").length, dotsOutside: [...r.querySelectorAll("circle.dot")].filter((d) => !inside(d.getBoundingClientRect())).length }; }),
    leavesOutside: leaves.filter((e) => { const b = e.getBoundingClientRect(); return b.left < -0.5 || b.right > width + 0.5; }).map((e) => e.textContent.trim().slice(0, 30)),
    leavesSmall: leaves.filter((e) => parseFloat(getComputedStyle(e).fontSize) < 11).map((e) => e.textContent.trim().slice(0, 30)) };
});
export const checkConstruction = async (page, check, when) => {
  const c = await constructionLayout(page);
  check(c.svgs === 1 && c.groups === c.years, `${when}: one chart, one group per year (${c.svgs}, ${c.groups} of ${c.years})`);
  check(!c.overflow, `${when}: the chart does not overflow sideways`);
  check(c.outside.length === 0, `${when}: every label inside the window (${c.outside})`);
  check(c.small.length === 0, `${when}: no chart text below 11 px (${c.small})`);
  check(c.overlaps.length === 0, `${when}: no chart text overlaps another (${c.overlaps})`);
  check(c.dashed === c.years, `${when}: one dashed frame of conversions per year (${c.dashed})`);
  check(c.bars === 0, `${when}: every bar inside the window (${c.bars})`);
  // the rents switch with the columns: drawn in px below 700 px of room, else the 760-unit drawing
  check(c.rents.length === 2, `${when}, rents: two charts (${c.rents.length})`);
  c.rents.forEach((r, k) => {
    const what = `${when}, rents ${k + 1}`;
    check(r.groups === r.years && r.old === r.oldWanted, `${what}: one group per year and one per hollow dot (${r.groups} of ${r.years}, ${r.old})`);
    check(r.room >= 700 ? r.units === 760 : Math.abs(r.units - r.room) < 1, `${what}: ${r.room >= 700 ? "the wide drawing" : "drawn at the width in px"} (room ${r.room}, ${r.units} units)`);
    check(!r.overflow, `${what}: the chart does not overflow sideways`);
    check(r.outside.length === 0, `${what}: every text inside the window (${r.outside})`);
    check(r.clipped.length === 0, `${what}: every text inside its svg (${r.clipped})`);
    check(r.small.length === 0, `${what}: no chart text below 11 px (${r.small})`);
    check(r.overlaps.length === 0, `${what}: no chart text overlaps another (${r.overlaps})`);
    check(r.dots > 0 && r.dotsOutside === 0, `${what}: every dot inside the window (${r.dotsOutside} of ${r.dots} outside)`);
    // a survey year in the ink, every other year grey, in any width
    check(r.yearFills.length > 0 && r.yearFills.every((t) => t.fill === (t.survey ? "rgb(26, 26, 26)" : "rgb(107, 107, 107)")),
      `${what}: the survey years in the ink, the other years grey (${r.yearFills.map((t) => `${t.year} ${t.fill}`)})`);
    // the key serves phones: shown below 700 px of room, as one column in the order of the line ends, then the old base;
    // from 700 px of room the end labels name the lines and the note under chart 1 explains the hollow dots
    const wide = r.room >= 700;
    check(r.key && r.key.cls.split(" ").includes("rents-key") && r.key.shown === !wide, `${what}: the key is ${wide ? "hidden" : "shown"} (room ${r.room}, ${r.key && r.key.shown})`);
    check(wide ? (r.note ? r.note.shown && r.note.text === r.want.noteText : r.want.noteText === null) : !r.note || !r.note.shown,
      `${what}: the note of the old base is ${wide ? "shown under chart 1 only" : "hidden"} (${JSON.stringify(r.note)})`);
    if (!wide) {
      const e = r.key.entries;
      check(JSON.stringify(e.map((x) => x.text)) === JSON.stringify(r.want.keyNames) && JSON.stringify(e.map((x) => x.text)) === JSON.stringify(r.want.endNames),
        `${what}: the key names in the order of the line ends, then the old base (${e.map((x) => x.text)})`);
      check(e.length > 0 && e.every((x) => Math.abs(x.left - e[0].left) < 0.5) && e.every((x, i) => i === 0 || x.top >= e[i - 1].bottom - 0.5),
        `${what}: the key is one column, every entry starts at the same x (${e.map((x) => Math.round(x.left))})`);
      check(e.every((x, i) => x.weight === "400" && x.color === (r.want.keyKinds[i] === "reference" ? "rgb(107, 107, 107)" : "rgb(26, 26, 26)")),
        `${what}: key names in normal weight, the references grey (${e.map((x) => x.weight + " " + x.color)})`);
    }
  });
  check(c.leavesOutside.length === 0, `${when}: every text of the view inside the window (${c.leavesOutside})`);
  check(c.leavesSmall.length === 0, `${when}: no text of the view below 11 px (${c.leavesSmall})`);
};

// The view Miete (docs/design.md, Phone and tablet): the wage bars and the bars of tenants at the width of the window.
// Per drawing: no sideways overflow, every text inside the window and inside its svg, at least 11 px and free of the
// others. The numbers in the segments follow the payload: a number stands only where Python set `text` and the segment
// is wide enough for it, inside its segment. The segments of a bar add up to the full bar. The key of the bars serves
// phones as a column, wide it stands in one line. The view has no key of lines.
const rentBurdenLayout = (page) => page.evaluate(() => {
  const width = window.innerWidth, view = document.getElementById("view-rent-burden");
  const inside = (b) => b.width > 0 && b.height > 0 && b.left >= -0.5 && b.right <= width + 0.5;
  // 2 px of slack: the boxes of SVG text include the line gap
  const meet = (a, c) => a.left + 2 < c.right && c.left + 2 < a.right && a.top + 2 < c.bottom && c.top + 2 < a.bottom;
  const svgs = [...view.querySelectorAll("svg.wage, svg.burden")].map((svg) => {
    const frame = svg.getBoundingClientRect(), scale = frame.width / svg.viewBox.baseVal.width;
    const texts = [...svg.querySelectorAll("text")].map((t) => ({ text: t.textContent, b: t.getBoundingClientRect(), px: parseFloat(getComputedStyle(t).fontSize) * scale }));
    const overlaps = [];
    texts.forEach((a, i) => texts.slice(i + 1).forEach((c) => { if (meet(a.b, c.b)) overlaps.push(a.text + " / " + c.text); }));
    return { cls: svg.getAttribute("class"), units: svg.viewBox.baseVal.width, room: svg.parentElement.clientWidth, overflow: !inside(frame), texts: texts.length,
      outside: texts.filter((t) => !inside(t.b)).map((t) => t.text),
      clipped: texts.filter((t) => t.b.left < frame.left - 0.5 || t.b.right > frame.right + 0.5 || t.b.top < frame.top - 0.5 || t.b.bottom > frame.bottom + 0.5).map((t) => t.text),
      small: texts.filter((t) => t.px < 11).map((t) => `${t.text} ${t.px}`), overlaps,
      dotsOutside: [...svg.querySelectorAll("circle.dot")].filter((d) => !inside(d.getBoundingClientRect())).length };
  });
  const burden = view.querySelector("svg.burden"), want = APP.data.rent_burden.low_income.bars;
  const segments = burden ? [...burden.querySelectorAll("g.segment")].map((g, i) => {
    const s = want.flatMap((b) => b.segments)[i], rect = g.querySelector("rect"), t = g.querySelector("text"), r = rect.getBoundingClientRect();
    const b = t && t.getBoundingClientRect();
    return { id: g.dataset.segment, want: s && s.id, text: t ? t.textContent.replace(/\u00a0/g, " ") : null, payload: s && s.text != null ? s.text : null,
      units: Number(rect.getAttribute("width")), share: s && s.value, left: r.left, right: r.right, textInside: b ? b.left >= r.left - 0.5 && b.right <= r.right + 0.5 : null }; }) : [];
  const frame = burden && burden.getBoundingClientRect();
  const bars = want.map((bar, k) => { const row = segments.slice(k * bar.segments.length, (k + 1) * bar.segments.length);
    return { left: row[0].left, right: row.at(-1).right, sum: row.reduce((a, s) => a + (s.right - s.left), 0),
      gap: Math.max(...row.map((s, i) => (i ? Math.abs(s.left - row[i - 1].right) : 0))) }; });
  const column = (e) => e && [...e.children].map((c) => { const b = c.getBoundingClientRect(); return { text: c.textContent.trim(), left: b.left, top: b.top, bottom: b.bottom }; });
  const shown = (e) => !!e && getComputedStyle(e).display !== "none";
  return { svgs, segments, bars, frameRight: frame && frame.right, viewOverflow: view.scrollWidth > view.clientWidth + 1,
    narrow: view.querySelector(".burden-key") && APP.burdenBody.clientWidth < APP.CONSTRUCTION_WIDE, char: APP.BURDEN_CHAR,
    linesKeys: view.querySelectorAll(".rents-key").length,
    barsKey: (() => { const k = view.querySelector(".burden-key"); return k && { column: k.classList.contains("column"), shown: shown(k), entries: column(k) }; })() };
});
export const checkRentBurden = async (page, check, when) => {
  const r = await rentBurdenLayout(page), classes = r.svgs.map((s) => s.cls).join();
  check(!r.viewOverflow && classes === "wage,burden", `${when}: no sideways overflow, two drawings (${classes})`);
  for (const [k, s] of r.svgs.entries()) {
    const what = `${when}, ${s.cls} ${k + 1}`;
    check(s.room >= 700 ? s.units === 760 : Math.abs(s.units - s.room) < 1, `${what}: ${s.room >= 700 ? "the wide drawing" : "drawn at the width in px"} (room ${s.room}, ${s.units} units)`);
    check(!s.overflow && s.texts > 0, `${what}: the drawing does not overflow sideways`);
    check(s.outside.length === 0, `${what}: every text inside the window (${s.outside})`);
    check(s.clipped.length === 0, `${what}: every text inside its svg (${s.clipped})`);
    check(s.small.length === 0, `${what}: no text below 11 px (${s.small})`);
    check(s.overlaps.length === 0, `${what}: no text overlaps another (${s.overlaps})`);
    check(s.dotsOutside === 0, `${what}: every dot inside the window`);
  }
  // the numbers in the segments: only where the payload has `text` and the segment is wide enough, inside the segment
  check(r.segments.length === 12 && r.segments.every((s) => s.id === s.want), `${when}: twelve segments in the order of the payload`);
  for (const s of r.segments) {
    const fits = s.payload !== null && s.units >= s.payload.length * r.char + 8;
    check(s.text === (fits ? s.payload : null), `${when}: segment ${s.id} shows its number only if the payload has one and it fits (${s.text} / ${s.payload}, ${s.units} units)`);
    check(s.text === null || s.textInside, `${when}: the number of segment ${s.id} stays inside its segment`);
  }
  // the segments add up to the full bar, and every bar has the same extent
  check(r.bars.length === 3 && r.bars.every((b) => Math.abs(b.sum - (b.right - b.left)) <= 1 && b.gap <= 1 && Math.abs(b.right - r.frameRight) <= 1
    && Math.abs(b.left - r.bars[0].left) <= 1), `${when}: the segments add up to the full bar (${JSON.stringify(r.bars.map((b) => [b.left, b.right, b.sum]))})`);
  check(r.linesKeys === 0, `${when}: no key of lines (${r.linesKeys})`);
  check(r.barsKey && r.barsKey.shown && r.barsKey.column === r.narrow, `${when}: the key of the bars is ${r.narrow ? "a column" : "in one line"}`);
  const e = r.barsKey && r.barsKey.entries;
  check(e && e.length === 4 && (r.narrow ? e.every((x, i) => Math.abs(x.left - e[0].left) < 0.5 && (!i || x.top >= e[i - 1].bottom - 0.5))
    : e.every((x) => Math.abs(x.top - e[0].top) < 1)), `${when}: the key of the bars ${r.narrow ? "stands in one column" : "stands in one line"}`);
};
