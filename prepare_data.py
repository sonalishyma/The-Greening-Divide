"""Replace the sample dataset in index.html with the project's real NDVI export.

Usage:
    python prepare_data.py your_export.csv [--index index.html]

CSV columns (case-insensitive):
    iso3          ISO 3166-1 alpha-3 country code            (required)
    year          2000..2024                                  (required)
    ndvi          annual mean NDVI       -- or --  pct_change (one required)
    income_group  World Bank group, e.g. "Low income"         (required)
    country       display name (optional; defaults to iso3)

If `ndvi` is given, percent change is computed against each country's own
2000-2005 mean. Group lines are unweighted means across member countries.
"""
import sys, json, re, argparse
import pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument('csv'); ap.add_argument('--index', default='index.html')
a = ap.parse_args()

df = pd.read_csv(a.csv)
df.columns = [c.strip().lower() for c in df.columns]
for req in ('iso3','year'):
    if req not in df: sys.exit(f'Missing column: {req}')
grp_col = 'income_group' if 'income_group' in df else ('group' if 'group' in df else None)
if not grp_col: sys.exit('Missing column: income_group')
years = sorted(int(y) for y in df['year'].unique())

out = []
for iso, g in df.groupby('iso3'):
    g = g.sort_values('year')
    series = g.set_index('year')
    if 'pct_change' in g:
        ch = [round(float(series.loc[y,'pct_change']),2) if y in series.index else None for y in years]
    else:
        base_years = [y for y in range(2000,2006) if y in series.index]
        if not base_years: continue
        base = series.loc[base_years,'ndvi'].mean()
        ch = [round((float(series.loc[y,'ndvi'])-base)/base*100,2) if y in series.index else None for y in years]
    if any(v is None for v in ch): continue   # require full coverage
    out.append({'iso3': iso,
                'admin': str(g['country'].iloc[0]) if 'country' in g else iso,
                'group': str(g[grp_col].iloc[0]).strip(),
                'change': ch})

groups = {}
for gname in sorted({c['group'] for c in out}):
    members = [c['change'] for c in out if c['group']==gname]
    groups[gname] = [round(sum(m[i] for m in members)/len(members),2) for i in range(len(years))]

data = {'sample': False, 'years': years, 'groups': groups, 'countries': out}
block = '/*NDVI_DATA_START*/const NDVI='+json.dumps(data,separators=(",",":"), ensure_ascii=False)+';/*NDVI_DATA_END*/'
html = open(a.index, encoding='utf-8').read()
if not re.search(r'/\*NDVI_DATA_START\*/.*?/\*NDVI_DATA_END\*/', html, flags=re.S):
    sys.exit('Data markers not found in index.html')
html2 = re.sub(r'/\*NDVI_DATA_START\*/.*?/\*NDVI_DATA_END\*/', lambda _: block, html, flags=re.S)
open(a.index,'w', encoding='utf-8').write(html2)
print(f'Done: {len(out)} countries, {len(groups)} groups, years {years[0]}-{years[-1]}. Sample banner is now off.')
