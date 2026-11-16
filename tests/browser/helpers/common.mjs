// Paths and small helpers that every area uses.
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

// The repo root, two levels above this folder. Env values relative to it, so they work from the repo root and from
// tests/browser alike.
const root = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..", "..");
const fromRoot = (value, fallback) => resolve(root, value || fallback);

export const paths = {
  root,
  mapHtml: fromRoot(process.env.MAP_HTML, "output/sozialraum-frankfurt.html"),
  candidatesCsv: fromRoot(process.env.CANDIDATES_CSV, "interim/candidates_reference.csv"),
  screens: fromRoot(process.env.SCREENS, "output/screens"),
};

// Two animation frames. The shared map tooltip is computed in the frame after a mouse move (05_tooltip.js); a scroll
// event comes a frame later and hides a chart tooltip.
export const frames = (page) => page.evaluate(() => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r))));

// The whole numbers of a text, every run of digits on its own ("Rang 44 bis 45 von 114" is [44, 45, 114]). Not the
// German number format: for that see `numbers` in helpers/layers.mjs.
export const integers = (text) => (String(text).match(/\d+/g) || []).map(Number);

// two frames plus the time of a Leaflet animation
export const settle = (page) => page.evaluate(() => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(r, 400)))));

// The map in a new page of the same context, loaded with `fragment` and settled like the fixture mapPage. The guard of
// fixtures.mjs covers every page of the context. viewport: a window size for the new page (a desktop in a phone project).
export const openMap = async (context, fragment, viewport) => {
  const page = await context.newPage();
  if (viewport) await page.setViewportSize(viewport);
  await page.goto(pathToFileURL(paths.mapHtml).href + fragment);
  await page.waitForFunction(() => window.APP && window.APP.ready);
  await page.evaluate(() => document.fonts.ready);
  await settle(page);
  return page;
};

// The centre of the visible map as [lat, lng]: on the phone the part above the panel, else the whole container. The
// panel is measured in the page, not taken from the map code. From getCenter (exact), not from a container point
// (rounded to the pixel origin of Leaflet: half a pixel is 35 m at zoom 10.5).
export const visibleCenter = (page) => page.evaluate(() => {
  const m = APP.map.getContainer().getBoundingClientRect(), s = APP.sidebar.getBoundingClientRect();
  const bottom = APP.phone() ? Math.min(m.bottom, s.top) : m.bottom, zoom = APP.map.getZoom();
  const c = APP.map.unproject(APP.map.project(APP.map.getCenter(), zoom).subtract([0, (m.bottom - bottom) / 2]), zoom);
  return [c.lat, c.lng];
});

// Box of the first element that matches, or null. visible: shown (an offset parent) or fixed.
export const rect = (page, selector) => page.evaluate((s) => {
  const e = document.querySelector(s);
  if (!e) return null;
  const b = e.getBoundingClientRect();
  return { left: b.left, top: b.top, right: b.right, bottom: b.bottom, width: b.width, height: b.height, visible: e.offsetParent !== null || getComputedStyle(e).position === "fixed" };
}, selector);

// no horizontal scrolling
export const noOverflow = (page) => page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1);

// Page function, installed by the mapPage fixture before the map loads: an ⓘ as "Label: part · part" lines joined
// by a space, read from its <dl> (docs/texts.md, ⓘ protocol).
export const installProtocolText = () => {
  window.protocolText = (el) => [...el.querySelectorAll("dt")].map((dt) =>
    `${dt.textContent}: ${[...dt.nextElementSibling.children].map((s) => s.textContent).join(" · ")}`).join(" ");
};
