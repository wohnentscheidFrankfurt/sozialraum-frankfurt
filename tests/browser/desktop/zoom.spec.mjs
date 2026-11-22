// Reset button of the zoom control: between + and −, shows the whole city again (docs/design.md, Zoom control).
import { test } from "../fixtures.mjs";
import { settle, visibleCenter } from "../helpers/common.mjs";

const BUTTON = ".leaflet-control-zoom .zoom-reset";
const start = (page) => page.evaluate(() => ({ zoom: APP.map.getZoom(), link: APP.startLink }));

test("the zoom control holds +, the reset button, −", async ({ mapPage: page, check }) => {
  const s = await page.evaluate((sel) => {
    const bar = document.querySelector(".leaflet-control-zoom"), b = bar.querySelector(sel);
    return { order: [...bar.children].map((e) => e.className.replace("leaflet-disabled", "").trim().split(" ").pop()),
      tag: b?.tagName, type: b?.getAttribute("type"), label: b?.getAttribute("aria-label"), title: b?.title, svg: b?.querySelector("svg[aria-hidden=true]") !== null, want: APP.t("zoom_reset") };
  }, BUTTON);
  check(JSON.stringify(s.order) === JSON.stringify(["leaflet-control-zoom-in", "zoom-reset", "leaflet-control-zoom-out"]), "order +, reset, −: " + JSON.stringify(s.order));
  check(s.tag === "BUTTON" && s.type === "button" && s.label && s.label === s.want && s.title === s.want && s.svg, "button, label and icon: " + JSON.stringify(s));
});

test("a click shows the whole city and keeps the address", async ({ mapPage: page, check }) => {
  const before = await start(page), c0 = await visibleCenter(page);
  await page.evaluate(() => APP.map.setView([50.11, 8.68], 16, { animate: false }));
  await settle(page);
  const hash = await page.evaluate(() => location.hash);
  await page.click(BUTTON);
  await page.waitForFunction((z) => Math.abs(APP.map.getZoom() - z) <= 0.5, before.zoom);
  await settle(page);
  const c1 = await visibleCenter(page), after = await page.evaluate(() => location.hash);
  check(Math.abs(c1[0] - c0[0]) < 0.01 && Math.abs(c1[1] - c0[1]) < 0.01, `centre back at the start: ${c0} ${c1}`);
  check(hash.startsWith("#karte/zoom=") && after !== "#" && after !== "" && after === "#" + (await page.evaluate(() => APP.mapLink())),
    `the hash holds a map link: ${hash} -> ${after}`);
});

test("a click keeps an explored area", async ({ mapPage: page, check }) => {
  await page.evaluate(() => APP.explore("Altstadt", { fly: false }));
  await settle(page);
  await page.click(BUTTON);
  await settle(page);
  check(await page.evaluate(() => APP.state.area) === "Altstadt", "area stays Altstadt");
});

test("keyboard: Tab reaches the button, Enter fits the city, the focus shows", async ({ mapPage: page, check }) => {
  const before = await start(page);
  await page.evaluate(() => APP.map.setView([50.11, 8.68], 16, { animate: false }));
  await page.focus(".leaflet-control-zoom-in");
  await page.keyboard.press("Tab");
  check(await page.evaluate((sel) => document.activeElement === document.querySelector(sel), BUTTON), "Tab from + reaches the reset button");
  const outline = await page.evaluate(() => { const s = getComputedStyle(document.activeElement); return [s.outlineStyle, s.outlineWidth, s.outlineColor]; });
  check(outline[0] === "solid" && outline[1] === "2px" && outline[2] === "rgb(0, 0, 0)", "focus outline black 2 px: " + outline);
  await page.keyboard.press("Enter");
  await page.waitForFunction((z) => Math.abs(APP.map.getZoom() - z) <= 0.5, before.zoom);
  await settle(page);
  const s = await page.evaluate(() => { const c = APP.map.getCenter(); return [APP.map.getZoom(), c.lat, c.lng]; });
  check(Math.abs(s[0] - before.zoom) <= 0.5 && Math.abs(s[1] - 50.12) < 0.05 && Math.abs(s[2] - 8.68) < 0.1, "Enter fits the city: zoom and centre " + s);
});
