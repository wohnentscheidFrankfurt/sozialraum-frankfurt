// Usage: node tests/browser/tools/readme_images.mjs <map.html> <folder>; writes the README images map.png, history.png,
// new_construction.png, rent_burden.png (the first figure of each view).
// Loads the basemap tiles from the network. Afterwards: sips --resampleWidth 1280 <folder>/*.png
import { chromium } from "@playwright/test";
import { pathToFileURL } from "node:url";
const [html, out] = process.argv.slice(2);
const browser = await chromium.launch({ channel: "chrome", headless: true });
const context = await browser.newContext({ viewport: { width: 1280, height: 800 }, deviceScaleFactor: 2 });
const page = await context.newPage();
await page.goto(pathToFileURL(html).href, { waitUntil: "networkidle" });
await page.waitForFunction(() => window.APP && window.APP.ready, null, { timeout: 30000 });
await page.evaluate(() => document.fonts.ready);
await page.addStyleTag({ content: ".leaflet-control-zoom { display: none; }" });
await new Promise((r) => setTimeout(r, 2500));
await page.locator("#map").screenshot({ path: `${out}/map.png` });
const pad = 16;
for (const [view, id] of [["history", "#view-history"], ["new_construction", "#view-new-construction"],
  ["rent_burden", "#view-rent-burden"]]) {
  await page.click(`#views button[data-view="${view}"]`);
  await new Promise((r) => setTimeout(r, 800));
  const measure = () => page.evaluate((s) => { const r = document.querySelector(s + " figure").getBoundingClientRect();
    return { x: r.left + scrollX, y: r.top + scrollY, width: r.width, height: r.height }; }, id);
  let box = await measure();
  // a view scrolls in its own box, so a figure taller than the window needs a taller window (same width, same drawing)
  const height = Math.ceil(box.y + box.height + 2 * pad);
  if (height > 800) {
    await page.setViewportSize({ width: 1280, height });
    await new Promise((r) => setTimeout(r, 800));
    box = await measure();
  }
  await page.screenshot({ path: `${out}/${view}.png`, fullPage: true,
    clip: { x: box.x - pad, y: box.y - pad, width: box.width + 2 * pad, height: box.height + 2 * pad } });
  await page.setViewportSize({ width: 1280, height: 800 });
}
await browser.close();
