// The frame of all browser tests. Import `test` and `expect` from here, never from "@playwright/test".
//
// Fixtures:
// - guard (auto, every test): the context lets only file:, data: and blob: load and aborts every other request.
//   WebSockets are not routed (context.route does not see them); the map opens none.
//   Console errors and page errors of every page of the context are collected; the one message Chrome logs for a
//   request the guard aborted is left out (WebKit logs those as info). At the end of the test the list must be
//   empty, else the test fails. Gives the list (array of strings).
// - mapPage: the default `page` with the map loaded from paths.mapHtml + fragment, after APP.ready,
//   document.fonts.ready and settle(). window.protocolText(el) is installed (helpers/common.mjs). A map that is not
//   ready within READY_MS fails with a message that says so.
// - fragment (option, default ""): the part of the URL after the file, for example "#trend/grosse-haeuser". Set it
//   for a file or a describe block with test.use({ fragment: "#trend/…" }).
// - check(condition, message): a soft assertion (expect.soft). A falsy condition marks the test failed with the
//   message and the line of the caller, and the test goes on, so one run reports every failed check. It throws only
//   when the condition is a Promise (a forgotten await), because a Promise is always truthy.
// - saveScreenshot(name, options): writes a screenshot of `page` to `${paths.screens}/${project}_${name}.png`. The
//   project name keeps parallel tests of different projects apart; within a project, names must be unique.
//   options go to page.screenshot (for example { fullPage: true } or { clip }). With options.element (a locator)
//   the screenshot shows that element only: it is scrolled into view, and a part below the window is cut off, so a
//   high figure needs a high window. Screenshots are files to look at, not assertions. (Not named "screenshot": that
//   is Playwright's own worker option use.screenshot.)
import { test as base, expect } from "@playwright/test";
import { mkdirSync } from "node:fs";
import { dirname, join, relative } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { installProtocolText, paths, settle } from "./helpers/common.mjs";

// The console error of Chrome for a request the route aborted. Its location is the URL of the request, so a message
// counts as an aborted load only if that URL is one the guard aborted (a missing file: gives ERR_FILE_NOT_FOUND).
const ABORTED_LOAD = "Failed to load resource: net::ERR_FAILED";
// time for APP.ready, below the test timeout, so a map that never gets ready says so
const READY_MS = 10000;

// "file:line" of the first stack frame outside this file, relative to tests/browser
const here = fileURLToPath(import.meta.url);
const callerLine = () => {
  for (const line of new Error().stack.split("\n").slice(1)) {
    const m = line.match(/(?:\(|\s)(?:file:\/\/)?(\/[^\s()]+):(\d+):\d+\)?$/);
    if (m && m[1] !== here) return `${relative(dirname(here), m[1])}:${m[2]}`;
  }
  return "unknown line";
};

export const test = base.extend({
  fragment: ["", { option: true }],

  guard: [async ({ context }, use) => {
    const aborted = new Set();
    await context.route(/^(?!(?:file|data|blob):)/, (route) => { aborted.add(route.request().url()); return route.abort(); });
    const errors = [];
    const isAbortedLoad = (m) => m.text() === ABORTED_LOAD && aborted.has(m.location().url);
    const watch = (page) => {
      page.on("console", (m) => { if (m.type() === "error" && !isAbortedLoad(m)) errors.push("Console: " + m.text()); });
      page.on("pageerror", (e) => errors.push("Page error: " + e.message));
    };
    context.pages().forEach(watch);
    context.on("page", watch);
    await use(errors);
    expect(errors, "no console or page errors").toEqual([]);
  }, { auto: true }],

  mapPage: async ({ page, guard, fragment }, use) => {
    await page.addInitScript(installProtocolText);
    await page.goto(pathToFileURL(paths.mapHtml).href + fragment);
    await page.waitForFunction(() => window.APP && window.APP.ready, null, { timeout: READY_MS }).catch((e) => {
      throw new Error(`map not ready (APP.ready) after ${READY_MS / 1000} s: ${page.url()}\n${e.message.split("\n")[0]}`);
    });
    await page.evaluate(() => document.fonts.ready);
    await settle(page);
    await use(page);
  },

  check: async ({}, use) => {
    await use((condition, message) => {
      if (typeof condition?.then === "function") throw new Error(`check() got a Promise: await it (${callerLine()})`);
      // Playwright points the failure at this file; the message names the line of the caller instead
      expect.soft(condition, condition ? message : `${message} (${callerLine()})`).toBeTruthy();
    });
  },

  saveScreenshot: async ({ page }, use, testInfo) => {
    mkdirSync(paths.screens, { recursive: true });
    await use((name, { element, ...options } = {}) =>
      (element ?? page).screenshot({ ...options, path: join(paths.screens, `${testInfo.project.name}_${name}.png`) }));
  },
});

export { expect };
