"""Export real gridded MODIS NDVI (not just country means) for the globe's spike layer.

Pulls MODIS/061/MOD13C2 (0.05 deg CMG monthly NDVI), averages to annual composites for
the 2000-2005 baseline, 2012, and 2024, downloads each at a coarse grid resolution
directly via getDownloadURL (no Drive export/task polling needed), and writes one
compact JSON file of {lat, lng, ndvi_base, ndvi_2012, ndvi_2024, change} per grid cell.

This is the real per-cell counterpart to greening_with_income.csv (which is one number
per country) -- it's what lets the globe render individual textured cells instead of
one flat color per country, the way the reference site's spike layer does.

Requires an authenticated Earth Engine account (free, at code.earthengine.google.com).

Usage:
    pip install earthengine-api rasterio numpy
    python3 build_grid.py            # first run opens a browser to authenticate
"""
import io
import json
import sys

import ee
import numpy as np
import rasterio
from shapely.geometry import Point, shape
from shapely.strtree import STRtree

# Max distance (degrees) a grid cell may sit from the nearest land polygon before it's
# dropped as a resampling artifact. Earth Engine's coarse-scale getDownloadURL occasionally
# leaks a stray non-masked value thousands of km out in open ocean (confirmed: sampling the
# same point at native 1km resolution returns fully masked/None -- the artifact is introduced
# by the coarse reprojection, not present in the source data). Generous enough to keep real
# small islands that aren't in our low-res countries.geojson basemap.
LAND_MASK_DEG = 2.0

# Grid cell size in meters. ~55 km ~= 0.5 deg at the equator, giving ~57k land cells
# globally -- close to the reference site's own texture density. Drop to 27750
# (~0.25 deg) for finer texture, or raise it if this is too slow on your machine.
SCALE_M = 55660

# Skip cells with implausible/no vegetation signal (open ocean, permanent ice, fill values).
NDVI_MIN, NDVI_MAX = -0.05, 1.0

OUT = "grid_ndvi.json"


def annual_mean(y0, y1):
    coll = (
        ee.ImageCollection("MODIS/061/MOD13A3")
        .filterDate(f"{y0}-01-01", f"{y1}-12-31")
        .select("NDVI")
    )
    return coll.mean().multiply(0.0001)


def download_array(image):
    url = image.getDownloadURL(
        {
            "scale": SCALE_M,
            "crs": "EPSG:4326",
            "format": "GEO_TIFF",
            "region": ee.Geometry.BBox(-180, -60, 180, 85),
        }
    )
    import urllib.request

    with urllib.request.urlopen(url) as resp:
        data = resp.read()
    with rasterio.open(io.BytesIO(data)) as src:
        arr = src.read(1).astype("float32")
        transform = src.transform
    return arr, transform


EE_PROJECT = "dsc-501305"


def build_land_tree():
    with open("countries.geojson", encoding="utf-8") as f:
        geo = json.load(f)
    geoms = [shape(f["geometry"]) for f in geo["features"]]
    return STRtree(geoms)


def main():
    try:
        ee.Initialize(project=EE_PROJECT)
    except Exception:
        ee.Authenticate()
        ee.Initialize(project=EE_PROJECT)

    print("Fetching 2000-2005 baseline...")
    base_arr, transform = download_array(annual_mean(2000, 2005))
    print("Fetching 2012...")
    y2012_arr, _ = download_array(annual_mean(2012, 2012))
    print("Fetching 2024...")
    y2024_arr, _ = download_array(annual_mean(2024, 2024))

    if base_arr.shape != y2012_arr.shape or base_arr.shape != y2024_arr.shape:
        sys.exit("Grid shapes did not match between years -- re-run.")

    print("Building land mask from countries.geojson...")
    land_tree = build_land_tree()

    nrows, ncols = base_arr.shape
    cells = []
    dropped_ocean = 0
    for row in range(nrows):
        for col in range(ncols):
            base = base_arr[row, col]
            v12 = y2012_arr[row, col]
            v24 = y2024_arr[row, col]
            if not (np.isfinite(base) and np.isfinite(v12) and np.isfinite(v24)):
                continue
            if base < NDVI_MIN or base > NDVI_MAX:
                continue
            # A tiny floor above zero, not build_data.py's 0.10 stability cutoff (this grid
            # only ever displays raw NDVI, never % change, so there's no division-blowup risk
            # to guard against) -- just enough to drop water/snow noise while keeping real
            # low vegetation (desert, tundra) so those areas get short spikes, not a blank gap.
            if base < 0.03:
                continue
            lng, lat = transform * (col + 0.5, row + 0.5)
            if lat < -60 or lat > 85:
                continue
            pt = Point(lng, lat)
            nearest_idx = land_tree.nearest(pt)
            if pt.distance(land_tree.geometries.take(nearest_idx)) > LAND_MASK_DEG:
                dropped_ocean += 1
                continue
            change = (v24 - base) / base * 100
            cells.append(
                {
                    "lat": round(float(lat), 3),
                    "lng": round(float(lng), 3),
                    "ndvi_base": round(float(base), 4),
                    "ndvi_2012": round(float(v12), 4),
                    "ndvi_2024": round(float(v24), 4),
                    "change": round(float(change), 2),
                }
            )

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(cells, f, separators=(",", ":"))
    print(f"Done: {len(cells):,} grid cells written to {OUT} ({dropped_ocean} open-ocean artifacts dropped)")


if __name__ == "__main__":
    main()
