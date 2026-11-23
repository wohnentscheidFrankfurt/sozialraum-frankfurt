// The English map (output/sozialraum-frankfurt.en.html, MAP_HTML_EN): it loads without console errors (the guard of
// fixtures.mjs), says en-GB, opens every view, resolves every chart link and writes the candidates CSV in English.
// The German map has the full suite; this is the smaller one for the English file, in english-chrome and
// english-webkit-390.
import { test, expect } from "../fixtures.mjs";
import { paths } from "../helpers/common.mjs";
import { LINKS, VIEW } from "../helpers/views.mjs";

test.use({ mapHtml: paths.mapHtmlEn });

test("the map says en-GB and offers the German map", async ({ mapPage: page, check }) => {
  const s = await page.evaluate(() => { const a = document.getElementById("lang-switch");
    return { lang: document.documentElement.lang, data: APP.data.lang, switch: a && { text: a.textContent, lang: a.lang } }; });
  check(s.lang === "en-GB" && s.data === "en", "html lang is en-GB: " + JSON.stringify(s));
  check(JSON.stringify(s.switch) === JSON.stringify({ text: "Deutsch", lang: "de" }), "the switch names the German map: " + JSON.stringify(s.switch));
  expect(await page.locator("link[rel=alternate][hreflang]").count()).toBe(0); // ENGLISH_ONLINE is off in the normal build
});

for (const link of LINKS) {
  test.describe(`#${link}`, () => {
    test.use({ fragment: "#" + link });
    test(`#${link} opens its view and its chart`, async ({ mapPage: page, check }) => {
      const [view, chart] = link.split("/");
      const s = await page.evaluate(() => ({
        view: [...document.querySelectorAll("#views button")].filter((b) => b.getAttribute("aria-pressed") === "true").map((b) => b.dataset.view).join(),
        hash: location.hash }));
      check(s.view === VIEW[view] && s.hash === "#" + link, `#${link} opens its view: ${JSON.stringify(s)}`);
      if (chart) {
        const shown = await page.evaluate((id) => { const f = document.getElementById(id); return !!f && f.offsetParent !== null && f.getBoundingClientRect().height > 50; }, `${view}-${chart}`);
        check(shown, `#${link} finds its figure`);
      }
    });
  });
}

test("the views open from their buttons", async ({ mapPage: page, check }) => {
  for (const view of Object.values(VIEW)) {
    await page.click(`#views button[data-view="${view}"]`);
    const open = await page.evaluate((v) => document.querySelector(`#views button[data-view="${v}"]`).getAttribute("aria-pressed") === "true", view);
    check(open, `view ${view} opens`);
  }
});

test("the candidates CSV has English headers and file names", async ({ mapPage: page, check }) => {
  const files = await page.evaluate(() => { APP.openTab("candidates");
    return APP.data.templates.map((t) => { APP.setTemplate(t.id); return { id: t.id, name: APP.downloadName(t.id), head: APP.csvText().replace(/^﻿/, "").split("\r\n")[0] }; }); });
  const want = { social_preservation: "candidates_social_preservation.csv", coop: "candidates_cooperatives.csv", public_company: "candidates_public_companies.csv" };
  for (const f of files) {
    check(want[f.id] === f.name, `${f.id}: file name ${f.name}`);
    const cols = f.head.split(";");
    check(cols.at(-2) === "met" && cols.at(-1) === "of" && cols.some((c) => c === "District"), `${f.id}: English headers: ${f.head}`);
    check(!/\b(Stadtteil|Bezirk|erfüllt|von|Nr\.)\b/.test(f.head), `${f.id}: no German word in the header`);
  }
  // the button saves the file under that name
  await page.evaluate(() => { APP.openTab("candidates"); APP.setTemplate("coop"); });
  const [download] = await Promise.all([page.waitForEvent("download"), page.click("#csv")]);
  check(download.suggestedFilename() === "candidates_cooperatives.csv", "the button saves " + download.suggestedFilename());
});
