// Layout checks of the phone, tablet and wide windows (docs/design.md, Phone and tablet; Legend).
import { noOverflow, rect } from "./common.mjs";

// collapsed legend: the body is hidden, title and note remain (at most 2 lines of the note at 220 px)
export const legendCollapsed = async (page) => (await rect(page, ".legend")).height <= 80 && (await rect(page, ".legend .legend-body")).visible === false;

// the note of the legend stands right under its title, inside the legend, with the given text (the legend_note of the
// layer in APP.meta)
export const noteUnderTitle = (page, text) => page.evaluate((t) => { const n = document.querySelector(".legend .legend-note");
  return !!n && n.textContent === t && n.previousElementSibling.classList.contains("legend-title") &&
    n.getBoundingClientRect().top >= n.previousElementSibling.getBoundingClientRect().bottom - 1 &&
    n.getBoundingClientRect().height > 0 && n.getBoundingClientRect().right <= document.querySelector(".legend").getBoundingClientRect().right; }, text);

// the view buttons: one line, side by side, inside the window; the header no higher than with one button less plus
// 4 px. `expected` are the views of the page: the map and the chart views of APP.VIEWS.
export const viewButtons = (page) => page.evaluate(() => {
  const buttons = [...document.querySelectorAll("#views button")], boxes = buttons.map((b) => b.getBoundingClientRect());
  const header = () => document.getElementById("header").getBoundingClientRect().height, all = header(), last = buttons[buttons.length - 1];
  last.style.display = "none";
  const fewer = header();
  last.style.display = "";
  return { count: buttons.length, heights: boxes.map((b) => b.height), tops: boxes.map((b) => b.top), right: boxes[boxes.length - 1].right,
    lines: buttons.map((b) => Math.round(b.scrollHeight / parseFloat(getComputedStyle(b).lineHeight === "normal" ? parseFloat(getComputedStyle(b).fontSize) * 1.3 : getComputedStyle(b).lineHeight))),
    order: boxes.every((b, i) => i === 0 || b.left >= boxes[i - 1].right - 0.5), all, fewer, width: window.innerWidth,
    labels: buttons.map((b) => b.textContent), views: buttons.map((b) => b.dataset.view),
    expected: ["map", ...Object.keys(APP.VIEWS)] };
});

// Layout that every window shares: no horizontal scrolling, Leaflet knows the map size, footer one line
export async function common({ page, check }) {
  check(await noOverflow(page), "no horizontal scrolling");
  check(await page.evaluate(() => { const c = APP.map.getContainer(), s = APP.map.getSize(); return s.x === c.clientWidth && s.y === c.clientHeight; }),
    "Leaflet knows the real map size");
  check(await page.evaluate(() => document.querySelector("#footer > details > summary") !== null), "footer is a details element");
  // the summary names the day of the build (APP.data.created) in the date format d.m.yyyy
  const summary = await page.evaluate(() => ({ text: document.querySelector("#footer summary")?.textContent || "", created: APP.data.created }));
  check(/^\d{1,2}\.\d{1,2}\.\d{4}$/.test(summary.created) && summary.text.includes(summary.created), `footer summary: ${summary.text}`);
  const footer = await rect(page, "#footer");
  check(footer && footer.height <= 32, `footer is one line (${footer && footer.height} px)`);
}
