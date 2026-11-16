// Browser tests of the map. Run from tests/browser: npx playwright test [file] [--project=…].
// Paths come from env with repo defaults (helpers/common.mjs): MAP_HTML, CANDIDATES_CSV, SCREENS.
// Desktop and Chrome with touch use the system Chrome, the iPhone windows Playwright's WebKit.
import { defineConfig, devices } from "@playwright/test";
import { join } from "node:path";
import { paths } from "./helpers/common.mjs";

const chrome = { browserName: "chromium", channel: "chrome" };
const phone = ["mobile/phone.spec.mjs"];
const medium = ["mobile/medium.spec.mjs"];

export default defineConfig({
  testDir: ".",
  fullyParallel: true,
  retries: 0,
  forbidOnly: true,
  outputDir: join(paths.root, "output/playwright/results"),
  reporter: [["list"], ["html", { open: "never", outputFolder: join(paths.root, "output/playwright/report") }]],
  use: { trace: "retain-on-failure" },
  projects: [
    { name: "desktop-chrome", testMatch: ["desktop/**/*.spec.mjs", "frame.spec.mjs"],
      use: { ...chrome, viewport: { width: 1400, height: 900 } } },
    { name: "webkit-iphone", testMatch: [...phone, "mobile/links.spec.mjs", "frame.spec.mjs"],
      use: { ...devices["iPhone 15"] } },
    { name: "webkit-iphone-se", testMatch: phone, use: { ...devices["iPhone SE"] } },
    { name: "webkit-iphone-landscape", testMatch: medium, use: { ...devices["iPhone 15 landscape"] } },
    { name: "chrome-390", testMatch: phone,
      use: { ...chrome, viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, deviceScaleFactor: 2 } },
    { name: "chrome-768", testMatch: medium,
      use: { ...chrome, viewport: { width: 768, height: 1024 }, isMobile: true, hasTouch: true } },
  ],
});
