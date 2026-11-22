# Design

Rules for the user interface of the map (`web/`) and its fixed colours (`pipeline/shared/core/palette.py`). The
wording of map texts follows `docs/texts.md`. The browser tests guard the rules: `tests/browser/desktop/` (desktop)
and `tests/browser/mobile/` (phones and tablet), see `docs/architecture.md`, Browser tests.

## Style

- The map is bold, not bland. Each region has one loud gesture; the rest stays calm.
- The look follows the flyer of the team (November 2026) and its website: condensed uppercase headings, black on
  white.
- The map itself is colourful enough, so the interface has no colour of its own (user, 16.11.2026). Title,
  navigation and headings are black, the ⓘ is grey. The loud gestures are
  the black uppercase condensed title, the black rule under the header and the active view as a black block with
  white text.
- Everything else is white ground, black text (`--text`), grey secondary text (`--grey`) and thin grey lines (`--line`).
- Two fonts of the flyer, both embedded: Archivo for headings, buttons and the numbers of a written sum; Mulish 400
  and 700 for text. Archivo is one variable file in two widths: `--font-tight` (72 %, weight 800) for the title, the
  sidebar headings and the view buttons below 1024 px; `--font-head` (85 %, weight 700) for the rest. The stacks stand
  in `:root` of `web/map.css`; `pipeline/map/html/sources.py` embeds each width as a family of its own. Why: the file
  works on its own, without the network, and the `font` shorthand resets `font-stretch`.
- The map demands nothing (`docs/texts.md`, Neutrality).
- The map explains itself in the moment of use. Labels, the legend note, the tooltip at the value and hints that follow
  the state come first. Little text stands on the surface; the ⓘ holds the rest.
- Colour never carries meaning alone. Tooltip, profile table and keys name every group.
- Focus is always visible: a black 2 px outline on buttons, tabs and profile rows.
- A chart is one `role="img"`. Its `aria-label` carries every value, because the children of an image are hidden from
  screen readers.

## Navigation and layouts

### Views and tabs

- The header holds the title and the views (`#views`: „Karte“, „Trend“, „Neubau“, „Miete“).

### Language switch

- A text link (`#lang-switch`) at the right end of the header: „English“ on the German map, „Deutsch“ on the English
  map. The label is written in the target language and carries its `lang`.
- Black text on white, underlined, 15 px (14 px in medium windows and on phones). No frame, no fill, no colour. It
  must not look like a view button.
- Under 700 px the title and the four views fill the first row. The link then wraps to a row of its own, right
  aligned. Why: the views must not shrink for it.
- It opens the other file with the current fragment, so view, chart, zoom, centre, level, area, layer and overlays
  stay. The fragment is language neutral. The link follows every change of the fragment.
- The German map shows it only while `ENGLISH_ONLINE` is on (`docs/architecture.md`, The map file).
- The sidebar holds the map tabs (`#tabs`): „Stadt“, „Gebiet“, „Kandidaten“, „Hilfe“. The help follows this order.
- One button per bar has `aria-pressed=true`. The active view is white with a black frame and a black shadow
  offset down right (4 px, 3 px in medium windows and on phones); the active tab is underlined black.
- „Stadt“ is the overview of the whole city. „Gebiet“ is the state of exploring one area. „Kandidaten“ colours the
  map by the criteria met.
- „Gebiet“ also switches the overlays, in its details line (Profile and pressed row). Why: a switch in „Stadt“ would
  end exploring.
- A map tab always shows the map view. A chart view is drawn when it first opens.
- The map starts on Stadtteile with „ABG und Nassauische Heimstätte“. It fits the whole city above the phone panel.

### Direct links

A link opens one view and, in „Trend“, „Neubau“ and „Miete“, one chart: `…/sozialraum-frankfurt/#trend/grosse-haeuser`.
The view „Karte“ also opens a state of the map (Map links).
GitHub Pages serves static files only, so the map reads the fragment itself (`APP.followLink`, `web/js/01_base.js`).
The fragment never reaches the server and works under `file:` too.

| fragment | opens |
|---|---|
| none, `#karte` | view „Karte“ |
| `#karte/zoom=…&…` | view „Karte“ in the state of the link, see Map links |
| `#trend` | view „Trend“, at the top |
| `#trend/wem-gehoeren-die-wohnungen` | chart `houses` |
| `#trend/wachstum-im-bestand` | chart `decades` |
| `#trend/wer-waechst` | chart `arrows` |
| `#trend/grosse-haeuser` | chart `sizes` |
| `#neubau` | view „Neubau“, at the top |
| `#neubau/gefoerderte-wohnungen` | chart of completions |
| `#neubau/wohnungen-und-mieten` | block of rents (both charts) |
| `#miete` | view „Miete“, at the top |
| `#miete/warmmiete-und-lohn` | wage example (both charts) |
| `#miete/warmmiete-und-einkommen` | bars of the tenants by income group |

- A published slug never changes: shared links would break. `tests/map/html/test_web.py` holds the fixed list.
- The view slugs stand as `data-link` on the view buttons in `web/map.html`. The chart slugs stand as `link` in the
  catalog of the use case and travel in the payload. A figure has the id `<view>-<chart>`, for example
  `trend-grosse-haeuser`.
- The two charts inside the block of rents and inside the wage example have no link of their own.
- The map scrolls the figure to the top of its view, and again once the fonts are loaded. The last figure of a short
  view stops where the view ends. An unknown view changes nothing. An unknown chart opens its view at the top, and the
  address bar then names only the view. The map also follows a fragment changed on a loaded page; „Zurück“ to no
  fragment shows the map.
- A click on a view writes its fragment with `history.replaceState`, so the address bar can be copied as a link. A
  fragment of the same view keeps its chart. The map clears every fragment except `#karte` and a map link. No history
  entry is added, so „Zurück“ leaves the page as before. Scrolling does not change the fragment.

### Map links

The address bar shows the map as the reader sees it. The reader copies it and sends it as a link:

`#karte/zoom=16.5&center=50.11281,8.68280&level=quarter&area=Altstadt&layer=ROOF_FLAT&overlays=social_preservation,flat_roofs`

- The keys come in this order: `zoom`, `center`, `level`, `area`, `layer`, `overlays`. `area` stands only while an
  area is explored.
- Zoom has at most one decimal. The centre has five decimals (about 1 m), latitude first. `area` goes through
  `encodeURIComponent`. `overlays` lists the names in the order of `APP.overlays` and is empty when none is on.
- Keys and values are addresses, not words: layer ids, overlay names and the levels `quarter` and `district`. They
  never change and carry no German word, except area ids. So an English map can read the same links. Area ids are
  proper names from the sources (Stadtteil names, monitoring numbers) and change only with a new area scheme. The
  rule is in `docs/architecture.md`, The map file.

Reading (`APP.parseMapLink`, `APP.applyMapLink`):

- A key that is missing or whose value is unknown is dropped. The map then keeps what it shows. A link with nothing
  valid still opens the map.
- Zoom is clamped to 10 to 19. The centre must lie within the city, with a margin of half its extent.
- Messengers change links. The map decodes `%2C`, `%3D` and umlauts, also in raw form, and cuts `. , ) ! ?` glued to
  the end.
- The layer wins over the level. A level that the layer lacks is dropped, so the map switches nothing and shows no
  note. The area must exist on the level shown. A Bezirk on a layer of Stadtteile only goes to its Stadtteil, as a
  switch of the level would.
- With zoom and centre the map explores the area without a flight and keeps that view. With only one of them, or with
  neither, it flies to the area as a click would.
- A link ends the candidates and shows „Stadt“, or „Gebiet“ with an area. The phone panel keeps its state: a link
  never opens it.
- After reading, the address bar holds the clean link.
- The map follows a map link also on a loaded page (a changed fragment).

Writing (`APP.writeMapLink`):

- The map writes after every `moveend`, change of level or layer and change of an overlay. Opening or closing the
  phone panel rewrites a map link that stands in the address bar. It uses `history.replaceState`, so there is no
  history entry.
- A fresh page writes nothing while the map equals the start. `#karte` stays `#karte`. A resize or the fonts must not
  put a link into a page that nobody changed.
- The centre stays as written while the map is less than 2 px (about 3 m at zoom 16) from it at the same zoom. Why:
  Leaflet rounds the centre to a pixel after a resize. That alone would change the fifth decimal.

The link names the centre of the visible map. On the phone that is the part above the panel (`APP.visibleCenter`).
Why: with the panel open the container centre lies under the panel. A desktop reader would see the area shifted.
Opening or closing the panel moves this centre, so it rewrites a map link that stands in the address bar. A switch
between phone and desktop in the same window keeps the visible centre while the map view is shown (`phoneQuery`
handler). It also keeps the sticky centre, so turning the phone and back changes no link.

### Layouts

The layout depends only on the window (`web/map.css`).

| Layout | Window | Sidebar |
|---|---|---|
| Wide | at least 1024 px wide and more than 500 px high | 410 px, left of the map |
| Medium | 701 to 1023 px wide, or at most 500 px high | 320 px, left of the map; compact header |
| Phone | at most 700 px wide | a panel over the lower part of the map |

- The page never scrolls sideways. It uses `100dvh`, `viewport-fit=cover` and the safe-area insets.
- The footer is one line („Erstellt am … · Quellen“). Open, it takes at most 40 % of the window.
- A source with a page (`Source.url`) links its title in the source list. The link opens a new tab. Only the
  Gemeinwohlbau has one (user, 15.11.2026: its idea deserves a pointer).
- Below 430 px of window width the header shrinks its gaps, below 360 px also its fonts. The four view buttons stay
  in one line.
- Below 320 px the header may wrap the view buttons to a row of their own. They still stay in one line.
- Print hides sidebar and view buttons, gives the map the full width and prints the full source list. The print rules
  stand last in `web/map.css`. Why: a printed page is narrower than 1024 px and would match the medium layout.

### Phone panel

- On the phone the sidebar is a panel, always 60 % of the map high. It starts closed: only its tab bar shows, and the
  content is `inert`.
- The arrow (▲ closed, ▼ open) or a swipe opens and closes the panel. A tap on a tab opens a closed panel.
- The panel follows the finger from 8 px of drag. A drag on the tab bar moves it both ways. In the content a drag down
  moves it only when the content is scrolled to its top. Sliders and selects keep their own gestures.
- On release a flick faster than 0.5 px/ms decides by its direction, else the position: more than half open opens. A
  second finger snaps the panel.
- No pull-to-refresh (`overscroll-behavior: none`). Why: Safari would reload the page and lose the state.
- Legend and zoom buttons move up with the panel (`--panel`). `APP.setPanel` is the only place that opens or closes
  it; the gestures live in `web/js/07_swipe.js`.

### Mouse and touch

- Input decides, not width: `APP.touch()` matches `(hover: none), (pointer: coarse)`. A tablet is touch.
- Hover styles exist only under `@media (hover: hover)`. Why: on touch screens a hover state sticks.
- Mouse: hover shows the tooltip anywhere in the city and never moves the map. A click explores the area.
- Touch: a tap shows the tooltip with the button „Gebiet erkunden“. The map does not move after a plain tap.
- Under `pointer: coarse` touch targets are at least 32 px and inputs 16 px. Why: below 16 px iOS zooms in on focus.

## Map

### Zoom control

- A third button sits between „+“ and „−“: four corner marks, „Ganz Frankfurt zeigen“ (`APP.fitCity`). It fits all
  Bezirke above the phone panel, as at the start. An explored area stays explored.
- It is a `<button type="button">`, not a link: `#` would replace the map link in the address bar.
- Under `pointer: coarse` the three buttons are 32 px.

### Areas and levels

- The background is the grey basemap.de, so the colours of the layers carry. Areas fill at 0.75 opacity with a 0.8 px
  border `#555`.
- Two levels: Stadtteile and Bezirke. The user never has to choose a level to see a value.
- A layer that the current level lacks greys its row in „Stadt“, ending in „(nur Stadtteile)“ or „(nur Bezirke)“.
- A level that lacks the layer takes its first layer. One line above the legend says so (`APP.switchNote`). The line
  goes with the next choice of layer, level or mode.
- A Bezirk shows Stadtteil-only values from its Stadtteil (`APP.valueSource`). A note names the Stadtteil.

### Classes

- A number layer gets 5 quantile classes over the shown values, without the small Bezirke. If more than a fifth of
  the values are 0, the 0 gets its own class.
- Printed classes of a report keep their limits and skip the lightest step. Why: it would merge with the white „k. A.“.
- No value („k. A.“) is white at 0.3 opacity.
- Small Bezirke are light grey with a dashed border. Survey classes stay coloured: they belong to the survey area.
- „Stärkste Liste“ fills each area with the colour of its list.

### Legend

- The legend sits bottom right. Under its title stands one small grey line, the `legend_note` of the layer. It says
  what the number is. Every layer has one.
- The body opens with an optional second line (`legend_detail`). Then come the classes with 16 × 12 px swatches,
  „k. A.“ and „Ganz Frankfurt“ with the city value. The overlay key closes it, below a thin line.
- A row stands only when the map shows it. „Stärkste Liste“ lists only lists that are strongest in some area.
- A count layer names its unit in the classes, not in the title. Count layers and ranks show no city value.
- An election layer ends with the bold line „Die Karte beschreibt Gebiete, nicht Menschen.“
- In candidates mode the title is „Kriterien erfüllt“, without a note line. White means none, the teal steps count the
  criteria met, and the hit swatch has the orange border. A grey row names the small Bezirke where one exists.
- On the phone and in low windows the legend starts collapsed. Title and note stay visible; a tap toggles the body
  (▸/▾). An open legend scrolls within the free height of the map.
- `tests/browser/mobile/phone.spec.mjs` keeps the note of a collapsed legend within two lines at 220 px.

### Tooltip

- One tooltip shows the area and every visible overlay at the point (`web/js/05_tooltip.js`). The overlay rows stand
  below a thin line, in overlay order.
- It is at most 320 px wide; long titles wrap. At the right edge it flips left; at the top and bottom it moves in.
- On a narrow map it goes above or below the point, without its arrow, and never covers the point. It stays above the
  phone panel.
- With a mouse it is computed at most once per frame. It hides over controls, outside the map and on a move or zoom.
  On touch it stays until the next tap or a move of the map.

### Exploring an area

- A mouse click or the tooltip button explores an area (`web/js/09_explore.js`). The tab „Gebiet“ opens, and the map
  flies to the area (zoom at most 15, above the phone panel).
- The other areas turn light grey. The explored area gets a black border of at least 3 px and lies on top.
- Classes and legend stay those of the whole city, and a candidate hit keeps its orange border. Why: the explored
  area stays comparable with the city.
- „Stadt“ and „Kandidaten“ end exploring and restore the view before. „Hilfe“ and closing the phone panel keep it.
- A switch in the details line of „Gebiet“ keeps exploring: no zoom, no flight, the area stays.
- On a change of level an explored Bezirk becomes its Stadtteil. A Stadtteil has no Bezirk (`APP.areaFor`).
- The profile keeps the area and the level it was chosen on (`APP.state.profile`). A level without a match shows a
  note. Back on the level of the area, the tab „Gebiet“ shows it again.
- The tooltip of the explored area has no button „Gebiet erkunden“.

### Profile and pressed row

- `APP.renderProfile` is the only writer of the markup of the tab „Gebiet“ (`tests/test_architecture.py`).
  `APP.syncProfile` and `APP.syncDetails` only set the pressed row and the names.
- Under the head (name, population line, warning of a small area) stands the details line, before „Eigentum“. It is a
  native `<details>`, so keyboard and screen reader work without own code. The summary holds an h3 like the other
  headings, with the short names of the overlays that are on, grey and small like a date. Thin lines above and below,
  ▸ closed and ▾ open. Open, it holds the overlay rows of „Stadt“ (Overlays). Without a profile there is no line.
- The line starts closed on each page load. Open or closed then stays while the page is open (`APP.detailsOpen`):
  another area, level or layer redraws the profile and keeps it. It is not part of a map link.
- The names follow every change of an overlay, in either tab or by a link (`APP.syncDetails`), without a redraw.
  Why: open ⓘ and the scroll position of the profile stay.
- Ownership shows a stacked bar in the owner colours, then a table with swatches, the area value and the city value.
- Other rows show label, value and a bar on a grey track. The bar is plain grey (`--bar-plain`), or the colour of the
  list. A black 2 px mark shows the city value.
- The breakdown of a layer (`breakdown_of`) shows as indented bars under its row: the lead line of the layer, then one
  row per entry with value, bar and city mark. The rows are no buttons and carry no ⓘ. Why: the ⓘ of the layer
  explains them.
- The breakdown bars share one scale, from 0 to the next multiple of 10 above the largest value of all districts and the
  city. Why: a scale per row would make the bars look alike.
- The breakdown bars take the ramp of the layer from the darkest step down, the first entry darkest.
- A row with its own layer is a button. A click, Enter or Space shows that layer on the map.
- The row of the layer on the map is pressed: a 5 px black mark in the free left edge and a bold title.
- Rows with a layer reach into the free edge of the tab (`--pad`). Why: the mark must never cover the first letter.
- In a table the mark lies on the first cell. Why: WebKit draws no `box-shadow` on a `tr`.
- The bar of the pressed row takes the class colour that the area has on the map, with a `#555` border. Why: the colour
  ties the row to the map; the border keeps the lightest class visible on the grey track.
- Without a class colour („k. A.“, a grey small Bezirk, a list colour) the bar keeps its own colour.
- A mouse hover tints a row light grey. On touch a row and the details line are at least 32 px high. Guarded by
  `tests/browser/desktop/profile-explore.spec.mjs` and `tests/browser/mobile/phone.spec.mjs` (also the height of the
  details line).

### Overlays

- The heading of the overlays is „Details“ (`APP.OVERLAY_HEADING`, text `ui.layers.details`).
  `APP.overlayRows(prefix)` builds the rows (checkbox, ⓘ, grid legend) and is the only place with the checkbox markup.
  One delegated `change` listener on the sidebar serves every checkbox, and `APP.setOverlay` sets all boxes of an
  overlay and the names of the details line.
- The rows stand in two places: open at the end of „Stadt“, and in the details line of „Gebiet“. Each place has its ⓘ
  key prefix (`overlay-`, `area-overlay-`). Why: the ids stay unique, and an ⓘ opens only in its own tab.
- Overlays stay readable on every layer colour: dark lines on a white casing, a pattern instead of a flat fill.
- Milieuschutz is black with a diagonal hatch; in procedure it is a dashed black line. Both are on at the start.
- Ortsbildsatzung is blue with dots; in procedure dashed blue. B-Pläne im Verfahren are a violet line. Bodenrichtwert
  zones are thin grey lines.
- The 100-m grid shows each cell in the colour of its largest owner group, from zoom 14. Below, the key asks to zoom.
- The low flat roofs are dark brown (`#5a3210`). A counted roof has a heavy outline on a white casing and a brown
  cross-hatch. A roof that does not count has a thin outline on a white casing and no fill. No flat fill and no dashes
  (dashes mean „im Verfahren“). The key has one row for each look.
- Building gaps are magenta (`#c51b7d`, the ramp end of the layer `GAP_AREA`). One look for every drawn parcel, counted
  or to check on site: a 2.5 px outline on a white casing, no fill. The key has one row „Baulücke“. The tooltip says
  „Muss vor Ort geprüft werden.“ for a site gap and never „Zählt nicht“. ΔE (CIEDE2000) to the nearest colour:
  20.9 (`#6a3d9a`), then 24.6 to 27 for the owner reds and violets. No minimum zoom: the drawn gaps are few.
- Each overlay may set a minimum zoom (`minZoom`, `zoomNote` in `APP.overlays`): grid 14, flat roofs 15. Below it the
  overlay is not drawn and the key shows its note. The roofs are 4,000 polygons: they must not exist at low zoom.
- Overlays catch no pointer (`interactive: false`), so a click reaches the area below. Milieuschutz lies on top
  (`APP.FRONT` in `web/js/04_overlays.js`).
- The legend key has one row per visible overlay; its swatch looks like the line on the map. An overlay without
  features has no checkbox, no ⓘ and no key row.

### Candidates

- Areas fill by the share of criteria met, in the teal ramp. An area that meets none is white.
- A hit (all criteria met) gets a 3.5 px orange border (`HIT_BORDER`). Why: Milieuschutz is drawn black, so a black
  border would look like Milieuschutz.
- Each criterion shows a histogram of the areas in light teal. The solid black line is the threshold. The dashed dark
  teal line is the city value.

### ⓘ and written sum

- The ⓘ is a round button with a grey symbol; open, it fills grey with a white symbol. Its protocol opens below its
  row, with a grey line at the left. Each label stands above its value.
- An indicator with a prose Rechnung and a worked example has two entries in the ⓘ: the prose, then the sum
  (`APP.infoEntries` in `web/js/01_base.js`). The ⓘ of a chart view may carry several sums (`calc_examples`), each
  under its own label; the ⓘ of the columns of Neubau and of the wage bars have two.
- A worked example is a written sum: operator, the number aligned right, then what the number is.
- The line above a subtotal or the result runs under operator and number only.
- The last row shows the map value at 24 px, without box or background. Why: size and line make it stand out; the accent
  stays for navigation and the ⓘ.

## Colours

### Interface

| Custom property | Colour | Use |
|---|---|---|
| `--accent` | `#6b6b6b` | the ⓘ, line of the ⓘ protocol |
| `--bar-plain` | `#8c8c8c` | default profile bar |
| `--text` | `#1a1a1a` | text; the population line and the end labels of the data lines in the view Neubau |
| `--grey` | `#6b6b6b` | secondary text, notes, sources |
| `--line` | `#d9d9d9` | thin rules and borders |

- The interface has no colour: black, white and greys. Colour belongs to the data. A profile bar without a colour
  of its own is grey.
- Teal is no longer a colour of the interface. It stays a data ramp where a theme has no colour of its own.

### Ramps

- Every layer ramps in five steps from almost white to its colour. `pipeline/shared/core/colours.py` builds the ramps;
  the browser reads the finished colours (`Indicator.colors`).
- The catalog of each use case names the ramp of its layer: a named ramp (teal, blue, purple, orange, red) or
  `color:#rrggbb` for the party lists and the owner groups. An unknown ramp falls back to teal.
- A light end colour (OKLab lightness above 0.59) ends darker. Why: light grey or FDP yellow would vanish.

### Owner groups

- `pipeline/shared/core/palette.py` holds the owner colours. The view Trend and the map catalog read it.
- Greys stand for „Privat“, reds around `#d40000` for „Gemeinschaft“. The scheme follows the city profile of the
  Rosa-Luxemburg-Stiftung.
- Only the ownership layers use this palette: choropleths, profile, grid and grid key. Other themes keep their ramps.

| Constant | Colour | View Trend | Map |
|---|---|---|---|
| `HOUSING_COMPANY` | `#262626` | Privatwirtschaftliche Wohnungsunternehmen; sector „Privat“ | Private Unternehmen (`COMPANIES`) |
| `OTHER_COMPANY` | `#575757` | Andere privatwirtschaftliche Unternehmen | – |
| `CONDO` | `#8c8c8c` | Wohnungseigentümer*innen (WEG) | – |
| `PERSON` | `#bfbfbf` | Privatpersonen | – |
| `PERSONS_AND_CONDOS` | `#a6a6a6` | – | Privatpersonen und WEG (halfway between the two greys) |
| `PUBLIC` | `#d40000` | Öffentlich; sector „Gemeinschaft“ | ABG und Nassauische Heimstätte |
| `STATE` | `#ffc9c2` | – (part of Öffentlich) | Bund oder Land |
| `COOP` | `#8c0000` | Genossenschaften | Genossenschaften |
| `NONPROFIT` | `#f07067` | Organisationen ohne Erwerbszweck | Organisationen ohne Erwerbszweck (profile and grid only) |

- The layer „Bund oder Land“ ramps to `#d40000`. Why: a ramp to its light red turns muddy when darkened.
- On the grid any two groups can touch. Check a new owner colour against all others with the palette validator of the
  dataviz skill: ΔE at least 15 with normal vision.
- `tests/shared/core/test_palette.py` and `tests/map/assembly/test_catalog.py` pin the colours.

### Special colours

| Colour | Use |
|---|---|
| `#e8590c` (`HIT_BORDER`) | border of a candidate hit; no overlay uses orange |
| `#d40000` (`SUBSIDISED`) | subsidised dwellings and the line of the dwellings in the view Neubau |
| `#8c0000` (`RENT_NEW` = `COOP`), `#f07067` (`RENT_OLD` = `NONPROFIT`) | rents of new and of older contracts in the view Neubau, in the red family of the house |
| `#8c8c8c` (`REFERENCE_PRICES`), `#6b6b6b` (`REFERENCE_WAGES`) | the edges of the band: prices solid, wages dashed |
| `#e6e6e6` (`REFERENCE_BAND`) | the band between prices and wages |
| `#d40000` (`PUBLIC`) | the warm rent in the wage bars of the view Miete, with white numbers |
| `#ffc9c2` (`STATE`), `#f07067`, `#d40000`, `#8c0000` | the burden classes from „unter 30 %“ to „50 % und mehr“ in the view Miete: darker means a heavier burden |
| `#555` | border of the areas and of the pressed profile bar |
| `#d0d0d0`, dashed | small Bezirke |
| `#e8e8e8`, border `#bbb` | the other areas while exploring |
| `#1a1a1a`; `#1d4f91`; `#6a3d9a`; `#7f7f7f` | overlays: Milieuschutz; Ortsbildsatzung; B-Pläne; Bodenrichtwert zones |
| `#5a3210` | overlay: low flat roofs |
| `#c51b7d` | overlay: building gaps; ramp end of `GAP_AREA` |
| `#fff3cd` | warning box of a small area in the profile |

## View Trend

`web/js/06_history.js`. Four charts of ownership 2011 and 2022, plain SVG without a chart library. Texts and numbers
come from Python (`pipeline/use_cases/ownership_history/README.md`).

### Charts

- `houses`: per year a bar of buildings („Häuser“) above a bar of dwellings, joined by bands. The groups stand in bar
  order: the sector „Privat“ from the left, then „Gemeinschaft“.
- `decades` and `sizes`: bar pairs per class, 2011 light grey `#bdbdbd`, 2022 dark grey `#4d4d4d`. The key names the
  unit („Häuser 2011“).
- `arrows`: per group a thin grey arrow for buildings and a thick arrow in the group colour for dwellings. Each runs
  from a circle (2011) to its head (2022) on an axis from 0 to 70 %.
- The two company classes stand out: denser bands and bold arrow labels.
- A number stands inside a bar only at a contrast of at least 4.5:1 and with 4 px room on each side. Otherwise the
  tooltip carries it. Text colour and contrast come from Python.
- A thick arrow keeps 3:1 against white; a lighter group colour is darkened in its own hue (`line_on` in
  `pipeline/shared/core/colours.py`).
- An arrow shorter than 14 px shows as circle and dot; the tooltip holds both values.
- Text is 14 px, secondary labels 12 px. A number and its „%“ never break apart (`APP.keepUnits`).
- One tooltip serves all charts. With a mouse it follows the pointer. On touch a tap shows it above the finger; a tap
  elsewhere or a scroll hides it. It shows the plain text of `data-tip`; the line charts of Neubau opt in to rows
  with a swatch (`APP.tipContent`).
- Every tooltip of a group carries its description. Examples stand only in the tooltips of 2022 and of the arrows.
- Invisible strips widen the hit area of thin arrows and of the sector labels. Numbers in bars catch no pointer.

### Sector boundary

- Per year a black line (`#1a1a1a`, 2.5 px) follows the boundary between „Privat“ and „Gemeinschaft“. It runs from
  just above the buildings bar, along the edge of the band, to below the dwellings bar.
- Under the dwellings the two sector labels face each other at the boundary, bold, each in its main colour: „Privat“
  `#262626` to the left, „Gemeinschaft“ `#d40000` to the right. Each label has a tooltip with the count and the groups.
- In 2022 a dashed grey line (`#6b6b6b`) marks the boundary of 2011 on the dwellings, with the text „Grenze 2011“.
- On a narrow chart the line bends below the dwellings to the point where both labels fit. The labels are placed for
  the current numbers; they do not move away from an edge.

## View Neubau

`web/js/08_new_construction.js`. Two figures: completed dwellings per year, and below them the block of rents, prices
and wages with two index charts (`pipeline/use_cases/new_construction/README.md`).

Columns:

- One column per year. New construction is a hollow frame: white with a black 1.5 px outline.
- The subsidised part fills the frame from the bottom in the red of the house (`SUBSIDISED`). Its key says „(Miete
  gebunden)“. Why: in the view Trend red means „Öffentlich“, but subsidised says nothing about the owner.
- Provisional years are hatched in the same red. The latest year has a 3 px outline and a bold total.
- Conversions sit on top as a dashed frame. Why: they are not new, so they get no solid frame.
- Above a column stands the total of all dwellings, below it the year and the share in red. No axis, no grid lines.
- The key has four entries: solid frame, red, hatched, dashed frame. The ⓘ closes the lead line; its protocol opens
  below the lead.
- The last word of each lead stands with its ⓘ in a `span.keep` that does not wrap. Why: Chrome breaks before a button
  even after a no-break space, and the ⓘ would stand alone on the next line.

Block of rents (`APP.rentsChart`):

- One figure: heading, lead with ⓘ, then per chart a title (bold, 15 px), one line below it, the key (phones only), one
  svg and, under chart 1 in the wide drawing, the note of the old base. One source line stands under both charts. The
  protocol of the ⓘ opens below the lead.
- The source line names its sources itself („Quellen:“). It has no „Quelle:“ in front, unlike the line of the columns.
- Both charts show the years 2017 to 2025, one slot per year, the value at the centre of the slot. Stocks count on
  31.12., rents, prices and wages at mid-year; all share the slot of their year.
- The value axis is an index with 2017 = 100. Chart 1 runs from 95 to 140 with a tick every 10 from 100, chart 2 from 86
  to 112 with a tick every 5 from 90 (`RENT_AXES` in `catalog.py`). Neither starts at 0. Thin grid lines (`#efefef`)
  run across, tick labels stand at the left edge. `rents_view` stops if a value lies outside its axis.
- The year labels of the survey years (`survey_years`: 2017, 2021, 2023, 2025) keep the ink colour. Every other year
  is grey (`--grey`), in the same font and weight. Why: the ink shows where a rent was measured.
- Prices and wages are a scale, not data. A light grey band (`REFERENCE_BAND`) fills the space between the two lines.
  It runs through the values of the wages and back through the prices. It lies under every line, right after the
  grid. Where the two lines cross, the band crosses too.
  Why: the lead compares the rents with the prices and the wages together.
- Each reference is a thin edge of the band: 1.5 units wide, round joins, drawn under the data lines. The prices are
  solid (`REFERENCE_PRICES`), the wages dashed with `5 3` and flat ends (`REFERENCE_WAGES`).
- Dwellings in the red of the view (`SUBSIDISED`) 2.5 units wide, population in black (`--text`) 2 units. Chart 1
  only. The two lines have no dot: a dot marks a survey day of the Mietspiegel, and a stock is counted every year, on
  31.12.
  Why red: the same look as the columns above. Red then means two things in the view, so each figure names its own
  lines: the end labels, and on phones the key.
- The rents of new contracts are dark red 3 units wide (`RENT_NEW`), those of older contracts light red 2.5 units
  (`RENT_OLD`). A rent exists in a survey year only (2017, 2021, 2023, 2025). The line joins these years and carries
  a dot in each (r 4.5, white rim). Chart 1 and 2. These are the only dots besides the hollow ones.
  Why red: the rents belong to the dwellings („Ich zahle Miete für meine Wohnung“), so they take the red family of the
  house. The light red keeps only about 2.9:1 against white. Every line is named by its end label or the key, so
  colour alone never tells them apart.
- The base changes in 2022 (Zensus 2022), chart 1 only. No segment joins 2021 and 2022. A dashed grey line stands
  between them, with the note „ab 2022 Zensus 2022“ left of it at the foot. Per stock line a dotted segment (2 units
  wide) leads from 2021 to a hollow dot (white, r 4, rim in the colour of the series) at the value of 2022 on the old
  base. Each hollow dot has its own tooltip.
- The end labels stand right of 2025: the value in bold with one decimal, then the name in regular weight in the wide
  drawing. Each label stands at the height of its value, from the top in the order of the values. A label keeps at
  least 17 units from the one above and moves down for it. If the last label falls below the base line, all move up
  together. A thin grey leader line joins each label to the end of its line. The text is in the ink colour for the
  data lines and grey (`--grey`) for the references.
- The key serves phones. It shows below `APP.CONSTRUCTION_WIDE` and is hidden from there on, where the end labels name
  the lines. Each layout sets it, also when the drawing keeps its width. Its entries stand one below the other in one
  column, in the order of the line ends from the top (`end_order`), then the old base. Chart 1 has seven entries,
  chart 2 four. The names are in normal weight, those of the references grey.
- A key swatch shows the line as the chart draws it: a rent line with a dot in its middle, a line of a stock without
  one (the entry says so with `dot`), the old base as a dotted line (the `dash` of its entry) to a hollow dot. A
  reference is a short piece of the band with its edge, in the colour, width and dash of the edge. The edge lies at
  the top for the reference with the higher last value and at the bottom for the other (`edge`).
- The note of the old base serves the wide drawing. It stands under the svg of chart 1: one line of 13 px in grey, the
  swatch of the old base in front. It is hidden on phones, where the key holds the same entry.
- One tooltip per year slot: a transparent hit area over the full height. The hollow dots keep their own tooltips.
- The tooltip of a year has a bold head, one row per series and a note. A row has a swatch in the colour, the width
  and the dash of its line, the value in bold and the label. This tooltip builds nodes. A chart opts in with
  `APP.tipContent` (`web/js/06_history.js`); every other tooltip stays the plain text of its `data-tip`.
- One `role="img"` svg per chart (class `rents`) with an `aria-label` of the chart title and every tooltip.
- The colours, widths, dashes, labels and positions on the axis come from Python. `web/map.css` holds only what is not
  data: the font sizes of ticks and notes (12 px), the grey of the other years, the white halo of end labels and notes,
  the lines of grid (`#efefef`), break and leaders, and the layout of the key and the note. Apart from the grid they
  use the interface token `--grey`, not colours of the payload.
- The wide drawing is 760 units wide with a margin of 46 units on the left and 200 on the right for the end labels. The
  plot is 300 units high in chart 1 and 230 in chart 2. Line widths are in units of the svg. A narrow drawing is drawn
  in px, so a unit is a px there.
- The ⓘ (`housing-rents`) closes the lead line of the block.

## View Miete

`web/js/10_rent_burden.js`. Two figures below each other: the wage example as wage bars, and the tenants by income
group as bars (`pipeline/use_cases/rent_burden/README.md`). Each figure has a heading, a lead with its ⓘ, its
drawings and one source line. The source line names its sources itself, as in the block of rents.

### Wage example

- It shows the latest survey year of the Mietspiegel only (`RENT_TO`). Why: from 2017 to 2025 the lines of the shares
  barely moved, so the time axis carried no message.
- One row per person: a hollow black frame as wide as the net wage, on one scale for all rows (the highest net wage
  fills the plot). From its left the red block of the warm rent (`PUBLIC`) fills the frame. It is equally wide in
  every row: the same flat costs the same rent. Why euros, not 100 % bars: the eye sees the same rent take a large
  part of a short bar and a small part of a long one.
- The block shows the share in white where it fits, by the rule of the segments below (`APP.BURDEN_CHAR`). Else the
  tooltip carries it.
- A switch above the line of `explain` shows „Neuer Vertrag“ (default) or „Älterer Vertrag“. Its buttons are
  underlined like the tabs of the sidebar, not the black block of the header. The choice survives every redraw. A
  switch moves the block from its old width (CSS transform, 0.4 s, none under `prefers-reduced-motion`); the number
  shows when the block stands.
- Wide: one drawing 760 units wide that scales, like the bars. Name and net wage stand left of the frame. What is left
  stands inside the white part of the frame, right-aligned, or right of the frame where it does not fit. A dashed
  guide at the right edge of the blocks runs through all rows. The warm rent is named once above it.
- Narrow (below `APP.CONSTRUCTION_WIDE`): drawn in px at its room. Name and a sub line (net wage, what is left) stand
  above the frame. The warm rent is named once on top. No guide: it would cross the labels.
- Every row has a tooltip: contract, person, warm rent, net wage, share and what is left.
- One `role="img"` svg (class `wage`) with an `aria-label` of the title and the tooltips of both contracts.

### Bars

- One bar per income group, split into the four burden classes in class order. A bar is 100 % of its group. A thin
  white line separates the segments.
- Wide: one drawing 760 units wide that scales. The label (the group, the median below it) stands left of its bar.
- Narrow (below `APP.CONSTRUCTION_WIDE`): drawn in px at its room. The label stands above its bar in one line.
- The key stands above the bars: one line in the wide drawing, one column on phones.
- A segment shows its number only where the payload has `text` and the number fits at the current width with 4 px on
  each side. Python sets `text` for a share of at least 9 points and a contrast of at least 4.5:1 (`segment_text`).
  The browser estimates the width of the number (`APP.BURDEN_CHAR` per character), because the svg is not in the page
  yet.
- Every segment and every label has a tooltip, also where the number shows.
- One `role="img"` svg (class `burden`) with an `aria-label` of the title and every tooltip.

## Phone and tablet

- Nothing scrolls sideways: not the page, not a chart, not the profile table, not an open legend.
- The Trend charts measure the room of the chart, not the window. From 600 px of room (`APP.WIDE`) a chart is one
  drawing 760 units wide that scales.
- Below 600 px a Trend chart is drawn at its room in px, so the text keeps its size. Row labels stand above their bars
  or arrows. In `houses` „Wohnungen“ stands below its bar, and the sector labels move one row lower.
- The view Neubau switches at 700 px of room (`APP.CONSTRUCTION_WIDE`). Below, it draws one row per year: year, bar,
  total. The share stands in the tooltip only.
  Why 700: its labels are 12 units high and measure 12 × 700 / 760 ≈ 11 px at the switch.
- The two charts of the block of rents switch at the same width. Below `APP.CONSTRUCTION_WIDE` they keep the
  orientation of the wide drawing (years across, values up) and are drawn in px at their room: the plot 220 px high,
  margins of 34 px on the left and 58 px on the right. Years stand at 2017, 2019, 2021, 2023 and 2025. 2019 is grey.
  The end labels show the value only; their names are in the key. A tap on the slot of a year shows its tooltip. A
  slot is about 30 px wide at 390 px, so a tap may hit the year next to it. The tooltip names its year.
  Why not rows with the axes across: the user saw the lines run down and read it as a fall. The lines rise as on a wide
  screen.
- A narrow drawing keeps every text at least 11 px.
- A resize or a turn of the phone redraws the charts after 150 ms.
- The medium layout serves a tablet upright (768 px) and a phone held across.
- `tests/browser/mobile/` runs iPhone SE, iPhone 15 and iPhone 15 across in WebKit, and 390 px and 768 px with
  touch in Chrome. It checks every chart text and mark inside the window, at least 11 px and free of the others. In
  the charts of rents every text also stays inside its svg, and the key is one column in the order of the line ends.
  The key and the note of the old base switch at 700 px of room in both directions.
- The view Miete switches at `APP.CONSTRUCTION_WIDE` too, measured on the room of the bars.
  `tests/browser/desktop/rent-burden.spec.mjs` checks it at 1400 px and at 420, 360, 320 and 300 px, both contracts,
  and the switch at 700 px of room, also after a resize while the view was hidden. It checks the four view buttons in
  one line from 300 to 390 px.
- On phones, across and on the tablet, `tests/browser/mobile/phone.spec.mjs` and
  `tests/browser/mobile/medium.spec.mjs` check the view Miete: every text inside the window and its svg, at least
  11 px and free of the others; the segments add up to the full bar; the key of the bars is one column in the narrow
  drawing. On a phone a tap on a row of the wage bars, a segment or a label shows its tooltip inside the window.
- `tests/browser/desktop/trend.spec.mjs` checks the Trend charts in the narrow drawing at 420 px and in the 760-unit
  drawing at 1400 px. `tests/browser/desktop/new-construction.spec.mjs` does the same for the view Neubau and the
  charts of rents. In the wide drawing of rents it also checks the band, the thin dashed edges, the dots, the year
  labels, the hidden key and the note.
