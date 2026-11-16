"use strict";
// Phone: the panel follows the finger (docs/design.md, Phone panel). A vertical drag on the head (tab bar) moves it
// both ways. In the content a drag down moves it only when the content is at its top; otherwise the content scrolls.
// On release a fast flick decides by its direction, a slow drag by the position. APP.setPanel opens or closes.
// Times come from performance.now(): the time stamps of real touch events do not share one clock in every browser.
APP.drag = null;
APP.sidebar.addEventListener("touchstart", (e) => {
  // a second finger ends a running drag: the panel snaps
  if (APP.drag) return APP.endDrag();
  // sliders and selects keep their own gestures
  if (!APP.phone() || e.touches.length !== 1 || e.target.closest("input, select")) return;
  const t = e.touches[0];
  // start from where the panel is now, also in the middle of a slide
  const base = new DOMMatrix(getComputedStyle(APP.sidebar).transform).m42;
  APP.drag = { x0: t.clientX, y0: t.clientY, content: e.target.closest(".tab"), moving: false, shift: base, base,
    last: [[t.clientY, performance.now()]] };
}, { passive: true });
APP.sidebar.addEventListener("touchmove", (e) => {
  const d = APP.drag;
  if (!d) return;
  const t = e.touches[0], dx = t.clientX - d.x0, dy = t.clientY - d.y0;
  if (!d.moving) {
    // below 8 px it is still a tap
    if (Math.abs(dx) < 8 && Math.abs(dy) < 8) return;
    // sideways, or a scroll of the content: not for the panel
    if (Math.abs(dx) > Math.abs(dy) || (d.content && (dy < 0 || d.content.scrollTop > 0))) {
      APP.drag = null;
      return;
    }
    d.moving = true;
    APP.sidebar.classList.add("dragging");
  }
  e.preventDefault();
  d.shift = Math.min(Math.max(d.base + dy, 0), APP.closedShift());
  APP.sidebar.style.transform = `translateY(${d.shift}px)`;
  d.last = [...d.last.slice(-4), [t.clientY, performance.now()]];
}, { passive: false });
APP.endDrag = function () {
  const d = APP.drag;
  APP.drag = null;
  if (!d || !d.moving) return;
  // speed over the last moves, in px per ms; down is positive. After a pause of the finger only the position counts.
  const [y1, t1] = d.last[0], [y2, t2] = d.last[d.last.length - 1];
  const speed = performance.now() - t2 > 100 ? 0 : (y2 - y1) / Math.max(1, t2 - t1);
  const open = Math.abs(speed) > 0.5 ? speed < 0 : d.shift < APP.closedShift() / 2;
  APP.sidebar.classList.remove("dragging");
  APP.sidebar.style.transform = "";
  APP.setPanel(open);
};
APP.sidebar.addEventListener("touchend", APP.endDrag);
APP.sidebar.addEventListener("touchcancel", APP.endDrag);
