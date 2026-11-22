// The language switch (docs/design.md, Language switch): it opens the other file in the same state. The German map is
// built with the English map online into paths.onlineDir (tools/build_online_maps.py); output/ stays as the normal build.
import { spawnSync } from "node:child_process";
import { join } from "node:path";
import { pathToFileURL } from "node:url";
import { test, expect } from "../fixtures.mjs";
import { paths, settle } from "../helpers/common.mjs";

const FILES = { de: "sozialraum-frankfurt.html", en: "sozialraum-frankfurt.en.html" };
const url = (lang, fragment = "") => pathToFileURL(join(paths.onlineDir, FILES[lang])).href + fragment;

test.describe.configure({ mode: "serial" }); // one worker builds the maps once
test.beforeAll(() => {
  const built = spawnSync(join(paths.root, ".venv/bin/python"), ["-I", "tests/browser/tools/build_online_maps.py", paths.onlineDir],
    { cwd: paths.root, encoding: "utf-8" });
  if (built.status !== 0) throw new Error("building the online maps failed:\n" + built.stdout + built.stderr);
});

const open = async (page, lang, fragment) => {
  await page.goto(url(lang, fragment));
  await page.waitForFunction(() => window.APP && window.APP.ready);
  await page.evaluate(() => document.fonts.ready);
  await settle(page);
};
const stateOf = (page) => page.evaluate(() => ({ lang: document.documentElement.lang, hash: location.hash, link: APP.mapLink() }));
const label = (page) => page.evaluate(() => { const a = document.getElementById("lang-switch");
  return { text: a.textContent, lang: a.lang, header: a.parentElement.id }; });

test("the switch keeps a chart link in both directions", async ({ page, check }) => {
  await open(page, "de", "#trend/grosse-haeuser");
  check(JSON.stringify(await label(page)) === JSON.stringify({ text: "English", lang: "en", header: "header" }), "German map: English switch in the header");
  await page.click("#lang-switch");
  await page.waitForURL(/\.en\.html#trend\/grosse-haeuser$/);
  await page.waitForFunction(() => window.APP && window.APP.ready);
  const en = await stateOf(page);
  check(en.lang === "en-GB" && en.hash === "#trend/grosse-haeuser", "English map keeps the chart: " + JSON.stringify(en));
  check(JSON.stringify(await label(page)) === JSON.stringify({ text: "Deutsch", lang: "de", header: "header" }), "English map: Deutsch switch");
  await page.click("#lang-switch");
  await page.waitForURL(/sozialraum-frankfurt\.html#trend\/grosse-haeuser$/);
  check((await stateOf(page)).lang === "de", "back on the German map");
});

test("the switch keeps a map link in both directions", async ({ page, check }) => {
  const fragment = "#karte/zoom=14.5&center=50.11500,8.68000&level=district&area=1&layer=SOC_INDEX&overlays=social_preservation";
  await open(page, "de", fragment);
  const de = await stateOf(page);
  check(de.link.includes("level=district") && de.link.includes("layer=SOC_INDEX") && de.link.includes("zoom=14.5"),
    "the German map shows the linked state: " + de.link);
  await page.click("#lang-switch");
  await page.waitForURL(/\.en\.html#karte/);
  await page.waitForFunction(() => window.APP && window.APP.ready);
  await settle(page);
  const en = await stateOf(page);
  check(en.link === de.link && en.hash === de.hash, `the English map shows the same state: ${en.link} vs ${de.link}`);
  // the link follows the fragment while the reader works: a click on a view writes the fragment, the switch carries it
  await page.click('#views button[data-view="rent_burden"]');
  const href = await page.getAttribute("#lang-switch", "href");
  check(href === "sozialraum-frankfurt.html#miete", "the switch follows the fragment: " + href);
  await page.click("#lang-switch");
  await page.waitForURL(/sozialraum-frankfurt\.html#miete$/);
  await page.waitForFunction(() => window.APP && window.APP.ready);
  check((await stateOf(page)).lang === "de", "back on the German map at #miete");
});

test("the switch is black text on white at the right end of the header", async ({ page, check }) => {
  await open(page, "de", "");
  const box = await page.evaluate(() => { const a = document.getElementById("lang-switch").getBoundingClientRect(),
    h = document.getElementById("header").getBoundingClientRect(), c = getComputedStyle(document.getElementById("lang-switch"));
    return { right: h.right - a.right, color: c.color, bg: c.backgroundColor }; });
  check(box.right < 24 && box.color === "rgb(0, 0, 0)" && box.bg === "rgba(0, 0, 0, 0)", "right end, black, no fill: " + JSON.stringify(box));
  expect(await page.locator("link[rel=alternate][hreflang]").count()).toBe(2);
});
