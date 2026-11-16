// Self-tests of the frame (fixtures.mjs): each marked test must fail, so the frame really catches what it promises.
// If one of them passes, Playwright reports it as an unexpected pass and the run is red.
import { existsSync, rmSync } from "node:fs";
import { createServer } from "node:http";
import { join } from "node:path";
import { test, expect } from "./fixtures.mjs";
import { paths } from "./helpers/common.mjs";

test("map is ready", async ({ mapPage }) => {
  expect(await mapPage.evaluate(() => window.APP && window.APP.ready)).toBe(true);
  expect(await mapPage.evaluate(() => typeof window.protocolText)).toBe("function");
});

test("saveScreenshot writes a file named by the project", async ({ mapPage, saveScreenshot }, testInfo) => {
  const file = join(paths.screens, `${testInfo.project.name}_frame.png`);
  rmSync(file, { force: true });
  await saveScreenshot("frame");
  expect(existsSync(file)).toBe(true);
});

test("console error fails the test", async ({ mapPage }) => {
  test.fail();
  await mapPage.evaluate(() => console.error("x"));
});

test("a console error that reads like an aborted load fails the test", async ({ mapPage }) => {
  test.fail();
  // the text of an aborted load, but from the page and not for a URL the guard aborted
  await mapPage.evaluate(() => console.error("Failed to load resource: net::ERR_FAILED"));
});

test("a missing file: resource fails the test", async ({ mapPage }) => {
  test.fail();
  await mapPage.evaluate(() => new Promise((resolve) => {
    const img = new Image();
    img.onload = img.onerror = resolve;
    img.src = "file:///nonexistent-frame-test.png";
  }));
});

test("page error fails the test", async ({ mapPage }) => {
  test.fail();
  // the second timer runs after the first, so the error is thrown before evaluate returns
  await mapPage.evaluate(() => new Promise((resolve) => {
    setTimeout(() => { throw new Error("x"); }, 0);
    setTimeout(resolve, 0);
  }));
});

// A throwaway server on 127.0.0.1: not file:, data: or blob:, so the guard aborts a request to it. Without the guard
// a no-cors fetch resolves, offline too. Gives whether the fetch resolved and the paths the server saw.
async function fetchLocal(page) {
  const hits = [];
  const server = createServer((req, res) => { hits.push(req.url); res.end("ok"); });
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  try {
    const url = `http://127.0.0.1:${server.address().port}/frame`;
    const resolved = await page.evaluate((u) => fetch(u, { mode: "no-cors" }).then(() => true, () => false), url);
    return { resolved, hits };
  } finally {
    server.close();
  }
}

test("request outside file: is blocked", async ({ mapPage }) => {
  test.fail();
  expect((await fetchLocal(mapPage)).resolved).toBe(true);
});

test("a blocked request never reaches the server", async ({ mapPage }) => {
  const { resolved, hits } = await fetchLocal(mapPage);
  expect(resolved).toBe(false);
  expect(hits).toEqual([]);
});

// The marked tests here fail in their body. afterEach sees why: a failure for another reason makes the test count as
// a real failure. A test that passes stays an unexpected pass.
test.describe("check", () => {
  let reachedEnd = false;
  const reasons = {
    "failed check fails the test": /^Error: x \(frame\.\w+\.mjs:\d+\)/,
    "a Promise as condition fails the test": /check\(\) got a Promise: await it \(frame\.\w+\.mjs:\d+\)/,
  };
  test.afterEach(async ({}, testInfo) => {
    const reason = reasons[testInfo.title];
    const right = testInfo.errors.length > 0 && testInfo.errors.every((e) => reason.test(e.message || ""));
    // a soft check runs on to the end of the test
    const ran = testInfo.title !== "failed check fails the test" || reachedEnd;
    if (testInfo.status === "failed" && (!right || !ran)) testInfo.expectedStatus = "passed";
  });
  test("failed check fails the test", async ({ check }) => {
    test.fail();
    reachedEnd = false;
    check(false, "x");
    reachedEnd = true;
  });
  test("a Promise as condition fails the test", async ({ check }) => {
    test.fail();
    check(Promise.resolve(true), "x");
  });
});
