// Wide layout (docs/design.md, Phone and tablet): the layout every window shares, the sidebar of 410 px, the full
// legend, and print. Runs in desktop-chrome (1400 × 900).
import { test } from "../fixtures.mjs";
import { rect, settle } from "../helpers/common.mjs";
import { common } from "../helpers/layout.mjs";

test("shared layout", async ({ mapPage: page, check }) => {
  await common({ page, check });
});

test("wide: sidebar 410 px and the full legend", async ({ mapPage: page, check }) => {
  check(Math.abs((await rect(page, "#sidebar")).width - 410) <= 1, "wide: sidebar 410 px");
  check((await rect(page, ".legend")).height > 100, "wide: full legend");
});

test("print: one column for the map, the source list in full", async ({ mapPage: page, check }) => {
  // print (A4 is narrower than 1024 px): one column for the map, the source list printed in full
  await page.setViewportSize({ width: 718, height: 1000 });
  await page.emulateMedia({ media: "print" });
  await page.evaluate(() => window.dispatchEvent(new Event("beforeprint")));
  await settle(page);
  const map = await rect(page, "#map"), footer = await rect(page, "#footer");
  check(map.width >= 700 && !(await rect(page, "#sidebar")).visible, `print: map over the full width (${map.width})`);
  check(await page.evaluate(() => document.querySelector("#footer details").open) && footer.height > 40, "print: source list open and in full");
  await page.emulateMedia({ media: "screen" });
  await page.evaluate(() => window.dispatchEvent(new Event("afterprint")));
  check(await page.evaluate(() => !document.querySelector("#footer details").open), "after print: source list closed again");
});
