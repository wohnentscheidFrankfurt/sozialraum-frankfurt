# Local council election Frankfurt 2026: votes, shares, change and seats per Ortsbeirat from the subpages kap2/Ortsbeirat-N.html
# Call: python kw_extract.py <folder with obr1.html ... obr16.html> <output folder>
import sys, re, json, os
import pandas as pd
input_dir, out_dir = sys.argv[1], sys.argv[2]
def widgets(html):
    # Plotly JSON of each widget, keyed by the id of the tab set before it
    tabs = [(m.start(), m.group(1)) for m in re.finditer(r'id="(tabset-[\d-]+)"', html)]
    result = {}
    for m in re.finditer(r'<script type="application/json" data-for="[^"]+"[^>]*>(.*?)</script>', html, re.S):
        tab = [t for pos, t in tabs if pos < m.start()]
        tab_id = tab[-1] if tab else None
        result.setdefault(tab_id, json.loads(m.group(1))['x'])
    return result
to_float = lambda s: float(s.replace('.', '').replace(',', '.'))
vote_rows, seat_rows = [], []
for i in range(1, 17):
    html = open(os.path.join(input_dir, f'obr{i}.html'), encoding='utf-8').read()
    name = re.sub(r'<[^>]+>', '', re.search(r'<title>(.*?)</title>', html, re.S).group(1)).strip()
    w = widgets(html)
    share_trace, change_trace = w['tabset-1-1']['data'][0], w['tabset-1-2']['data'][0]
    change = {p: x for p, x in zip(change_trace['y'], change_trace['x'])}
    for party, pct, text in zip(share_trace['y'], share_trace['x'], share_trace['text']):
        votes = to_float(re.search(r'([\d.]+) Stimmen', text).group(1))
        vote_rows.append({'Ortsbeirat': i, 'Partei': party, 'Stimmen': int(votes), 'Anteil_%': pct, 'Veraenderung_%Punkte': round(change.get(party, float('nan')), 1)})
    for year, tab in (('2026', 'tabset-2-1'), ('2021', 'tabset-2-2')):
        pie = w[tab]['data'][0]
        for party, n_seats in zip(pie['labels'], pie['values']):
            if party != 'Dummy': seat_rows.append({'Ortsbeirat': i, 'Jahr': year, 'Partei': party, 'Sitze': n_seats})
    print(i, name)
votes_df = pd.DataFrame(vote_rows); seats_df = pd.DataFrame(seat_rows)
votes_df.to_csv(os.path.join(out_dir, 'Ortsbeiraete_2026_Stimmen.csv'), index=False); seats_df.to_csv(os.path.join(out_dir, 'Ortsbeiraete_2026_Sitze.csv'), index=False)
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 30)
print(votes_df.pivot_table(index='Partei', columns='Ortsbeirat', values='Anteil_%').round(1).fillna('–').to_string())
print(seats_df[seats_df.Jahr == '2026'].pivot_table(index='Partei', columns='Ortsbeirat', values='Sitze', aggfunc='sum').fillna(0).astype(int).to_string())
