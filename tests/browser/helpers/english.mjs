// Helpers of the English suite (english/*.spec.mjs): every state of the map whose text a reader can see.
import { frames, settle } from "./common.mjs";

// The visible text of the page now: the body, the labels of the buttons and figures, and the tips of the charts
export const pageText = (page) => page.evaluate(() => {
  const attrs = [...document.querySelectorAll("[aria-label],[title],[alt],[data-tip]")]
    .filter((e) => !e.closest("[hidden]"))
    .flatMap((e) => ["aria-label", "title", "alt", "data-tip"].map((a) => e.getAttribute(a)).filter(Boolean));
  return [document.body.innerText, ...attrs].join("\n");
});

// Open every ⓘ that is shut, so its protocol is visible
const openInfos = async (page) => {
  await page.evaluate(() => document.querySelectorAll(".info-button[aria-expanded=false]").forEach((b) => { if (b.offsetParent !== null) b.click(); }));
  await frames(page);
};

// Calls visit(name) after each state of the map has been set; name says which state
export const eachState = async (page, visit) => {
  const see = async (name) => { await openInfos(page); await visit(name, await pageText(page)); };
  for (const tab of ["city", "area", "candidates", "help"]) {
    await page.evaluate((t) => APP.openTab(t), tab);
    await settle(page);
    await see(`tab ${tab}`);
  }
  await page.evaluate(() => APP.openTab("city"));
  for (const id of await page.evaluate(() => Object.keys(APP.meta))) {
    await page.evaluate((i) => { const levels = APP.meta[i].levels; if (levels && !levels.includes(APP.state.level)) APP.setLevel(levels[0]); APP.setIndicator(i); }, id);
    await frames(page);
    await see(`layer ${id}`);
  }
  await page.evaluate(() => { for (const u of Object.values(APP.overlays)) u.on = true; APP.updateOverlays(); });
  await see("overlays on");
  await page.evaluate(() => { for (const u of Object.values(APP.overlays)) u.on = false; APP.updateOverlays(); });
  await page.evaluate(() => APP.openTab("candidates"));
  for (const id of await page.evaluate(() => APP.data.templates.map((t) => t.id))) {
    await page.evaluate((i) => APP.setTemplate(i), id);
    await frames(page);
    await see(`template ${id}`);
  }
  for (const level of ["district", "quarter"]) {
    await page.evaluate((l) => { APP.openTab("city"); APP.setLevel(l); const f = APP.data[l === "district" ? "districts" : "quarters"].features[0]; APP.explore(f.properties.id, { fly: false }); }, level);
    await settle(page);
    await see(`area ${level}`);
  }
  for (const view of ["history", "new_construction", "rent_burden"]) {
    await page.evaluate((v) => document.querySelector(`#views button[data-view="${v}"]`).click(), view);
    await settle(page);
    await see(`view ${view}`);
  }
};
