// Medium layout (docs/design.md, Phone and tablet): sidebar 320 px left, map beside it. Low windows collapse the
// legend, the others show it full. Runs in webkit-iphone-landscape (low) and chrome-768.
import { test } from "../fixtures.mjs";
import { rect, settle } from "../helpers/common.mjs";
import { checkRentBurden } from "../helpers/charts.mjs";
import { common, legendCollapsed } from "../helpers/layout.mjs";
import { tab, tap } from "../helpers/touch.mjs";
import { drawnRentBurden } from "../helpers/views.mjs";

// per project: the smallest map and whether the window is low
const WINDOWS = {
  "webkit-iphone-landscape": { minMapWidth: 400, minMapHeight: 200, low: true },
  "chrome-768": { minMapWidth: 400, minMapHeight: 600, low: false },
};
const windowOf = (testInfo) => WINDOWS[testInfo.project.name];

test("shared layout", async ({ mapPage: page, check }) => {
  await common({ page, check });
});

test("sidebar left of the map, legend, layers usable", async ({ mapPage: page, check }, testInfo) => {
  const { minMapWidth, minMapHeight, low } = windowOf(testInfo);
  const side = await rect(page, "#sidebar"), map = await rect(page, "#map");
  check(Math.abs(side.width - 320) <= 1, `sidebar 320 px (${side.width})`);
  check(side.right <= map.left + 1, "sidebar left of the map");
  check(map.width >= minMapWidth, `map at least ${minMapWidth} px wide (${map.width})`);
  check(map.height >= minMapHeight, `map at least ${minMapHeight} px high (${map.height})`);
  if (low) {
    check(await legendCollapsed(page), "low window: legend collapsed");
    await tap(page, ".legend");
    check((await rect(page, ".legend")).height > 100, "low window: tap opens the legend");
  } else check((await rect(page, ".legend")).height > 100, "full legend");
  check(await page.evaluate(() => document.getElementById("tab-city").offsetHeight > 0 && [...document.querySelectorAll("#sidebar .tab")].every((t) => !t.inert)),
    "layers show without a tap and are usable");
});

test("a tap on an area shows the button and keeps the tab", async ({ mapPage: page, check }) => {
  // a tap on an area shows the button and keeps the tab Stadt
  const at = await page.evaluate(() => { const m = APP.map, b = m.getContainer().getBoundingClientRect();
    for (let y = 60; y < m.getSize().x + 400; y += 20) for (let x = 40; x < m.getSize().x - 40; x += 20) {
      if (y >= m.getSize().y - 40) break;
      const p = APP.areaAt(m.containerPointToLatLng([x, y]));
      if (p && !document.elementFromPoint(b.left + x, b.top + y).closest(".leaflet-control")) return { x: b.left + x, y: b.top + y };
    } return null; });
  check(at !== null, "medium: an area on the map");
  if (!at) return;
  await page.touchscreen.tap(at.x, at.y);
  await settle(page);
  check(await page.evaluate(() => { const b = APP.tip.getElement()?.querySelector(".tip-explore"); return !!b && b.textContent.trim() !== "" && !!b.dataset.explore; })
    && await page.evaluate(() => document.querySelector('#tabs button[aria-pressed="true"]').dataset.tab) === "city", "medium: a tap shows the button and keeps tab Stadt");
});

test("help without the phone paragraph, no arrow beside the map", async ({ mapPage: page, check, saveScreenshot }) => {
  await tap(page, tab("help"));
  check(await page.evaluate(() => document.getElementById("tab-help").offsetHeight > 0 && document.querySelector("#tab-help .phone-only").offsetHeight === 0),
    "medium: help open, the Handy paragraph is hidden");
  await tap(page, tab("city"));
  check((await rect(page, "#panel-toggle"))?.visible === false, "no arrow beside the map");
  await saveScreenshot("layout");
});

test("view Miete: the drawings at the room of the window", async ({ mapPage: page, check, saveScreenshot }) => {
  await tap(page, '#views button[data-view="rent_burden"]');
  check(await page.evaluate(() => !document.getElementById("view-rent-burden").hidden && document.querySelector("main").hidden), "medium: the view Miete shows");
  // the wide drawing from 700 px of room (APP.CONSTRUCTION_WIDE), below it the drawing in px; judged by the measured room
  const room = await page.evaluate(() => APP.burdenBody.clientWidth);
  check(await drawnRentBurden(page, room >= 700 ? 760 : 0), `medium: room ${room} px, ${room >= 700 ? "the wide drawing" : "drawn at the width in px"}`);
  await checkRentBurden(page, check, "Miete, medium");
  await saveScreenshot("rent_burden");
});
