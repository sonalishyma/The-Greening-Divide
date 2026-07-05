# The Greening Mirage — Global Greening Inequality Explorer (DSC 106)

An interactive, scroll-driven site that tests a hypothesis and reports an honest null result:
**does the planet's post-2000 greening favor rich countries? It doesn't.**

Built from real NASA MODIS Terra (MOD13C2) NDVI, 2000–2024, aggregated to 166 countries in
Google Earth Engine and grouped by World Bank income tier.

## The finding
- **83%** of countries are greener in 2024 than their 2000–2005 baseline — greening is near-universal.
- The four income groups land within **~1.6 points** of each other by 2024 (Low +6.4, High +5.7,
  Upper-mid +5.3, Lower-mid +4.8). No wealth gradient.
- **Within-group spread is ~10× the between-group spread** (6.8 vs 0.7 pts), and income rank
  correlates with greening at just **−0.30**. Income is the wrong lens.
- The real signal is geographic: fastest greening is dryland/agricultural (Pakistan +31%,
  Eritrea +34%, Kenya, Cabo Verde); browning is arid/cold (Turkmenistan, Iceland, Namibia).
  Both ends cut across income groups.

This overturns the placeholder narrative the site originally shipped with ("greening favors the
rich"). The real data said otherwise, so the story was rebuilt to match it — that reversal is
the point of the piece.

## Two edits before publishing
1. **Add your original DSC 106 teammates** in the two `[add original teammates]` spots (hero + footer).
2. Nothing else required — the real data is already embedded and the site runs as-is.

## Regenerating the data (reproducible pipeline)
`build_data.py` is the full pipeline: it takes the raw Earth Engine export, re-derives ISO3 from
country names (GEE's LSIB codes are FIPS 10-4, **not** ISO3 — a real gotcha), joins World Bank
income groups, cleans (drops sub-territories and unstable near-desert baselines), computes the
group trajectories + summary statistics, and injects everything into `index.html`.

```bash
pip install pandas country_converter
python build_data.py greening_ndvi_by_country.csv
```

Outputs the embedded data block and `greening_with_income.csv` (the joined intermediate).
The World Bank income mapping inside the script is FY2024-25 — spot-check it before publishing.

## Files
- `index.html` — the site (self-contained; data embedded)
- `build_data.py` — raw CSV → cleaned, income-joined, stats → injected into index.html
- `greening_ndvi_by_country.csv` — the raw Earth Engine export (country × year × NDVI)
- `greening_with_income.csv` — joined intermediate (ISO3 + income group)

## Preview locally / deploy
`python -m http.server` then open http://localhost:8000 (needs internet: the globe library and
Natural Earth boundaries load from CDNs). Deploy: push to a repo → Settings → Pages → `main`, root.

## Credits & method notes
Signal: MODIS Terra MOD13C2 (0.05° CMG) NDVI, GEE zonal means over national boundaries, expressed
as % change vs each country's 2000–2005 mean. Groups: unweighted country means within World Bank
tiers. The between-vs-within variance decomposition is the core test. Footer carries the
permission-based "format inspired by" credit to the classmates' project; all data, analysis, code,
and design here are original.
