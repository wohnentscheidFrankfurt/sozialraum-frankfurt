// Touch input and the phone panel (docs/design.md, Phone panel). WebKit and Chrome, except realDrag (Chrome only).
import { expect } from "../fixtures.mjs";
import { settle } from "./common.mjs";

// selector of the button of a tab in the tab bar
export const tab = (name) => `#tabs button[data-tab="${name}"]`;

// Tap the first element that matches, then settle. A failed tap is recorded as a soft failure and the test goes on.
export const tap = async (page, selector) => {
  try { await page.locator(selector).first().tap({ timeout: 3000 }); } catch { expect.soft(false, `cannot tap ${selector}`).toBeTruthy(); }
  await settle(page);
};

// Visible part of the phone panel: main clips it, and closed it is moved down until only the tab bar shows
export const panel = (page) => page.evaluate(() => {
  const s = document.getElementById("sidebar").getBoundingClientRect(), m = document.querySelector("main").getBoundingClientRect();
  const top = Math.min(s.top, m.bottom);
  return { left: s.left, right: s.right, width: s.width, top, bottom: Math.min(s.bottom, m.bottom), height: Math.min(s.bottom, m.bottom) - top, visible: true };
});

// glyph and aria-expanded of the arrow, for example "▲ false"
export const arrow = (page) => page.evaluate(() => { const b = document.getElementById("panel-toggle"); return b && [b.textContent, b.getAttribute("aria-expanded")].join(" "); });
// the aria-label of the arrow, or "pressed" when it carries aria-pressed (it must not: it is no toggle button)
export const arrowLabel = (page) => page.evaluate(() => { const b = document.getElementById("panel-toggle"); return b.hasAttribute("aria-pressed") ? "pressed" : b.getAttribute("aria-label"); });
const tabsHeight = (page) => page.evaluate(() => document.getElementById("tabs").getBoundingClientRect().height);
export const isOpen = async (page) => (await panel(page)).height > 150 && await arrow(page) === "▼ true";
export const isClosed = async (page) => (await panel(page)).height <= (await tabsHeight(page)) + 3 && await arrow(page) === "▲ false";

// Dispatched touch drag on an element (WebKit and Chrome): start near its top, move by dx/dy in ms, then release.
// hold: pause in ms before the release. Returns the visible height of the panel at the start and just before the
// release, to see that it follows the finger.
// 07_swipe.js measures the speed of the last moves with performance.now(). A timer only fires late, so a busy machine
// makes a drag slower, never faster: a flick needs a margin above the threshold of 0.5 px per ms.
export const drag = (page, selector, dy, ms = 300, dx = 0, hold = 0) => page.evaluate(async ([sel, dy, ms, dx, hold]) => {
  const el = document.querySelector(sel), b = el.getBoundingClientRect(), x0 = b.left + b.width / 2, y0 = b.top + Math.min(20, b.height / 2);
  const fire = (type, x, y) => {
    const t = { identifier: 1, target: el, clientX: x, clientY: y, pageX: x, pageY: y, screenX: x, screenY: y };
    const e = new Event(type, { bubbles: true, cancelable: true });
    Object.defineProperty(e, "touches", { value: type === "touchend" ? [] : [t] });
    Object.defineProperty(e, "changedTouches", { value: [t] });
    el.dispatchEvent(e);
  };
  const visible = () => document.querySelector("main").getBoundingClientRect().bottom - document.getElementById("sidebar").getBoundingClientRect().top;
  const start = visible();
  fire("touchstart", x0, y0);
  const steps = 10;
  for (let i = 1; i <= steps; i++) {
    await new Promise((r) => setTimeout(r, ms / steps));
    fire("touchmove", x0 + (dx * i) / steps, y0 + (dy * i) / steps);
  }
  await new Promise((r) => setTimeout(r, hold));
  const mid = visible();
  fire("touchend", x0 + dx, y0 + dy);
  return { start, mid };
}, [selector, dy, ms, dx, hold]);

// A sequence of touch events on an element: [type, dy, fingers, wait before in ms]. Returns the visible height of the
// panel after each step. For a second finger, a cancel, or a drag that starts while the panel slides.
export const touchSeq = (page, selector, steps) => page.evaluate(async ([sel, steps]) => {
  const el = document.querySelector(sel), b = el.getBoundingClientRect(), x = b.left + b.width / 2, y0 = b.top + Math.min(20, b.height / 2);
  const visible = () => document.querySelector("main").getBoundingClientRect().bottom - document.getElementById("sidebar").getBoundingClientRect().top;
  const out = [];
  for (const [type, dy, fingers, wait] of steps) {
    await new Promise((r) => setTimeout(r, wait));
    if (type === "arrow") { document.getElementById("panel-toggle").click(); out.push(visible()); continue; }
    const list = Array.from({ length: fingers }, (_, i) => ({ identifier: i + 1, target: el, clientX: x + 40 * i, clientY: y0 + dy, pageX: x + 40 * i, pageY: y0 + dy }));
    const e = new Event(type, { bubbles: true, cancelable: true });
    Object.defineProperty(e, "touches", { value: type === "touchend" || type === "touchcancel" ? [] : list });
    Object.defineProperty(e, "changedTouches", { value: list.slice(-1) });
    el.dispatchEvent(e);
    out.push(visible());
  }
  return out;
}, [selector, steps]);

// Real touch input through the DevTools protocol (Chrome only): the browser decides about scrolling and clicks
export async function realDrag(page, x, y, dy, ms = 300) {
  const cdp = await page.context().newCDPSession(page);
  const send = (type, py) => cdp.send("Input.dispatchTouchEvent", { type, touchPoints: type === "touchEnd" ? [] : [{ x, y: py }] });
  await send("touchStart", y);
  for (let i = 1; i <= 10; i++) { await new Promise((r) => setTimeout(r, ms / 10)); await send("touchMove", y + (dy * i) / 10); }
  await send("touchEnd", y + dy);
  await cdp.detach();
}
