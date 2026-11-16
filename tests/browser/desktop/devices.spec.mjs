// Map links across devices (docs/design.md, Direct links): one Chrome page switches between a phone and a desktop
// through the DevTools protocol (CDP), in place and as a fresh receiver. The link names the centre of the visible map,
// so both devices show the same place. Runs in desktop-chrome. Playwright's page.screenshot ignores the CDP metrics:
// a screenshot here would need Page.captureScreenshot.
import { test } from "../fixtures.mjs";
import { paths, settle } from "../helpers/common.mjs";
import { pathToFileURL } from "node:url";

const PHONE = { width: 390, height: 844, deviceScaleFactor: 3, mobile: true };
const DESKTOP = { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false };
const AGENT = {
  phone: "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1",
  desktop: "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36",
};
const OVERLAYS = ["social_preservation", "flat_roofs"];

const setDevice = async (cdp, d) => {
  await cdp.send("Emulation.setDeviceMetricsOverride", d);
  // maxTouchPoints 0 is a protocol error: switch touch off with enabled alone
  await cdp.send("Emulation.setTouchEmulationEnabled", d.mobile ? { enabled: true, maxTouchPoints: 5 } : { enabled: false });
  await cdp.send("Emulation.setUserAgentOverride", { userAgent: d.mobile ? AGENT.phone : AGENT.desktop });
};
// a fresh load: about:blank first, else the same URL with another fragment is only a hashchange
const open = async (page, fragment) => {
  await page.goto("about:blank");
  await page.goto(pathToFileURL(paths.mapHtml).href + fragment);
  await page.waitForFunction(() => window.APP && window.APP.ready);
  await page.evaluate(() => document.fonts.ready);
  await settle(page);
};
// after a device switch: the resize, the panel and the debounced moveend of Leaflet
const switched = (page) => page.waitForTimeout(800);

const state = (page) => page.evaluate(() => {
  const m = APP.map.getContainer().getBoundingClientRect(), s = APP.sidebar.getBoundingClientRect();
  // the centre of the map above the panel, from the exact centre of Leaflet (helpers/common.mjs, visibleCenter)
  const bottom = APP.phone() ? Math.min(m.bottom, s.top) : m.bottom, zoom = APP.map.getZoom();
  const c = APP.map.unproject(APP.map.project(APP.map.getCenter(), zoom).subtract([0, (m.bottom - bottom) / 2]), zoom);
  return { zoom: APP.map.getZoom(), center: [c.lat, c.lng], level: APP.state.level, area: APP.state.area, layer: APP.state.indicator,
    on: Object.keys(APP.overlays).filter((n) => APP.overlays[n].on), roofs: document.querySelectorAll("path.flat-roof").length,
    tab: document.querySelector('#tabs button[data-tab="area"]').getAttribute("aria-pressed"), closed: APP.sidebar.classList.contains("closed"),
    phone: APP.phone(), touch: APP.touch(), hash: location.hash };
});
const near = (a, b, d = 1e-4) => Math.abs(a[0] - b[0]) < d && Math.abs(a[1] - b[1]) < d;
// center of the link as [lat, lng]
const linkCenter = (hash) => hash.match(/center=([\d.]+),([\d.]+)/).slice(1).map(Number);

test.describe("devices", () => {
  let link, center;
  test.beforeEach(async ({ page }) => {
    await open(page, "#karte");
    // Altstadt explored, at the centre of its bounds, zoom 16, flat roofs and Milieuschutz
    center = await page.evaluate(() => {
      let b;
      APP.layers.quarter.eachLayer((l) => { if (l.feature.properties.id === "Altstadt") b = l.getBounds(); });
      return [Number(b.getCenter().lat.toFixed(5)), Number(b.getCenter().lng.toFixed(5))];
    });
    link = `#karte/zoom=16&center=${center[0].toFixed(5)},${center[1].toFixed(5)}&level=quarter&area=Altstadt&layer=ROOF_FLAT&overlays=${OVERLAYS.join(",")}`;
  });

  // one state on one device; closed: the expected panel state on the phone (undefined on the desktop)
  const expectShown = (check, s, where, { phone, closed, at = center }) => {
    check(s.phone === phone && s.touch === phone, `${where}: the device ${JSON.stringify(s)}`);
    check(s.zoom === 16 && near(s.center, at) && s.level === "quarter" && s.area === "Altstadt" && s.layer === "ROOF_FLAT"
      && s.on.join() === OVERLAYS.join() && s.roofs > 0 && s.tab === "true", `${where}: the map of the link ${JSON.stringify(s)}`);
    if (phone) check(s.closed === closed, `${where}: the panel ${closed ? "closed" : "open"} ${JSON.stringify(s)}`);
  };

  test("desktop, then a phone in place, then a fresh phone", async ({ page, check }) => {
    const cdp = await page.context().newCDPSession(page);
    await setDevice(cdp, DESKTOP);
    await open(page, link);
    expectShown(check, await state(page), "desktop", { phone: false });
    await setDevice(cdp, PHONE);
    await switched(page);
    // the panel keeps its state: open, as beside the map on the desktop
    expectShown(check, await state(page), "phone in place", { phone: true, closed: false });
    await open(page, link);
    expectShown(check, await state(page), "fresh phone", { phone: true, closed: true });
    await cdp.detach();
  });

  test("phone, then a desktop in place, then a fresh desktop", async ({ page, check }) => {
    const cdp = await page.context().newCDPSession(page);
    await setDevice(cdp, PHONE);
    await open(page, link);
    expectShown(check, await state(page), "phone", { phone: true, closed: true });
    await setDevice(cdp, DESKTOP);
    await switched(page);
    expectShown(check, await state(page), "desktop in place", { phone: false });
    await open(page, link);
    expectShown(check, await state(page), "fresh desktop", { phone: false });
    await cdp.detach();
  });

  test("a link written on the phone with the panel open opens on a desktop", async ({ page, check }) => {
    const cdp = await page.context().newCDPSession(page);
    await setDevice(cdp, PHONE);
    await open(page, link);
    await page.click("#panel-toggle");
    await settle(page);
    await page.evaluate(() => APP.map.panBy([0, 80], { animate: false }));
    const a = await state(page);
    check(!a.closed && a.hash !== link && near(linkCenter(a.hash), a.center, 2e-5), "phone: the written link names the visible centre " + JSON.stringify(a));
    await setDevice(cdp, DESKTOP);
    await open(page, a.hash);
    expectShown(check, await state(page), "fresh desktop", { phone: false, at: a.center });
    await cdp.detach();
  });

  test("the panel opened and closed by hand on the phone moves the centre of the link", async ({ page, check }) => {
    const cdp = await page.context().newCDPSession(page);
    await setDevice(cdp, PHONE);
    await open(page, link);
    for (const [step, closed] of [["open", false], ["closed", true]]) {
      await page.click("#panel-toggle");
      await settle(page);
      const s = await state(page);
      check(s.closed === closed && near(linkCenter(s.hash), s.center), `phone, panel ${step}: the link names the visible centre ${JSON.stringify(s)}`);
    }
    await cdp.detach();
  });

  test("a link written on the desktop opens on a phone with the panel closed and open", async ({ page, check }) => {
    const cdp = await page.context().newCDPSession(page);
    await setDevice(cdp, DESKTOP);
    await open(page, link);
    await page.evaluate(() => APP.map.panBy([0, 80], { animate: false }));
    const a = await state(page);
    check(a.hash !== link && near(linkCenter(a.hash), a.center, 2e-5), "desktop: the written link names the centre " + JSON.stringify(a));
    await setDevice(cdp, PHONE);
    await open(page, a.hash);
    expectShown(check, await state(page), "fresh phone", { phone: true, closed: true, at: a.center });
    // the same link followed on a phone with the panel open: by way of Trend, so the fragment changes
    await page.click("#panel-toggle");
    await page.evaluate(() => { location.hash = "#trend"; });
    await page.waitForFunction(() => !document.getElementById("view-history").hidden);
    await page.evaluate((hash) => { location.hash = hash; }, a.hash);
    await page.waitForFunction(() => !document.querySelector("main").hidden);
    await settle(page);
    expectShown(check, await state(page), "phone with the panel open", { phone: true, closed: false, at: a.center });
    await cdp.detach();
  });
});

// A desktop window narrowed below 700 px turns on the phone layout and back (docs/design.md, Map links). A fresh page
// writes no link, and a map link stays byte for byte, however often the window crosses.
test.describe("window across 700 px", () => {
  const resized = async (page) => {
    const hashes = [];
    for (const width of [1280, 650, 1280, 650, 1280]) {
      await page.setViewportSize({ width, height: 800 });
      await settle(page);
      await switched(page);
      hashes.push(await page.evaluate(() => location.hash));
    }
    return hashes;
  };
  for (const fragment of ["", "#karte/zoom=14&center=50.11040,8.68280&level=quarter&layer=OWN_PUBLIC&overlays="]) {
    test(`a resize across 700 px keeps ${fragment || "no fragment"}`, async ({ page, check }) => {
      await open(page, fragment);
      const hashes = await resized(page);
      check(hashes.every((h) => h === fragment), `resize: the address bar stays ${JSON.stringify(hashes)}`);
    });
  }
});
