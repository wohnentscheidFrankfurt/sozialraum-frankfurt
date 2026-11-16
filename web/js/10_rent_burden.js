"use strict";
// View "Miete" (pipeline/use_cases/rent_burden/README.md): two figures. The first shows the warm rent against the net
// wage of three model persons in the latest year, as wage bars with a switch of the contract (new or older). The second
// shows the warm rent against the income of tenants, one stacked bar per income group. Every number, colour and text
// comes from Python.

// The wage bars (w = APP.data.rent_burden.wage) of one contract: one row per person, a hollow frame as wide as the net
// wage on one scale (w.max_net fills the plot) and from its left the red block of the warm rent, equally wide in every
// row. The block shows the share where it fits (as the segments of the bars below); the tooltip of the row carries
// every number. Wide: a drawing 760 units wide that scales; name and net wage stand left of the frame, what is left
// inside the white part of the frame or, where it does not fit, right of it; a dashed guide marks the right edge of
// the blocks through all rows. Narrow (below APP.CONSTRUCTION_WIDE px): drawn in px at the room; name and the sub line
// (net wage, what is left) stand above the frame, without a guide, which would cross them. The warm rent is named once
// on top. `from`: the width of the block before a switch; the block and the guide start there and move, and the
// number waits until the block stands (APP.wageMove).
APP.wageBars = function (w, contract, W, from) {
  const narrow = W < APP.CONSTRUCTION_WIDE, x0 = narrow ? 0 : 210, plot = W - x0, bar = narrow ? 26 : 34;
  const head = narrow ? 40 : 0, gap = narrow ? 18 : 22, top0 = 34, row = head + bar + gap;
  const c = w.contracts.find((e) => e.id === contract), scale = plot / w.max_net, rent = c.rent * scale;
  const bottom = top0 + c.rows.length * row - gap;
  const svg = APP.svgElement("svg", { viewBox: `0 0 ${W} ${bottom + 4}`, ...(narrow ? { width: W } : {}), class: "wage", role: "img",
    "aria-label": w.aria_label });
  const moved = (e, transform) => { if (from != null) e.style.transform = transform; return e; };
  if (!narrow) svg.append(moved(APP.svgElement("line", { x1: x0 + rent, x2: x0 + rent, y1: 22, y2: bottom, class: "guide" }), `translateX(${from - rent}px)`));
  svg.append(APP.svgElement("text", { x: x0, y: 14, class: "rent-label" }, c.rent_text));
  c.rows.forEach((r, k) => {
    const top = top0 + k * row + head, width = r.net * scale, g = APP.svgElement("g", { class: "row", "data-tip": r.tip, "data-person": r.id });
    g.append(APP.svgElement("rect", { x: 0, y: top - head, width: narrow ? W : x0 + width, height: head + bar, fill: "transparent", class: "hit" }));
    if (narrow) {
      const sub = APP.svgElement("text", { x: 0, y: top - 6, class: "sub" }, r.net_text);
      sub.append(APP.svgElement("tspan", { dx: 8 }, r.left_text));
      g.append(APP.svgElement("text", { x: 0, y: top - 22, class: "name" }, r.name), sub);
    } else {
      g.append(APP.svgElement("text", { x: 0, y: top + 14, class: "name" }, r.name),
        APP.svgElement("text", { x: 0, y: top + 30, class: "sub" }, r.net_text));
    }
    g.append(APP.svgElement("rect", { x: x0, y: top, width, height: bar, class: "frame" }),
      moved(APP.svgElement("rect", { x: x0, y: top, width: rent, height: bar, fill: w.colour, class: "rent" }), `scaleX(${from / rent})`));
    if (r.share_text.length * APP.BURDEN_CHAR + 8 <= rent) g.append(APP.svgElement("text", { x: x0 + rent / 2, y: top + bar / 2, dy: "0.35em",
      "text-anchor": "middle", class: "in-bar", style: `fill:${w.ink}${from != null ? ";opacity:0" : ""}` }, APP.keepUnits(r.share_text)));
    if (!narrow) {
      const inside = width - rent >= r.left_text.length * APP.BURDEN_CHAR + 16;
      g.append(APP.svgElement("text", { x: inside ? x0 + width - 10 : x0 + width + 8, y: top + bar / 2, dy: "0.35em",
        "text-anchor": inside ? "end" : "start", class: "left" }, r.left_text));
    }
    svg.append(g);
  });
  return svg;
};

// The svg in the page: the blocks and the guide of a switch move from their old width to the new one (CSS transition,
// none under prefers-reduced-motion). Reading the layout first fixes the start, so the change of style is a transition.
APP.wageMove = function (svg) {
  svg.getBoundingClientRect();
  svg.querySelectorAll(".rent, .guide, .in-bar").forEach((e) => { e.style.transform = ""; e.style.opacity = ""; });
};

// The contract the wage bars show; a switch keeps it across every later redraw
APP.wageContract = null;
APP.wageSwitch = function (w) {
  const div = document.createElement("div");
  div.className = "wage-switch";
  div.setAttribute("role", "group");
  for (const c of w.contracts) {
    const b = document.createElement("button");
    b.type = "button";
    b.dataset.contract = c.id;
    b.textContent = c.name;
    b.setAttribute("aria-pressed", String(c.id === APP.wageContract));
    b.addEventListener("click", () => {
      if (c.id === APP.wageContract) return;
      // the width the block shows now: during a move its scale is not yet 1
      const rent = APP.wageBody.querySelector("rect.rent");
      const from = rent && parseFloat(rent.getAttribute("width")) * new DOMMatrix(getComputedStyle(rent).transform).a;
      APP.wageContract = c.id;
      div.querySelectorAll("button").forEach((e) => e.setAttribute("aria-pressed", String(e.dataset.contract === c.id)));
      APP.drawWage(from);
    });
    div.append(b);
  }
  return div;
};

// Draws the wage bars of the chosen contract at the width of the last layout; `from` as in APP.wageBars
APP.drawWage = function (from) {
  const svg = APP.wageBars(APP.data.rent_burden.wage, APP.wageContract, APP.rentBurdenWidth, from);
  APP.wageBody.replaceChildren(svg);
  if (from != null) APP.wageMove(svg);
  document.querySelector("#view-rent-burden .chart-tip").hidden = true;
};

// The bars of tenants by income group (b = APP.data.rent_burden.low_income): one row per group, a bar of 100 % with
// one segment per class in class order. Wide: a drawing 760 units wide that scales; the label (name, below it
// „Median ~53 %“) stands left of its bar. Narrow (below APP.CONSTRUCTION_WIDE px): drawn in px at the room; the label
// stands above its bar in one line. A segment shows its number where Python set `text` (share and contrast) and the
// number fits with 4 px on each side at this width; else its tooltip carries it. The label and each segment have a
// tooltip. The width of a number is estimated (APP.BURDEN_CHAR per character), because the svg is not in the page yet.
APP.BURDEN_CHAR = 7.5;
APP.burdenBars = function (b, W) {
  const narrow = W < APP.CONSTRUCTION_WIDE, x0 = narrow ? 0 : 210, width = W - x0, bar = narrow ? 26 : 34;
  const head = narrow ? 24 : 0, gap = narrow ? 18 : 22, row = head + bar + gap;
  const svg = APP.svgElement("svg", { viewBox: `0 0 ${W} ${b.bars.length * row - gap + 4}`, ...(narrow ? { width: W } : {}),
    class: "burden", role: "img", "aria-label": b.aria_label });
  b.bars.forEach((r, k) => {
    const top = k * row + head, label = APP.svgElement("g", { class: "label", "data-tip": r.tip });
    if (narrow) {
      const text = APP.svgElement("text", { x: 0, y: top - 8, class: "name" }, r.name);
      text.append(APP.svgElement("tspan", { dx: 8, class: "median" }, APP.keepUnits(r.label)));
      label.append(APP.svgElement("rect", { x: 0, y: top - head, width: W, height: head, fill: "transparent", class: "hit" }), text);
    } else {
      label.append(APP.svgElement("rect", { x: 0, y: top, width: x0 - 8, height: bar, fill: "transparent", class: "hit" }),
        APP.svgElement("text", { x: 0, y: top + 14, class: "name" }, r.name),
        APP.svgElement("text", { x: 0, y: top + 30, class: "median" }, APP.keepUnits(r.label)));
    }
    svg.append(label);
    let x = x0;
    for (const s of r.segments) {
      const w = (s.value / 100) * width, g = APP.svgElement("g", { class: "segment", "data-tip": s.tip, "data-segment": s.id });
      g.append(APP.svgElement("rect", { x, y: top, width: w, height: bar, fill: s.colour }));
      if (s.text && s.text.length * APP.BURDEN_CHAR + 8 <= w) g.append(APP.svgElement("text", { x: x + w / 2, y: top + bar / 2,
        dy: "0.35em", "text-anchor": "middle", class: "in-bar", style: `fill:${s.text_colour}` }, APP.keepUnits(s.text)));
      svg.append(g);
      x += w;
    }
  });
  return svg;
};

// The key of the bars: per class its colour and its name, in one line; a column below APP.CONSTRUCTION_WIDE (layout)
APP.burdenKey = function (b) {
  const key = APP.keyLine(b.key.map((e) => [e.name, e.colour]));
  key.classList.add("burden-key");
  return key;
};

// A source line names its sources itself, so it stands as it comes, without „Quelle:“ in front
APP.burdenSource = function (text) {
  const p = document.createElement("p");
  p.className = "source";
  p.textContent = text;
  return p;
};

// Both figures are built once; APP.layoutRentBurden draws the drawings into them. The first figure: the switch, the
// line that explains the drawing, the wage bars, the source line.
APP.drawRentBurden = function () {
  const { wage, low_income: low } = APP.data.rent_burden, view = document.getElementById("view-rent-burden");
  const inner = document.createElement("div");
  inner.className = "history";
  APP.wageContract = APP.wageContract || wage.contracts[0].id;
  APP.wageBody = document.createElement("div");
  APP.burdenBody = document.createElement("div");
  const explain = document.createElement("p");
  explain.className = "explain";
  explain.textContent = wage.explain;
  const texts = (t) => ({ title: t.title, lead: t.lead, info: t.info, link: t.link });
  const first = APP.infoFigure("rent_burden", texts(wage), "rent-wage", APP.wageSwitch(wage), explain, APP.wageBody);
  const second = APP.infoFigure("rent_burden", texts(low), "rent-low-income", APP.burdenKey(low), APP.burdenBody);
  first.append(APP.burdenSource(wage.source));
  second.append(APP.burdenSource(low.source));
  inner.append(first, second);
  view.replaceChildren(inner);
  APP.bindInfo(view);
  APP.chartTip(view);
  APP.rentBurdenDrawn = true;
  APP.layoutRentBurden();
};

// The key of the bars is a column on phones; set on every layout, also when the width leaves the drawings as they are
APP.layoutRentBurden = function () {
  const room = APP.burdenBody.clientWidth, W = room >= APP.CONSTRUCTION_WIDE ? 760 : room;
  if (!room) return;
  const narrow = W < APP.CONSTRUCTION_WIDE, view = document.getElementById("view-rent-burden");
  view.querySelector(".burden-key").classList.toggle("column", narrow);
  if (W === APP.rentBurdenWidth) return;
  APP.rentBurdenWidth = W;
  APP.drawWage();
  APP.burdenBody.replaceChildren(APP.burdenBars(APP.data.rent_burden.low_income, W));
};
let rentBurdenResize;
window.addEventListener("resize", () => {
  clearTimeout(rentBurdenResize);
  rentBurdenResize = setTimeout(() => { if (APP.rentBurdenDrawn) APP.layoutRentBurden(); }, 150);
});
