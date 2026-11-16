// Legend: classes of sparse layers, party colours and ramps, titles, notes, rows and the overlay key, the levels of
// the layer rows and the switch line above the legend.
import { test } from "../fixtures.mjs";
import { numbers } from "../helpers/layers.mjs";

// the rows of a layer on districts, from the tab Stadt
const districtRows = (page, id) => page.evaluate((k) => { APP.setLevel("district"); APP.openTab("city"); APP.setIndicator(k);
  return [...APP.legendDiv.querySelectorAll("i")].map((i) => i.nextSibling.textContent.trim()); }, id);

test("sparse layers without an empty class, 0 % with its own class", async ({ mapPage: page, check }) => {
  const zero = await districtRows(page, "PROT_SOCIAL");
  // a row whose only number is 0: the zero class, and only as the first row (no class "below 0,0")
  const onlyZero = (row) => numbers(row).length > 0 && numbers(row).every((x) => x === 0);
  check(zero.slice(1).every((row) => !onlyZero(row)), `PROT_SOCIAL: no legend row "unter 0,0": ${zero.join(" | ")}`);
  const unit = await page.evaluate(() => APP.meta.PROT_SOCIAL.unit);
  check(onlyZero(zero[0]) && unit && zero[0].includes(unit) && zero[0].length > `0 ${unit}`.length, `PROT_SOCIAL: first class is "0 % (keine)": ${zero[0]}`);
  check(new Set(zero).size === zero.length, `PROT_SOCIAL: no duplicate legend rows: ${zero.join(" | ")}`);
  const zeroColors = await page.evaluate(() => {
    const small = (p) => p.small;
    const feats = APP.properties("district").filter((p) => !small(p));
    const zeroColor = APP.style({ properties: feats.find((p) => p.PROT_SOCIAL === 0) }).fillColor;
    const positiveColors = new Set(feats.filter((p) => p.PROT_SOCIAL > 0).map((p) => APP.style({ properties: p }).fillColor));
    return { zeroColor, sharesZeroColor: positiveColors.has(zeroColor) };
  });
  check(!zeroColors.sharesZeroColor, "PROT_SOCIAL: districts with 0 % have their own colour, which no positive value shares");
  const publicRows = await districtRows(page, "OWN_PUBLIC");
  // the first class names only its upper bound
  check(publicRows.length === 5 && !publicRows.includes("k. A.") && numbers(publicRows[0]).length === 1, `OWN_PUBLIC: 5 classes, no k. A.: ${publicRows.join(" | ")}`);
});

test("party colours and the ramp per list", async ({ mapPage: page, check, saveScreenshot }) => {
  const colors = await page.evaluate(() => {
    const spd = APP.data.lists.find((l) => l.name === "SPD");
    const cdu = APP.data.lists.find((l) => l.name === "CDU");
    const fdp = APP.data.lists.find((l) => l.name === "FDP");
    return { cdu: cdu && cdu.color, spd: spd && APP.rampFor(APP.meta[spd.key]), fdp: fdp && APP.rampFor(APP.meta[fdp.key]),
             allFinished: APP.data.catalog.every((m) => Array.isArray(m.colors) && m.colors.length === 5 && m.colors.every((c) => /^#[0-9a-f]{6}$/.test(c))),
             teal: APP.data.ramp_teal };
  });
  check(colors.cdu === "#1d1d1b", "list colour CDU from the Statistikportal: " + colors.cdu);
  check(colors.spd && colors.spd.length === 5 && colors.spd[4] === "#e30613" && colors.spd.every((c) => /^#[0-9a-f]{6}$/i.test(c)), "SPD ramp ends in #e30613: " + JSON.stringify(colors.spd));
  check(colors.fdp && colors.fdp.length === 5 && colors.fdp[4] !== "#ffd600", "FDP ramp ends darker than the yellow: " + JSON.stringify(colors.fdp));
  // the fallback to teal for an invalid ramp is decided in Python (tests/shared/core/test_colours.py)
  check(colors.allFinished && colors.teal.length === 5, "every catalog entry carries its 5 finished colours; ramp_teal for the candidates");
  const mainLists = await page.evaluate(() => APP.data.lists.filter((l) => l.position > 0 && l.key !== "ELEC_OTHER").map((l) => {
    const r = APP.rampFor(APP.meta[l.key]);
    // OKLab lightness; the map no longer computes it, only this check does
    const oklabL = (rgb) => {
      const [R, G, B] = rgb.map((v) => { const x = v / 255; return x <= 0.04045 ? x / 12.92 : Math.pow((x + 0.055) / 1.055, 2.4); });
      const a = Math.cbrt(0.4122214708 * R + 0.5363325363 * G + 0.0514459929 * B);
      const b = Math.cbrt(0.2119034982 * R + 0.6806995451 * G + 0.1073969566 * B);
      const c = Math.cbrt(0.0883024619 * R + 0.2817188376 * G + 0.6299787005 * B);
      return 0.2104542553 * a + 0.793617785 * b - 0.0040720468 * c;
    };
    const L = (c) => oklabL([1, 3, 5].map((i) => parseInt(c.slice(i, i + 2), 16)));
    return { name: l.name, ramp: r, gap: L(r[0]) - L(r[4]) };
  }));
  check(mainLists.length >= 7, "at least 7 lists with a share layer");
  for (const h of mainLists) check(h.gap >= 0.35, `ramp ${h.name}: lightness gap step 1 to 5 (OKLab L) ${h.gap.toFixed(2)} < 0.35`);
  if (process.env.SHOW_RAMPS) console.log(mainLists.map((h) => `${h.name} ${h.ramp.join(" ")} dL=${h.gap.toFixed(2)}`).join("\n"));
  for (const name of ["SPD", "GRÜNE", "FDP"]) {
    const id = await page.evaluate((n) => APP.data.lists.find((l) => l.name === n).key, name);
    await page.evaluate((k) => { APP.openTab("city"); APP.setIndicator(k); }, id);
    await saveScreenshot(`election_share_${name}`);
  }
  await page.evaluate(() => { APP.openTab("city"); APP.setIndicator("ELEC_STRONGEST"); });
  await saveScreenshot("election_strongest");
});

// docs/texts.md, Map texts: 1.1-1.3 titles, unit and classes; 1.7 "Ganz Frankfurt"
const legend = (page) => page.evaluate(() => ({ title: document.querySelector(".legend-title").textContent,
  note: document.querySelector(".legend-note")?.textContent, text: document.querySelector(".legend").textContent,
  rows: [...document.querySelectorAll(".legend i")].map((i) => i.nextSibling.textContent.trim()) }));

test("texts 1.1-1.7: title, notes and the city value", async ({ mapPage: page, check }) => {
  await page.evaluate(() => { APP.openTab("city"); APP.setLevel("quarter"); });
  await page.evaluate(() => APP.setIndicator("SH_SHARE"));
  // title and note are those of the catalog (APP.meta)
  const share = await legend(page);
  const shareMeta = await page.evaluate(() => ({ title: APP.meta.SH_SHARE.title, note: APP.meta.SH_SHARE.legend_note }));
  check(shareMeta.title && shareMeta.note && share.title === shareMeta.title && share.note === shareMeta.note, "10 1.1: SH_SHARE title and note: " + JSON.stringify(share));
  for (const id of ["OWN_PUBLIC", "SH_SHARE"]) {
    await page.evaluate((i) => APP.setIndicator(i), id);
    // the city value stands in a line of its own, after the classes: the text of the body that follows no swatch
    const r = await page.evaluate((i) => {
      const body = APP.legendDiv.querySelector(".legend-body");
      const lines = [...body.childNodes].filter((n) => n.nodeType === Node.TEXT_NODE && n.previousSibling?.tagName !== "I").map((n) => n.textContent.trim()).filter(Boolean);
      return { lines, value: APP.valueText(i, APP.data.city_values[i]), text: APP.legendDiv.textContent };
    }, id);
    check(r.lines.length === 1 && r.lines[0].endsWith(": " + r.value) && numbers(r.value).length > 0 && !r.text.includes("Stadtwert"),
      "10 1.7: Ganz Frankfurt in the legend of " + id + ": " + JSON.stringify(r.lines));
  }
  // 1.4, 1.5: the note is the legend_note of the catalog
  const noteOf = (id) => page.evaluate((i) => { APP.setIndicator(i); return { shown: document.querySelector(".legend-note")?.textContent, catalog: APP.meta[i].legend_note }; }, id);
  const listNote = await noteOf("ELEC_CDU");
  check(listNote.catalog && listNote.shown === listNote.catalog, "10 1.4: note of a list share: " + JSON.stringify(listNote));
  const rentNote = await noteOf("HOU_RENT");
  check(rentNote.catalog && rentNote.shown === rentNote.catalog, "10 1.5: note of HOU_RENT: " + JSON.stringify(rentNote));
  // 1.6 second note line: the legend_detail of the catalog, first in the body, below the note
  for (const id of ["OWN_COMPANY", "OWN_PERSON"]) {
    const r = await page.evaluate((i) => { APP.setIndicator(i); const d = document.querySelector(".legend-body > .legend-detail");
      const n = document.querySelector(".legend-note");
      return { text: d?.textContent, catalog: APP.meta[i].legend_detail, first: d === document.querySelector(".legend-body").firstElementChild,
        below: d ? d.getBoundingClientRect().top >= n.getBoundingClientRect().bottom - 1 : false }; }, id);
    check(r.catalog && r.text === r.catalog && r.first && r.below, "10 1.6: second note line of " + id + ": " + JSON.stringify(r));
  }
  check(await page.evaluate(() => { APP.setIndicator("OWN_PUBLIC"); return !document.querySelector(".legend-detail"); }),
    "10 1.6: OWN_PUBLIC has no second note line");
});

test("texts 1.10: rows only where the map has them", async ({ mapPage: page, check }) => {
  await page.evaluate(() => APP.openTab("city"));
  const rowsOf = (level, id) => page.evaluate(([l, i]) => { APP.setLevel(l); APP.setIndicator(i); return [...APP.legendDiv.querySelectorAll("i")].map((e) => e.nextSibling.textContent.trim()); }, [level, id]);
  check((await rowsOf("district", "SOC_MIN_INCOME")).at(-1) === "k. A.", "10 1.10: SOC_MIN_INCOME has a k. A. row (one district without value)");
  check(!(await rowsOf("district", "HOU_RENTERS")).includes("k. A."), "10 1.10: HOU_RENTERS has no k. A. row");
  {
    const r = await page.evaluate(() => { APP.setLevel("quarter"); APP.setIndicator("ELEC_STRONGEST");
      return { rows: [...APP.legendDiv.querySelectorAll("i")].map((e) => e.nextSibling.textContent.trim()),
        want: APP.data.lists.filter((l) => l.position > 0 && APP.properties("quarter").some((p) => p.ELEC_STRONGEST === l.name)).map((l) => l.name) }; });
    check(JSON.stringify(r.rows) === JSON.stringify(r.want) && !r.rows.includes("AfD"), "10 1.10: ELEC_STRONGEST lists only the strongest lists: " + JSON.stringify(r));
  }
  {
    const r = await page.evaluate(() => { APP.openTab("candidates"); APP.setTemplate("social_preservation"); const rows = () => [...APP.legendDiv.querySelectorAll("i")];
      const text = () => rows().map((e) => e.nextSibling.textContent.trim());
      // row n is "all met": one row per number of criteria met, 0 to n
      const n = APP.activeCriteria().length, last = rows()[n];
      const out = { n, rows: text(), bg: last.style.backgroundColor, border: last.style.border, ramp: APP.data.ramp_teal[4], hit: APP.data.hit_border };
      const d = APP.properties("district")[0]; const old = d.small; d.small = 1; APP.legend(); out.withSmall = text();
      d.small = old; APP.legend(); out.after = text(); return out; });
    const dummy = await page.evaluate((c) => { const e = document.createElement("i"); e.style.background = c; return e.style.backgroundColor; }, r.ramp);
    // rows 1 to n-1 name "i of n"; the first ("none") and the last ("all met") hold no number
    check(r.n === 5 && r.rows.length === r.n + 1 && new Set(r.rows).size === r.rows.length && r.rows.every((t) => t !== "")
      && r.rows.slice(1, -1).every((t, i) => JSON.stringify(numbers(t)) === JSON.stringify([i + 1, r.n]))
      && numbers(r.rows[0]).length === 0 && numbers(r.rows.at(-1)).length === 0, "10 1.10: candidates legend rows: " + JSON.stringify(r.rows));
    check(r.bg === dummy && r.border.includes("3px solid"), "10 1.10: swatch of alle erfüllt takes the top ramp step and the orange border: " + JSON.stringify(r));
    // the extra row names the population limit 1.000
    const extra = r.withSmall.filter((t) => !r.after.includes(t));
    check(r.withSmall.length === r.after.length + 1 && JSON.stringify(r.after) === JSON.stringify(r.rows) && extra.length === 1 && numbers(extra[0]).includes(1000),
      "10 1.10: the small-district row appears only with a small district: " + JSON.stringify(r));
  }
});

test("texts 1.8-1.10: overlay key in the legend", async ({ mapPage: page, check }) => {
  // 1.8-1.10 overlay key in the legend; overlays without features leave the list
  const keyRows = () => page.evaluate(() => [...document.querySelectorAll(".legend-overlays .key-row")].map((e) => e.textContent.trim()));
  // the key of an overlay comes from the payload (APP.data.overlays); the grid row is a note below zoom 14
  const keys = await page.evaluate(() => Object.fromEntries(Object.entries(APP.data.overlays).map(([k, o]) => [k, o.key])));
  const zoomNote = () => page.evaluate(() => { const rows = [...document.querySelectorAll(".legend-overlays .key-row")];
    return { last: rows.at(-1)?.classList.contains("note") && rows.at(-1).textContent.trim() !== "", count: rows.filter((e) => e.classList.contains("note")).length }; });
  const zoomTo = (z) => page.evaluate((zz) => { APP.map.setZoom(zz, { animate: false }); return APP.map.getZoom(); }, z);
  await page.evaluate(() => { APP.setLevel("district"); APP.setIndicator("OWN_PUBLIC"); APP.openTab("city"); });
  await page.evaluate(() => { for (const u of Object.values(APP.overlays)) u.on = false;
    APP.overlays.social_preservation.on = true; APP.overlays.social_preservation_pending.on = true; APP.updateOverlays(); });
  check(keys.social_preservation && JSON.stringify(await keyRows()) === JSON.stringify([keys.social_preservation]), "10 1.8: start state keys only Milieuschutz: " + JSON.stringify(await keyRows()));
  const empties = await page.evaluate(() => ({ sidebar: Boolean(document.querySelector('input[data-overlay="social_preservation_pending"]')),
    infos: document.querySelectorAll("#overlays .info-button").length,
    withFeatures: Object.entries(APP.overlays).filter(([, u]) => !u.empty).length,
    empty: Object.entries(APP.overlays).filter(([, u]) => u.empty).map(([n]) => n) }));
  check(!empties.sidebar && empties.infos === 8 && empties.withFeatures === 8 && empties.empty.join() === "social_preservation_pending",
    "10 1.9: an overlay without features has no checkbox and no ⓘ: " + JSON.stringify(empties));
  await page.evaluate(() => { for (const [n, u] of Object.entries(APP.overlays)) u.on = !u.empty && n !== "flat_roofs"; APP.updateOverlays(); }); // the roofs are checked in flat-roofs.spec.mjs
  await zoomTo(13);
  const all13 = await keyRows();
  const want13 = ["social_preservation", "townscape", "townscape_pending", "pending_plans", "land_value", "building_gaps"].map((k) => keys[k]);
  check(want13.every(Boolean) && JSON.stringify(all13.slice(0, -1)) === JSON.stringify(want13) && (await zoomNote()).last,
    "10 1.8: all overlays on at zoom 13: " + JSON.stringify(all13));
  await zoomTo(15);
  const g15 = await page.evaluate(() => { const row = [...document.querySelectorAll(".legend-overlays .key-row")].at(-1);
    return { text: [...row.querySelectorAll(".key-swatch")].map((e) => e.nextSibling.textContent.trim()),
      colors: [...row.querySelectorAll(".key-swatch")].map((e) => e.style.backgroundColor),
      want: APP.data.grid_groups.map((g) => APP.ownershipById[g].title),
      wantColors: APP.data.grid_groups.map((g) => { const e = document.createElement("i"); e.style.background = APP.ownershipById[g].color; return e.style.backgroundColor; }),
      note: document.querySelectorAll(".legend-overlays .key-row.note").length > 0 }; });
  check(JSON.stringify(g15.text) === JSON.stringify(g15.want) && JSON.stringify(g15.colors) === JSON.stringify(g15.wantColors) && !g15.note,
    "10 1.8: at zoom 15 the grid row lists the groups with their colours: " + JSON.stringify(g15));
  await zoomTo(13);
  check((await zoomNote()).last, "10 1.8: the zoom note returns at zoom 13");
  await page.evaluate(() => { APP.overlays.grid.on = false; APP.updateOverlays(); });
  const noGrid = [];
  for (const z of [13, 15]) { await zoomTo(z); noGrid.push({ rows: await keyRows(), notes: (await zoomNote()).count }); }
  check(noGrid.every((r) => r.notes === 0 && JSON.stringify(r.rows) === JSON.stringify(want13)), "10 1.8: grid off: no grid row at any zoom: " + JSON.stringify(noGrid));
  await page.evaluate(() => { const c = document.querySelector('#tab-city input[data-overlay="townscape"]'); c.checked = true; c.click(); });
  check(!(await keyRows()).includes(keys.townscape), "10 1.8: the checkbox townscape off removes its row");
  const sw = await page.evaluate(() => { const before = document.querySelectorAll(".legend i").length;
    APP.overlays.grid.on = true; APP.overlays.townscape.on = true; APP.updateOverlays();
    return { styles: [...document.querySelectorAll(".key-swatch")].map((e) => e.getAttribute("style")), tags: [...document.querySelectorAll(".key-swatch")].map((e) => e.tagName),
      before, after: document.querySelectorAll(".legend i").length, last: APP.legendDiv.querySelector(".legend-body").lastElementChild.className }; });
  check(sw.styles.length > 0 && sw.styles.every((t) => t && t.trim().length > 0) && sw.tags.every((t) => t === "SPAN") && sw.before === sw.after && sw.last === "legend-overlays",
    "10 1.8: every key swatch has a style, is a span, adds no legend <i>, and the key ends the body: " + JSON.stringify(sw));
  await page.evaluate(() => { APP.openTab("candidates"); APP.setTemplate("social_preservation"); });
  check(await page.evaluate(() => Boolean(APP.legendDiv.querySelector(".legend-body > .legend-overlays .key-row"))), "10 1.8: the candidates legend has the same key");
});

test("texts 5.1: levels of the layer rows and the switch line", async ({ mapPage: page, check }) => {
  // greyed rows name their level, a silent layer switch says so above the legend
  // the level suffix of a row: its own span, after the title; it names the level of the layer (APP.LEVEL_NAMES)
  const labels = () => page.evaluate(() => [...document.querySelectorAll("#tab-city label[data-id]")].map((l) => {
    const m = APP.meta[l.dataset.id === "ELEC_LIST" ? document.getElementById("list-choice").value : l.dataset.id];
    const only = l.querySelector(".only-level").textContent.trim();
    return { id: l.dataset.id, off: l.classList.contains("off"), text: l.textContent.trim(), only,
      names: only !== "" && only.includes(APP.LEVEL_NAMES[m.levels[0]]) && l.textContent.trim().endsWith(only) };
  }));
  // the switch line names the title of the layer that left and the level it has (APP.LEVEL_SINGULAR)
  const names = (sw, id) => page.evaluate(([t, i]) => Boolean(t) && t.includes(APP.meta[i].title) && t.includes(APP.LEVEL_SINGULAR[APP.meta[i].levels[0]]), [sw.text, id]);
  const note = () => page.evaluate(() => { const e = document.querySelector(".legend-switch");
    return { text: e?.textContent, visible: !!e && e.offsetParent !== null }; });
  await page.evaluate(() => { APP.openTab("city"); APP.setLevel("district"); APP.setIndicator("SOC_INDEX"); });
  const district = await labels();
  const own = district.find((l) => l.id === "OWN_PUBLIC"), list = district.find((l) => l.id === "ELEC_LIST");
  check(own.off && own.names && list.off && list.names,
    "10 5.1: districts, greyed rows end with (nur Stadtteile): " + JSON.stringify([own, list]));
  await page.evaluate(() => { APP.setLevel("quarter"); APP.setIndicator("OWN_PUBLIC"); });
  const quarter = await labels();
  check(quarter.find((l) => l.id === "SOC_INDEX").names && quarter.every((l) => l.off === (l.only !== "") && (!l.off || l.names)),
    "10 5.1: quarters, only greyed rows say (nur ...): " + JSON.stringify(quarter.filter((l) => (l.only !== "") !== l.off || (l.off && !l.names))));
  await page.evaluate(() => { APP.setLevel("quarter"); APP.setIndicator("OWN_COMPANY"); });
  await page.click('#tab-city input[name="level"][value="district"]');
  const sw = await note();
  check(sw.visible && await names(sw, "OWN_COMPANY"),
    "10 5.1: switch line after a level click: " + JSON.stringify(sw));
  check(await page.evaluate(() => document.querySelector(".legend-switch").getBoundingClientRect().bottom <= document.querySelector(".legend").getBoundingClientRect().top + 1),
    "10 5.1: the switch line stands above the legend");
  await page.evaluate(() => { APP.setLevel("quarter"); APP.setIndicator("HOU_RENTERS"); });
  check(!(await note()).visible, "10 5.1: no note after an indicator change");
  await page.click('#tab-city input[name="level"][value="district"]');
  await page.click('#tab-city input[name="level"][value="quarter"]');
  check(!(await note()).visible, "10 5.1: HOU_RENTERS on both levels, no note");
  await page.evaluate(() => { APP.setLevel("district"); APP.setIndicator("SOC_INDEX"); });
  await page.click('#tab-city input[name="level"][value="quarter"]');
  check(await names(await note(), "SOC_INDEX"),
    "10 5.1: switch line to the quarter level: " + JSON.stringify(await note()));
  await page.evaluate(() => APP.openTab("candidates"));
  check(!(await note()).visible, "10 5.1: hidden in the candidates");
  await page.evaluate(() => APP.openTab("city"));
  check(!(await note()).visible, "10 5.1: the note does not return");
});
