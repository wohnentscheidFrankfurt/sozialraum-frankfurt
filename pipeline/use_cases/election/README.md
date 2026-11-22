# election: „Wahl“

## Shows
`ELEC_STRONGEST`, `ELEC_TURNOUT` and one share per list (`ELEC_<LIST>`, lists under 2 % in Frankfurt as
`ELEC_OTHER`, named by the text `other_share.name`). Stadtteile only. `ELEC_VOTERS` is the count of the turnout
(`count_of`, no layer): the tooltip reads „Wählende: 1.343 von 2.871“ with `ELEC_ELIGIBLE` (`count_total`). It has no
city value.

## Formula
1. Share of a list = votes of the list ÷ valid votes in the Stadtteil (Stadtverordnetenwahl, with postal votes).
2. Turnout = voters ÷ eligible voters.
3. Strongest list = the list with the most votes in the Stadtteil.

## Why
The Stadtverordnetenwahl 2026 gives the political context per Stadtteil. The title names the
Stadtverordnetenwahl, because the Ortsbeiratswahl took place on the same day.

## Inputs
No dataset. The votemanager files in `sources/frankfurt/offices/` (`ELECTION_RESULT_JSON`, `ELECTION_CITY_CSV`,
`ELECTION_QUARTERS_CSV` in `pipeline/config.py`), `reference/party_colors.csv`, the gazette (Amtsblatt) in
`sources/frankfurt/offices/`.

## Output
`election_by_quarter`, `election_lists` (lists shown, colours, city shares), `election_city`, `election_checks`.

## Checks
- The Stadtteile add up to the city result in every field.
- Every number of the city result stands in the official gazette.

4. Colour of a list: `reference/party_colors.csv` (Statistikportal), else the colour of votemanager, else grey
   `#9e9e9e`; only valid `#rrggbb`.
5. The ramp of a list has 5 steps mixed with white (88, 68, 46, 22 and 0 %). If the OKLab lightness of the colour is
   above 0.59, the dark end is pulled towards black to L 0.57 (`pipeline/shared/core/colours.py`).

## Limits
- Postal votes are counted per Stadtteil as votemanager publishes them.
