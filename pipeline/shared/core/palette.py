"""Colours of the owner groups, for the view „Trend“ and the map. Pure module.

As in the city profile of the Rosa-Luxemburg-Stiftung: greys for „Privat“, reds for „Gemeinschaft“ around the base
#d40000 (docs/design.md, Owner groups).
"""
from __future__ import annotations

# Zensus classes of the view „Trend“, in bar order
HOUSING_COMPANY = "#262626"
OTHER_COMPANY = "#575757"
CONDO = "#8c8c8c"
PERSON = "#bfbfbf"
PUBLIC = "#d40000"
# view „Neubau“: the subsidised part in the red of the house; the key says „Miete gebunden“, because subsidised says
# nothing about the owner (docs/design.md, View Neubau)
SUBSIDISED = PUBLIC
COOP = "#8c0000"
NONPROFIT = "#f07067"
# view „Neubau“, rents: the rents belong to the dwellings („Ich zahle Miete für meine Wohnung“), so they take the red
# family of the house. Prices and wages are a scale, not data: a light grey band between them with a thin grey edge
# each; their names (end labels, key) use the grey of the interface (docs/design.md, View Neubau)
RENT_NEW = COOP
RENT_OLD = NONPROFIT
REFERENCE_PRICES = "#8c8c8c"
REFERENCE_WAGES = "#6b6b6b"
REFERENCE_BAND = "#e6e6e6"

# Groups only the map has. Both company classes take the main colour of „Privat“. Privatpersonen and WEG lie halfway
# between their two greys. Bund oder Land is a fourth red, light enough to stay apart from the three of „Trend“.
COMPANIES = HOUSING_COMPANY
PERSONS_AND_CONDOS = "#a6a6a6"
STATE = "#ffc9c2"

# Border of a hit in the candidates (all criteria met). The overlays use black, white, blue and violet, so a hit
# differs from Milieuschutz (docs/design.md, Candidates).
HIT_BORDER = "#e8590c"
