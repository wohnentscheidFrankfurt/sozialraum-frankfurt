// Texts of the candidates tab (docs/texts.md, Map texts): 3.1 the template sentence, 3.2 the upper end, 3.5 the own
// query, 3.6 what a bar counts (stands once, in the tab note).
import { test } from "../fixtures.mjs";

test("texts 3.1, 3.2, 3.5, 3.6 of the candidates tab", async ({ mapPage: page, check }) => {
  const cand = await page.evaluate(() => {
    APP.openTab("candidates");
    const out = { lead: {}, upper: {}, custom: {}, note: {}, wantUpper: {}, wantNote: {}, high: {} };
    const vis = (e) => !!e && !e.hidden && e.offsetParent !== null;
    for (const t of APP.data.templates) {
      APP.setTemplate(t.id);
      const lead = document.getElementById("template-lead");
      out.lead[t.id] = [lead.textContent === t.lead && vis(lead), vis(document.getElementById("custom-note"))];
      out.upper[t.id] = [...document.querySelectorAll("#criteria .criterion")].map((c) => c.querySelector(".criterion-note")?.textContent ?? null);
      out.note[t.id] = document.getElementById("candidates-note").textContent;
      // the note of a criterion "<" from the payload; the criteria with a note are the upper ends of an estimate (_HIGH)
      out.wantUpper[t.id] = t.criteria.map((k) => (k.note && k.op === "<" ? k.note : null));
      out.high[t.id] = t.criteria.map((k) => k.indicator.endsWith("_HIGH"));
      // the tab note names the areas of the level of the template (APP.candidatesNote, APP.LEVEL_NAMES)
      out.wantNote[t.id] = { text: APP.candidatesNote(APP.LEVEL_NAMES[APP.candidateLevel()]), level: APP.LEVEL_NAMES[APP.candidateLevel()] };
    }
    APP.setTemplate("custom");
    const lead = document.getElementById("template-lead"), note = document.getElementById("custom-note");
    out.custom = { leadHidden: !vis(lead), leadText: lead.textContent, visible: vis(note), text: note.textContent,
      after: document.getElementById("new-criterion").nextElementSibling === note, want: APP.data.custom_note, districts: APP.LEVEL_NAMES.district };
    APP.setTemplate("social_preservation");
    const before = document.getElementById("candidates-note").textContent;
    const slider = document.querySelector("#criteria input[type=range]");
    slider.value = slider.max; slider.dispatchEvent(new Event("input", { bubbles: true }));
    out.afterSlider = document.getElementById("candidates-note").textContent === before;
    APP.openTab("city");
    return out;
  });
  check(Object.values(cand.lead).every(([ok, customVisible]) => ok && !customVisible)
    && cand.custom.leadHidden && cand.custom.leadText === "", "10 3.1: each template has its sentence under the select, none for the own query: " + JSON.stringify(cand.lead));
  const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);
  check(Object.keys(cand.upper).every((t) => same(cand.upper[t], cand.wantUpper[t]) && cand.wantUpper[t].every((n, i) => Boolean(n) === cand.high[t][i]))
    && cand.upper.coop.filter(Boolean).length === 1 && cand.upper.public_company.filter(Boolean).length === 1
    && cand.upper.social_preservation.every((t) => t === null), "10 3.2: only the estimate criteria explain the upper end: " + JSON.stringify(cand.upper));
  // the note of the payload, which names the level of the own query
  check(cand.custom.visible && cand.custom.want && cand.custom.text === cand.custom.want && cand.custom.after && cand.custom.text.includes(cand.custom.districts),
    "10 3.5: the own query names what is missing: " + JSON.stringify(cand.custom));
  // the note of each template is the note of its level; districts and Stadtteile give two different notes
  check(Object.keys(cand.note).every((t) => cand.note[t] === cand.wantNote[t].text && cand.note[t].includes(cand.wantNote[t].level))
    && cand.wantNote.social_preservation.level !== cand.wantNote.coop.level && cand.note.social_preservation !== cand.note.coop
    && cand.wantNote.coop.level === cand.wantNote.public_company.level && cand.afterSlider,
    "10 3.6: the tab note says what a bar counts, on both levels: " + JSON.stringify(cand.note));
  // the label names the areas of the level (Stadtteile for public_company)
  check(await page.evaluate(() => { APP.openTab("candidates"); APP.setTemplate("public_company");
    const svgs = [...document.querySelectorAll("#criteria svg")], words = APP.LEVEL_NAMES[APP.candidateLevel()];
    const ok = svgs.length > 0 && APP.candidateLevel() === "quarter" && svgs.every((s) => (s.getAttribute("aria-label") || "").endsWith(" " + words) && s.getAttribute("aria-label").length > words.length + 1);
    APP.openTab("city"); return ok; }),
    "10 3.6: histogram aria-label unchanged");
});
