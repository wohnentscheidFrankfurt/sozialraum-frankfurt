// Direct links on a phone (docs/design.md, Direct links): a chart link lands on its figure; a tap on a view writes its
// fragment. Runs in webkit-iphone.
import { test } from "../fixtures.mjs";
import { openMap, settle, visibleCenter } from "../helpers/common.mjs";
import { drag, tap } from "../helpers/touch.mjs";

test.use({ fragment: "#trend/grosse-haeuser" });

test("a chart link lands on its figure, a tap on a view writes its fragment", async ({ mapPage: page, check }) => {
  const r = await page.evaluate(() => {
    const fig = document.getElementById("trend-grosse-haeuser"), view = document.getElementById("view-history");
    const f = fig.getBoundingClientRect(), v = view.getBoundingClientRect();
    return { shown: !view.hidden, top: f.top - Math.max(v.top, 0), height: Math.min(v.bottom, window.innerHeight) - Math.max(v.top, 0),
      scrolled: view.scrollTop > 0 || window.scrollY > 0 };
  });
  check(r.shown && r.scrolled && r.top > -2 && r.top < r.height / 2, "link: #trend/grosse-haeuser scrolls to its figure " + JSON.stringify(r));
  await tap(page, '#views button[data-view="new_construction"]');
  check(await page.evaluate(() => location.hash === "#" + APP.viewLink("new_construction")), "link: a tap on Neubau writes #neubau");
  await tap(page, '#views button[data-view="rent_burden"]');
  check(await page.evaluate(() => location.hash === "#" + APP.viewLink("rent_burden") && !document.getElementById("view-rent-burden").hidden), "link: a tap on Miete writes #miete");
});

test.describe("#miete/warmmiete-und-einkommen", () => {
  test.use({ fragment: "#miete/warmmiete-und-einkommen" });
  test("a chart link of Miete lands on its figure", async ({ mapPage: page, check }) => {
    const r = await page.evaluate(() => {
      const fig = document.getElementById(`${APP.viewLink("rent_burden")}-${APP.data.rent_burden.low_income.link}`), view = document.getElementById("view-rent-burden");
      if (!fig) return null;
      const f = fig.getBoundingClientRect(), v = view.getBoundingClientRect();
      return { shown: !view.hidden, top: f.top - Math.max(v.top, 0), height: Math.min(v.bottom, window.innerHeight) - Math.max(v.top, 0),
        scrolled: view.scrollTop > 0 || window.scrollY > 0 };
    });
    check(r && r.shown && r.scrolled && r.top > -2 && r.top < r.height / 2, "link: #miete/warmmiete-und-einkommen scrolls to its figure " + JSON.stringify(r));
  });
});

// A map link keeps the panel as it is: closed on a fresh load, so the map shows what the link is about
test.describe("#karte/…&area=Altstadt", () => {
  test.use({ fragment: "#karte/zoom=16.5&center=50.11040,8.68280&level=quarter&area=Altstadt&layer=ROOF_FLAT&overlays=flat_roofs" });
  test("a map link with an area leaves the panel closed", async ({ mapPage: page, check }) => {
    const r = await page.evaluate(() => ({ area: APP.state.area, zoom: APP.map.getZoom(), closed: APP.sidebar.classList.contains("closed"),
      tab: document.querySelector('#tabs button[data-tab="area"]').getAttribute("aria-pressed"),
      on: Object.keys(APP.overlays).filter((n) => APP.overlays[n].on), roofs: document.querySelectorAll("path.flat-roof").length }));
    check(r.area === "Altstadt" && r.zoom === 16.5 && r.closed && r.tab === "true", "link: Altstadt with the panel closed " + JSON.stringify(r));
    check(r.on.join() === "flat_roofs" && r.roofs > 0, "link: the overlays of the link are drawn " + JSON.stringify(r));
    // the centre of the link stands in the middle of the map above the closed panel
    const c = await visibleCenter(page);
    check(Math.abs(c[0] - 50.1104) < 2e-5 && Math.abs(c[1] - 8.6828) < 2e-5, "link: the centre of the link is the visible centre " + JSON.stringify(c));
  });
});

// A pan by touch writes the link; a desktop opens it with the same centre and zoom
test.describe("#karte, written by touch", () => {
  test.use({ fragment: "#karte" });
  test("a pan by touch writes the map link, a desktop opens the same map", async ({ mapPage: page, context, check }) => {
    check(await page.evaluate(() => location.hash) === "#karte", "link: a fresh phone keeps #karte");
    // near enough that a pixel is about a metre
    const before = await page.evaluate(() => { APP.map.setView([50.1104, 8.6828], 16, { animate: false }); return location.hash; });
    await drag(page, "#map", 120, 300, -150);
    await page.waitForTimeout(500);
    const a = await page.evaluate(() => ({ hash: location.hash, link: "#" + APP.mapLink(), zoom: APP.map.getZoom() }));
    check(a.hash !== before && a.hash.startsWith("#karte/zoom=16&") && a.hash === a.link, "link: the pan wrote the map link " + JSON.stringify([before, a]));
    const phone = await visibleCenter(page);
    const other = await openMap(context, a.hash, { width: 1280, height: 800 });
    const b = await other.evaluate(() => ({ zoom: APP.map.getZoom(), phone: APP.phone(), hash: location.hash }));
    const desktop = await visibleCenter(other);
    check(!b.phone && b.zoom === a.zoom && b.hash === a.hash, "link: the desktop opens the link " + JSON.stringify(b));
    check(Math.abs(desktop[0] - phone[0]) < 1e-4 && Math.abs(desktop[1] - phone[1]) < 1e-4, "link: the same visible centre " + JSON.stringify([phone, desktop]));
    await other.close();
  });
});

// A phone with the panel opened and closed by hand: the link follows the visible centre, a fresh page gets none
test.describe("#karte, panel by hand", () => {
  test.use({ fragment: "#karte" });
  test("opening and closing the panel moves the centre of the link with the visible centre", async ({ mapPage: page, check }) => {
    const centre = () => page.evaluate(() => location.hash.match(/center=([\d.]+),([\d.]+)/)?.slice(1).map(Number) ?? null);
    const near = (a, b) => a && b && Math.abs(a[0] - b[0]) < 1e-4 && Math.abs(a[1] - b[1]) < 1e-4;
    await tap(page, "#panel-toggle");
    await tap(page, "#panel-toggle");
    check(await page.evaluate(() => location.hash) === "#karte", "link: a fresh phone that opens and closes the panel keeps #karte");
    await page.evaluate(() => APP.map.setView([50.1104, 8.6828], 16, { animate: false }));
    await tap(page, "#panel-toggle");
    await tap(page, 'input[name="indicator"][value="OWN_COOP"]');
    const open = [await centre(), await visibleCenter(page)];
    check(near(...open) && await page.evaluate(() => location.hash.includes("&layer=OWN_COOP&")), "link: panel open, the visible centre " + JSON.stringify(open));
    await tap(page, "#panel-toggle");
    const closed = [await centre(), await visibleCenter(page), await page.evaluate(() => APP.sidebar.classList.contains("closed"))];
    check(closed[2] && near(closed[0], closed[1]), "link: panel closed, the visible centre " + JSON.stringify(closed));
  });
});

// Turning the phone crosses 700 px and back (docs/design.md, Map links): a fresh page writes no link, and a map link
// stays byte for byte. 844 x 390 is a phone in landscape, wider than the phone layout.
const LANDSCAPE = { width: 844, height: 390 };
// the resize, the frame of the phoneQuery handler and the debounced moveend of Leaflet
const turn = async (page, size) => { await page.setViewportSize(size); await settle(page); await page.waitForTimeout(400); };
for (const fragment of ["", "#karte"]) {
  test.describe(`turned, fresh ${fragment || "page"}`, () => {
    test.use({ fragment });
    test(`turning the phone keeps ${fragment || "no fragment"}`, async ({ mapPage: page, check }) => {
      const portrait = page.viewportSize(), hashes = [];
      for (const size of [LANDSCAPE, portrait]) {
        await turn(page, size);
        hashes.push(await page.evaluate(() => location.hash));
      }
      check(hashes.every((h) => h === fragment), `link: a turn writes no map link: ${JSON.stringify(hashes)}`);
    });
  });
}
test.describe("turned, a map link", () => {
  const link = "#karte/zoom=14&center=50.11040,8.68280&level=quarter&layer=OWN_PUBLIC&overlays=";
  test.use({ fragment: link });
  test("four turns keep the map link", async ({ mapPage: page, check }) => {
    const portrait = page.viewportSize(), hashes = [];
    for (let i = 0; i < 4; i++) {
      for (const size of [LANDSCAPE, portrait]) {
        await turn(page, size);
        hashes.push(await page.evaluate(() => location.hash));
      }
    }
    check(hashes.every((h) => h === link), `link: the turns keep the link: ${JSON.stringify(hashes)}`);
  });
});
