// Negative control of the German word scan: it flags a German sentence and passes an English one with an allowed name.
import { test, expect } from "@playwright/test";
import { germanWords } from "../helpers/german.mjs";

test("the scan flags a seeded German sentence", () => {
  expect(germanWords("Die Wohnungen im Gebiet", []).length).toBeGreaterThan(0);
});

test("the scan passes an English sentence with an allowed name", () => {
  const allowed = ["Nordend-West"];
  expect(germanWords("The dwellings in Nordend-West are rented (Wohnungen).", allowed)).toEqual([]);
  expect(germanWords("Sozialraum Frankfurt shows the area.", allowed)).toEqual([]);
});
