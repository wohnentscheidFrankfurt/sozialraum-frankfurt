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
