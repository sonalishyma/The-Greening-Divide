"""Full data pipeline for The Greening Divide.

Takes the raw Google Earth Engine export (country x year x NDVI), joins World Bank
income groups, cleans, computes the group trajectories + summary statistics, and
writes greening_with_income.csv -- the dataset index.html fetches at runtime.

Usage:  pip install pandas country_converter
        python build_data.py greening_ndvi_by_country.csv

Raw CSV columns (from the GEE script): a country code column, `country` (name),
`year`, `ndvi` (already scaled to -1..1). The code column is IGNORED because
GEE's LSIB boundaries use FIPS 10-4 codes, not ISO3 — we re-derive ISO3 from the
country NAME, which is unambiguous.
"""
import sys, logging
import pandas as pd, numpy as np
logging.disable(logging.WARNING)
import country_converter as coco

CSV = sys.argv[1] if len(sys.argv) > 1 else 'greening_ndvi_by_country.csv'
BASE_YEARS = list(range(2000, 2006))

# World Bank income classification (FY2024-25). Spot-check against the current
# World Bank list before publishing; group means are unweighted so a few edge
# reclassifications don't change the headline finding.
INC = {'USA':'H','CAN':'H','GBR':'H','FRA':'H','DEU':'H','ITA':'H','ESP':'H','PRT':'H','NLD':'H','BEL':'H','CHE':'H','AUT':'H','SWE':'H','NOR':'H','DNK':'H','FIN':'H','IRL':'H','ISL':'H','LUX':'H','GRC':'H','JPN':'H','KOR':'H','AUS':'H','NZL':'H','SGP':'H','ISR':'H','SAU':'H','ARE':'H','QAT':'H','KWT':'H','BHR':'H','OMN':'H','CZE':'H','SVK':'H','SVN':'H','EST':'H','LVA':'H','LTU':'H','POL':'H','HRV':'H','HUN':'H','CHL':'H','URY':'H','PAN':'H','TTO':'H','BRN':'H','CYP':'H','MLT':'H','TWN':'H',
'CHN':'UM','BRA':'UM','MEX':'UM','RUS':'UM','TUR':'UM','ARG':'UM','ZAF':'UM','THA':'UM','MYS':'UM','COL':'UM','PER':'UM','KAZ':'UM','ROU':'UM','BGR':'UM','SRB':'UM','BLR':'UM','AZE':'UM','TKM':'UM','ARM':'UM','GEO':'UM','ALB':'UM','MKD':'UM','BIH':'UM','MNE':'UM','MDA':'UM','ECU':'UM','PRY':'UM','DOM':'UM','CRI':'UM','JAM':'UM','BWA':'UM','NAM':'UM','GAB':'UM','MUS':'UM','LBY':'UM','IRQ':'UM','IRN':'UM','JOR':'UM','LBN':'UM','FJI':'UM','SUR':'UM','BLZ':'UM','CUB':'UM','MDV':'UM','TON':'UM',
'IND':'LM','IDN':'LM','PAK':'LM','BGD':'LM','NGA':'LM','EGY':'LM','PHL':'LM','VNM':'LM','MAR':'LM','UKR':'LM','UZB':'LM','KEN':'LM','GHA':'LM','TZA':'LM','CIV':'LM','CMR':'LM','AGO':'LM','ZMB':'LM','ZWE':'LM','SEN':'LM','TUN':'LM','DZA':'LM','LKA':'LM','MMR':'LM','KHM':'LM','LAO':'LM','NPL':'LM','MNG':'LM','BOL':'LM','HND':'LM','NIC':'LM','SLV':'LM','KGZ':'LM','TJK':'LM','PNG':'LM','HTI':'LM','BEN':'LM','COG':'LM','GIN':'LM','MRT':'LM','LSO':'LM','SWZ':'LM','DJI':'LM','COM':'LM','SLB':'LM','VUT':'LM','TLS':'LM','BTN':'LM','CPV':'LM','GTM':'LM',
'ETH':'L','COD':'L','TCD':'L','NER':'L','MLI':'L','MOZ':'L','MWI':'L','SDN':'L','AFG':'L','MDG':'L','BFA':'L','SOM':'L','SSD':'L','RWA':'L','BDI':'L','UGA':'L','TGO':'L','SLE':'L','LBR':'L','GNB':'L','GMB':'L','CAF':'L','ERI':'L','YEM':'L','SYR':'L','PRK':'L'}
LAB = {'L':'Low income','LM':'Lower middle income','UM':'Upper middle income','H':'High income'}
ORDER = ['Low income','Lower middle income','Upper middle income','High income']
RANK = {'Low income':1,'Lower middle income':2,'Upper middle income':3,'High income':4}

# Non-sovereign places with no World Bank income tier that country_converter's fuzzy
# matching has been observed to mis-map onto a real country's ISO3 (confirmed case:
# "S Georgia & S Sandwich Is", an uninhabited UK territory, was resolving to Georgia's
# GEO code and silently corrupting/blending with the real country's NDVI trend).
NON_COUNTRY_NAMES = {'S Georgia & S Sandwich Is'}

cc = coco.CountryConverter()
df = pd.read_csv(CSV)
df['year'] = df['year'].astype(int)
df = df[~df['country'].astype(str).str.contains(r'\(')]                 # drop sub-territories
df = df[~df['country'].isin(NON_COUNTRY_NAMES)]
conv = cc.pandas_convert(pd.Series(df['country'].unique()), to='ISO3', not_found=None)
m = dict(zip(df['country'].unique(), conv))
def iso3(n):
    v = m.get(n)
    return v[0] if isinstance(v, list) and v else (None if v in (None,'not found') or isinstance(v,list) else v)
df['iso3'] = df['country'].map(iso3)
df = df[df['iso3'].notna()].copy()
df['income_group'] = df['iso3'].map(INC).map(LAB)

# Sanity check: two *different* source country names silently colliding on the same ISO3
# would blend/overwrite one real country's NDVI trend with another's (this is exactly how
# the Georgia bug above was found -- "Georgia" and "S Georgia & S Sandwich Is" both
# resolved to GEO). This is distinct from large countries like China or Russia
# legitimately having several polygon-part rows per year under one name -- pivot_table's
# mean aggregation already handles that safely. Only flag it when more than one distinct
# `country` name maps to the same ISO3, and only among countries that get an income tier
# (collisions among places we drop anyway, e.g. Gaza Strip/West Bank both -> PSE, are
# harmless since PSE has no World Bank tier here).
_classified = df[df['income_group'].notna()]
_name_counts = _classified.groupby('iso3')['country'].nunique()
_dupes = sorted(_name_counts[_name_counts > 1].index.tolist())
assert not _dupes, f"ISO3 collision among classified countries: {_dupes} -- two source names are mapping to the same code"

piv = df.pivot_table(index=['iso3','income_group'], columns='year', values='ndvi').reindex(columns=range(2000,2025))
full = piv.dropna()
base = full[BASE_YEARS].mean(axis=1)
full = full[base >= 0.10]; base = base[base >= 0.10]                     # stable baseline only
pct = full.sub(base, axis=0).div(base, axis=0) * 100
grp = pd.Series([i[1] for i in full.index], index=full.index)
years = list(range(2000,2025))

def name(iso):
    n = cc.convert(iso, src='ISO3', to='name_short', not_found=iso)
    return n[0] if isinstance(n, list) else n
countries = [{'iso3':i[0],'admin':name(i[0]),'group':i[1],
              'change':[round(float(v),2) for v in row]} for i,row in pct.iterrows()]
groups = {g:[round(float(pct[grp==g][y].mean()),2) for y in years] for g in ORDER}
gm2024 = {g: round(float(pct[grp==g][2024].mean()),1) for g in ORDER}
within = float(pct[2024].groupby(grp).std().mean())
between = float(pd.Series(gm2024).std())
corr = float(np.corrcoef([RANK[g] for g in ORDER], [gm2024[g] for g in ORDER])[0,1])
p24 = pct[2024].sort_values()
stats = {'n':len(countries),'pct_greener':round(float((pct[2024]>0).mean()*100)),
         'global_mean':round(float(pct[2024].mean()),1),'group2024':gm2024,
         'within_sd':round(within,1),'between_sd':round(between,1),'ratio':round(within/between,1),
         'corr':round(corr,2),
         'top_green':[[name(i[0]),round(float(p24[i]),1),i[1]] for i in p24.index[-6:][::-1]],
         'top_brown':[[name(i[0]),round(float(p24[i]),1),i[1]] for i in p24.index[:6]]}

# The current index.html fetches greening_with_income.csv directly at runtime (no
# embedded data block to inject into) -- this pipeline's job is just to produce that
# CSV and print the headline stats so GLOBAL_STATS/REGION_COPY in index.html can be
# spot-checked or updated if the underlying numbers change.
df[df['iso3'].isin([c['iso3'] for c in countries])][['iso3','country','income_group','year','ndvi']]\
  .to_csv('greening_with_income.csv', index=False)

print(f"Done: {len(countries)} countries. within/between = {within:.1f}/{between:.1f} = {within/between:.1f}x, corr={corr:.2f}")
print(f"pct_greener={stats['pct_greener']}%, global_mean={stats['global_mean']}%")
print("group2024:", gm2024)
print("top_green:", stats['top_green'])
print("top_brown:", stats['top_brown'])
