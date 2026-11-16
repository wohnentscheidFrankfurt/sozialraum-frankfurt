// Direct links (docs/design.md, Direct links): a fragment opens its view on a fresh page and scrolls to its figure.
// The fragments are the addresses of the links (part of the contract of the map), not texts of the map.
import { test } from "../fixtures.mjs";
import { openMap, settle, visibleCenter } from "../helpers/common.mjs";

const LINKS = ["karte", "trend", "trend/wem-gehoeren-die-wohnungen", "trend/wachstum-im-bestand", "trend/wer-waechst",
  "trend/grosse-haeuser", "neubau", "neubau/gefoerderte-wohnungen", "neubau/wohnungen-und-mieten", "miete", "miete/warmmiete-und-lohn",
  "miete/warmmiete-und-einkommen"];
const VIEW = { karte: "map", trend: "history", neubau: "new_construction", miete: "rent_burden" };

const shown = (page) => page.evaluate(() => ({
  view: [...document.querySelectorAll("#views button")].filter((b) => b.getAttribute("aria-pressed") === "true").map((b) => b.dataset.view).join(),
  map: !document.querySelector("main").hidden, history: !document.getElementById("view-history").hidden,
  construction: !document.getElementById("view-new-construction").hidden, rent: !document.getElementById("view-rent-burden").hidden, hash: location.hash }));

for (const link of LINKS) {
  test.describe(`#${link}`, () => {
    test.use({ fragment: "#" + link });
    test(`#${link} opens its view`, async ({ mapPage: page, check }) => {
      const [view, chart] = link.split("/"), s = await shown(page);
      check(s.view === VIEW[view] && s.map === (view === "karte") && s.history === (view === "trend")
        && s.construction === (view === "neubau") && s.rent === (view === "miete") && s.hash === "#" + link, `#${link} opens its view: ${JSON.stringify(s)}`);
      if (chart) {
        const r = await page.evaluate((id) => {
          const fig = document.getElementById(id), box = fig?.closest("section");
          if (!fig) return null;
          const f = fig.getBoundingClientRect(), v = box.getBoundingClientRect(), first = box.querySelector("figure") === fig;
          // only the last figure of a view may stay below the top, when the view stands at its end
          const last = [...box.querySelectorAll("figure")].at(-1) === fig;
          return { top: f.top - v.top, height: v.height, scrolled: box.scrollTop > 0, first, end: last && box.scrollTop + box.clientHeight >= box.scrollHeight - 1 };
        }, `${view}-${chart}`);
        check(r && r.top > -2 && (r.top < r.height / 2 || r.end) && (r.first || r.scrolled), `#${link} scrolls its figure to the top: ${JSON.stringify(r)}`);
      }
    });
  });
}

test.describe("from #trend", () => {
  test.use({ fragment: "#trend" });
  test("figure ids and the address bar", async ({ mapPage: page, check }) => {
    // every figure of the chart views has the id of its link, and no other figure has one
    const ids = await page.evaluate(() => { APP.openView("new_construction"); APP.openView("rent_burden"); return [...document.querySelectorAll("figure[id]")].map((f) => f.id); });
    check(JSON.stringify(ids) === JSON.stringify(LINKS.filter((l) => l.includes("/")).map((l) => l.replace("/", "-"))),
      "figure ids are the chart links: " + JSON.stringify(ids));
    // a click on a view writes its fragment; the map clears it while the map is as at the start, and writes its map
    // link once it has moved; a fragment of the same view keeps its chart
    await page.click('#views button[data-view="new_construction"]');
    const a = await page.evaluate(() => location.hash);
    await page.click('#views button[data-view="map"]');
    const b = await page.evaluate(() => location.href.includes("#"));
    await page.evaluate(() => APP.map.panBy([200, 0], { animate: false }));
    await page.click('#views button[data-view="new_construction"]');
    await page.click('#views button[data-view="map"]');
    const e = await page.evaluate(() => location.hash.startsWith("#karte/zoom=") && location.hash === "#" + APP.mapLink());
    await page.evaluate(() => { location.hash = "#trend/grosse-haeuser"; });
    await page.waitForFunction(() => !document.getElementById("view-history").hidden);
    await page.click('#views button[data-view="history"]');
    const c = await page.evaluate(() => location.hash);
    // a link followed on a loaded page (hashchange) and back to the top of the view
    await page.evaluate(() => { location.hash = "#neubau/wohnungen-und-mieten"; });
    await page.waitForFunction(() => !document.getElementById("view-new-construction").hidden);
    const d = await page.evaluate(() => document.getElementById("view-new-construction").scrollTop > 0);
    await page.evaluate(() => { location.hash = "#neubau"; });
    await page.waitForFunction(() => document.getElementById("view-new-construction").scrollTop === 0);
    check(a === "#neubau" && b === false && e && c === "#trend/grosse-haeuser" && d,
      "the address bar follows the view: " + JSON.stringify([a, b, e, c, d]));
  });
});

// an unknown fragment starts the map as without one; an unknown chart opens its view at the top, and the address
// bar then names only the view
for (const [link, view, hash] of [["unbekannt", "map", "#unbekannt"], ["trend/unbekannt", "history", "#trend"], ["", "map", ""]]) {
  test.describe(`#${link}`, () => {
    test.use({ fragment: "#" + link });
    test(`#${link} starts on ${view}`, async ({ mapPage: page, check }) => {
      const s = await shown(page);
      const top = await page.evaluate(() => document.getElementById("view-history").scrollTop);
      check(s.view === view && s.hash === hash && top === 0, `#${link} starts on ${view}: ${JSON.stringify([s, top])}`);
    });
  });
}

test.describe("from #unbekannt", () => {
  test.use({ fragment: "#unbekannt" });
  test("Karte clears the fragment, Zurück shows the map", async ({ mapPage: page, check }) => {
    // a click on Karte clears an unknown fragment; „Zurück“ to no fragment shows the map again
    await page.click('#views button[data-view="map"]');
    const a = await page.evaluate(() => location.href.includes("#"));
    await page.evaluate(() => { location.hash = "#trend/grosse-haeuser"; });
    await page.waitForFunction(() => !document.getElementById("view-history").hidden);
    await page.evaluate(() => history.back());
    await page.waitForFunction(() => !location.hash);
    await page.evaluate(() => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r))));
    const s = await shown(page);
    check(a === false && s.view === "map" && s.map && !s.history, "Karte clears the fragment, Zurück shows the map: " + JSON.stringify([a, s]));
  });
});

// Map links (docs/design.md, Direct links): #karte/zoom=…&center=…&level=…&area=…&layer=…&overlays=… opens the map as
// the sender saw it. Keys, levels, layer ids and overlay names are addresses (part of the contract of the map).
const mapState = (page) => page.evaluate(() => ({
  zoom: APP.map.getZoom(), center: [APP.map.getCenter().lat, APP.map.getCenter().lng],
  inCity: APP.layers.district.getBounds().contains(APP.map.getCenter()),
  level: APP.state.level, layer: APP.state.indicator, mode: APP.state.mode, area: APP.state.area,
  on: Object.keys(APP.overlays).filter((n) => APP.overlays[n].on),
  checked: [...document.querySelectorAll("#tab-city input[data-overlay]:checked")].map((c) => c.dataset.overlay),
  tab: [...document.querySelectorAll("#tabs button[data-tab]")].filter((b) => b.getAttribute("aria-pressed") === "true").map((b) => b.dataset.tab).join(),
  cityTab: document.getElementById("tab-city").classList.contains("active"),
  areaTab: document.getElementById("tab-area").classList.contains("active"),
  note: !APP.switchDiv.hidden, map: !document.querySelector("main").hidden, hash: location.hash }));
const near = (a, b) => Math.abs(a[0] - b[0]) < 1e-5 && Math.abs(a[1] - b[1]) < 1e-5;
const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);
// the zoom of the start fit: all Bezirke above the phone panel (99_start.js)
const startZoom = (page) => page.evaluate(() => APP.map.getBoundsZoom(APP.layers.district.getBounds(), false, L.point(0, APP.panelHeight())));

test.describe("map links", () => {
  test.describe("position, level, layer, overlays", () => {
    const link = "#karte/zoom=16&center=50.10712,8.66380&level=quarter&layer=ROOF_FLAT&overlays=social_preservation,flat_roofs";
    test.use({ fragment: link });
    test("a map link opens the map as the sender saw it", async ({ mapPage: page, check }) => {
      const s = await mapState(page);
      const roofs = await page.evaluate(() => document.querySelectorAll("path.flat-roof").length);
      check(s.map && s.zoom === 16 && near(s.center, [50.10712, 8.6638]) && s.level === "quarter" && s.layer === "ROOF_FLAT"
        && s.mode === "layer" && s.area === null && s.tab === "city" && s.cityTab, "link: position, level and layer " + JSON.stringify(s));
      check(same(s.on, ["social_preservation", "flat_roofs"]) && same(s.checked, ["social_preservation", "flat_roofs"]), "link: exactly the overlays of the link " + JSON.stringify(s));
      check(roofs > 0, "link: the flat roofs are drawn: " + roofs);
      check(s.hash === link, "link: the address bar keeps the link " + s.hash);
    });
  });

  test.describe("area", () => {
    const link = "#karte/zoom=16.5&center=50.11040,8.68280&level=quarter&area=Altstadt&layer=ROOF_FLAT&overlays=flat_roofs";
    test.use({ fragment: link });
    test("a map link with an area explores it at the zoom of the link", async ({ mapPage: page, check }) => {
      const a = await mapState(page);
      check(a.area === "Altstadt" && a.tab === "area" && a.areaTab && a.layer === "ROOF_FLAT" && same(a.on, ["flat_roofs"]), "link: explores Altstadt " + JSON.stringify(a));
      await page.waitForTimeout(1000);
      const b = await mapState(page);
      check(b.zoom === 16.5 && near(b.center, [50.1104, 8.6828]), "link: no flight, the zoom of the link stays " + JSON.stringify(b));
      check(b.hash === link, "link: the address bar keeps the link " + b.hash);
      await page.click('#tabs button[data-tab="city"]');
      const c = await mapState(page), zoom = await startZoom(page);
      check(c.area === null && c.tab === "city" && c.zoom === zoom && c.inCity, `link: Stadt shows the whole city (zoom ${zoom}) ` + JSON.stringify(c));
    });
  });

  // a Bezirk links by its number, which holds slashes: encoded or decoded, it is the same area
  for (const area of ["40%2F50%2F60", "40/50/60"]) {
    test.describe(`Bezirk ${area}`, () => {
      test.use({ fragment: `#karte/zoom=15&center=50.10330,8.66210&level=district&area=${area}&layer=SOC_MIN_INCOME&overlays=` });
      test(`area=${area} explores the Bezirk 40/50/60`, async ({ mapPage: page, check }) => {
        const s = await mapState(page);
        check(s.area === "40/50/60" && s.level === "district" && s.layer === "SOC_MIN_INCOME" && s.tab === "area" && same(s.on, []),
          `link: area=${area} explores 40/50/60 ` + JSON.stringify(s));
        check(s.hash === "#karte/zoom=15&center=50.10330,8.66210&level=district&area=40%2F50%2F60&layer=SOC_MIN_INCOME&overlays=", "link: the clean link " + s.hash);
      });
    });
  }

  // messengers encode parts of a link and glue punctuation to its end
  const clean = "#karte/zoom=16&center=50.10712,8.66380&level=quarter&area=Westend-S%C3%BCd&layer=ROOF_FLAT&overlays=social_preservation,flat_roofs";
  for (const link of [
    "#karte/zoom=16&center=50.10712,8.66380&level=quarter&area=Westend-S%C3%BCd&layer=ROOF_FLAT&overlays=social_preservation%2Cflat_roofs",
    "#karte/zoom=16&center=50.10712%2C8.66380&level=quarter&area=Westend-Süd&layer=ROOF_FLAT&overlays=social_preservation,flat_roofs.",
    "#karte/zoom%3D16&center=50.10712,8.66380&level=quarter&area=Westend-S%C3%BCd&layer=ROOF_FLAT&overlays=social_preservation,flat_roofs).",
  ]) {
    test.describe(`messenger ${link}`, () => {
      test.use({ fragment: link });
      test(`${link} opens the same map`, async ({ mapPage: page, check }) => {
        const s = await mapState(page);
        check(s.zoom === 16 && near(s.center, [50.10712, 8.6638]) && s.area === "Westend-Süd" && s.layer === "ROOF_FLAT"
          && same(s.on, ["social_preservation", "flat_roofs"]), "link: the same state " + JSON.stringify(s));
        check(s.hash === clean, "link: the address bar holds the clean link " + s.hash);
      });
    });
  }

  test.describe("defaults and drops", () => {
    test.use({ fragment: "#karte/layer=NOPE&zoom=99&center=0,0&foo=bar&area=Nirgendwo" });
    test("unknown keys and ids are dropped, the zoom is clamped", async ({ mapPage: page, check }) => {
      const s = await mapState(page);
      check(s.layer === "OWN_PUBLIC" && s.zoom === 19 && s.inCity && s.area === null && s.tab === "city"
        && same(s.on, ["social_preservation", "social_preservation_pending"]), "link: defaults " + JSON.stringify(s));
      check(s.hash.startsWith("#karte/zoom=19&center=") && !/foo|NOPE|Nirgendwo|area=/.test(s.hash), "link: the clean link " + s.hash);
    });
  });

  // from Bezirke: a link that set the level first would switch the layer and write a note
  test.describe("level the layer lacks", () => {
    test.use({ fragment: "#karte" });
    test("the layer wins over the level, without a note", async ({ mapPage: page, check }) => {
      await page.evaluate(() => { APP.setIndicator("HOU_RENTERS"); APP.setLevel("district"); });
      const a = await mapState(page);
      await page.evaluate(() => { location.hash = "#karte/level=district&layer=OWN_PUBLIC"; });
      await page.waitForFunction(() => APP.state.indicator !== "HOU_RENTERS");
      const s = await mapState(page);
      check(a.level === "district" && a.layer === "HOU_RENTERS", "link: Bezirke before " + JSON.stringify(a));
      check(s.level === "quarter" && s.layer === "OWN_PUBLIC" && !s.note, "link: OWN_PUBLIC shows Stadtteile " + JSON.stringify(s));
    });
  });

  // a Stadtteil on a page of Bezirke: the area exists on the level shown, so it stays
  test.describe("Stadtteil from Bezirke", () => {
    test.use({ fragment: "#karte" });
    test("a Stadtteil link on a page of Bezirke explores the Stadtteil", async ({ mapPage: page, check }) => {
      await page.evaluate(() => { APP.setIndicator("SOC_MIN_INCOME"); APP.setLevel("district"); });
      const a = await mapState(page);
      await page.evaluate(() => { location.hash = "#karte/area=Altstadt&layer=OWN_PUBLIC"; });
      await page.waitForFunction(() => APP.state.indicator === "OWN_PUBLIC");
      const b = await mapState(page);
      check(a.level === "district" && a.layer === "SOC_MIN_INCOME", "link: Bezirke before " + JSON.stringify(a));
      check(b.level === "quarter" && b.area === "Altstadt" && b.layer === "OWN_PUBLIC" && b.tab === "area" && !b.note,
        "link: Altstadt explored on Stadtteile " + JSON.stringify(b));
    });
  });

  // a Bezirk on a layer of Stadtteile only: the link explores the Stadtteil of the Bezirk, as a switch of the level would
  test.describe("Bezirk on a layer of Stadtteile", () => {
    test.use({ fragment: "#karte/zoom=15&center=50.11040,8.68280&level=district&area=10&layer=OWN_PUBLIC&overlays=" });
    test("the link explores the Stadtteil of Bezirk 10", async ({ mapPage: page, check }) => {
      const s = await mapState(page);
      check(s.level === "quarter" && s.area === "Altstadt" && s.layer === "OWN_PUBLIC" && s.tab === "area" && !s.note && s.zoom === 15,
        "link: Bezirk 10 explores Altstadt " + JSON.stringify(s));
      check(s.hash === "#karte/zoom=15&center=50.11040,8.68280&level=quarter&area=Altstadt&layer=OWN_PUBLIC&overlays=", "link: the clean link " + s.hash);
    });
  });

  test.describe("share of a list", () => {
    test.use({ fragment: "#karte/layer=ELEC_SPD" });
    test("a list share checks the row of the list", async ({ mapPage: page, check }) => {
      const r = await page.evaluate(() => ({ layer: APP.state.indicator,
        radio: document.querySelector('input[name="indicator"]:checked')?.value, list: document.getElementById("list-choice").value }));
      check(r.layer === "ELEC_SPD" && r.radio === "ELEC_LIST" && r.list === "ELEC_SPD", "link: ELEC_SPD " + JSON.stringify(r));
    });
  });

  test.describe("parse", () => {
    test.use({ fragment: "#karte" });
    test("parseMapLink keeps known values and drops the rest", async ({ mapPage: page, check }) => {
      const r = await page.evaluate(() => Object.fromEntries([
        "level=quarter", "level=district", "level=Bezirke", "level=constructor", "layer=constructor", "zoom=5", "zoom=15.5", "zoom=", "zoom=abc", "center=50.1,8.6", "center=50.1",
        "overlays=", "overlays=flat_roofs,nope,social_preservation", "layer=ELEC_LIST", "area=%E0%A4%A", "area=Gallus&foo=1", "area=213",
        "level=district&area=213&layer=SOC_MIN_INCOME", "level=district&area=10&layer=OWN_PUBLIC", "level=district&area=Altstadt&layer=OWN_PUBLIC", "",
      ].map((t) => [t, APP.parseMapLink(t)])));
      const want = {
        "level=quarter": { level: "quarter" }, "level=district": { level: "district" }, "level=Bezirke": {}, "level=constructor": {}, "layer=constructor": {}, "zoom=5": { zoom: 10 },
        "zoom=15.5": { zoom: 15.5 }, "zoom=": {}, "zoom=abc": {}, "center=50.1,8.6": { center: [50.1, 8.6] }, "center=50.1": {},
        "overlays=": { overlays: [] }, "overlays=flat_roofs,nope,social_preservation": { overlays: ["social_preservation", "flat_roofs"] },
        "layer=ELEC_LIST": {}, "area=%E0%A4%A": {}, "area=Gallus&foo=1": { area: "Gallus" }, "area=213": {},
        "level=district&area=213&layer=SOC_MIN_INCOME": { level: "district", area: "213", indicator: "SOC_MIN_INCOME" },
        "level=district&area=10&layer=OWN_PUBLIC": { level: "district", area: "Altstadt", indicator: "OWN_PUBLIC" },
        "level=district&area=Altstadt&layer=OWN_PUBLIC": { level: "district", area: "Altstadt", indicator: "OWN_PUBLIC" }, "": {},
      };
      for (const [t, w] of Object.entries(want)) check(same(r[t], w), `parse ${JSON.stringify(t)}: ${JSON.stringify(r[t])}, want ${JSON.stringify(w)}`);
    });
  });

  test.describe("hashchange", () => {
    test.use({ fragment: "#karte" });
    test("a map link on a loaded page ends the candidates and exploring", async ({ mapPage: page, check }) => {
      await page.evaluate(() => { APP.openTab("candidates"); APP.setTemplate("coop"); APP.explore("Gallus"); });
      const a = await mapState(page);
      await page.evaluate(() => { location.hash = "#karte/zoom=13&center=50.11000,8.68000&level=quarter&layer=OWN_COOP&overlays="; });
      await page.waitForFunction(() => APP.state.indicator === "OWN_COOP");
      const b = await mapState(page);
      check(a.mode === "candidates" && a.area === "Gallus", "link: candidates and Gallus before " + JSON.stringify(a));
      check(b.area === null && b.mode === "layer" && b.tab === "city" && b.cityTab && same(b.on, []) && b.zoom === 13
        && near(b.center, [50.11, 8.68]), "link: hashchange applies the link " + JSON.stringify(b));
    });

    // the candidates of Milieuschutz work on Bezirke; the layers came from Stadtteile, so the link explores a Stadtteil
    test("a map link on candidates of Bezirke explores on the level of the layers", async ({ mapPage: page, check }) => {
      await page.evaluate(() => { APP.openTab("candidates"); APP.setTemplate("social_preservation"); APP.explore("10"); });
      const a = await mapState(page);
      const parsed = await page.evaluate(() => [APP.parseMapLink("area=Altstadt&layer=SOC_MIN_INCOME"), APP.parseMapLink("area=10&layer=SOC_MIN_INCOME")]);
      check(same(parsed, [{ area: "Altstadt", indicator: "SOC_MIN_INCOME" }, { indicator: "SOC_MIN_INCOME" }]),
        "parse: the area lies on the level of the layers " + JSON.stringify(parsed));
      await page.evaluate(() => { location.hash = "#karte/zoom=15&center=50.11040,8.68280&area=Altstadt&layer=SOC_MIN_INCOME"; });
      await page.waitForFunction(() => APP.state.mode === "layer");
      const b = await mapState(page);
      check(a.mode === "candidates" && a.level === "district" && a.area === "10", "link: candidates on Bezirke with 10 before " + JSON.stringify(a));
      check(b.mode === "layer" && b.level === "quarter" && b.area === "Altstadt" && b.layer === "SOC_MIN_INCOME" && b.tab === "area" && b.zoom === 15,
        "link: Altstadt explored on Stadtteile " + JSON.stringify(b));
    });
  });
});

// Writing (docs/design.md, Direct links): the address bar holds the link of the map shown, written with replaceState
test.describe("writing map links", () => {
  // a resize or the fonts move nothing: a fresh page keeps its fragment
  for (const fragment of ["", "#karte"]) {
    test.describe(`fresh ${fragment || "page"}`, () => {
      test.use({ fragment });
      test(`a resize keeps ${fragment || "no fragment"}`, async ({ mapPage: page, check }) => {
        await page.evaluate(() => APP.map.invalidateSize());
        await page.setViewportSize({ width: 1100, height: 700 });
        await settle(page);
        await page.setViewportSize({ width: 1400, height: 900 });
        await settle(page);
        const hash = await page.evaluate(() => location.hash);
        check(hash === fragment, `link: a resize writes no map link: ${JSON.stringify(hash)}`);
      });
    });
  }

  test.describe("the address bar follows the map", () => {
    test.use({ fragment: "#karte" });
    test("pan, overlay, layer, area", async ({ mapPage: page, check }) => {
      const length = await page.evaluate(() => history.length);
      await page.evaluate(() => APP.map.panBy([200, 0], { animate: false }));
      const a = await mapState(page);
      check(a.hash.startsWith("#karte/zoom=") && a.hash === "#" + await page.evaluate(() => APP.mapLink()), "link: a pan writes the map link " + a.hash);
      await page.click('#tab-city input[data-overlay="townscape"]');
      const b = await mapState(page);
      check(b.hash.endsWith("&overlays=social_preservation,social_preservation_pending,townscape"), "link: an overlay joins in order " + b.hash);
      await page.click('input[name="indicator"][value="OWN_COOP"]');
      const c = await mapState(page);
      check(c.hash.includes("&layer=OWN_COOP&"), "link: the layer Genossenschaften " + c.hash);
      await page.evaluate(() => APP.explore("Altstadt"));
      await page.waitForTimeout(1000); // the flight
      const d = await mapState(page);
      check(d.hash.includes("&level=quarter&area=Altstadt&layer=OWN_COOP&") && d.hash === "#" + await page.evaluate(() => APP.mapLink()),
        "link: exploring writes the area and the landed view " + d.hash);
      await page.click('#tabs button[data-tab="city"]');
      const e = await mapState(page);
      check(!e.hash.includes("area=") && e.hash.includes("&layer=OWN_COOP&"), "link: Stadt removes the area " + e.hash);
      check(await page.evaluate(() => history.length) === length, "link: no history entry");
    });

    test("ten pans add no history entry", async ({ mapPage: page, check }) => {
      const length = await page.evaluate(() => history.length);
      for (let i = 0; i < 10; i++) await page.evaluate((i) => APP.map.panBy([i % 2 ? -50 : 60, 20], { animate: false }), i);
      const r = await page.evaluate(() => ({ length: history.length, hash: location.hash, link: "#" + APP.mapLink() }));
      check(r.length === length && r.hash === r.link, `link: ten pans, no history entry: ${length} ${JSON.stringify(r)}`);
    });
  });

  test.describe("round trip", () => {
    test.use({ fragment: "#karte" });
    test("a written link opens the same map in a new page", async ({ mapPage: page, context, check }) => {
      await page.click('#tab-city input[data-overlay="flat_roofs"]');
      await page.click('input[name="indicator"][value="ROOF_FLAT"]');
      await page.evaluate(() => APP.explore("Altstadt"));
      await page.waitForTimeout(1000); // the flight
      await page.evaluate(() => APP.map.setView([50.1105, 8.6825], 16, { animate: false }));
      const a = await mapState(page);
      const other = await openMap(context, a.hash);
      const b = await mapState(other);
      check(a.zoom === 16 && a.area === "Altstadt" && a.layer === "ROOF_FLAT", "link: the sender " + JSON.stringify(a));
      check(b.zoom === a.zoom && near(b.center, a.center) && b.level === a.level && b.area === a.area && b.layer === a.layer
        && same(b.on, a.on) && b.hash === a.hash, "link: the receiver sees the same map " + JSON.stringify([a, b]));
      check(near(await visibleCenter(other), await visibleCenter(page)), "link: the same visible centre");
      await other.close();
    });
  });
});
