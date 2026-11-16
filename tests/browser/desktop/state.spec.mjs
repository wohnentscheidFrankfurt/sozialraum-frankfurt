// State transitions of setState (guard for the refactoring of web/js, recorded before it), each from a fresh page.
import { test } from "../fixtures.mjs";

// runs each step and records mode, level, indicator, the checked level radio and the layers on the map after it
const transitions = (page, steps) => page.evaluate((code) => { const rows = []; for (const step of code) { new Function(step)();
  rows.push({ mode: APP.state.mode, level: APP.state.level, indicator: APP.state.indicator,
    radio: document.querySelector('#tab-city input[name="level"]:checked')?.value,
    layer: Object.keys(APP.layers).filter((k) => APP.map.hasLayer(APP.layers[k])).join(",") }); } return rows; }, steps);

test("a layer of the districts stays through candidates on Stadtteile", async ({ mapPage: page, check }) => {
  // a layer that only exists on districts stays when the candidates switch to a template on Stadtteile and back
  const keep = await transitions(page, ["APP.setLevel('district')", "APP.setIndicator('SOC_INDEX')", "APP.openTab('candidates')",
    "APP.setTemplate('public_company')", "APP.openTab('city')"]);
  check(keep[3].mode === "candidates" && keep[3].level === "quarter" && keep[3].indicator === "SOC_INDEX",
    "candidates on Stadtteile keep the layer of the districts: " + JSON.stringify(keep[3]));
  check(keep[4].mode === "layer" && keep[4].level === "district" && keep[4].indicator === "SOC_INDEX" && keep[4].radio === "district"
    && keep[4].layer === "district", "back to the layers: the layer is on its own level again: " + JSON.stringify(keep[4]));
});

test("an indicator chosen in the candidates wins over the earlier level", async ({ mapPage: page, check }) => {
  // a layer chosen while the candidates are open wins over the level that the layers had before
  const wins = await transitions(page, ["APP.setLevel('district')", "APP.openTab('candidates')", "APP.setIndicator('OWN_COOP')",
    "APP.openTab('city')"]);
  check(wins[2].indicator === "OWN_COOP" && wins[2].level === "quarter" && wins[2].mode === "candidates",
    "indicator chosen in the candidates: " + JSON.stringify(wins[2]));
  check(wins[3].mode === "layer" && wins[3].level === "quarter" && wins[3].indicator === "OWN_COOP" && wins[3].radio === "quarter"
    && wins[3].layer === "quarter", "back to the layers: the indicator wins over the earlier level: " + JSON.stringify(wins[3]));
});
