// View Miete (pipeline/use_cases/rent_burden/README.md): the warm rent against the net wage as wage bars of the latest
// year with a switch of the contract, and the warm rent against the income as stacked bars (docs/design.md, View Miete). Every text and number is read from
// the payload (APP.data.rent_burden); the tests check rules, numbers and structure, never the wording.
import { test } from "../fixtures.mjs";
import { noOverflow, settle } from "../helpers/common.mjs";
import { checkRentBurden } from "../helpers/charts.mjs";
import { viewButtons } from "../helpers/layout.mjs";
import { drawnRentBurden, openRentBurden, rentTipText, rgb } from "../helpers/views.mjs";

const VIEW = "#view-rent-burden";
const payload = (page) => page.evaluate(() => APP.data.rent_burden);
// a text as the page shows it: a number and its % keep together (APP.keepUnits), a space that does not break
const plain = (text) => text.replace(/ /g, " ");
// the wage bars as drawn: per row its tooltip, frame, red block, number in the block, what is left and the sub line
const wageDrawn = (page) => page.evaluate((view) => {
  const svg = document.querySelector(view + " svg.wage"), num = (e, a) => e && parseFloat(e.getAttribute(a)), text = (e) => e && e.textContent.replace(/ /g, " ");
  return { units: svg.viewBox.baseVal.width, hasWidth: svg.hasAttribute("width"), char: APP.BURDEN_CHAR, contract: APP.wageContract,
    rentLabel: text(svg.querySelector("text.rent-label")), labels: svg.querySelectorAll("text.rent-label").length,
    guides: [...svg.querySelectorAll("line.guide")].map((l) => ({ x1: num(l, "x1"), x2: num(l, "x2") })),
    rows: [...svg.querySelectorAll("g.row")].map((g) => { const frame = g.querySelector("rect.frame"), rent = g.querySelector("rect.rent");
      return { person: g.dataset.person, tip: g.dataset.tip, name: text(g.querySelector("text.name")), sub: text(g.querySelector("text.sub")),
        frame: { x: num(frame, "x"), w: num(frame, "width") }, rent: { x: num(rent, "x"), w: num(rent, "width"), fill: getComputedStyle(rent).fill,
          box: rent.getBoundingClientRect().width, frameBox: frame.getBoundingClientRect().width },
        inBar: text(g.querySelector("text.in-bar")), inBarFill: g.querySelector("text.in-bar") && getComputedStyle(g.querySelector("text.in-bar")).fill,
        left: text(g.querySelector("text.left")) }; }) };
}, VIEW);
// the switch as shown: per button its contract, text and aria-pressed
const switchShown = (page) => page.evaluate((view) => [...document.querySelectorAll(view + " .wage-switch button")].map((b) => ({ contract: b.dataset.contract, text: b.textContent,
  pressed: b.getAttribute("aria-pressed"), type: b.type })), VIEW);
// wait until the red blocks stand still (the move after a switch)
const still = (page) => page.waitForFunction((view) => [...document.querySelectorAll(view + " svg.wage rect.rent")].every((r) => getComputedStyle(r).transform === "none"
  && r.getAnimations().length === 0), VIEW, { timeout: 3000 }).then(() => true, () => false);
// the wide drawing of one contract against the payload: frames in euros on one scale, the same red block in every row
const checkWide = (check, d, w, c, what) => {
  const plot = d.units - d.rows[0].frame.x, scale = plot / w.max_net;
  check(d.contract === c.id && d.rows.length === 3 && d.rows.map((r) => r.person).join() === c.rows.map((r) => r.id).join(), `${what}: one row per person in the order of the payload`);
  check(d.rows.every((r, k) => Math.abs(r.frame.w - c.rows[k].net * scale) <= 0.5 && r.frame.x === d.rows[0].frame.x), `${what}: each frame is the net wage on one scale`);
  check(Math.abs(Math.max(...d.rows.map((r) => r.frame.w)) - plot) <= 0.5, `${what}: the highest net wage fills the plot`);
  check(d.rows.every((r) => Math.abs(r.rent.w - c.rent * scale) <= 0.5 && r.rent.x === r.frame.x && r.rent.fill === rgb(w.colour)), `${what}: the same red block in every row`);
  check(d.rows.every((r, k) => r.name === c.rows[k].name && r.sub === plain(c.rows[k].net_text) && r.left === plain(c.rows[k].left_text) && r.tip === c.rows[k].tip),
    `${what}: name, net wage, what is left and tooltip of the payload`);
  check(d.rows.every((r, k) => r.inBar === (c.rows[k].share_text.length * d.char + 8 <= r.rent.w ? plain(c.rows[k].share_text) : null) && (r.inBar === null || r.inBarFill === rgb(w.ink))),
    `${what}: the share in the block where it fits, in the ink of the payload`);
  check(d.labels === 1 && d.rentLabel === plain(c.rent_text), `${what}: the warm rent named once`);
  check(d.guides.length === 1 && d.guides.every((g) => Math.abs(g.x1 - (d.rows[0].frame.x + c.rent * scale)) <= 0.5 && g.x1 === g.x2), `${what}: one guide at the right edge of the red block`);
};

test("the switch opens the view Miete: two figures, two drawings", async ({ mapPage: page, check, saveScreenshot }) => {
  const r = await payload(page);
  await openRentBurden(page);
  const v = await page.evaluate((view) => ({
    mainHidden: document.querySelector("main").hidden, others: ["view-history", "view-new-construction"].map((id) => document.getElementById(id).hidden),
    shown: !document.querySelector(view).hidden, hash: location.hash, link: APP.viewLink("rent_burden"),
    pressed: [...document.querySelectorAll("#views button")].filter((b) => b.getAttribute("aria-pressed") === "true").map((b) => b.dataset.view),
    figures: [...document.querySelectorAll(view + " figure")].map((f) => ({ id: f.id, title: f.querySelector("h2").textContent, lead: f.querySelector(".lead").textContent.replace(/ /g, " "),
      info: f.querySelector(".lead .info-button")?.dataset.info, sources: [...f.querySelectorAll("p.source")].map((p) => p.textContent) })),
    svgs: [...document.querySelectorAll(view + " svg")].filter((s) => !s.classList.contains("swatch")).map((s) => s.getAttribute("class")),
    labels: [...document.querySelectorAll(view + " svg.wage, " + view + " svg.burden")].map((s) => [s.getAttribute("role"), s.getAttribute("aria-label")]),
    explain: document.querySelector(view + " figure p.explain")?.textContent,
  }), VIEW);
  check(v.mainHidden && v.others.every(Boolean) && v.shown && v.pressed.join() === "rent_burden" && v.hash === "#" + v.link, "the switch opens the view Miete and writes its fragment");
  check(v.svgs.join() === "wage,burden", "two drawings: the wage bars and the bars of tenants: " + v.svgs);
  check(v.explain === r.wage.explain, "the line that explains the wage bars comes from the payload");
  check(v.figures.length === 2 && v.figures[0].id === `${v.link}-${r.wage.link}` && v.figures[1].id === `${v.link}-${r.low_income.link}`, "the figures have the ids of their links");
  for (const [k, p] of [r.wage, r.low_income].entries()) {
    const f = v.figures[k], words = plain(p.lead).split(" ");
    check(f && f.title === plain(p.title) && f.lead.startsWith(words.slice(0, -1).join(" ")) && f.lead.endsWith(words.at(-1) + " ⓘ"), `figure ${k + 1}: heading and lead from the payload`);
    check(f && f.info === ["rent-wage", "rent-low-income"][k], `figure ${k + 1}: the ⓘ closes its lead line`);
    check(f && f.sources.length === 1 && f.sources[0] === p.source, `figure ${k + 1}: one source line from the payload`);
  }
  check(v.labels.length === 2 && v.labels.every(([role, label]) => role === "img" && label), "each drawing is an image with a label");
  check(v.labels[0][1] === r.wage.aria_label && v.labels[1][1] === r.low_income.aria_label,
    "the labels are the aria labels of the payload");
  check(await noOverflow(page), "Miete: no horizontal scrolling");
  check(await drawnRentBurden(page, 760), "Miete: wide window, 760 units");
  await page.setViewportSize({ width: 1400, height: 2300 });
  await saveScreenshot("rent_burden", { element: page.locator(VIEW) });
});

test("wage bars: one frame per person in euros, the same red block in every row", async ({ mapPage: page, check }) => {
  const r = await payload(page), w = r.wage;
  await openRentBurden(page);
  await page.setViewportSize({ width: 1400, height: 1200 });
  check(await drawnRentBurden(page, 760), "wide: 760 units");
  const d = await wageDrawn(page);
  check(!d.hasWidth && d.units === 760, "wide: a drawing 760 units wide that scales");
  check(w.contracts.length === 2 && w.contracts.every((c) => c.rows.every((row) => row.net <= w.max_net)), "the payload: two contracts, no net wage above the full width");
  checkWide(check, d, w, w.contracts[0], "new contract");
  check(d.rows.filter((row) => row.inBar !== null).length === 3, "wide: every block shows its share");
  const shown = await switchShown(page);
  check(shown.length === 2 && shown.every((b, k) => b.contract === w.contracts[k].id && b.text === w.contracts[k].name && b.type === "button")
    && shown.map((b) => b.pressed).join() === "true,false", "the switch: one button per contract, the first pressed");
  await checkRentBurden(page, check, "Miete, wage bars wide");
});

test("wage bars: the switch shows the older contract and keeps it", async ({ mapPage: page, check }) => {
  const r = await payload(page), w = r.wage, [first, second] = w.contracts;
  await openRentBurden(page);
  await page.setViewportSize({ width: 1400, height: 1200 });
  check(await drawnRentBurden(page, 760), "wide: 760 units");
  await page.click(`${VIEW} .wage-switch button[data-contract="${second.id}"]`);
  check((await switchShown(page)).map((b) => b.pressed).join() === "false,true", "a click presses the second button");
  check(await still(page), "the red blocks come to rest");
  let d = await wageDrawn(page);
  checkWide(check, d, w, second, "older contract after the click");
  check(d.rows.every((row) => Math.abs(row.rent.box / row.rent.frameBox - row.rent.w / row.frame.w) < 0.01), "at rest each block shows its full width");
  check((await page.evaluate((view) => document.querySelector(view + " svg.wage").getAttribute("aria-label"), VIEW)) === w.aria_label, "the label of the drawing names both contracts");
  // the chosen contract survives a redraw across the boundary of the wide drawing
  await page.setViewportSize({ width: 420, height: 900 });
  check(await drawnRentBurden(page, 0), "narrow after the switch");
  d = await wageDrawn(page);
  check(d.contract === second.id && d.rows.every((row, k) => row.tip === second.rows[k].tip), "narrow: still the older contract");
  await page.setViewportSize({ width: 1400, height: 1200 });
  check(await drawnRentBurden(page, 760), "wide again");
  check((await wageDrawn(page)).rows.every((row, k) => row.tip === second.rows[k].tip), "wide again: still the older contract");
  // the keyboard: Shift+Tab moves from the second button to the first, Space presses it, the focus shows a black
  // outline of 2 px
  await page.focus(`${VIEW} .wage-switch button[data-contract="${second.id}"]`);
  await page.keyboard.press("Shift+Tab");
  const focused = await page.evaluate(() => ({ contract: document.activeElement.dataset.contract, outline: getComputedStyle(document.activeElement).outlineWidth,
    style: getComputedStyle(document.activeElement).outlineStyle, colour: getComputedStyle(document.activeElement).outlineColor }));
  check(focused.contract === first.id && focused.outline === "2px" && focused.style === "solid" && focused.colour === "rgb(0, 0, 0)", "the focused button has a black outline of 2 px: " + JSON.stringify(focused));
  await page.keyboard.press("Space");
  check((await switchShown(page)).map((b) => b.pressed).join() === "true,false", "Space presses the first button again");
  check(await still(page), "the red blocks come to rest again");
  checkWide(check, await wageDrawn(page), w, first, "new contract after Space");
});

test("wage bars: a switch during a move starts from the width the block shows", async ({ mapPage: page, check }) => {
  const r = await payload(page), [first, second] = r.wage.contracts;
  await openRentBurden(page);
  await page.setViewportSize({ width: 1400, height: 1200 });
  check(await drawnRentBurden(page, 760), "wide: 760 units");
  // the shown width in units of the svg: the box of the block divided by the scale of the drawing
  const jump = await page.evaluate(([view, a, b]) => new Promise((done) => {
    const shown = () => { const svg = document.querySelector(view + " svg.wage"), rent = svg.querySelector("rect.rent");
      return rent.getBoundingClientRect().width * svg.viewBox.baseVal.width / svg.getBoundingClientRect().width; };
    const button = (c) => document.querySelector(`${view} .wage-switch button[data-contract="${c}"]`);
    button(b).click();
    setTimeout(() => { const before = shown(); button(a).click(); requestAnimationFrame(() => done({ before, after: shown() })); }, 150);
  }), [VIEW, first.id, second.id]);
  check(Math.abs(jump.after - jump.before) < 3, `the block goes on from where it stands (${jump.before.toFixed(1)} → ${jump.after.toFixed(1)} units)`);
  check(await still(page), "the block comes to rest");
  checkWide(check, await wageDrawn(page), r.wage, first, "new contract after the quick switch");
});

test("wage bars: the tooltip of every row names its numbers", async ({ mapPage: page, check }) => {
  const r = await payload(page), w = r.wage;
  await openRentBurden(page);
  await page.setViewportSize({ width: 1400, height: 1200 });
  check(await drawnRentBurden(page, 760), "wide: 760 units");
  for (const c of w.contracts) {
    await page.click(`${VIEW} .wage-switch button[data-contract="${c.id}"]`);
    await still(page);
    for (const [k, row] of c.rows.entries()) {
      const shown = await rentTipText(page, page.locator(`${VIEW} svg.wage g.row`).nth(k));
      check(shown === row.tip, `${c.id}, ${row.id}: the tooltip of the payload: ${shown}`);
    }
  }
});

test("the keys: no key of lines, the key of the bars in the order of the segments", async ({ mapPage: page, check }) => {
  const r = await payload(page);
  await openRentBurden(page);
  check(await page.evaluate((view) => document.querySelectorAll(view + " .rents-key, " + view + " svg.rents").length === 0, VIEW), "no line chart and no key of lines");
  // the key of the bars: one entry per class in the order of the segments
  const bars = await page.evaluate((view) => ({ key: [...document.querySelectorAll(view + " .burden-key > span")].map((s) => ({ text: s.textContent.trim(), bg: getComputedStyle(s.querySelector("i")).backgroundColor })),
    segments: [...document.querySelectorAll(view + " svg.burden g.segment")].slice(0, 4).map((g) => g.dataset.segment) }), VIEW);
  const low = r.low_income;
  check(bars.key.map((e) => e.text).join() === low.key.map((e) => e.name).join() && bars.key.every((e, i) => e.bg === rgb(low.key[i].colour)),
    "the key of the bars: the names and colours of the classes of the payload");
  check(bars.segments.join() === low.key.map((e) => e.id).join(), "the segments of a bar follow the order of the key");
});

test("bars: three bars, the segments add up to the full bar, numbers only where the payload has them", async ({ mapPage: page, check }) => {
  const r = await payload(page), low = r.low_income;
  await openRentBurden(page);
  check(low.bars.length === 3 && low.bars.every((b) => b.segments.length === 4 && Math.abs(b.segments.reduce((a, s) => a + s.value, 0) - 100) < 1e-6), "the payload: three bars of four segments adding up to 100");
  const d = await page.evaluate((view) => {
    const svg = document.querySelector(view + " svg.burden"), num = (e, a) => parseFloat(e.getAttribute(a));
    return { labels: [...svg.querySelectorAll("g.label")].map((g) => ({ tip: g.dataset.tip, name: g.querySelector("text.name").textContent, median: g.querySelector("text.median").textContent.replace(/ /g, " ") })),
      segments: [...svg.querySelectorAll("g.segment")].map((g) => { const rect = g.querySelector("rect"), t = g.querySelector("text");
        return { id: g.dataset.segment, tip: g.dataset.tip, fill: getComputedStyle(rect).fill, w: num(rect, "width"), x: num(rect, "x"), y: num(rect, "y"), height: num(rect, "height"),
          text: t && t.textContent.replace(/ /g, " "), ink: t && getComputedStyle(t).fill }; }),
      units: svg.viewBox.baseVal.width, hasWidth: svg.hasAttribute("width"), char: APP.BURDEN_CHAR };
  }, VIEW);
  check(!d.hasWidth && d.units === 760 && d.labels.length === 3, "wide: 760 units, one label per bar");
  low.bars.forEach((bar, k) => {
    check(d.labels[k].name === bar.name && d.labels[k].median === plain(bar.label) && d.labels[k].tip === bar.tip, `bar ${k + 1}: name, median and tooltip of the payload`);
    const row = d.segments.slice(k * 4, k * 4 + 4), x0 = row[0].x;
    // the segments follow each other and add up to the full bar, each as wide as its share in the payload
    check(row.every((s, i) => s.id === bar.segments[i].id && s.fill === rgb(bar.segments[i].colour) && s.tip === bar.segments[i].tip), `bar ${k + 1}: id, colour and tooltip of each segment`);
    check(row.every((s, i) => Math.abs(s.w - bar.segments[i].value / 100 * (760 - x0)) < 1e-6 && (!i || Math.abs(s.x - (row[i - 1].x + row[i - 1].w)) < 1e-6)),
      `bar ${k + 1}: the segments follow each other, each as wide as its share`);
    check(Math.abs(row.reduce((a, s) => a + s.w, 0) - (760 - x0)) <= 1 && Math.abs(row.at(-1).x + row.at(-1).w - 760) <= 1, `bar ${k + 1}: the segments add up to the full bar`);
    check(row.every((s) => s.y === row[0].y && s.height === row[0].height), `bar ${k + 1}: all segments equally high`);
    row.forEach((s, i) => { const p = bar.segments[i];
      check(s.text === (p.text !== null && p.text.length * d.char + 8 <= s.w ? p.text : null), `bar ${k + 1}, ${s.id}: the number only where the payload has one`);
      check(s.text === null || s.ink === rgb(p.text_colour), `bar ${k + 1}, ${s.id}: the number in the colour of the payload`); });
  });
  check(d.segments.length === 12 && d.segments.filter((s) => s.text !== null).length >= 6, "wide: most segments show their number");
  await checkRentBurden(page, check, "Miete, wide");
  // every tooltip: the label and each segment name their numbers
  const sel = (g) => page.locator(`${VIEW} svg.burden ${g}`);
  for (const [k, bar] of low.bars.entries()) {
    check(await rentTipText(page, sel("g.label").nth(k)) === bar.tip, `bar ${k + 1}: the label has its tooltip`);
    for (const [i, s] of bar.segments.entries()) check(await rentTipText(page, sel("g.segment").nth(k * 4 + i)) === s.tip, `bar ${k + 1}, ${s.id}: the segment has its tooltip`);
  }
});

test("the ⓘ of both figures opens the protocol with its five labels and its written sums", async ({ mapPage: page, check }) => {
  const r = await payload(page);
  await openRentBurden(page);
  for (const [key, p] of [["rent-wage", r.wage], ["rent-low-income", r.low_income]]) {
    const button = `${VIEW} .info-button[data-info="${key}"]`;
    const closed = await page.evaluate(([k]) => ({ hidden: document.getElementById("info-" + k).hidden, expanded: document.querySelector(`.info-button[data-info="${k}"]`).getAttribute("aria-expanded") }), [key]);
    await page.click(button);
    const open = await page.evaluate(([k]) => { const info = document.getElementById("info-" + k), b = document.querySelector(`.info-button[data-info="${k}"]`);
      return { hidden: info.hidden, expanded: b.getAttribute("aria-expanded"), labels: [...info.querySelectorAll("dl > dt")].map((d) => d.textContent), text: window.protocolText(info),
        sums: [...info.querySelectorAll(".sum")].map((s) => ({ role: s.getAttribute("role"), label: s.getAttribute("aria-label"), ops: [...s.querySelectorAll(".op")].map((o) => o.textContent),
          numbers: [...s.querySelectorAll(".n")].map((n) => n.textContent), whats: [...s.querySelectorAll(".what")].map((w) => w.textContent), rules: s.querySelectorAll(".rule").length,
          result: s.querySelector(".result")?.textContent })) }; }, [key]);
    const want = await page.evaluate((info) => APP.PROTOCOL.filter(([k]) => info[k]).map(([k, l]) => ({ key: k, label: l, value: info[k] })), p.info);
    // the written sums follow the prose of the Rechnung, each under its label (docs/texts.md, Written sums)
    const examples = p.info.calc_examples, labelOf = (ex) => ex.label || `Rechnung am Beispiel ${ex.area}`;
    const labels = want.flatMap((w) => (w.key === "calc" ? [w.label, ...examples.map(labelOf)] : [w.label]));
    const numberOf = (row) => (row.estimate ? "~" : "") + row.number.toLocaleString("de-DE", { minimumFractionDigits: row.decimals, maximumFractionDigits: row.decimals }) + (row.unit ? " " + row.unit : "");
    check(closed.hidden && closed.expanded === "false", `${key}: the protocol starts closed`);
    check(!open.hidden && open.expanded === "true" && want.length === 5 && open.labels.join() === labels.join(), `${key}: the ⓘ opens a list with the five labels of the protocol and the labels of its sums: ${open.labels}`);
    check(examples.length === [2, 1][key === "rent-wage" ? 0 : 1] && open.sums.length === examples.length, `${key}: one drawn sum per example of the payload (${open.sums.length})`);
    open.sums.forEach((s, i) => { const ex = examples[i];
      check(s.role === "group" && s.label === labelOf(ex) && s.ops.join("|") === ex.rows.map((row) => row.op).join("|") && s.whats.join("|") === ex.rows.map((row) => row.text).join("|"),
        `${key}, sum ${i + 1}: label, operators and texts of the payload`);
      check(s.numbers.map((n) => n.replace(/ /g, " ")).join("|") === ex.rows.map(numberOf).join("|") && s.result === numberOf(ex.rows.at(-1)) && s.rules === ex.rows.filter((row) => row.total).length,
        `${key}, sum ${i + 1}: the numbers of the payload, a line above each total, the last one large (${s.numbers})`); });
    check(want.every((w) => open.text.includes(w.label + ": ")) && want.every((w) => w.value.split(" · ").every((part) => open.text.includes(part))), `${key}: every line of the payload stands in the protocol`);
    await page.click(button);
    check(await page.evaluate(([k]) => document.getElementById("info-" + k).hidden, [key]), `${key}: a second click closes it`);
  }
  check(await page.evaluate((view) => document.querySelectorAll(view + " .info-button").length === 2 && !document.querySelector(view + " .info:not([hidden])"), VIEW), "two ⓘ, both closed again");
});

test("narrow window: the two drawings at their width, texts free of each other", async ({ mapPage: page, check, saveScreenshot }) => {
  const r = await payload(page), w = r.wage;
  await openRentBurden(page);
  for (const width of [420, 360, 320, 300]) {
    await page.setViewportSize({ width, height: 900 });
    for (const c of w.contracts) {
      await page.click(`${VIEW} .wage-switch button[data-contract="${c.id}"]`);
      check(await drawnRentBurden(page, 0) && await still(page), `${width} px, ${c.id}: the drawings at their width in px`);
      check(await noOverflow(page), `${width} px, ${c.id}: no horizontal scrolling`);
      await checkRentBurden(page, check, `Miete, ${width} px, ${c.id}`);
      const d = await wageDrawn(page), scale = d.units / w.max_net;
      check(d.hasWidth && d.guides.length === 0 && d.rentLabel === plain(c.rent_text), `${width} px, ${c.id}: in px, no guide, the warm rent named once`);
      check(d.rows.every((row, k) => row.frame.x === 0 && Math.abs(row.frame.w - c.rows[k].net * scale) <= 0.5 && Math.abs(row.rent.w - c.rent * scale) <= 0.5),
        `${width} px, ${c.id}: frames in euros over the full width, the same red block`);
      check(d.rows.every((row, k) => row.name === c.rows[k].name && row.sub.includes(plain(c.rows[k].net_text)) && row.sub.includes(plain(c.rows[k].left_text)) && row.left === null),
        `${width} px, ${c.id}: the sub line under the name holds the net wage and what is left`);
      check(d.rows.every((row, k) => row.inBar === (c.rows[k].share_text.length * d.char + 8 <= row.rent.w ? plain(c.rows[k].share_text) : null)),
        `${width} px, ${c.id}: the share in the block only where it fits (${d.rows.map((row) => Math.round(row.rent.w))})`);
      // at 300 px the block of the older contract is too narrow for its number: the tooltip carries it
      if (width === 300 && c.id === w.contracts[1].id) check(d.rows.every((row) => row.inBar === null), "300 px, older contract: no number in the narrow blocks");
    }
    const labels = await page.evaluate((view) => document.querySelectorAll(view + " svg.burden g.label text").length, VIEW);
    check(labels === 3, `${width} px: one label above each bar`);
    if (width === 420) await saveScreenshot("rent_burden_narrow", { element: page.locator(VIEW) });
  }
  await page.click(`${VIEW} .wage-switch button[data-contract="${w.contracts[0].id}"]`);
});

test("four view buttons in one line from 300 to 390 px, no horizontal scrolling", async ({ mapPage: page, check }) => {
  for (const width of [300, 320, 360, 390]) {
    await page.setViewportSize({ width, height: 800 });
    for (const view of ["map", "rent_burden"]) {
      await page.click(`#views button[data-view="${view}"]`);
      const vb = await viewButtons(page), what = `${width} px, ${view}`;
      check(vb.count === 4 && vb.views.join() === vb.expected.join() && vb.labels.every((l) => l.trim() !== ""), `${what}: one button per view with its label (${vb.labels})`);
      check(vb.lines.every((n) => n === 1) && Math.max(...vb.heights) - Math.min(...vb.heights) <= 1, `${what}: no view button wraps (heights ${vb.heights})`);
      check(Math.max(...vb.tops) - Math.min(...vb.tops) <= 1 && vb.order && vb.right <= vb.width + 0.5, `${what}: the buttons in one line inside the window (tops ${vb.tops}, right ${vb.right})`);
      // below 320 px (no phone) the buttons may move to a row of their own, so the header grows
      check(width < 320 || vb.all <= vb.fewer + 4, `${what}: the header no higher than with one button less plus 4 px (${vb.all} vs ${vb.fewer})`);
      check(await noOverflow(page) && await page.evaluate(() => [...document.querySelectorAll("#views button")].every((b) => b.scrollWidth <= b.clientWidth + 1)), `${what}: no horizontal scrolling, no clipped button`);
    }
    check(await drawnRentBurden(page, 0), `${width} px: the drawings at their width`);
  }
});

test("the boundary of the wide drawing at 700 px of room, resized while hidden", async ({ mapPage: page, check }) => {
  await openRentBurden(page);
  await page.setViewportSize({ width: 800, height: 900 });
  await settle(page);
  const offset = await page.evaluate(() => 800 - APP.burdenBody.clientWidth);
  for (const [room, units] of [[650, 0], [699, 0], [700, 760]]) {
    await page.setViewportSize({ width: room + offset, height: 900 });
    check(await drawnRentBurden(page, units) && await page.evaluate(() => APP.burdenBody.clientWidth) === room, `${room} px of room: ${units ? "the wide drawing" : "drawn at the width in px"}`);
    await checkRentBurden(page, check, `Miete, ${room} px of room`);
  }
  // resized while the view is hidden: the debounced resize runs while hidden, the next opening fits the width
  await page.click('#views button[data-view="map"]');
  await page.setViewportSize({ width: 420, height: 900 });
  await settle(page);
  await page.click('#views button[data-view="rent_burden"]');
  check(await drawnRentBurden(page, 0), "resized while hidden: the opening fits the width");
  await page.setViewportSize({ width: 1400, height: 900 });
  check(await drawnRentBurden(page, 760), "wide again after the narrow opening");
  await checkRentBurden(page, check, "Miete, wide again");
});
