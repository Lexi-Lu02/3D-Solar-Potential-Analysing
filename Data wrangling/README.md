# Data Wrangling — Melbourne Solar Potential

This folder contains the data processing pipeline that transforms raw open data into clean, database-ready tables for Epic 1 and Epic 2.

---

## Output Files

| File | Rows | Description |
|---|---|---|
| `buildings.csv` | 40,951 | Cleaned building footprints — used for 3D map rendering |
| `rooftop_solar.csv` | 14,995 | Aggregated solar potential per building — used for solar info panel |

These two files are ready to import directly into PostgreSQL.

---

## Source Data

| File | Source | Description |
|---|---|---|
| `2023-building-footprints.csv` | [City of Melbourne Open Data](https://data.melbourne.vic.gov.au/explore/dataset/2023-building-footprints/) | Building geometry, height, and roof type — captured May 2023 |
| `mga55_gda95_green_roof_solar.shp` (.shx .dbf .prj) | [City of Melbourne Rooftop Project](https://data.melbourne.vic.gov.au/explore/dataset/rooftops-with-environmental-retrofitting-opportunities-rooftop-project/) | Solar suitability polygons for Melbourne rooftops — rated Excellent / Good / Moderate / Poor / Very Poor |

Both datasets are licensed under **CC BY 4.0 — City of Melbourne**.

---

## What the Script Does

Run `process_melbourne_solar.py` to reproduce both output CSVs from the raw source files.

### Step-by-step

**Step 1 — Load raw data**
Reads the building footprints CSV and the solar shapefile.

**Step 2 — Clean building footprints**
- Converts the `Geo Shape` GeoJSON column into geometry objects
- Reprojects coordinate system from `EPSG:4326` (lat/lng) to `EPSG:28355` (MGA Zone 55, matching the solar shapefile)
- Extracts `lat` and `lng` as separate columns from `Geo Point`
- Converts `date_captured` from integer format `20180528` to proper date `2018-05-28`
- Filters out non-building structures (walls, fences, etc.) — keeps `footprint_type == 'Structure'` only

**Step 3 — Clean solar shapefile**
- Maps text ratings to numeric scores: `Excellent=5, Good=4, Moderate=3, Poor=2, Very Poor=1`
- Removes noise polygons smaller than 4 m²

**Step 4 — Spatial join**
- Matches each solar roof polygon to the building it sits on using `intersects` spatial predicate
- Where one polygon overlaps multiple buildings, keeps only the first match
- Overall match rate: **94.9%**

**Step 5 — Aggregate solar data per building**
- Groups all roof polygons by `structure_id` and calculates:
  - `total_roof_area` — total roof area in m²
  - `usable_roof_area` — area rated Good or above (score ≥ 4)
  - `dominant_rating` — most common rating across all patches
  - `solar_score_avg` — average score (1–5)
  - `roof_patch_count` — number of roof polygons
  - `excellent_area` — area rated Excellent
  - `usable_ratio` — usable area / total area (0–1)

**Step 6 — Build buildings table**
Selects and renames the relevant columns from the cleaned building footprints.

**Step 7 — Export**
Writes `buildings.csv` and `rooftop_solar.csv`.

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
| `building_height` | float | Total building height in metres (for 3D rendering) |
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
| `dominant_rating` | string | Most common solar rating: Excellent / Good / Moderate / Poor / Very Poor |
| `solar_score_avg` | float | Average solar score 1–5 |
| `roof_patch_count` | int | Number of individual roof polygons |
| `excellent_area` | float | Area rated Excellent in m² |
| `usable_ratio` | float | Usable roof ratio 0–1 (e.g. 0.86 = 86% usable) |

---

## How to Reproduce

### 1. Install dependencies
```bash
pip install geopandas pandas shapely pyproj
```

### 2. Make sure these files are in the same folder as the script
```
Data wrangling/
├── process_melbourne_solar.py
├── 2023-building-footprints.csv
├── mga55_gda95_green_roof_solar.shp
├── mga55_gda95_green_roof_solar.shx
├── mga55_gda95_green_roof_solar.dbf
└── mga55_gda95_green_roof_solar.prj
```

### 3. Run the script
```bash
cd "Data wrangling"
python process_melbourne_solar.py
```

Output: `buildings.csv` and `rooftop_solar.csv` will be generated in the same folder.

---

## How to Import into PostgreSQL

Run in order (buildings first, as rooftop_solar references it):

```sql
-- Enable PostGIS extension (run once)
CREATE EXTENSION IF NOT EXISTS postgis;

-- Create tables (see backend schema file for full SQL)
-- Then import:
\copy buildings FROM 'buildings.csv' CSV HEADER
\copy rooftop_solar FROM 'rooftop_solar.csv' CSV HEADER
```

Join the two tables using `structure_id`:
```sql
SELECT b.structure_id, b.roof_type, b.building_height,
       s.total_roof_area, s.dominant_rating, s.solar_score_avg
FROM buildings b
LEFT JOIN rooftop_solar s ON b.structure_id = s.structure_id;
```

---

## Notes

- 40,951 buildings in total after filtering
- 14,995 buildings (~77.5%) have solar rating data — the remaining 22.5% had no matching solar polygons (mostly very small structures or structures outside the solar dataset coverage)
- The solar data was originally produced in 2015 as part of Melbourne's Rooftop Project — it reflects rooftop conditions at that time
- Cool roof, extensive green roof, and intensive green roof shapefiles are available in the same download but are reserved for Epic 3
