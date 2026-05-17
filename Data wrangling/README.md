# Data Wrangling — Melbourne Solar Potential

This folder contains the data processing pipeline that transforms raw open data into clean, database-ready tables.

---

## Scripts

| Script | Purpose |
|---|---|
| `MelSolar.py` | Cleans building footprints and rooftop solar polygons, produces `buildings.csv` and `rooftop_solar.csv` |
| `build_geojson.py` | Joins the two CSVs and writes `combined-buildings.geojson` for the frontend map |
| `precincts.py` | Aggregates solar data per suburb, reads CER postcode capacity, produces `melbourne_cbd_precincts.csv` and `.geojson` |
| `solar score.py` | Computes a composite solar score (0–100) per building from Google Solar API data and upserts into the `solar_score` table |

---

## Output Files

| File | Rows | Description |
|---|---|---|
| `buildings.csv` | 40,951 | Cleaned building footprints — imported into `buildings` table |
| `rooftop_solar.csv` | 14,995 | Aggregated solar potential per building — imported into `rooftop_solar` table |
| `combined-buildings.geojson` | 40,951 | Frontend map file combining buildings and solar data |
| `melbourne_cbd_precincts.csv` | 13 | Precinct-level aggregation — imported into `precincts` table |
| `melbourne_cbd_precincts.geojson` | 13 | Precinct boundary polygons for the suburb map |

---

## Source Data

| File | Source | Description |
|---|---|---|
| `2023-building-footprints.csv` | [City of Melbourne Open Data](https://data.melbourne.vic.gov.au/explore/dataset/2023-building-footprints/) | Building geometry, height, and roof type |
| `mga55_gda95_green_roof_solar.shp` (.shx .dbf .prj) | [City of Melbourne Rooftop Project](https://data.melbourne.vic.gov.au/explore/dataset/rooftops-with-environmental-retrofitting-opportunities-rooftop-project/) | Solar suitability polygons rated Excellent / Good / Moderate / Poor / Very Poor (2015) |
| `Postcode capacity.csv` | [Clean Energy Regulator (CER)](https://www.cleanenergyregulator.gov.au/) | Installed rooftop solar capacity by postcode |
| Google Solar API | [Google Maps Platform](https://developers.google.com/maps/documentation/solar/overview) | Per-building solar potential: max panels, annual kWh, sunshine hours, carbon offset |

Both City of Melbourne datasets are licensed under **CC BY 4.0**.

---

## MelSolar.py — Step by Step

**Step 1 — Load raw data**
Reads the building footprints CSV and the solar shapefile.

**Step 2 — Clean building footprints**
- Converts the `Geo Shape` GeoJSON column into geometry objects
- Reprojects from `EPSG:4326` to `EPSG:28355` (MGA Zone 55, matching the solar shapefile)
- Extracts `lat` and `lng` from `Geo Point`
- Converts `date_captured` from integer `20180528` to date `2018-05-28`
- Filters out non-building structures — keeps `footprint_type == 'Structure'` only

**Step 3 — Clean solar shapefile**
- Maps text ratings to numeric scores: `Excellent=5, Good=4, Moderate=3, Poor=2, Very Poor=1`
- Removes noise polygons smaller than 4 m²

**Step 4 — Spatial join**
- Matches each solar roof polygon to the building it sits on using `intersects`
- Where one polygon overlaps multiple buildings, keeps only the first match
- Overall match rate: **94.9%**

**Step 5 — Aggregate solar data per building**
Groups all roof polygons by `structure_id` and calculates:
- `total_roof_area` — total roof area in m²
- `usable_roof_area` — area rated Good or above (score ≥ 4)
- `dominant_rating` — most common rating across all patches
- `solar_score_avg` — average score (1–5)
- `roof_patch_count` — number of roof polygons
- `excellent_area` — area rated Excellent in m²
- `usable_ratio` — usable / total (0–1)

**Step 6 — Build buildings table**
Selects and renames relevant columns from the cleaned building footprints.

**Step 7 — Export**
Writes `buildings.csv` and `rooftop_solar.csv`.

---

## precincts.py — Step by Step

**Step 1–4 — Load suburb boundaries**
Reads ABS 2021 SAL shapefile, filters to Melbourne CBD suburbs, reprojects to WGS84.

**Step 5 — Match CER installed capacity**
Maps each suburb to a postcode and looks up already-installed solar capacity (kW) from the CER CSV.

**Step 6 — Aggregate solar data from DB**
Queries `buildings` and `solar_api_cache` via spatial join to compute per-precinct:
- `total_kwh_annual` — sum of `max_panels_kwh_annual`
- `total_usable_area_m2` — sum of `max_array_area_m2`
- `potential_capacity_kw` — sum of `max_panels × panel_capacity_watts / 1000`

**Step 7 — Compute adoption gap**
```
adoption_gap_kw = potential_capacity_kw − installed_capacity_kw  (clipped to 0)
```

**Step 8–9 — Export**
Writes `melbourne_cbd_precincts.geojson` and `melbourne_cbd_precincts.csv`.

---

## build_geojson.py — What it does

Joins `buildings.csv` + `rooftop_solar.csv`, computes per-building:
- `footprint_area` — actual 2D roof footprint in m² (from the polygon via spherical shoelace formula)
- `usable_roof_area` — `footprint_area × usable_ratio`
- `kwh_annual` — estimated from usable area using Melbourne CBD formula: `4.1 PSH × 20% efficiency × 75% PR`

Outputs `../Backend/combined-buildings.geojson` used by the frontend map.

---

## solar score.py — What it does

Reads `max_sunshine_hours_per_year` and `max_panels_kwh_annual` from `solar_api_cache`, computes:
- `quality_norm` — sunshine intensity per m² (normalised 0–100)
- `quantity_norm` — annual kWh output (normalised 0–100)
- `composite_score` — weighted combination: `0.5 × quality + 0.5 × quantity` (re-normalised to 0–100)

Upserts results into the `solar_score` table.

---

## Output Column Reference

### `buildings.csv`

| Column | Type | Description |
|---|---|---|
| `structure_id` | int | Primary key — unique building ID |
| `lat` | float | Latitude of building centroid |
| `lng` | float | Longitude of building centroid |
| `roof_type` | string | Flat / Gable / Hip / Pyramid / Shed |
| `footprint_type` | string | Always "Structure" after filtering |
| `building_height` | float | Total building height in metres |
| `base_height` | float | Base/podium height in metres |
| `max_elevation` | float | Highest point above sea level (AHD) |
| `min_elevation` | float | Lowest point above sea level (AHD) |
| `date_captured` | date | Date the building data was captured |
| `geo_shape` | string | GeoJSON polygon of building footprint |

### `rooftop_solar.csv`

| Column | Type | Description |
|---|---|---|
| `structure_id` | int | Foreign key — links to `buildings.structure_id` |
| `total_roof_area` | float | Total roof area in m² |
| `usable_roof_area` | float | Usable roof area (Good or above) in m² |
| `dominant_rating` | string | Most common solar rating |
| `solar_score_avg` | float | Average solar score 1–5 |
| `roof_patch_count` | int | Number of individual roof polygons |
| `excellent_area` | float | Area rated Excellent in m² |
| `usable_ratio` | float | Usable roof ratio 0–1 |

### `melbourne_cbd_precincts.csv`

| Column | Type | Description |
|---|---|---|
| `precinct_id` | int | ABS SAL code |
| `name` | string | Suburb name |
| `postcode` | string | Postcode |
| `total_kwh_annual` | float | Sum of annual kWh across all buildings |
| `total_usable_area_m2` | float | Sum of usable roof area in m² |
| `installed_capacity_kw` | float | Already-installed solar capacity from CER |
| `potential_capacity_kw` | float | Maximum achievable capacity from Google Solar API |
| `adoption_gap_kw` | float | Untapped capacity (potential − installed) |
| `geo_boundary` | string | WKT polygon of suburb boundary |

---

## How to Reproduce

### 1. Install dependencies
```bash
pip install geopandas pandas shapely pyproj psycopg2-binary numpy
```

### 2. Run in order
```bash
cd "Data wrangling"
python MelSolar.py          # → buildings.csv, rooftop_solar.csv
python build_geojson.py     # → ../Backend/combined-buildings.geojson
python precincts.py         # → melbourne_cbd_precincts.csv/.geojson
python "solar score.py"     # → upserts into solar_score table (requires DB connection)
```

---

## How to Import into PostgreSQL

```sql
-- Enable PostGIS (run once)
CREATE EXTENSION IF NOT EXISTS postgis;

-- Import (buildings first, rooftop_solar references it)
\copy buildings FROM 'buildings.csv' CSV HEADER
\copy rooftop_solar FROM 'rooftop_solar.csv' CSV HEADER
\copy precincts FROM 'melbourne_cbd_precincts.csv' CSV HEADER
```

---

## Notes

- 40,951 buildings in total after filtering
- 14,995 buildings (~36.6%) have rooftop solar rating data from the 2015 Rooftop Project
- The solar rating data reflects rooftop conditions as of 2015 — newer buildings may not be covered
- Google Solar API data is stored in `solar_api_cache` and covers ~95% of buildings
- CER installed capacity is aggregated at postcode level — suburbs sharing a postcode will show the same installed capacity
