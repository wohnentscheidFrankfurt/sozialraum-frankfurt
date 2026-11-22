// No German word of GERMAN_UI_WORDS in the visible text of the English map, in any state, outside the allow list
// (helpers/german.mjs).
import { test, expect } from "../fixtures.mjs";
import { eachState } from "../helpers/english.mjs";
import { allowedFromPayload, germanWords } from "../helpers/german.mjs";
import { paths } from "../helpers/common.mjs";

test.use({ mapHtml: paths.mapHtmlEn });

test("the visible text holds no German word", async ({ mapPage: page, check }) => {
  test.setTimeout(120000);
  const allowed = await allowedFromPayload(page);
  expect(allowed.length).toBeGreaterThan(100);
  const found = {}, seen = new Set(); // a leftover is named at the first state that shows it
  await eachState(page, (name, text) => {
    const fresh = germanWords(text, allowed).filter((w) => !seen.has(w));
    fresh.forEach((w) => seen.add(w));
    if (fresh.length) found[name] = fresh;
  });
  check(Object.keys(found).length === 0, "German words in the English map: " + JSON.stringify(found, null, 1));
});
