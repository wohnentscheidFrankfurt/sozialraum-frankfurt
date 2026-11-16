// The details line in „Gebiet“ (docs/design.md, Profile and pressed row; Overlays): under the head of the profile a
// closed line names the overlays that are on; open, it holds the same rows as „Stadt“. A switch there keeps exploring.
// Names come from APP.overlayNames() and the titles of the payload, never from literals (docs/texts.md, Where texts live).
import { test } from "../fixtures.mjs";
import { pointIn, rowDo, settleView, view } from "../helpers/profile.mjs";
import { settle } from "../helpers/common.mjs";

const LINE = "#tab-area details.area-details";

// Explore an area of the level shown by a mouse click on the map; false if no free point of it is in view
const clickArea = async (page, check, id) => {
  await settleView(page);
  const pt = await pointIn(page, await page.evaluate(() => APP.state.level), id);
  check(pt !== null, `details: a point in ${id} on the map`);
  if (!pt) return false;
  await page.mouse.click(pt.x, pt.y);
  await settleView(page);
  return true;
};

// The line in the tab Gebiet: open or closed, its names, the names of APP, and its place in the profile
const line = (page) => page.evaluate((sel) => {
  const d = document.querySelector(sel);
  if (!d) return null;
  const firstSection = [...document.querySelectorAll("#tab-area h3")].find((h) => !d.contains(h));
  const h2 = document.querySelector("#tab-area h2");
  return { open: d.open, names: d.querySelector(".details-names")?.textContent ?? null, want: APP.overlayNames().join(", "),
    afterHead: Boolean(h2 && h2.compareDocumentPosition(d) & Node.DOCUMENT_POSITION_FOLLOWING),
    beforeSection: Boolean(firstSection) && d.nextElementSibling === firstSection, remembered: APP.detailsOpen };
}, LINE);

// the short name of an overlay: its title without a final look in brackets
const shortName = (page, name) => page.evaluate((n) => APP.overlays[n].title.replace(/ \([^()]*\)$/, ""), name);

// the overlay checkboxes that are checked, as "tab:name", sorted
const checkedBoxes = (page) => page.evaluate(() => [...document.querySelectorAll("input[data-overlay]:checked")]
  .map((c) => `${c.closest(".tab").id}:${c.dataset.overlay}`).sort());

const openLine = async (page) => {
  await page.click(`${LINE} summary`);
  await settle(page);
};

test("the line stands under the head, closed", async ({ mapPage: page, check }) => {
  if (!await clickArea(page, check, "Bornheim")) return;
  const l = await line(page);
  check(l !== null, "details: the profile of Bornheim has the line");
  if (!l) return;
  check(!l.open && l.remembered === false, "details: the line starts closed " + JSON.stringify(l));
  check(l.afterHead && l.beforeSection, "details: the line stands after the head and right before the first section " + JSON.stringify(l));
  check(l.want !== "" && l.names === l.want, "details: the names are those of the overlays on (Milieuschutz at the start) " + JSON.stringify(l));
  // every name is the title of its overlay without a final look in brackets
  const rule = await page.evaluate(() => {
    const on = Object.entries(APP.overlays).filter(([, u]) => u.on && !u.empty);
    return { names: APP.overlayNames(), titles: on.map(([, u]) => u.title) };
  });
  check(rule.names.length === rule.titles.length && rule.names.every((n, i) => n === rule.titles[i].replace(/ \([^()]*\)$/, "") && !n.endsWith(")")),
    "details: a name is its title without the look " + JSON.stringify(rule));
});

test("switching an overlay keeps exploring", async ({ mapPage: page, check }) => {
  if (!await clickArea(page, check, "Bornheim")) return;
  await page.evaluate(() => { document.querySelector("#tab-area h2").detailsMark = true; });
  const v0 = await view(page);
  await openLine(page);
  check((await line(page))?.open === true, "details: a click on the summary opens the line");
  await page.click('#tab-area input[data-overlay="flat_roofs"]');
  await settleView(page);
  const v1 = await view(page);
  const s = await page.evaluate(() => ({ on: APP.overlays.flat_roofs.on, area: APP.state.area,
    tab: document.querySelector("#tabs button.active")?.dataset.tab, hash: location.hash,
    kept: document.querySelector("#tab-area h2")?.detailsMark === true }));
  const overlays = (/[#&]overlays=([^&]*)/.exec(s.hash)?.[1] ?? "").split(",");
  check(s.on && s.area === "Bornheim" && s.tab === "area", "details: the overlay is on and Bornheim stays explored in Gebiet " + JSON.stringify(s));
  check(v0.lat === v1.lat && v0.lng === v1.lng && v0.zoom === v1.zoom, `details: zoom and centre stay ${JSON.stringify([v0, v1])}`);
  check(overlays.includes("flat_roofs"), "details: the link has the overlay " + s.hash);
  check(s.kept, "details: the profile is not drawn again");
  const l = await line(page), roofs = await shortName(page, "flat_roofs");
  check(l && l.open && l.names === l.want && l.names.split(", ").includes(roofs), `details: the names follow (${roofs}) ` + JSON.stringify(l));
});

test("checkboxes of both tabs agree", async ({ mapPage: page, check }) => {
  if (!await clickArea(page, check, "Bornheim")) return;
  await openLine(page);
  await page.click('#tab-area input[data-overlay="flat_roofs"]');
  const city = await page.evaluate(() => document.querySelector('#tab-city input[data-overlay="flat_roofs"]').checked);
  check(city, "details: the checkbox in Stadt follows the one in Gebiet");
  const count = await page.evaluate(() => Object.entries(APP.overlays).filter(([, u]) => !u.empty).map(([n]) => {
    const boxes = [...document.querySelectorAll(`input[data-overlay="${n}"]`)];
    return [n, boxes.length, boxes.map((b) => b.closest(".tab").id).sort().join()];
  }));
  check(count.every(([, n, tabs]) => n === 2 && tabs === "tab-area,tab-city"), "details: two checkboxes per overlay, one in each tab " + JSON.stringify(count));
  await page.evaluate(() => APP.setOverlay("flat_roofs", false));
  const off = await page.evaluate(() => [...document.querySelectorAll('input[data-overlay="flat_roofs"]')].map((b) => b.checked));
  check(off.length === 2 && off.every((c) => !c), "details: APP.setOverlay unchecks both " + JSON.stringify(off));
  // the other way round: a click in Stadt (it ends exploring; the profile stays in Gebiet)
  await page.click('#tabs button[data-tab="city"]');
  await page.click('#tab-city input[data-overlay="townscape"]');
  const back = await page.evaluate(() => ({ area: document.querySelector('#tab-area input[data-overlay="townscape"]')?.checked,
    names: document.querySelector("#tab-area .details-names")?.textContent, want: APP.overlayNames().join(", ") }));
  const townscape = await shortName(page, "townscape");
  check(back.area === true && back.names === back.want && back.names.split(", ").includes(townscape),
    "details: a click in Stadt checks the box in Gebiet and the names follow " + JSON.stringify(back));
});

test("names: none and below the minimum zoom", async ({ mapPage: page, check }) => {
  if (!await clickArea(page, check, "Bornheim")) return;
  await page.evaluate(() => { for (const n of Object.keys(APP.overlays)) APP.setOverlay(n, false); });
  const none = await line(page);
  check(none && none.names === "" && none.want === "", "details: with none on, no names " + JSON.stringify(none));
  await page.evaluate(() => { APP.map.setZoom(12, { animate: false }); APP.setOverlay("flat_roofs", true); });
  const low = await line(page), roofs = await shortName(page, "flat_roofs");
  const zoom = await page.evaluate(() => APP.map.getZoom());
  check(zoom < 15 && low && low.names === roofs, `details: an overlay on below its minimum zoom is named (${roofs}, zoom ${zoom}) ` + JSON.stringify(low));
});

test("the open state survives redraws", async ({ mapPage: page, check }) => {
  if (!await clickArea(page, check, "Bornheim")) return;
  await openLine(page);
  check((await line(page))?.open === true, "details: open on Bornheim");
  // another area
  if (await clickArea(page, check, "Nordend-Ost")) {
    const l = await line(page), area = await page.evaluate(() => APP.state.area);
    check(area === "Nordend-Ost" && l && l.open, `details: open after exploring Nordend-Ost (${area}) ` + JSON.stringify(l));
  }
  // another level: a Stadtteil has no Bezirk, the tab shows the note; the next profile opens the line again
  await page.evaluate(() => APP.setLevel("district"));
  const district = await page.evaluate(() => APP.properties("district").find((p) => p.quarter === "Nordend-Ost")?.id ?? null);
  check(district !== null && await page.evaluate(() => APP.detailsOpen) === true, `details: the open state stays on the level of Bezirke (${district})`);
  await page.evaluate((id) => APP.explore(id), district);
  await settleView(page);
  const d = await line(page);
  check(d && d.open, "details: open on a Bezirk of Nordend-Ost " + JSON.stringify(d));
  // back to Stadtteile: the Bezirk becomes its Stadtteil, the profile is drawn again
  await page.evaluate(() => APP.setLevel("quarter"));
  await settleView(page);
  const q = await line(page), area = await page.evaluate(() => APP.state.area);
  check(area === "Nordend-Ost" && q && q.open, `details: open after the level of Stadtteile (${area}) ` + JSON.stringify(q));
  // another layer, chosen by a profile row
  const row = await page.evaluate(() => [...document.querySelectorAll("#tab-area [data-layer]")].map((r) => r.dataset.layer).find((id) => id !== APP.state.indicator));
  check(Boolean(row) && await rowDo(page, row, "click"), "details: a profile row of another layer " + row);
  await settleView(page);
  const r = await line(page), layer = await page.evaluate(() => APP.state.indicator);
  check(layer === row && r && r.open, `details: open after a row click (${layer}) ` + JSON.stringify(r));
  // a new page starts closed
  await page.reload();
  await page.waitForFunction(() => window.APP && window.APP.ready);
  await settle(page);
  await page.evaluate(() => APP.explore("Bornheim"));
  await settleView(page);
  const fresh = await line(page);
  check(fresh && !fresh.open && fresh.remembered === false, "details: closed after a reload " + JSON.stringify(fresh));
});

test("the ⓘ of a details row opens in its tab only", async ({ mapPage: page, check }) => {
  if (!await clickArea(page, check, "Bornheim")) return;
  await openLine(page);
  await page.click('#tab-area .info-button[data-info="area-overlay-land_value"]');
  const s = await page.evaluate(() => {
    const ids = [...document.querySelectorAll("[id]")].map((e) => e.id);
    return { area: document.getElementById("info-area-overlay-land_value")?.checkVisibility() ?? null,
      city: document.getElementById("info-overlay-land_value")?.hidden ?? null, unique: new Set(ids).size === ids.length,
      twice: ids.filter((id, i) => ids.indexOf(id) !== i) };
  });
  check(s.area === true && s.city === true, "details: the ⓘ opens its block in Gebiet only " + JSON.stringify(s));
  check(s.unique, "details: no id stands twice " + JSON.stringify(s.twice));
});

test.describe("a map link with an area", () => {
  test.use({ fragment: "#karte/zoom=15&center=50.12700,8.71200&level=quarter&area=Bornheim&layer=OWN_PUBLIC&overlays=townscape,flat_roofs" });
  test("a map link with an area sets the details line", async ({ mapPage: page, check }) => {
    const l = await line(page), want = [await shortName(page, "townscape"), await shortName(page, "flat_roofs")].join(", ");
    check(await page.evaluate(() => APP.state.area) === "Bornheim", "details: the link explores Bornheim");
    check(l && !l.open && l.names === want, `details: the names of the link (${want}) ` + JSON.stringify(l));
    const boxes = await checkedBoxes(page);
    check(JSON.stringify(boxes) === JSON.stringify(["tab-area:flat_roofs", "tab-area:townscape", "tab-city:flat_roofs", "tab-city:townscape"]),
      "details: both checkboxes of each overlay of the link are checked, no other " + JSON.stringify(boxes));
  });
});

test("without a profile no line", async ({ mapPage: page, check }) => {
  await page.evaluate(() => APP.openTab("area"));
  check(await page.evaluate((sel) => document.querySelector(sel) === null, LINE), "details: the note of an empty tab has no line");
});
