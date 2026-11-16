"""Paths, source files and download URLs. The only module that builds paths."""
from __future__ import annotations

import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "cache"
INTERIM = ROOT / "interim"
OUTPUT = ROOT / "output"
EXPORTS = OUTPUT / "data"  # stays local, never published
REFERENCE = ROOT / "reference"
WEB = ROOT / "web"
SOURCES = ROOT / "sources"  # originals, each exactly once, in folders by origin (docs/architecture.md, Layout)
CITY = SOURCES / "frankfurt"  # publications of the city of Frankfurt, one folder per publishing body
MAP_NAME = "sozialraum-frankfurt.html"
ZENSUS_GRID = SOURCES / "zensus" / "grid"
FETCHED_CSV = SOURCES / "fetched.csv"  # file below sources/, URL, date of the download (pipeline/update_sources.py)
# Frankfurt extracts of the 100 m grids: download in cache/ -> extract in sources/ (pipeline/update_sources.py)
GRID_EXTRACTS = {
    "zensus_population.zip": ZENSUS_GRID / "Zensus2022_Bevoelkerungszahl_100m-Gitter_Frankfurt.csv",
    "zensus_owner_rate.zip": ZENSUS_GRID / "Zensus2022_Eigentuemerquote_100m-Gitter_Frankfurt.csv",
    "zensus_rent.zip": ZENSUS_GRID / "Zensus2022_Durchschn_Nettokaltmiete_Anzahl_der_Wohnungen_100m-Gitter_Frankfurt.csv",
    "zensus_vacancy.zip": ZENSUS_GRID / "Zensus2022_Leerstandsquote_100m-Gitter_Frankfurt.csv",
    "zensus_vacancy_market.zip": ZENSUS_GRID / "Zensus2022_Marktaktive_Leerstandsquote_100m-Gitter_Frankfurt.csv",
    "zensus_dwellings.zip": ZENSUS_GRID / "Zensus2022_Flaeche_der_Wohnung_10m2_Intervalle_100m-Gitter_Frankfurt.csv",
    "zensus_ownership.zip": ZENSUS_GRID / "Zensus2022_Gebaeude_nach_Eigentumsform_100m_Gitterzellen_Frankfurt.csv",
    "zensus_buildings_by_size.zip": ZENSUS_GRID / "Zensus2022_Gebaeude_nach_Anzahl_der_Wohnungen_100m-Gitter_Frankfurt.csv",
    "zensus2011_dwellings.zip": ZENSUS_GRID / "Wohnungen100m_Frankfurt.csv",
    "zensus2011_buildings.zip": ZENSUS_GRID / "Geb100m_Frankfurt.csv",
}
# Frankfurt extracts of the 1 km grids of the vacancy rates, from the same ZIPs (pipeline/update_sources.py)
GRID_KM_EXTRACTS = {
    "zensus_vacancy.zip": ZENSUS_GRID / "Zensus2022_Leerstandsquote_1km-Gitter_Frankfurt.csv",
    "zensus_vacancy_market.zip": ZENSUS_GRID / "Zensus2022_Marktaktive_Leerstandsquote_1km-Gitter_Frankfurt.csv",
}

DISTRICTS_GML = CITY / "geodata" / "Stadtbezirke.gml"
QUARTERS_GML = CITY / "geodata" / "Stadtteile.gml"
MONITORING_CSV = CITY / "offices" / "Monitoring2024_Stadtbezirke_nach_Umfragebezirk.csv"
ZENSUS_4000W = SOURCES / "zensus" / "Zensus2022_4000W-2002_Frankfurt_2011_2022.csv"
ZENSUS_4000W_1011 = SOURCES / "zensus" / "Zensus2022_4000W-1011_Frankfurt_2011_2022.csv"
ZENSUS_3000G_2001 = SOURCES / "zensus" / "Zensus2022_3000G-2001_Frankfurt_2011_2022.csv"
ZENSUS_3000G_2007 = SOURCES / "zensus" / "Zensus2022_3000G-2007_Frankfurt_2011_2022.csv"
ZENSUS_4000W_2013 = SOURCES / "zensus" / "Zensus2022_4000W-2013_Frankfurt_2011_2022.csv"
ZENSUS_4000W_1008 = SOURCES / "zensus" / "Zensus2022_4000W-1008_Frankfurt_2011_2022.csv"
ZENSUS_4000W_0001 = SOURCES / "zensus" / "Zensus2022_4000W-0001_Frankfurt_2011_2022.csv"
ZENSUS_4000W_0004 = SOURCES / "zensus" / "Zensus2022_4000W-0004_Frankfurt.csv"
ABG_SITES_GEOJSON = SOURCES / "other" / "ABG-Holding-Karte.geojson"  # own research, as of 8.10.2026
# examples in the ⓘ of OWN_COMPANY (pipeline/use_cases/ownership_shares/catalog.py, EXAMPLES)
VONOVIA_PRESS_PDF = SOURCES / "companies" / "Vonovia_PM_2026-02-24_Frankfurt.pdf"
GWH_STOCK_PDF = CITY / "parlis" / "F_3283_2025.pdf"
GWH_REPORT_PDF = SOURCES / "companies" / "GWH_Geschaeftsbericht_2022.pdf"
INDUSTRIA_PAGE_HTML = SOURCES / "companies" / "Catella_2019_Living_Lyon.html"
HAMBURG_TRUST_PAGE_HTML = SOURCES / "companies" / "cash-online_2014-12-05_Hamburg_Trust_Little_East.html"
# examples in the tooltips of the view „Trend“ (pipeline/use_cases/ownership_history/catalog.py, EXAMPLES)
HOUSING_MARKET_REPORT_PDF = CITY / "parlis" / "B_430_2022_AN_Wohnungsmarktbericht.pdf"
BIMA_ANSWER_PDF = SOURCES / "other" / "BT-Drs_19_7092.pdf"
COOP_VBS_HTML = SOURCES / "companies" / "Kooperation_Frankfurt_vbs.html"
COOP_BWV_HTML = SOURCES / "companies" / "Kooperation_Frankfurt_bwv.html"
COOP_BVH_HTML = SOURCES / "companies" / "Kooperation_Frankfurt_bvh.html"
CHURCH_INTERVIEW_HTML = SOURCES / "other" / "efo-magazin_2019-09-17_Kirche_und_Immobilien.html"
SAHLE_SUBSIDISED_PDF = CITY / "parlis" / "F_677_2017.pdf"
# view „Neubau“ (pipeline/use_cases/new_construction/README.md)
REGIONAL_COMPLETIONS_CSV = SOURCES / "regionalstatistik" / "Regionalstatistik_31121-01-02-4_Frankfurt.csv"
REGIONAL_ALL_DWELLINGS_CSV = SOURCES / "regionalstatistik" / "Regionalstatistik_31121-03-02-4_Frankfurt.csv"
REGIONAL_NEW_NONRES_CSV = SOURCES / "regionalstatistik" / "Regionalstatistik_31121-02-02-4_Frankfurt.csv"
HSL_COMPLETIONS_2025_PDF = SOURCES / "hessen" / "statistics" / "fii2_j25.pdf"
HSL_COMPLETIONS_2024_PDF = SOURCES / "hessen" / "statistics" / "FII2_j24_a.pdf"
REGIONAL_STOCK_CSV = SOURCES / "regionalstatistik" / "Regionalstatistik_31231-02-01-4_Frankfurt.csv"
HSL_STOCK_2025_PDF = SOURCES / "hessen" / "statistics" / "fi1_j25.pdf"
HSL_STOCK_2022_OLD_BASE_PDF = SOURCES / "hessen" / "statistics" / "FI1_j22_a.pdf"  # 31.12.2022 on the GWZ 2011
REGIONAL_POPULATION_CSV = SOURCES / "regionalstatistik" / "Regionalstatistik_12411-01-01-4_Frankfurt.csv"
# 31.12.2022 on the Zensus 2011 (HSL A I 2 mit A II, A III, A V, 2. Halbjahr 2022)
HSL_POPULATION_2022_OLD_BASE_PDF = SOURCES / "hessen" / "statistics" / "AI2_AII_AIII_AV_22-2hj_a.pdf"
# 31.12.2025 on the Zensus 2022 (HSL A I 2 mit A II, A III, A V, 2. Halbjahr 2025), a check of the Regionaldatenbank
HSL_POPULATION_2025_PDF = SOURCES / "hessen" / "statistics" / "AI2_AII_AIII_AV_25-2hj_a.pdf"
SUBSIDISED_B12_PDF = CITY / "parlis" / "B_12_2024.pdf"
ANSWER_F_3150_2025_PDF = CITY / "parlis" / "F_3150_2025.pdf"
ANSWER_F_79_2026_PDF = CITY / "parlis" / "F_79_2026.pdf"
ANSWER_F_9_2026_PDF = CITY / "parlis" / "F_9_2026.pdf"
ANSWER_F_158_2026_PDF = CITY / "parlis" / "F_158_2026.pdf"
ANSWER_B_483_2025_PDF = CITY / "parlis" / "B_483_2025.pdf"
# rents, prices and wages (pipeline/use_cases/new_construction/README.md): the Gutachten of the Mietspiegel hold the
# means of the new and the older contracts, the brochures the survey day
MIETSPIEGEL_2018_REPORT_PDF = CITY / "offices" / "64_S1_Frankfurter Mietspiegel 2018 - Gutachten_Dokumentation.pdf"
MIETSPIEGEL_2022_REPORT_PDF = CITY / "offices" / "64_S1_Frankfurter Mietspiegel 2022 - Gutachten_Dokumentation.pdf"
MIETSPIEGEL_2022_PDF = CITY / "offices" / "64_S1_Frankfurter Mietspiegel 2022.pdf"
MIETSPIEGEL_2024_REPORT_PDF = CITY / "offices" / "64_S1_Frankfurter Mietspiegel 2024 - Gutachten.pdf"
MIETSPIEGEL_2024_PDF = CITY / "offices" / "64_S1_Frankfurter Mietspiegel 2024.pdf"
MIETSPIEGEL_2026_REPORT_PDF = CITY / "offices" / "64_S1_Frankfurter_Mietspiegel_2026_Dokumentation.pdf"
MIETSPIEGEL_2026_PDF = CITY / "offices" / "64_S1_Frankfurter_Mietspiegel_2026.pdf"
HSL_PRICES_PDF = SOURCES / "hessen" / "statistics" / "mi2_j25.pdf"  # Verbraucherpreisindex Hessen, table 3
HSL_WAGES_XLSX = SOURCES / "hessen" / "statistics" / "pm_verdienste_q3_2025_statistikhessen.xlsx"
HOUSEHOLDS_CSV = CITY / "statistics" / "bevoelkerung_in_haushalten_stadtbezirke_.csv"  # Melderegister
SAHLE_PAGE_HTML = SOURCES / "companies" / "Sahle_Wohnen_Geschaeftsfuehrung.html"
ANNUAL_REPORT_PDF = CITY / "parlis" / "B_223_2026_AN1_Bericht_2025.pdf"
DWELLING_STOCK_XLSX = CITY / "statistics" / "Wohnungsbestand und Räume.xlsx"
SURVEY_REPORT_PDF = CITY / "statistics" / "FU_5_Leben_in_Frankfurt_2025.pdf"
SURVEY_REPORT_2024_PDF = CITY / "statistics" / "FU_4_Leben_in_Frankfurt_2024.pdf"
SURVEY_MICRODATA = {2024: CITY / "statistics" / "leben-in-frankfurt_2024.csv",
                    2025: CITY / "statistics" / "leben-in-frankfurt_2025.csv"}
GAZETTE_PDF = CITY / "offices" / "AB2026_Nr_S4 Wahlergebnis Kommunalwahl Frankfurt.pdf"
# view „Miete“ (pipeline/use_cases/rent_burden/README.md). The Entgeltstatistik of 31.12.2016 is read by the research
# only (mid-year sensitivity), not by the build.
BA_KDU_XLSX = {year: SOURCES / "arbeitsagentur" / f"kdu-06412-0-{year}06-xlsx.xlsx" for year in (2017, 2021, 2023, 2025)}
BA_WAGES_2017_XLSM = SOURCES / "arbeitsagentur" / "entgelt-d-0-201712-xlsm.xlsm"
BA_WAGES_SERIES_XLSX = SOURCES / "arbeitsagentur" / "entgelt-dwolk-0-202512-xlsx.xlsx"
HSL_WAGE_DISTRIBUTION_PDF = SOURCES / "hessen" / "statistics" / "ni9_j25_2aa.pdf"
HOUSING_MARKET_REPORT_2019_2020_PDF = CITY / "offices" / "Wohnungsmarktbericht 2019_2020.pdf"  # text version of B 430/2022

PARTY_COLORS_CSV = REFERENCE / "party_colors.csv"
EXPECTED_SOCIAL_PRESERVATION_CSV = REFERENCE / "social_preservation_expected.csv"
CHECK_REFERENCE_CSV = REFERENCE / "check_reference.csv"
MONITORING_CITY_VALUES_CSV = REFERENCE / "monitoring_city_values.csv"
FLAT_ROOFS_REFERENCE_CSV = REFERENCE / "flat_roofs_reference.csv"  # buildings read in the raw GML, check the extract
BUILDING_GAPS_REFERENCE_CSV = REFERENCE / "building_gaps_reference.csv"  # hand verdicts of the candidates
BUILDING_GAPS_PARCELS_CSV = REFERENCE / "building_gaps_parcels.csv"  # parcels read in the raw NAS, check the extract
BUILDING_GAPS_KNOWN_CSV = REFERENCE / "building_gaps_known.csv"  # known cases of the user
BUILDING_GAPS_EXAMPLES_CSV = REFERENCE / "building_gaps_examples.csv"  # the examples of the suitability texts
BMF_WAGE_TAX_CSV = REFERENCE / "bmf_wage_tax.csv"  # wage tax and Soli of the BMF calculators, checks the net wage

_ZENSUS_2022 = "https://www.destatis.de/static/DE/zensus/gitterdaten/"
_ZENSUS_2011 = "https://www.destatis.de/static/DE/zensus/2011_gitterdaten/"
_VOTEMANAGER = "https://votemanager-ffm.ekom21cdn.de/2026-03-15/06412000/daten/"
_PLANAS = "https://planas.frankfurt.de/wfs/"
_WFS_11 = "?service=WFS&version=1.1.0&request=GetFeature&srsName=EPSG:25832&typeName="

# 3D-Gebäudemodell LoD2 Hessen (HVBG, Geodaten online): the REST API of the download center names the package of all
# Frankfurt; its link holds a date, so update_lod2 reads it from the API (pipeline/update_sources.py)
LOD2_HOST = "https://gds.hessen.de"
LOD2_FOLDER = "3D-Daten/3D-Gebäudemodelle/3D-Gebäudemodelle LoD2/Kreisfreie Stadt Frankfurt"
LOD2_API = (LOD2_HOST + "/INTERSHOP/rest/WFS/HLBG-Geodaten-Site/-/downloadcenter?path="
            + urllib.parse.quote(LOD2_FOLDER) + "&navigation=all")
LOD2_PRODUCT_DESCRIPTION_PATH = ("/INTERSHOP/static/WFS/HLBG-Geodaten-Site/-/HLBG-Geodaten/de_DE/Downloadcenter/Daten/"
                                 "3D-Daten/Produktbeschreibung_3D-Gebäudemodelle.pdf")
LOD2_DIR = SOURCES / "hessen" / "lod2"
LOD2_PARTS_CSV = LOD2_DIR / "lod2_frankfurt_parts.csv.gz"  # one row per part of each building (sources/README.md)
LOD2_GEMARKUNGEN_CSV = LOD2_DIR / "lod2_frankfurt_gemarkungen.csv"
LOD2_PRODUCT_DESCRIPTION_PDF = LOD2_DIR / "Produktbeschreibung_3D-Gebäudemodelle.pdf"
LOD2_PACKAGE = CACHE / "lod2" / "frankfurt_lod2.zip"
LOD2_LISTING = CACHE / "lod2" / "listing.json"
# ALKIS (Liegenschaftskataster, NAS), DOM1 and DGM1 of Hessen: the same download center. The orthophoto comes from the
# free WMS (building gaps: ALKIS extracts and the cover of the candidates, sources/README.md)
ALKIS_FOLDER = "Liegenschaftskataster/Bestandsdatenausgabe Grundriss (xml)/Kreisfreie Stadt Frankfurt am Main"
DOM_FOLDER = "3D-Daten/Digitales Oberflächenmodell (DOM1)/Kreisfreie Stadt Frankfurt am Main"
DGM_FOLDER = "3D-Daten/Digitales Geländemodell (DGM1)/Kreisfreie Stadt Frankfurt am Main"
_CENTER = LOD2_HOST + "/INTERSHOP/rest/WFS/HLBG-Geodaten-Site/-/downloadcenter?path="
ALKIS_API = _CENTER + urllib.parse.quote(ALKIS_FOLDER) + "&navigation=all"
DOM_API = _CENTER + urllib.parse.quote(DOM_FOLDER) + "&navigation=all"
DGM_API = _CENTER + urllib.parse.quote(DGM_FOLDER) + "&navigation=all"
ALKIS_PACKAGE = CACHE / "alkis" / "frankfurt_alkis.zip"
DOM_PACKAGE = CACHE / "dom" / "frankfurt_dom1.zip"
DGM_PACKAGE = CACHE / "dgm" / "frankfurt_dgm1.zip"
ALKIS_LISTING = CACHE / "alkis" / "listing.json"
DOM_LISTING = CACHE / "dom" / "listing.json"
DGM_LISTING = CACHE / "dgm" / "listing.json"
DOP_WMS = "https://www.gds-srv.hessen.de/cgi-bin/lika-services/ogc-free-images.ows"
DOP_CACHE = CACHE / "dop"
ALKIS_DIR = SOURCES / "hessen" / "alkis"
ALKIS_PARCELS_CSV = ALKIS_DIR / "alkis_parcels.csv.gz"
ALKIS_BUILDINGS_CSV = ALKIS_DIR / "alkis_buildings.csv.gz"
ALKIS_LANDUSE_CSV = ALKIS_DIR / "alkis_landuse.csv.gz"
ALKIS_META_CSV = ALKIS_DIR / "alkis_meta.csv"
BUILDING_GAPS_COVER_CSV = ALKIS_DIR / "building_gaps_cover.csv"
# Synopsis of the HMWVW on Baupaket I (22.10.2025): the smallest Abstandsfläche of HBO § 6 (5), the wall strip of the
# flat roofs (pipeline/use_cases/flat_roofs/checks.py, check_building_code)
HBO_SYNOPSIS_PDF = SOURCES / "other" / "2025_HBO_Synopse_Baupaket_I.pdf"
DOWNLOADS = {  # file name in cache/ -> URL
    "zensus_population.zip": _ZENSUS_2022 + "Zensus2022_Bevoelkerungszahl.zip",
    "zensus_owner_rate.zip": _ZENSUS_2022 + "Eigentuemerquote_in_Gitterzellen.zip",
    "zensus_rent.zip": _ZENSUS_2022 + "Durchschnittliche_Nettokaltmiete_und_Anzahl_der_Wohnungen.zip",
    "zensus_vacancy.zip": _ZENSUS_2022 + "Leerstandsquote_in_Gitterzellen.zip",
    "zensus_vacancy_market.zip": _ZENSUS_2022 + "Marktaktive_Leerstandsquote_in_Gitterzellen.zip",
    "zensus_dwellings.zip": _ZENSUS_2022 + "Flaeche_der_Wohnung_10m2_Intervalle.zip",
    "zensus_ownership.zip": _ZENSUS_2022 + "Gebaeude_nach_Eigentumsform_100mGitter.zip",
    "zensus_buildings_by_size.zip": _ZENSUS_2022 + "Gebaeude_nach_Anzahl_der_Wohnungen_im_Gebaeude.zip",
    "zensus2011_dwellings.zip": _ZENSUS_2011 + "Wohnungen_im_100_Meter-Gitter.zip",
    "zensus2011_buildings.zip": _ZENSUS_2011 + "Gebaeude_und_Wohnungen_im_100_Meter-Gitter.zip",
    "election_quarters.csv": _VOTEMANAGER + "opendata/Open-Data-06412000-Stadtverordnetenwahl-Ortsteil.csv",
    "election_city.csv": _VOTEMANAGER + "opendata/Open-Data-06412000-Stadtverordnetenwahl-Gemeinde.csv",
    "election_result.json": _VOTEMANAGER + "api/wahl_54/ergebnis_ebene_3_id_1_0.json",
    "social_preservation.gml": _PLANAS + "erhaltungssatzungen" + _WFS_11 + "e-rv",
    "social_preservation_pending.gml": _PLANAS + "erhaltungssatzungen" + _WFS_11 + "e-iv",
    "lod2_product_description.pdf": LOD2_HOST + urllib.parse.quote(LOD2_PRODUCT_DESCRIPTION_PATH),
    "pending_plans.gml": _PLANAS + "bebauungsplaene_geltungsbereiche" + _WFS_11 + "bplan_iv",
}
OFFICES = CITY / "offices"
GEODATA = CITY / "geodata"
BORIS_DIR = SOURCES / "hessen" / "boris"  # pages of the BORIS WFS, unchanged (pipeline/update_sources.py)
BORIS_VALUES_CSV = BORIS_DIR / "values_2026.csv"  # value of 2026 per zone number (pipeline/update_sources.py)
SNAPSHOTS = {  # download in cache/ -> copy in sources/, unchanged (pipeline/update_sources.py)
    "election_quarters.csv": OFFICES / "Open-Data-06412000-Stadtverordnetenwahl-Ortsteil.csv",
    "election_city.csv": OFFICES / "Open-Data-06412000-Stadtverordnetenwahl-Gemeinde.csv",
    "election_result.json": OFFICES / "votemanager_ergebnis_ebene_3_id_1_0.json",
    "social_preservation.gml": GEODATA / "planAS_erhaltungssatzungen_e-rv.gml",
    "social_preservation_pending.gml": GEODATA / "planAS_erhaltungssatzungen_e-iv.gml",
    "pending_plans.gml": GEODATA / "planAS_bebauungsplaene_bplan_iv.gml",
    "lod2_product_description.pdf": LOD2_PRODUCT_DESCRIPTION_PDF,
}
# Long CSV extracts of two GENESIS web clients: download in cache/tables/ -> extract in sources/
# (pipeline/update_sources.py). File -> (table, key); the key is the statistic code plus the variable codes of the
# selection (sorted in the Zensus database). Not every extract is read by the build (sources/README.md).
ZENSUS_API = "https://ergebnisse.zensus2022.de/proxy/api/rest/tables/"
ZENSUS_REGION = "064120000000"  # Frankfurt am Main in GEOGM4, Zensus 2011 and 2022 on the territory of 2022
_ZENSUS_DB = SOURCES / "zensus"
ZENSUS_TABLES = {
    _ZENSUS_DB / "Zensus2022_1000A-0004_Frankfurt.csv": ("1000A-0004", "1000A GEOGM4"),
    ZENSUS_3000G_2001: ("3000G-2001", "3000G GEB001 GEBBJ5 GEBEG1 GEOGM4 STAG"),
    ZENSUS_3000G_2007: ("3000G-2007", "3000G GEB001 GEBEG1 GEBWG2 GEOGM4 STAG"),
    ZENSUS_4000W_0001: ("4000W-0001", "4000W GEOGM4 STAG"),
    ZENSUS_4000W_0004: ("4000W-0004", "4000W GEOGM4 STAG"),
    ZENSUS_4000W_1008: ("4000W-1008", "4000W GEBBJ7 GEOGM4 STAG WHG002"),
    ZENSUS_4000W_1011: ("4000W-1011", "4000W GEBEG1 GEOGM4 STAG WHG002"),
    ZENSUS_4000W: ("4000W-2002", "4000W GEBEG1 GEOGM4 STAG WHG002 WHGNZ2"),
    ZENSUS_4000W_2013: ("4000W-2013", "4000W GEBEG1 GEBWG2 GEOGM4 STAG WHG002"),
    _ZENSUS_DB / "Zensus2022_4000W-2013_Heizungsart_Frankfurt_2011_2022.csv":
        ("4000W-2013", "4000W GEBEG1 GEOGM4 HZGAT1 STAG WHG002"),
    _ZENSUS_DB / "Zensus2022_5000H-1001_Frankfurt_2011_2022.csv": ("5000H-1001", "5000H GEOGM4 HSH002 HSHGR2 STAG"),
    _ZENSUS_DB / "Zensus2022_5000H-1005_Frankfurt_2011_2022.csv": ("5000H-1005", "5000H GEOGM4 HSH002 HSHTP1 STAG"),
    _ZENSUS_DB / "Zensus2022_5000H-2001_Frankfurt_2011_2022.csv":
        ("5000H-2001", "5000H GEOGM4 HSH002 HSHGR2 HSHTP1 STAG"),
}
REGIONAL_API = "https://www.regionalstatistik.de/gngServer/api/rest/tables/"
REGIONAL_REGION = "06412"  # Frankfurt am Main in KREISE
REGIONAL_TABLES = {
    REGIONAL_COMPLETIONS_CSV: ("31121-01-02-4", "31121 BAUF03 GEBWH1 JAHR KREISE"),
    REGIONAL_NEW_NONRES_CSV: ("31121-02-02-4", "31121 BAUF04 JAHR KREISE"),
    REGIONAL_ALL_DWELLINGS_CSV: ("31121-03-02-4", "31121 WHGGR2 JAHR KREISE"),
    REGIONAL_STOCK_CSV: ("31231-02-01-4", "31231 GEBGR1 WHGGR1 STAG KREISE"),
    REGIONAL_POPULATION_CSV: ("12411-01-01-4", "12411 STAG GES KREISE"),
}
ELECTION_QUARTERS_CSV, ELECTION_CITY_CSV, ELECTION_RESULT_JSON = (SNAPSHOTS[k] for k in (
    "election_quarters.csv", "election_city.csv", "election_result.json"))
SOCIAL_PRESERVATION_GML, SOCIAL_PRESERVATION_PENDING_GML, PENDING_PLANS_GML = (SNAPSHOTS[k] for k in (
    "social_preservation.gml", "social_preservation_pending.gml", "pending_plans.gml"))
# planAS: preservation statutes and pending plans; their download date is the „Abruf“ of the map
WFS_FILES = (SOCIAL_PRESERVATION_GML, SOCIAL_PRESERVATION_PENDING_GML, PENDING_PLANS_GML)
BORIS_URL = ("https://www.gds.hessen.de/wfs2/boris/cgi-bin/brw/2024/wfs?SERVICE=WFS&VERSION=2.0.0"
             "&REQUEST=GetFeature&TYPENAMES=boris:BR_BodenrichtwertZonal"
             "&BBOX=462000,5540000,486000,5564000,urn:ogc:def:crs:EPSG::25832")
BORIS_PAGE_SIZE = 500
# The values of 1.1.2026: no WFS yet, so the WMS answers per point (GetFeatureInfo; land README, Inputs)
BORIS_VALUES_URL = ("https://www.gds-srv.hessen.de/cgi-bin/lika-services/ogc-free-maps.ows?language=ger&SERVICE=WMS"
                    "&VERSION=1.1.1&REQUEST=GetFeatureInfo&LAYERS=hboris_feature&QUERY_LAYERS=hboris_feature"
                    "&INFO_FORMAT=text/plain&FEATURE_COUNT=10&SRS=EPSG:25832&BBOX={x0},{y0},{x1},{y1}"
                    "&WIDTH=101&HEIGHT=101&X=50&Y=50")
