// The ⓘ protocols (docs/texts.md, ⓘ protocol): list form, the button, the lines in their order, the worked examples.
import { test } from "../fixtures.mjs";
import { clean, numbers } from "../helpers/layers.mjs";

// The protocol of a catalog entry as the page should show it, read from the catalog (APP.meta) and the labels of
// APP.PROTOCOL: [label, value] per line; Quelle and Stand split at " · "; a worked example under its own label.
const expectedProtocol = (page, id) => page.evaluate((i) => {
  const m = APP.meta[i] || APP.data.overlays[i], label = Object.fromEntries(APP.PROTOCOL);
  const lines = APP.PROTOCOL.filter(([k]) => m[k]).map(([k, l]) => ({ key: k, label: l, value: String(m[k]), parts: APP.SPLIT_PARTS.includes(k) ? String(m[k]).split(" · ").length : 1 }));
  const ex = m.calc_example;
  if (ex) {
    const at = lines.findIndex((l) => l.key === "calc"), after = at >= 0 ? at + 1 : lines.findIndex((l) => l.key === "as_of") + 1;
    const last = ex.rows.at(-1);
    lines.splice(after, 0, { key: "example", area: ex.area, labelStart: label.calc, parts: 1,
      result: (last.estimate ? "~" : "") + APP.format(last.number, last.decimals) + (last.unit ? " " + last.unit : ""), lastText: last.text });
  }
  return { lines, label };
}, id);
// a shown label fits an expected line: the same label, or for the worked example the calc label with the area
const fits = (shown, line) => (line.key === "example" ? shown.startsWith(line.labelStart + " ") && shown.includes(line.area) : shown === line.label);

test("ⓘ of OWN_PUBLIC: list, button and protocol", async ({ mapPage: page, check }) => {
  await page.evaluate(() => { APP.setLevel("district"); APP.openTab("city"); APP.setIndicator("OWN_PUBLIC"); });
  const publicInfo = await page.evaluate(() => {
    const button = document.querySelector('.info-button[data-info="OWN_PUBLIC"]'), info = document.getElementById("info-OWN_PUBLIC");
    if (!button || !info) return null;
    const closed = button.getAttribute("aria-expanded");
    button.click();
    const dl = info.querySelector("dl"), dts = [...info.querySelectorAll("dt")];
    if (!dl || dts.length < 2) return { visible: !info.hidden, text: info.textContent, dl: false };
    const parts = dts.map((dt) => dt.nextElementSibling.children.length);
    // every label above its value, every value above the next label
    const boxes = [...dl.children].map((c) => c.getBoundingClientRect());
    const stacked = boxes.every((b, i) => i === 0 || (b.top >= boxes[i - 1].bottom - 1 && Math.abs(b.left - boxes[0].left) < 2));
    return { visible: !info.hidden, text: protocolText(info), dl: Boolean(dl) && dl.parentElement === info,
             labels: dts.map((dt) => dt.textContent), parts, closed, open: button.getAttribute("aria-expanded"),
             controls: button.getAttribute("aria-controls"), label: button.getAttribute("aria-label"), stacked,
             fill: getComputedStyle(button).backgroundColor === getComputedStyle(document.documentElement).getPropertyValue("--accent").trim().replace(
               /^#(..)(..)(..)$/, (_, r, g, b) => `rgb(${parseInt(r, 16)}, ${parseInt(g, 16)}, ${parseInt(b, 16)})`) };
  });
  // docs/texts.md, ⓘ protocol: label above its value, several sources and dates one per line, the button shows the open state
  const want = await expectedProtocol(page, "OWN_PUBLIC");
  check(publicInfo && publicInfo.dl && publicInfo.labels.length === want.lines.length && want.lines.every((l, i) => fits(publicInfo.labels[i], l))
    && JSON.stringify(publicInfo.parts) === JSON.stringify(want.lines.map((l) => l.parts)) && want.lines.some((l) => l.parts > 1),
    "OWN_PUBLIC: ⓘ is a list, sources and dates split: " + JSON.stringify(publicInfo));
  check(publicInfo && publicInfo.closed === "false" && publicInfo.open === "true" && publicInfo.controls === "info-OWN_PUBLIC"
    && clean(publicInfo.label) && publicInfo.fill, "ⓘ button has a name, says whether its protocol is open and is filled: " + JSON.stringify(publicInfo));
  check(await page.evaluate(() => { const ids = [...document.querySelectorAll('[id^="info-"]')].map((e) => e.id); return ids.length > 30 && new Set(ids).size === ids.length; }),
    "ids of the ⓘ protocols are unique");
  check(publicInfo && publicInfo.stacked, "ⓘ: label above its value");
  // docs/texts.md, ⓘ protocol: fixed lines in a fixed order, only facts
  // the lines of the catalog in the order of APP.PROTOCOL, the worked example ends with its last row; the Unsicherheit
  // names the range of the deviation as two numbers
  const lineText = (l) => (l.key === "example" ? null : `${l.label}: ${l.value}`);
  const at = (t) => (publicInfo ? publicInfo.text.indexOf(t) : -1);
  const plain = want.lines.filter((l) => l.key !== "example").map(lineText), example = want.lines.find((l) => l.key === "example");
  // the two numbers around " bis ": the ends of the range
  const ends = (want.lines.find((l) => l.key === "uncertainty")?.value ?? "").match(/(\d+(?:,\d+)?) bis (\d+(?:,\d+)?)/);
  const range = ends ? [numbers(ends[1])[0], numbers(ends[2])[0]] : [];
  check(publicInfo && publicInfo.visible && clean(publicInfo.text) && publicInfo.text.startsWith(plain[0]) && publicInfo.text.endsWith(plain.at(-1))
    && plain.every((t, i) => at(t) >= 0 && (i === 0 || at(t) > at(plain[i - 1]))) && example && at(`${example.lastText} ${want.label.rule}: `) > at(example.area)
    && range.length === 2 && range[0] <= range[1] && !publicInfo.text.includes("21,8"), "OWN_PUBLIC: ⓘ is a protocol: " + JSON.stringify(publicInfo));
});

test("ⓘ of the tab Stadt: lines, Unsicherheit, no Abgleich", async ({ mapPage: page, check }) => {
  await page.evaluate(() => APP.openTab("city"));
  // docs/texts.md, ⓘ protocol: every ownership layer of the tab Stadt ends with its Unsicherheit and the one
  // of the count in the tooltip, no Abgleich (OWN_NONPROFIT has no layer)
  // each ends with the Unsicherheit of the catalog, which names a number; the last sentence (the count of the
  // tooltip) is the same for all five
  const ownProtocols = await page.evaluate(() => ["OWN_PUBLIC", "OWN_COOP", "OWN_COMPANY", "OWN_PERSON", "OWN_STATE"]
    .map((id) => { const info = document.getElementById("info-" + id);
      return { id, text: info ? protocolText(info) : "", labels: info ? [...info.querySelectorAll("dt")].map((d) => d.textContent) : [],
        want: `${Object.fromEntries(APP.PROTOCOL).uncertainty}: ${APP.meta[id].uncertainty}`, uncertainty: APP.meta[id].uncertainty }; }));
  const lastSentence = (t) => t.split(/(?<=\.) /).at(-1);
  const plainLabels = await page.evaluate(() => APP.PROTOCOL.map(([, l]) => l));
  check(ownProtocols.every((o) => o.uncertainty && o.text.endsWith(o.want) && o.text.split(o.want).length === 2 && numbers(o.uncertainty).length > 0
    && o.labels.every((l) => plainLabels.includes(l) || l.startsWith(plainLabels[2] + " ")))
    && new Set(ownProtocols.map((o) => lastSentence(o.uncertainty))).size === 1 && ownProtocols.every((o) => o.uncertainty !== lastSentence(o.uncertainty)),
    "ownership ⓘ: one plain Unsicherheit, no Abgleich: " + JSON.stringify(ownProtocols));
  const protocols = await page.evaluate(() => [...document.querySelectorAll("#tab-city .info")].map(protocolText));
  const label = await page.evaluate(() => Object.fromEntries(APP.PROTOCOL));
  check(protocols.length > 10 && protocols.every((t) => t.startsWith(label.source + ": ") && t.includes(label.as_of + ": ") && !t.includes("undefined")),
    "every ⓘ in the tab Stadt starts with Quelle and has Stand: " + JSON.stringify(protocols.filter((t) => !t.startsWith(label.source + ": ")).slice(0, 2)));
  check(protocols.every((t) => !/[{}]/.test(t)), "no placeholder left in an ⓘ");
  check(protocols.every((t) => !t.includes("Abgleich: ")), "no ⓘ has a line Abgleich");
  // pipeline/use_cases/survey/README.md: the ⓘ of the rent burden names the median for
  // the whole city only and the missing margin
  // its calc and Unsicherheit are those of the catalog; the calc names the city value (the median of the report);
  // the Unsicherheit is not that of the survey shares (LIF_ATTACHMENT) and names three half widths (±) of the income
  // groups at the lower income limit (the title of the first breakdown entry)
  const rent = await page.evaluate(() => { const m = APP.meta.LIF_RENT_BURDEN_RATIO;
    return { text: protocolText(document.getElementById("info-LIF_RENT_BURDEN_RATIO")), calc: m.calc, uncertainty: m.uncertainty,
      city: APP.format(APP.data.city_values.LIF_RENT_BURDEN_RATIO, 0), shares: APP.meta.LIF_ATTACHMENT.uncertainty,
      limit: APP.breakdownFor(m)[0].title.match(/\d+(\.\d{3})*/)[0] }; });
  const rentBurden = rent.text;
  check(rent.calc && rentBurden.includes(`${label.calc}: ${rent.calc}`) && numbers(rent.calc).includes(Number(rent.city))
    && !rentBurden.includes("Die Zahl ist der Median")
    && rent.uncertainty && rentBurden.includes(`${label.uncertainty}: ${rent.uncertainty}`)
    && rent.shares && !rentBurden.includes(rent.shares) && !rentBurden.includes("±4 bis 4,5")
    && (rent.uncertainty.match(/±\d+/g) || []).length === 3 && rent.uncertainty.includes(rent.limit),
    "ⓘ of the rent burden: median, no margin of the shares, the half widths of the income groups: " + rentBurden);
});

test("ⓘ worked examples: OWN_STATE, HOU_VACANT_ALL, OWN_NONPROFIT", async ({ mapPage: page, check, saveScreenshot }) => {
  await page.evaluate(() => { APP.setLevel("district"); APP.openTab("city"); APP.setIndicator("OWN_PUBLIC"); });
  // the worked example of OWN_STATE: a written sum with its label, the tilde, the tooltip count and the large result
  const stateWant = (await expectedProtocol(page, "OWN_STATE")).lines.find((l) => l.key === "example");
  const ruleLabel = (await expectedProtocol(page, "OWN_STATE")).label.rule;
  const sum = await page.evaluate(() => { const info = document.getElementById("info-OWN_STATE"); info.hidden = false;
    const r = { label: info.querySelectorAll("dt")[2]?.textContent, text: info.textContent, result: !!info.querySelector(".result"),
      list: info.querySelector(".sum")?.getAttribute("role") };
    return r; });
  await page.evaluate(() => { APP.openTab("city"); document.getElementById("info-OWN_STATE").scrollIntoView(); });
  await saveScreenshot("info_OWN_STATE_sum");
  await page.evaluate(() => { document.getElementById("info-OWN_STATE").hidden = true; });
  // the label names the area of the example, the result is the last row of the example (with its tilde), the rule follows it
  check(stateWant && fits(sum.label, stateWant) && sum.text.includes(stateWant.result) && stateWant.result.startsWith("~") && !sum.text.includes("Im Tooltip steht")
    && sum.text.includes(stateWant.lastText + ruleLabel) && sum.result && sum.list === "group", "OWN_STATE: ⓘ shows the sum alone, no note: " + JSON.stringify(sum));
  // the worked example of the vacancy: label, large result and the value of the quarter
  const vacant = await page.evaluate(() => { const info = document.getElementById("info-HOU_VACANT_ALL"); info.hidden = false;
    const r = { label: info.querySelectorAll("dt")[2]?.textContent, text: info.textContent, result: !!info.querySelector(".result") };
    info.hidden = true; return r; });
  const vacantWant = (await expectedProtocol(page, "HOU_VACANT_ALL")).lines.find((l) => l.key === "example");
  check(vacantWant && vacantWant.area === "Innenstadt" && fits(vacant.label, vacantWant) && vacant.result && vacant.text.includes(vacantWant.result) && vacantWant.result.startsWith("~"),
    "HOU_VACANT_ALL: ⓘ shows the sum for Innenstadt: " + JSON.stringify(vacant));
  // the profile row without its own layer carries the sum too
  const nonprofit = await page.evaluate(() => { APP.setLevel("quarter"); APP.showProfile("Gutleutviertel", false);
    const info = document.getElementById("info-profile-OWN_NONPROFIT"); return info ? { sum: !!info.querySelector(".sum"), text: info.textContent } : null; });
  check(nonprofit && nonprofit.sum, "OWN_NONPROFIT in the profile: sum: " + JSON.stringify(nonprofit));
});
