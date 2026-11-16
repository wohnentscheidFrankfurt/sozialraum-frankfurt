// Survey layers on districts: printed classes of the report figures, the income breakdown of the rent burden, the
// survey area in the profile (pipeline/use_cases/survey/README.md).
import { test } from "../fixtures.mjs";
import { numbers } from "../helpers/layers.mjs";

// the numbers of each row: the printed classes of the report figure
const classes = (rows) => JSON.stringify(rows.map(numbers));
// the value line of tooltip i of surveyLayer, if it holds the title, the printed class and the survey area of the
// district; else null
const valueLine = (r, i) => { const line = r.tips[i].split("<br>")[1] ?? "", w = r.want[i];
  return line.startsWith(`${w.title}: ${w.value} `) && line.endsWith(" " + w.area) ? line : null; };

// legend rows, fill step per survey area and three tooltips of a survey layer
const surveyLayer = (page, id) => page.evaluate((k) => {
  APP.openTab("city"); APP.setIndicator(k);
  const ramp = APP.rampFor(APP.meta[k]);
  const fill = {};
  APP.layers.district.eachLayer((l) => { fill[l.feature.properties.id] = ramp.indexOf(l.options.fillColor); });
  // fill steps per survey area; one area, one step
  const steps = {};
  for (const p of APP.properties("district")) (steps[p.survey_area] ??= new Set()).add(fill[p.id]);
  const tip = (d) => APP.tooltipHead(APP.properties("district").find((p) => p.id === d));
  // the value line of a tooltip, and what it should hold: title, the class and the survey area of the district
  const want = (d) => { const p = APP.properties("district").find((x) => x.id === d);
    return { title: APP.meta[k].title, value: APP.withUnit(k, p[k], p), area: p.survey_area }; };
  // the city line of the legend: the text of the body that follows no swatch
  const cityLines = [...APP.legendDiv.querySelector(".legend-body").childNodes].filter((n) => n.nodeType === Node.TEXT_NODE && n.previousSibling?.tagName !== "I")
    .map((n) => n.textContent.trim()).filter(Boolean);
  return { rows: [...APP.legendDiv.querySelectorAll("i")].map((i) => i.nextSibling.textContent.trim()), cityLines,
    city: APP.valueText(k, APP.data.city_values[k]), want: ["10", "120", "300"].map(want),
    legend: APP.legendDiv.textContent, steps: Object.fromEntries(Object.entries(steps).map(([a, s]) => [a, [...s]])),
    tips: ["10", "120", "300"].map(tip) };
}, id);

test("levels and the rent burden of Abb. 4.5", async ({ mapPage: page, check }) => {
  check(await page.evaluate(() => [...document.querySelectorAll('input[name="level"]')].map((r) => r.value).join()) === "district,quarter",
    "level choice: districts and quarters only");
  check(await page.evaluate(() => !("survey_areas" in APP.data)), "no survey areas in the payload");
  await page.evaluate(() => { APP.openTab("city"); APP.setLevel("quarter"); APP.setIndicator("LIF_RENT_BURDEN_RATIO"); });
  check(await page.evaluate(() => APP.state.level) === "district", "LIF_RENT_BURDEN_RATIO on quarters switches to districts");
  const ratio = await surveyLayer(page, "LIF_RENT_BURDEN_RATIO");
  // the classes as printed: 26–28, 29, 30, 31–33 %; the city value 29 %
  check(classes(ratio.rows) === "[[26,28],[29],[30],[31,33]]" && ratio.rows.every((r) => r.endsWith(" %"))
    && ratio.cityLines.length === 1 && ratio.cityLines[0].endsWith(": " + ratio.city) && JSON.stringify(numbers(ratio.city)) === "[29]",
    "legend of Abb. 4.5 as printed: " + JSON.stringify(ratio.rows));
  check(Object.values(ratio.steps).every((s) => s.length === 1 && s[0] >= 1), "all districts of a survey area share one colour: " + JSON.stringify(ratio.steps));
  // classes use ramp steps 1 to 4: the lightest step stays apart from the white "k. A."
  check(ratio.steps["Innenstadt III"][0] === 1 && ratio.steps["Innenstadt I"][0] === 2 && ratio.steps["Ost"][0] === 3 && ratio.steps["Nord-Ost"][0] === 4,
    "colours of Abb. 4.5: " + JSON.stringify(ratio.steps));
  check(numbers(valueLine(ratio, 0)).join() === "29" && numbers(valueLine(ratio, 1)).join() === "26,28", "tooltips show the printed class: " + JSON.stringify(ratio.tips));
});

test("income breakdown of the rent burden: tooltip, profile bars and ⓘ", async ({ mapPage: page, check }) => {
  await page.evaluate(() => { APP.openTab("city"); APP.setLevel("district"); APP.setIndicator("LIF_RENT_BURDEN_RATIO"); });
  // income breakdown of the rent burden: lines under the value in the tooltip, no layer, row or ⓘ of their own
  const income = await page.evaluate(() => {
    const ids = APP.data.catalog.filter((m) => m.breakdown_of === "LIF_RENT_BURDEN_RATIO").map((m) => m.id);
    APP.openTab("city"); APP.setIndicator("LIF_RENT_BURDEN_RATIO");
    const p = APP.properties("district").find((x) => x.id === "10"), tip = APP.tooltipText(p);
    const saved = p[ids[0]]; p[ids[0]] = null; const missing = APP.tooltipText(p); p[ids[0]] = saved;
    APP.setIndicator("LIF_ATTACHMENT"); const other = APP.tooltipText(p);
    APP.setIndicator("LIF_RENT_BURDEN_RATIO");
    const titles = ids.map((k) => APP.meta[k].title), lead = APP.meta.LIF_RENT_BURDEN_RATIO.breakdown_lead;
    const screen = [...document.querySelectorAll("#tab-city .layer-row label"), APP.legendDiv, document.getElementById("criterion-new")].map((e) => e.textContent).join(" ");
    APP.showProfile("10"); const profile = document.getElementById("tab-area").textContent;
    APP.openTab("city"); APP.setIndicator("LIF_RENT_BURDEN_RATIO");
    const info = document.getElementById("info-LIF_RENT_BURDEN_RATIO"); info.hidden = false;
    const dts = [...info.querySelectorAll("dt")].map((d) => d.textContent);
    const ex = APP.meta.LIF_RENT_BURDEN_RATIO.calc_example;
    const sumRows = [...info.querySelectorAll(".sum .op, .sum .n")].map((e) => e.textContent.replace(/ /g, " "));
    const wanted = ex.rows.flatMap((r) => [r.op, APP.format(r.number, r.decimals) + (r.unit ? " " + r.unit : "")]);
    const parent = APP.meta.LIF_RENT_BURDEN_RATIO;
    const hiddenTexts = ids.flatMap((k) => ["calc", "source", "as_of"].filter((f) => !String(parent[f]).includes(APP.meta[k][f])).map((f) => APP.meta[k][f]).filter(Boolean));
    document.querySelectorAll(".info").forEach((e) => { e.hidden = false; });
    APP.showProfile("10"); document.querySelectorAll(".info").forEach((e) => { e.hidden = false; });
    const everything = document.body.innerText + " " + [...document.querySelectorAll(".info")].map((e) => e.textContent).join(" ");
    document.querySelectorAll(".info").forEach((e) => { e.hidden = true; });
    info.hidden = true;
    const label = Object.fromEntries(APP.PROTOCOL);
    return { tip, missing, other, titles, lead, screen, profile, dts, sumRows, wanted, text: info.textContent, result: info.querySelector(".sum .result")?.textContent,
      source: parent.source, calcLabel: label.calc, exampleLabel: APP.calcExampleHtml(parent.calc_example).label, area: ex.area,
      hiddenShown: hiddenTexts.filter((t) => everything.includes(t)), ownership: (() => { const o = document.getElementById("info-OWN_STATE"); return [...o.querySelectorAll("dt")].map((d) => d.textContent); })() };
  });
  // the lead of the catalog, then one line per entry: its title and its value with a tilde
  const tipLines = income.tip.split("<br>");
  const leadAt = tipLines.indexOf(income.lead + ":");
  check(income.lead && leadAt > 0 && income.titles.every((t, i) => (tipLines[leadAt + 1 + i] ?? "").startsWith(t + ": ~")
    && /: ~\d+ %$/.test(tipLines[leadAt + 1 + i])),
    "tooltip of the rent burden lists the income breakdown: " + income.tip);
  check(income.missing.includes(`${income.titles[0]}: k. A.`), "a missing breakdown value reads k. A.: " + income.missing);
  check(!income.other.includes(income.lead), "no breakdown in other tooltips");
  check(income.titles.length === 3 && income.titles.every((t) => !income.screen.includes(t)), "breakdown values have no layer row, criterion or legend row: " + income.titles);
  // income bars in the profile under the row of the rent burden: common scale, ramp steps 5/4/3, no layer, no ⓘ
  const bars = await page.evaluate(() => {
    const parent = APP.meta.LIF_RENT_BURDEN_RATIO, entries = APP.breakdownFor(parent);
    const district = APP.properties("district").find((p) => p.survey_area === "West" && entries.every((c) => p[c.id] != null));
    APP.showProfile(district.id);
    const rgb = (c) => { const e = document.createElement("i"); e.style.color = c; document.body.append(e); const v = getComputedStyle(e).color; e.remove(); return v; };
    const read = () => {
      const box = document.querySelector("#tab-area .breakdown");
      return box && { text: box.textContent.replace(/\s+/g, " "), lead: box.querySelector(".note")?.textContent,
        dataLayer: box.querySelectorAll("[data-layer]").length, info: box.querySelectorAll(".info-button, .info").length,
        rows: [...box.querySelectorAll(".row")].map((r) => ({ text: r.textContent.replace(/\s+/g, " "), width: parseFloat(r.querySelector(".bar span").style.width),
          city: parseFloat(r.querySelector(".bar .city")?.style.left), colour: getComputedStyle(r.querySelector(".bar span")).backgroundColor })) };
    };
    const out = read();
    const all = [...APP.properties("district").flatMap((p) => entries.map((c) => p[c.id])), ...entries.map((c) => APP.data.city_values[c.id])].filter((v) => v != null);
    const scale = Math.floor(Math.max(...all) / 10) * 10 + 10;
    const saved = district[entries[0].id]; district[entries[0].id] = null; APP.renderProfile();
    const missing = read(); district[entries[0].id] = saved; APP.renderProfile();
    const before = document.querySelector("#tab-area .breakdown")?.previousElementSibling.textContent ?? "";
    const prev = document.querySelector("#tab-area .breakdown")?.previousElementSibling;
    return { out, missing, scale, ramp: parent.colors.map(rgb), values: entries.map((c) => district[c.id]), cities: entries.map((c) => APP.data.city_values[c.id]), before,
      beforeLayer: prev?.dataset.layer, lead: parent.breakdown_lead, titles: entries.map((c) => c.title),
      shown: entries.map((c) => APP.valueText(c.id, district[c.id], district)), city: entries.map((c) => APP.valueText(c.id, APP.data.city_values[c.id])) };
  });
  check(bars.out && bars.lead && bars.out.lead === bars.lead + ":" && bars.out.rows.length === 3 && bars.beforeLayer === "LIF_RENT_BURDEN_RATIO", "profile: income bars after the row of the rent burden: " + JSON.stringify(bars.out));
  // title, the value and then the city value, both with a tilde
  check(bars.out && bars.out.rows.every((r, i) => r.text.includes(bars.titles[i]) && bars.shown[i].startsWith("~") && bars.city[i].startsWith("~")
    && r.text.indexOf(bars.shown[i], bars.titles[i].length) > 0 && r.text.endsWith(" " + bars.city[i])), "profile: income rows have title, ~value and Stadt ~: " + JSON.stringify(bars.out?.rows));
  check(bars.out && bars.out.rows.every((r, i) => Math.abs(r.width - (bars.values[i] / bars.scale) * 100) < 0.01 && Math.abs(r.city - (bars.cities[i] / bars.scale) * 100) < 0.01),
    "profile: income bars on the common scale 0 to " + bars.scale + ": " + JSON.stringify(bars.out?.rows));
  check(bars.out && bars.out.rows.map((r) => r.colour).join("|") === [bars.ramp[4], bars.ramp[3], bars.ramp[2]].join("|"), "profile: income bars use ramp steps 5, 4, 3");
  check(bars.out && bars.out.dataLayer === 0 && bars.out.info === 0, "profile: income rows are no buttons and carry no ⓘ");
  check(bars.missing && bars.missing.rows[0].text.includes("k. A.") && bars.missing.rows[0].width === 0, "profile: a missing income value reads k. A. with an empty bar: " + JSON.stringify(bars.missing?.rows[0]));
  // every source of the catalog, the microdata among them
  check(income.source.split(" · ").length > 1 && income.source.split(" · ").every((part) => income.text.includes(part)) && !income.text.includes("{"), "ⓘ of the rent burden names the microdata");
  check(JSON.stringify(income.dts.filter((t) => t.startsWith(income.calcLabel))) === JSON.stringify([income.calcLabel, income.exampleLabel]) && income.exampleLabel.includes(income.area)
    && income.sumRows.join("|") === income.wanted.join("|") && income.result === income.wanted.at(-1), "ⓘ of the rent burden: prose, then the sum: " + JSON.stringify(income.dts) + JSON.stringify(income.sumRows));
  check(income.hiddenShown.length === 0, "texts of the hidden breakdown entries never appear: " + JSON.stringify(income.hiddenShown));
  check(income.ownership.filter((t) => t.startsWith(income.calcLabel)).length === 1, "ⓘ of an ownership layer shows only the sum: " + JSON.stringify(income.ownership));
});

test("attachment of Abb. 4.11, the survey area in the profile and in the candidates", async ({ mapPage: page, check }) => {
  await page.evaluate(() => { APP.openTab("city"); APP.setLevel("district"); APP.setIndicator("LIF_RENT_BURDEN_RATIO"); });
  const attachment = await surveyLayer(page, "LIF_ATTACHMENT");
  // the classes as printed: 51–61, 62–63, 64–70, 71–82 %; the city value 62 %
  check(classes(attachment.rows.slice(0, 4)) === "[[51,61],[62,63],[64,70],[71,82]]"
    && attachment.cityLines.length === 1 && attachment.cityLines[0].endsWith(": " + attachment.city) && JSON.stringify(numbers(attachment.city)) === "[62]",
    "legend of Abb. 4.11 as printed: " + JSON.stringify(attachment.rows));
  check(attachment.want[2].area === "Süd" && numbers(valueLine(attachment, 2)).join() === "64,70", "Süd shows the class of Abb. 4.11: " + attachment.tips[2]);
  const ownership = await page.evaluate(() => { APP.setIndicator("OWN_PUBLIC"); const p = APP.properties("district").find((x) => x.id === "10");
    return { tip: APP.tooltipHead(p), area: p.survey_area }; });
  check(ownership.area && !ownership.tip.includes(ownership.area), "other layers do not name the survey area: " + ownership.tip);
  // the rule of the catalog is the line Regel; no line Ebene (no label outside APP.PROTOCOL)
  const info = await page.evaluate(() => { const d = document.createElement("div"); d.innerHTML = APP.infoBlock(APP.meta.LIF_ATTACHMENT, "check");
    const label = Object.fromEntries(APP.PROTOCOL);
    return { text: protocolText(d), rule: `${label.rule}: ${APP.meta.LIF_ATTACHMENT.rule}`, labels: [...d.querySelectorAll("dt")].map((e) => e.textContent),
      known: APP.PROTOCOL.map(([, l]) => l) }; });
  check(!info.text.includes("Ebene:") && info.labels.every((l) => info.known.includes(l)) && info.text.includes(info.rule), "ⓘ names the survey area rule, no level line");
  await page.evaluate(() => APP.setLevel("quarter"));
  check(await page.evaluate(() => APP.state.indicator) === "OWN_PUBLIC", "quarters fall back to OWN_PUBLIC");
  await page.evaluate(() => APP.setLevel("district"));
  // two notes name its survey area (one per topic), and the rows show the classes of that area
  const districtSurvey = await page.evaluate(() => { APP.showProfile("10"); const p = APP.properties("district").find((x) => x.id === "10");
    const t = document.getElementById("tab-area");
    return { text: t.textContent, area: p.survey_area, notes: [...t.querySelectorAll("p.note")].filter((n) => n.textContent.includes(p.survey_area)).length,
      rows: ["LIF_RENT_BURDEN_RATIO", "LIF_ATTACHMENT"].map((k) => [t.querySelector(`.row[data-layer="${k}"] strong`)?.textContent, APP.valueText(k, p[k], p)]) }; });
  check(districtSurvey.area === "Innenstadt I" && districtSurvey.notes === 2 && districtSurvey.rows.every(([shown, want]) => want && shown === want)
    && classes(districtSurvey.rows.map(([shown]) => shown)) === "[[29],[51,61]]", "district profile shows the classes of its survey area: " + JSON.stringify(districtSurvey.rows));
  check(!/Mieter hoch|Einzeldatensatz|Neumieter/.test(districtSurvey.text), "no counted survey values in the profile");
  await page.evaluate(() => { APP.openTab("candidates"); APP.setTemplate("social_preservation"); });
  check(await page.evaluate(() => APP.state.level) === "district", "candidates still force districts");
  check(await page.evaluate(() => ![...document.querySelectorAll("#criterion-new option")].some((o) => o.value.startsWith("LIF_"))),
    "survey layers are no criteria");
  check(await page.evaluate(() => [...document.querySelectorAll("#criterion-new option")].some((o) => o.value === "HOU_RENTERS"
    && o.textContent === `${APP.meta.HOU_RENTERS.group}: ${APP.meta.HOU_RENTERS.title}`)),
    "a criterion option names its topic heading");
});
