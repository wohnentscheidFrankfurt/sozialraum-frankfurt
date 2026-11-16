// Screenshots of fixed states, to look at. They are files under SCREENS, no assertions.
// The assertion of this test is the guard of the fixture: no console error and no page error in these states.
import { test } from "../fixtures.mjs";

test("screenshots of fixed states", async ({ mapPage: page, saveScreenshot }) => {
  // tab Stadt on the district level, so a layer that has districts shows them
  await page.evaluate(() => { APP.openTab("city"); APP.setLevel("district"); });
  for (const id of ["OWN_PUBLIC", "OWN_COOP", "OWN_COMPANY", "SOC_MIN_INCOME", "HOU_RENT", "LAND_VALUE", "ELEC_STRONGEST"]) {
    await page.evaluate((k) => { APP.openTab("city"); APP.setIndicator(k); }, id);
    await saveScreenshot(`layer_${id}`);
  }
  for (const template of ["social_preservation", "coop", "public_company"]) {
    await page.evaluate((v) => { APP.openTab("candidates"); APP.setTemplate(v); }, template);
    await saveScreenshot(`candidates_${template}`);
  }
  await page.evaluate(() => APP.showProfile("10"));
  await saveScreenshot("profile_altstadt");
});
