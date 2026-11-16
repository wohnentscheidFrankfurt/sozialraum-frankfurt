// Usage: node tests/browser/tools/teaser_image.mjs <map.html> <out.png>; writes the teaser image of the website:
// the whole page at 1400x900 CSS px (2800x1800 px), default view, with the basemap tiles.
// Loads the tiles from basemap.de. Exits with 1 when no tile loads, so an offline run leaves no blank image.
import { chromium } from "@playwright/test";
import { pathToFileURL } from "node:url";
const [html, out] = process.argv.slice(2);
const browser = await chromium.launch({ channel: "chrome", headless: true });
const context = await browser.newContext({ viewport: { width: 1400, height: 900 }, deviceScaleFactor: 2 });
const page = await context.newPage();
let tiles = 0;
page.on("response", (response) => {
  if (response.url().includes("geodatenzentrum.de") && response.ok()) tiles++;
});
await page.goto(pathToFileURL(html).href, { waitUntil: "networkidle" });
await page.waitForFunction(() => window.APP && window.APP.ready, null, { timeout: 30000 });
await page.evaluate(() => document.fonts.ready);
await new Promise((r) => setTimeout(r, 2500));
await page.screenshot({ path: out });
await browser.close();
if (tiles === 0) {
  console.error("No basemap tile loaded: the image has no background.");
  process.exit(1);
}
console.log(`${out}: ${tiles} tiles`);
