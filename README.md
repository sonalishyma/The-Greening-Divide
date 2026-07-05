# The Greening Divide

**An interactive globe that tests a hypothesis with real satellite data — and finds the hypothesis wrong.**

[**Live site →**](https://sonalishyma.github.io/The-Greening-Divide/) · DSC 80, UC San Diego

---

## The story

Satellites have shown for years that the planet, on net, has gotten greener since 2000 — more leaf area, more vegetation, even in a warming world. The obvious next question, and the one this project set out to answer, is: **does that greening favor wealthy countries?** Rich nations have more capital for irrigation, agricultural technology, land management, and conservation, so the intuitive hypothesis is that greening should track income.

It doesn't.

Using real MODIS satellite NDVI (vegetation index) data for 166 countries with complete, stable 2000–2024 coverage, joined to World Bank income tiers, the numbers say:

- **Greening is nearly universal, not a rich-country phenomenon.** 83% of the 166 countries are greener in 2024 than their own 2000–2005 baseline.
- **Income barely separates the four World Bank tiers.** By 2024, Low, Lower-middle, Upper-middle, and High income countries all land within **1.6 percentage points** of each other (+6.4, +4.8, +5.3, +5.7).
- **The spread *within* each income group is about 10× the spread *between* groups.** Knowing a country's income tier tells you almost nothing about where it falls.
- **Income rank correlates with greening at only −0.31** — weak, and pointing the "wrong" direction if wealth were protective.
- **The extremes actively contradict the hypothesis.** The two fastest-*greening* countries in the dataset are Eritrea (+34.0%, low income) and Pakistan (+30.6%, lower-middle income) — driven by dryland recovery and Indus-basin irrigation expansion, not wealth. The two fastest-*browning* countries are Turkmenistan (−11.9%, upper-middle income) and Iceland (−11.7%, **high income**) — arid-land degradation and Arctic vegetation stress, again with no regard for GDP.

**The real driver is geography, water, and land use** — irrigated drylands and recovering agricultural land green fastest; arid and cold regions brown, regardless of income tier. Income is the wrong lens for this question, and that reversal — setting out to confirm a wealth gradient and instead finding a geographic one — is the actual finding worth reporting.

## Why this matters

- **Substantively**: if greening were wealth-driven, it would suggest environmental recovery is a privilege of rich nations. It isn't — near-universal greening driven by geography and land/water use means recovery is happening broadly, including in some of the world's poorest countries, which is a materially different (and more hopeful, more actionable) policy story than "only rich countries can afford to green."
- **Methodologically**: this project is a case study in letting data overturn a starting hypothesis rather than cherry-picking evidence for it. The pipeline, the income join, and the statistics are all reproducible from the raw satellite export (see below) — the finding isn't asserted, it's checkable.
- **As a portfolio piece**: the interesting result here isn't the one that confirms what everyone already assumes ("rich countries do better") — it's the one that forces a more precise, falsifiable claim about what actually explains the pattern in the data.

## How the site tells this story

The globe (built with [globe.gl](https://globe.gl), no external map API key required) has three views:

| Mode | What it shows |
|---|---|
| **Vegetation 2024** | Real per-cell MODIS NDVI rendered as 63,615 individual grid-cell spikes (color + height both driven by actual satellite measurements, not per-country averages) — the same texture-level detail as the underlying data, not a smoothed proxy. |
| **Compare Years** | The same grid, but for the 2000–2005 baseline, so you can see how much has changed. |
| **Show Change** | Each country becomes a single dot: **color** = greener or browner since baseline, **size** = magnitude of change, and — the key encoding — **height = income tier**. Tall spikes are rich countries; short ones are poor. If wealth predicted greening, tall spikes should skew green and short ones should skew orange. They don't. |

A guided 5-step tour walks through the argument in order: the hypothesis → near-universal greening → the poorest countries greening fastest → the richest countries browning fastest → the geographic explanation that actually fits. Selecting Pakistan, Eritrea, Turkmenistan, or Iceland from the "Jump to" menu drops you straight into each of those contradicting examples, with real per-country stats (NDVI trend, world rank, income-tier average for comparison) in the side panel.

## Data & methods

- **Vegetation signal**: NASA MODIS Terra NDVI (`MODIS/061/MOD13A3`, 1km monthly), pulled live from Google Earth Engine — not simulated or placeholder data.
- **Income tiers**: World Bank FY2024–25 classification (Low / Lower-middle / Upper-middle / High income), joined by ISO3 country code.
- **A real gotcha, fixed**: Earth Engine's LSIB country boundaries expose a `country code` field that looks like ISO3 but is actually **FIPS 10-4** (e.g. `ZA` = Zambia, not South Africa). The pipeline ignores that column entirely and re-derives ISO3 from the country **name**, which is unambiguous.
- **Change metric**: percent NDVI change versus each country's own 2000–2005 mean (a stable multi-year baseline, not a single noisy year).
- **Filtering**: the country-level analysis excludes countries without complete 2000–2024 coverage or a stable baseline (mean NDVI ≥ 0.10) — this avoids division-by-near-zero blowups in percent-change math. The grid-cell layer only ever displays *raw* NDVI (never percent change), so it uses a much lighter floor (NDVI ≥ 0.03) to keep true low-vegetation land like deserts and tundra visible instead of leaving blank gaps.
- **A second real bug, fixed**: Earth Engine's coarse-resolution grid export occasionally leaked a handful of non-masked pixel values into open ocean (confirmed by sampling the same coordinates at native 1km resolution, which correctly returns no data) — an artifact of its resampling, not the source data. The grid pipeline now cross-checks every cell against real country boundaries (via a spatial index) and drops anything more than ~220km from land.
- **Limitations, stated plainly**: this is an observational, cross-sectional analysis — it establishes that income doesn't explain the *variation* in greening, not a causal mechanism for what does. "Geography and water use" is the pattern that survives scrutiny in the data (dryland/irrigation examples at both extremes), not a fully modeled causal claim.

## Files

| File | Purpose |
|---|---|
| `index.html` | The site itself — self-contained HTML/CSS/JS, no build step, no external API key. |
| `globe.gl.min.js` | Local copy of the globe renderer (so the site has no runtime CDN dependency). |
| `countries.geojson` | Country boundary polygons for the globe. |
| `build_data.py` | Reproducible pipeline: raw country-level GEE export → ISO3 fix → World Bank income join → stats → injects the payload into `index.html`. |
| `build_grid.py` | Pulls real per-cell MODIS NDVI grid data directly from Earth Engine, land-masks it against `countries.geojson`, and writes `grid_ndvi.json`. |
| `prepare_data.py` | Alternate injector for a CSV that already has `iso3`, `year`, `ndvi`, and `income_group` columns. |
| `greening_ndvi_by_country.csv` | Raw Earth Engine export: country × year × NDVI. |
| `greening_with_income.csv` | Generated: the country-level dataset joined with income tier, used by the site. |
| `grid_ndvi.json` | Generated: real per-cell NDVI grid (baseline / 2012 / 2024), used by the site's spike layer. |
| `requirements.txt` | Python dependencies for the pipeline. |
| `*-preview.png` | Static chart previews of the headline finding. |

## Reproducing the pipeline

```bash
python3 -m venv .venv && source .venv/bin/activate
python3 -m pip install -r requirements.txt

# Country-level dataset + stats (writes greening_with_income.csv, updates index.html)
python3 build_data.py greening_ndvi_by_country.csv

# Real per-cell grid for the globe's spike layer (writes grid_ndvi.json)
# Requires a free Earth Engine account: https://code.earthengine.google.com
python3 build_grid.py
```

If you already have a cleaned CSV with `iso3`, `year`, `ndvi`, and `income_group`, you can skip `build_data.py` and use `python3 prepare_data.py your_export.csv` instead.

## Running it locally

```bash
python3 -m http.server
```

Then open `http://localhost:8000`.

## Deployment

Already live at [sonalishyma.github.io/The-Greening-Divide](https://sonalishyma.github.io/The-Greening-Divide/) via GitHub Pages, serving directly from the root of the `main` branch — the site is fully static and self-contained, so no build step is involved.

## Credits

Data and analysis: real MODIS Terra NDVI processed in Google Earth Engine, joined to World Bank income classifications.
