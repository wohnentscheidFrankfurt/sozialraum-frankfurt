// Helpers of the areas legend, ⓘ, layers and tooltip (desktop).
import { frames } from "./common.mjs";

// Texts of the open tooltips. Leaflet hides a closed tooltip (opacity 0) and removes it only after 200 ms: count only
// open ones.
export const openTooltips = (page) => page.evaluate(() => [...document.querySelectorAll(".leaflet-tooltip")]
  .filter((t) => t.style.opacity !== "0").map((t) => t.textContent));

// The mouse at a point of the map (from 3 px beside it, so Leaflet sees a move); the open tooltips after that
export const hoverAt = async (page, [lat, lng]) => {
  const p = await page.evaluate(([la, ln]) => { const r = APP.map.getContainer().getBoundingClientRect(), q = APP.map.latLngToContainerPoint([la, ln]);
    return { x: r.left + q.x, y: r.top + q.y }; }, [lat, lng]);
  await page.mouse.move(p.x - 3, p.y - 3);
  await page.mouse.move(p.x, p.y);
  await frames(page);
  return openTooltips(page);
};

// The numbers of a map text in German format ("1.234,5" is 1234.5), in their order. Plain runs of digits: `integers`
// in helpers/common.mjs.
export const numbers = (text) => (String(text).match(/\d+(?:\.\d{3})*(?:,\d+)?/g) || []).map((n) => Number(n.replace(/\./g, "").replace(",", ".")));

// No leftover of a template or a missing value in a text
export const clean = (text) => typeof text === "string" && text.trim() !== "" && !/undefined|NaN|null|[{}]/.test(text);
