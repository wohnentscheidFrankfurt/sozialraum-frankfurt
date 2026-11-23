// The language switch on the phone (docs/design.md, Language switch): own right-aligned row under the views, a touch
// target of 32 px, the views stay in one row, the header stays compact. Against the German map built with the English
// map online. Runs in webkit-iphone, webkit-iphone-se and chrome-390.
import { test } from "../fixtures.mjs";
import { buildOnlineMaps, rect, settle } from "../helpers/common.mjs";

let url;
test.describe.configure({ mode: "serial" });
test.beforeAll(({}, testInfo) => { url = buildOnlineMaps(testInfo.project.name); });

for (const lang of ["de", "en"]) {
  test(`switch in the header (${lang})`, async ({ page, check }) => {
    await page.goto(url(lang));
    await page.waitForFunction(() => window.APP && window.APP.ready);
    await page.evaluate(() => document.fonts.ready);
    await settle(page);
    const m = await page.evaluate(() => {
      const r = (el) => el.getBoundingClientRect(), a = r(document.getElementById("lang-switch")), h = r(document.getElementById("header"));
      const views = [...document.querySelectorAll("#views button")].map(r);
      return { link: { top: a.top, bottom: a.bottom, right: a.right, height: a.height }, header: { height: h.height, right: h.right },
        viewsBottom: Math.max(...views.map((v) => v.bottom)), viewTops: views.map((v) => Math.round(v.top)),
        width: window.innerWidth, overflow: document.documentElement.scrollWidth > window.innerWidth };
    });
    check(m.viewTops.every((t) => t === m.viewTops[0]), "the views stay in one row: " + m.viewTops);
    check(m.link.top >= m.viewsBottom - 1, `the switch lies below the views: ${m.link.top} vs ${m.viewsBottom}`);
    check(m.header.right - m.link.right <= 16, `the switch is right aligned: ${m.header.right - m.link.right} px from the edge`);
    check(m.link.height >= 32, `the switch is at least 32 px high: ${m.link.height}`);
    check(m.header.height <= 90, `the header with the switch row: ${m.header.height} px`);
    check(!m.overflow, "no horizontal scrolling");
  });
}

// docs/design.md, Language switch: under 700 px the title and the four views fill the first row, the switch takes a
// row of its own. The English views are wider („New housing“), so check the narrow widths where they could wrap.
for (const lang of ["de", "en"]) {
  test(`title and views share the first row from 320 to 429 px (${lang})`, async ({ page, check }) => {
    await page.goto(url(lang));
    await page.waitForFunction(() => window.APP && window.APP.ready);
    await page.evaluate(() => document.fonts.ready);
    for (const width of [320, 340, 360, 375, 380, 400, 429]) {
      await page.setViewportSize({ width, height: 800 });
      await settle(page);
      const m = await page.evaluate(() => {
        const r = (el) => el.getBoundingClientRect(), title = r(document.querySelector("#header h1"));
        const views = [...document.querySelectorAll("#views button")].map(r), link = r(document.getElementById("lang-switch"));
        return { titleBottom: title.bottom, viewTops: views.map((v) => Math.round(v.top)),
          viewsBottom: Math.max(...views.map((v) => v.bottom)), linkTop: link.top,
          overflow: document.documentElement.scrollWidth > window.innerWidth };
      });
      check(m.viewTops.every((t) => t === m.viewTops[0]), `${width} px: the views stay in one row: ${m.viewTops}`);
      check(m.viewTops[0] < m.titleBottom, `${width} px: the views stand beside the title: ${m.viewTops[0]} vs ${m.titleBottom}`);
      check(m.linkTop >= m.viewsBottom - 1, `${width} px: the switch lies below the views: ${m.linkTop} vs ${m.viewsBottom}`);
      check(!m.overflow, `${width} px: no horizontal scrolling`);
    }
  });
}
