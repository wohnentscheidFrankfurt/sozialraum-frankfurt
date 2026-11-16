# Monitoring 2024 on social segregation (part 1): read the tables per district (Stadtbezirk) from the PDF,
# assign districts to survey areas (Umfragebezirke) and quarters (Stadtteile) via the geodata, summarise the indicators.
# Call: python mon.py <Monitoring.pdf> <Umfragebezirke.gml> <Stadtbezirke.gml> <Stadtteile.gml> <output folder> [<Demographische Kennzahlen (Stadtbezirke).xlsx>]
# Values: column 2022. Rank: 115 minus index value of table 28 (114 ranks, rank 1 = most deprived); kept in memory for
# the research outputs, not written to Monitoring2024_Stadtbezirke_nach_Umfragebezirk.csv.
# The output columns keep the German names of the sources; the pipeline reads Monitoring2024_Stadtbezirke_nach_Umfragebezirk.csv.
# Gruppe_<column>: the number label of the source row as printed in that table (e.g. 202/203/213), empty if the table has no
# row for the district. The tables merge different districts, so a value shared by a group needs its label to be told apart.
import re, sys, os
import fitz, numpy as np, pandas as pd
from shapely.geometry import Polygon
from shapely.ops import unary_union

def layout_lines(pdf):
    # Collect the words of each line by y position so that table rows stay together
    out = []
    for p in fitz.open(pdf):
        out.append('=== page ===')
        lines = []
        for w in sorted(p.get_text('words'), key=lambda w: ((w[1] + w[3]) / 2, w[0])):
            yc = (w[1] + w[3]) / 2
            if lines and abs(lines[-1][0] - yc) < 2.5: lines[-1][1].append(w)
            else: lines.append([yc, [w]])
        for _, ws in lines:
            out.append('   '.join(w[4] for w in sorted(ws, key=lambda w: w[0])))
    return out

def load(path, id_field, name_field):
    text = open(path).read(); out = {}
    for member in re.split(r'<wfs:member>', text)[1:]:
        key = re.search(rf'<[^>]*:{id_field}>([^<]*)<', member).group(1); name = re.search(rf'<[^>]*:{name_field}>([^<]*)<', member).group(1)
        polys = []
        for polygon in re.findall(r'<gml:Polygon.*?</gml:Polygon>', member, re.S):
            rings = re.findall(r'<gml:posList[^>]*>(.*?)</gml:posList>', polygon, re.S)
            points = lambda t: (lambda v: list(zip(v[0::2], v[1::2])))(list(map(float, t.split())))
            if rings: polys.append(Polygon(points(rings[0]), [points(r) for r in rings[1:]]).buffer(0))
        out[key] = (name, unary_union(polys))
    return out

pdf_path, survey_areas_gml, districts_gml, quarters_gml, out_dir = sys.argv[1:6]
text_lines = layout_lines(pdf_path)
page_starts = [i for i, l in enumerate(text_lines) if l.startswith('=== page')]
def table_title(t): return [i for i, l in enumerate(text_lines) if re.search(rf'Tabelle\s+{t}:', l)][0]
def page_start_of(i): return max(p for p in page_starts if p <= i)
def page_end_of(i): return min([p for p in page_starts if p > i] + [len(text_lines)])

# Row: no. (also 591/592 or 325/27/28/29), name, 4 numbers (2009, 2019, 2022, change); '---' = no value, '*' = corrected value
number_re = r'(\*?-?\d+(?:,\d+)?|–+|-+)'
row_re = re.compile(rf'(?<![\d,])(\d+(?:/\d+)*)\s+([A-Za-zÄÖÜäöüß][A-Za-zÄÖÜäöüß.\-+ ]*?)\s+{number_re}\s+{number_re}\s+{number_re}\s+{number_re}(?![\d,])')
def ids_of(s):
    p = s.split('/'); first = p[0]
    return [int(first)] + [int(x) if len(x) >= len(first) else int(first[:len(first) - len(x)] + x) for x in p[1:]]
# Table: (number, end of the search range)
TABLES = {'Minderj_%': (2, lambda: table_title(3)), 'Alleinerz_%': (4, lambda: table_title(5)), 'ab65_%': (7, lambda: table_title(8)),
     'Migration_%': (9, lambda: table_title(10)), 'Arbeitslosendichte_%': (12, lambda: table_title(13)),
     'Mindestsich_%': (14, lambda: table_title(15)), 'GrusiAlter_%': (16, lambda: table_title(17)),
     'm2_pro_Kopf': (18, lambda: table_title(19)), 'Sozialwhg_%': (19, lambda: table_title(21)),
     'Benacht_Index': (28, lambda: page_end_of(table_title(29)))}
values, labels, merged_units = {}, {}, {}
for col, (table_no, end) in TABLES.items():
    rows, row_labels = {}, {}
    for l in text_lines[page_start_of(table_title(table_no)):end()]:
        for m in row_re.finditer(l):
            v = m.group(5).lstrip('*')
            if not re.match(r'-?\d', v): continue
            ids = ids_of(m.group(1))
            for i in ids:
                rows.setdefault(i, float(v.replace(',', '.'))); row_labels.setdefault(i, m.group(1))
            if col == 'Benacht_Index' and len(ids) > 1: merged_units[tuple(ids)] = m.group(1)
    values[col], labels[col] = rows, row_labels
# Table 14, row 362 (Bockenheim): covered by the map label in the PDF, value 2022 read off by hand
values['Mindestsich_%'].setdefault(362, 7.7)

GROUP_COLUMNS = ['Arbeitslosendichte_%', 'Mindestsich_%', 'Benacht_Index']
survey_areas = load(survey_areas_gml, 'UMFBZ_ID', 'UMFBZ_NAME'); districts = load(districts_gml, 'STBZ_ID', 'STBZ_NAME'); quarters = load(quarters_gml, 'STT_ID', 'STT_NAME')
recs = []
for key, (name, geometry) in districts.items():
    district_id = int(key)
    survey_area = max(survey_areas.values(), key=lambda x: x[1].intersection(geometry).area)[0]
    quarter = max(quarters.values(), key=lambda x: x[1].intersection(geometry).area)[0]
    unit = next((label for ids, label in merged_units.items() if district_id in ids), str(district_id))
    rec = {'STBZ': district_id, 'Name': name, 'Stadtteil': quarter, 'Umfragebezirk': survey_area, 'Einheit': unit}
    for c in TABLES: rec[c] = values[c].get(district_id, np.nan)
    for c in GROUP_COLUMNS: rec['Gruppe_' + c] = labels[c].get(district_id, '')
    recs.append(rec)
df = pd.DataFrame(recs).sort_values('STBZ')
df['Rang'] = 115 - df.Benacht_Index
print('missing values per table:', df[list(TABLES)].isna().sum().to_dict())
os.makedirs(out_dir, exist_ok=True)
extract_path = os.path.join(out_dir, 'Monitoring2024_Stadtbezirke_nach_Umfragebezirk.csv')
df.drop(columns='Rang').to_csv(extract_path, index=False)

# Merged districts (e.g. 591/592) count as one unit, as in the monitoring
cols = ['Mindestsich_%', 'Arbeitslosendichte_%', 'm2_pro_Kopf', 'Sozialwhg_%', 'Alleinerz_%', 'Migration_%', 'Rang']
units = df.groupby(['Einheit', 'Umfragebezirk', 'Stadtteil'], as_index=False)[cols].mean()
units = units.sort_values('Rang').drop_duplicates('Einheit')
agg = units.groupby('Umfragebezirk').agg(Einheiten=('Einheit', 'count'),
    Mindestsich_Median=('Mindestsich_%', 'median'), Arbeitslosendichte_Median=('Arbeitslosendichte_%', 'median'),
    m2_pro_Kopf_Median=('m2_pro_Kopf', 'median'), Sozialwhg_Median=('Sozialwhg_%', 'median'),
    Top20=('Rang', lambda s: int((s <= 20).sum())))
if len(sys.argv) > 6:
    # Weighting with the population register at the end of 2022 (Statistikportal "Demographische Kennzahlen (Stadtbezirke)"):
    # minimum income support and floor space by residents, unemployment density by residents aged 15 to 64,
    # social housing by households. Merged districts are listed there under the first number.
    import openpyxl
    # '-' in the source = suppressed: NaN, not 0
    to_float = lambda x: float(str(x).replace('.', '').replace(',', '.')) if re.match(r'^[\d.,]+$', str(x)) else np.nan
    sheet = [w for w in openpyxl.load_workbook(sys.argv[6], read_only=True, data_only=True).worksheets
             if any(str(r[0]).strip() == 'Jahr = 2022' for r in w.iter_rows(max_col=1, values_only=True))][0]
    population = {}
    for r in sheet.iter_rows(values_only=True):
        r = [c for c in r if c is not None]
        if r and re.match(r'^\d{3} ', str(r[0])): population[int(str(r[0])[:3])] = (to_float(r[1]), to_float(r[8]), to_float(r[10]))
    df['EW'] = df.STBZ.map(lambda i: population.get(i, (0, 0, 0))[0]); df['HH'] = df.STBZ.map(lambda i: population.get(i, (0, 0, 0))[1])
    df['EW15_65'] = df.STBZ.map(lambda i: population.get(i, (0, 0, 0))[2])
    def weighted_mean(g, c, w):
        m = g[c].notna() & (g[w] > 0); return np.average(g.loc[m, c], weights=g.loc[m, w])
    for c, w, label in [('Mindestsich_%', 'EW', 'Mindestsich_gewichtet'), ('Arbeitslosendichte_%', 'EW15_65', 'Arbeitslosendichte_gewichtet'),
                      ('m2_pro_Kopf', 'EW', 'm2_pro_Kopf_gewichtet'), ('Sozialwhg_%', 'HH', 'Sozialwhg_gewichtet')]:
        agg[label] = df.groupby('Umfragebezirk')[[c, w]].apply(lambda g: weighted_mean(g, c, w))
    agg['Einwohner_2022'] = df.groupby('Umfragebezirk').EW.sum()
    print('Total residents 2022:', int(df.EW.sum()))
    df.drop(columns='Rang').to_csv(extract_path, index=False)
agg = agg.sort_values('Mindestsich_gewichtet' if 'Mindestsich_gewichtet' in agg else 'Mindestsich_Median', ascending=False).round(1)
agg.to_csv(os.path.join(out_dir, 'Monitoring2024_Umfragebezirke.csv'))
pd.set_option('display.width', 220); print(agg.to_string())
west = units[units.Umfragebezirk == 'West'].groupby('Stadtteil').agg(Einheiten=('Einheit', 'count'),
    Mindestsich_min=('Mindestsich_%', 'min'), Mindestsich_max=('Mindestsich_%', 'max'),
    ALdichte_max=('Arbeitslosendichte_%', 'max'), Sozialwhg_min=('Sozialwhg_%', 'min'), Sozialwhg_max=('Sozialwhg_%', 'max'),
    Alleinerz_max=('Alleinerz_%', 'max'), Migration_min=('Migration_%', 'min'), Migration_max=('Migration_%', 'max'),
    bester_Rang=('Rang', 'min'), Top20=('Rang', lambda s: int((s <= 20).sum()))).sort_values('Mindestsich_max', ascending=False).round(1)
west.to_csv(os.path.join(out_dir, 'Monitoring2024_West_nach_Stadtteil.csv'))
print(west.to_string())
print(units[units.Rang <= 20].sort_values('Rang')[['Einheit', 'Stadtteil', 'Umfragebezirk', 'Rang']].to_string(index=False))
