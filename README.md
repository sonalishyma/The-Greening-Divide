# The Greening Divide — Global Greening Inequality Explorer 

This was a DSC 80 project was built around the real data. The original hypothesis — that global greening favors wealthy countries — does not survive the numbers.
The site now uses 166 countries with clean 2000–2024 MODIS NDVI coverage, joined to World Bank income groups, and the story is honest: income explains almost nothing about who greened.

## Key findings
- 166 countries with complete coverage and a stable baseline (mean NDVI ≥ 0.10).
- 83% of countries are greener in 2024 than their own 2000–2005 baseline.
- Income group means are within ~1.6 percentage points by 2024:
  Low +6.4, Lower middle +4.8, Upper middle +5.3, High +5.7.
- The within-group spread is about 10× the between-group spread.
- The income-rank correlation with greening is only −0.31, and the extremes cut across income.

## Files
- `greening_ndvi_by_country.csv` — raw GEE export (country, year, NDVI).
- `build_data.py` — reproducible pipeline from raw export to joined dataset and site injection.
- `greening_with_income.csv` — generated intermediate dataset with ISO3, income group, year, and NDVI.
- `prepare_data.py` — alternate injector for already-prepared CSVs that already have `iso3` and `income_group`.
- `index.html` — full-screen interactive Greening Earth map story.
- `countries.geojson` — local country boundaries for the globe.
- `globe.gl.min.js` — local copy of the globe renderer, so the site does not depend on a remote script at runtime.
- `requirements.txt` — Python dependencies for the pipeline.

## Rebuild the data and site
1. Create a clean environment (recommended):
   `python3 -m venv .venv && source .venv/bin/activate`
2. Install dependencies:
   `python3 -m pip install -r requirements.txt`
3. Run the pipeline:
   `python3 build_data.py greening_ndvi_by_country.csv`

This writes `greening_with_income.csv` and updates `index.html` with the embedded NDVI payload.

If you already have a cleaned CSV with `iso3`, `year`, `ndvi`, and `income_group`, use:
`python3 prepare_data.py your_export.csv`

## Local preview
Run a local server and open the page:

```bash
python3 -m http.server
```

Then visit `http://localhost:8000`.

## Deployment
Upload the folder to GitHub and deploy from the root on GitHub Pages.

## Method notes
- NDVI is expressed as percent change versus each country’s 2000–2005 mean.
- Group lines are unweighted means across member countries.
- The analysis excludes countries without a stable baseline or complete 2000–2024 coverage.
- The biggest story here is not that rich countries green more; it's that income is a very weak explanatory lens, while geography and water/agriculture appear to matter much more.

## Credits
Data and analysis: real MODIS Terra NDVI processed in Google Earth Engine.
Site: vanilla HTML/CSS/JS with `globe.gl` for the interactive world map.
Narrative, charts, and code: the project author and team.
