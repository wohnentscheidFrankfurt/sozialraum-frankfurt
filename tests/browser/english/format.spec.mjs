// English number format in the tooltip and the ⓘ of three layers: 1,754 and 6.6% and €1,200, never 1.754 or 6,6 %.
// The tooltip opens through the map's own handler (APP.tipPoint, APP.showTip), so the same test runs with touch.
import { test } from "../fixtures.mjs";
import { paths } from "../helpers/common.mjs";

test.use({ mapHtml: paths.mapHtmlEn });

const GALLUS = [50.1001, 8.6366];
// the tooltip and the open ⓘ of a layer on a level, as text
const textsOf = (page, level, layer) => page.evaluate(([l, id, [lat, lng]]) => {
  APP.openTab("city"); APP.setLevel(l); APP.setIndicator(id);
  APP.map.setView([lat, lng], 13, { animate: false });
  APP.tipPoint = L.latLng(lat, lng); APP.showTip();
  const button = document.querySelector(`.info-button[data-info="${id}"]`);
  if (button && button.getAttribute("aria-expanded") === "false") button.click();
  return { tip: document.querySelector(".leaflet-tooltip")?.textContent, info: document.getElementById(`info-${id}`)?.textContent };
}, [level, layer, GALLUS]);

// German format: a point before three digits, a comma before decimals or a space before the percent sign
const GERMAN_FORMAT = /\d\.\d{3}(?!\d)|\d,\d{1,2}(?!\d)|\d %/;

const LAYERS = [
  // quarter layer with a share and a dwelling count (~24.9%, ~5,700; the ⓘ example ~3,336 and ~29.3%)
  { level: "quarter", id: "OWN_PUBLIC", tip: [/\d\.\d%/, /\d,\d{3}/], info: [/\d\.\d%/, /\d,\d{3}/] },
  // quarter layer with a count (1,754 dwellings)
  { level: "quarter", id: "SH_COUNT", tip: [/\d,\d{3} dwellings/], info: [] },
  // district layer with euros (€1,600/m²); its ⓘ has a date (1 January 2026)
  { level: "district", id: "LAND_VALUE", tip: [/€\d,\d{3}\/m²/], info: [/\d{1,2} [A-Z][a-z]+ \d{4}/] },
];
for (const { level, id, tip, info } of LAYERS) {
  test(`${id}: tooltip and ⓘ in English format`, async ({ mapPage: page, check }) => {
    const got = await textsOf(page, level, id);
    check(got.tip, `${id}: a tooltip opens`);
    for (const re of tip) check(re.test(got.tip), `${id}: tooltip matches ${re}: ${got.tip}`);
    check(!GERMAN_FORMAT.test(got.tip), `${id}: no German number format in the tooltip: ${got.tip}`);
    if (info.length || got.info) {
      check(got.info, `${id}: the ⓘ opens`);
      for (const re of info) check(re.test(got.info), `${id}: ⓘ matches ${re}: ${got.info?.slice(0, 300)}`);
      check(!GERMAN_FORMAT.test(got.info ?? ""), `${id}: no German number format in the ⓘ: ${got.info?.slice(0, 300)}`);
    }
  });
}
