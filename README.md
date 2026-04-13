# 3D Solar Potential Analysing — Melbourne CBD

An interactive 3D web platform for exploring rooftop solar potential across Melbourne's CBD. Built for FIT5120 Industry Experience Studio, Iteration 1.

---

## Overview

The platform visualises every building in Melbourne CBD as a true-to-scale 3D extrusion coloured by solar potential score. Users can filter by roof type and solar rating, inspect individual buildings for detailed metrics, compare two buildings side-by-side, and search by Structure ID.

Live solar data is optionally fetched from the Google Solar API on demand when a building is selected, and falls back to pre-computed local estimates when unavailable.

---

## Features

| Feature | Description |
|---|---|
| 3D Building Map | MapLibre GL extrusions for 19,326 Melbourne CBD buildings, colour-coded by solar score (Excellent → Very Poor) |
| Solar Score | 0–100 score derived from City of Melbourne rooftop solar survey ratings (1–5 scale linearly mapped) |
| Roof Type Filter | Filter by Flat, Hip, Gable, Pyramid, Shed — each type shown with a distinct dash pattern on outlines |
| Solar Potential Filter | Filter buildings by score tier (Excellent / Good / Moderate / Poor / Very Poor) — combinable with roof type filter |
| Collapsible Panels | Building details sidebar and both filter cards can be collapsed/expanded independently |
| Building Details | Click any building to see solar score, annual kWh, usable roof area, roof footprint, height, roof type, usable ratio, and max solar panels |
| Monthly Output Chart | 12-bar chart distributing annual kWh across months using NASA POWER PSH data; hover for exact monthly value |
| Building Comparison | Add up to 2 buildings to compare side-by-side; winning metrics highlighted; third selection replaces oldest |
| Structure ID Search | Search bar in the sidebar accepts a Structure ID and flies to + highlights the matching building |
| Shareable Links | "Copy Shareable Link" copies a URL with `?buildingId=` so others can open the same building directly |
| Google Solar API | On-demand fetch of `maxArrayPanelsCount`, `maxArrayAreaMeters2`, `wholeRoofStats.areaMeters2`, and annual kWh; session-cached per building to avoid repeat billing; silently falls back to local data if unavailable |
| Compass Rotation | Clicking the compass cycles through 8 bearings (0° → 45° → … → 315°) with smooth animation |
| Home Page Stats | Live counts of buildings, usable roof area, annual yield, and high-potential sites computed from the GeoJSON |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Vue 3 (Composition API), Vite 5 |
| Map | MapLibre GL JS 4.x |
| Routing | Vue Router 5 |
| Styling | Global CSS with CSS custom properties (no framework) |
| Data pipeline | Python 3, pandas, geopandas, shapely |
| Backend API | FastAPI + psycopg3 + PostgreSQL *(health endpoint only — building/yield routes in progress)* |

---

## Project Structure

```
3D_Solar_Modelling/
├── Frontend/
│   ├── src/
│   │   ├── views/
│   │   │   ├── HomeView.vue          # Landing page with stats and feature cards
│   │   │   ├── ExploreView.vue       # Main 3D map with sidebar and filters
│   │   │   ├── FeaturePlaceholderView.vue
│   │   │   └── PasswordView.vue      # Login gate
│   │   ├── components/
│   │   │   └── MainNavbar.vue        # Shared navigation bar
│   │   ├── router/
│   │   │   └── index.js              # Vue Router routes (/, /explore, /precincts, /insights)
│   │   ├── pictures/                 # PNG icons for navbar and feature cards
│   │   ├── main.js
│   │   └── style.css                 # Global styles and CSS variables
│   └── .env                          # Local env vars (not committed)
│
├── Backend/
│   ├── combined-buildings.geojson    # 19,326 buildings, 15.4 MB (served as static asset)
│   └── api/                          # FastAPI backend (PostgreSQL-backed)
│       ├── app/
│       │   ├── main.py
│       │   ├── config.py
│       │   ├── db.py
│       │   ├── models/schemas.py     # Pydantic response models
│       │   ├── routers/health.py     # GET /api/v1/health
│       │   └── sql/
│       └── pyproject.toml
│
├── Data wrangling/
│   ├── buildings.csv                 # 19,326 building footprints (City of Melbourne 2023)
│   ├── rooftop_solar.csv             # 14,969 buildings with solar survey data
│   ├── build_geojson.py              # Joins CSVs → combined-buildings.geojson
│   ├── process_melbourne_solar.py    # Raw shapefile → cleaned CSVs
│   └── mga55_gda95_green_roof_solar.shp  # Source solar survey shapefile
│
├── vite.config.js                    # root: ./Frontend, publicDir: ../Backend
└── package.json
```

---

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.11+ (only needed to regenerate the GeoJSON)

### Run the dev server

```bash
# Install dependencies (from repo root)
npm install

# Start dev server
npm run dev
# → http://localhost:5173
```

### Environment variables

Create `Frontend/.env` (Vite reads `.env` relative to its configured `root`):

```env
VITE_SOLAR_API_KEY=your_google_solar_api_key_here
```

Leave `VITE_SOLAR_API_KEY` blank or omit the file entirely to run on local data only at zero API cost.

### Regenerate the GeoJSON

Run this whenever `buildings.csv` or `rooftop_solar.csv` changes:

```bash
cd "Data wrangling"
python build_geojson.py
# → writes ../Backend/combined-buildings.geojson
```

### Build for production

```bash
npm run build
# → outputs to dist/
```

---

## Data Sources

| Dataset | Source | Licence |
|---|---|---|
| Building footprints | City of Melbourne Open Data — 2023 Building Footprints | CC BY 4.0 |
| Rooftop solar survey | City of Melbourne — Green Roof & Solar Potential (shapefile) | CC BY 4.0 |
| Monthly PSH values | NASA POWER API (20-year climatology 2001–2020), scaled to BOM station 086338 baseline (4.1 PSH/day) | Public domain |
| Base map tiles | CartoDB Light (via OpenStreetMap) | ODbL |

---

## Solar Score Methodology

```
solar_score_avg  =  mean of patch ratings across the building's roof segments
                    (Very Poor=1, Poor=2, Moderate=3, Good=4, Excellent=5)

solar_score (0–100)  =  round( (solar_score_avg − 1) / 4 × 100 )

usable_roof_area  =  footprint_area × usable_ratio
                     where usable_ratio = fraction of patches rated Good or Excellent

kwh_annual  =  usable_roof_area × 0.20 (efficiency) × 0.75 (PR) × 4.1 (PSH/day) × 365
```

When the Google Solar API is available, `usable_roof_area`, `roofAreaM2`, and `kwh_annual` are replaced with live values from `maxArrayAreaMeters2`, `wholeRoofStats.areaMeters2`, and `solarPanelConfigs[-1].yearlyEnergyDcKwh` respectively.

---

## Backend API (In Progress)

Base URL: `http://localhost:8000/api/v1`

| Endpoint | Status | Description |
|---|---|---|
| `GET /health` | ✅ Live | Liveness + DB readiness probe |
| `GET /buildings/{id}` | 🔄 Planned | Single building details from PostgreSQL |
| `GET /buildings/{id}/yield` | 🔄 Planned | Monthly kWh breakdown (NASA POWER PSH) |

See `Backend/api/README.md` for full API documentation.

---

## Iteration 1 Scope

User stories implemented:

- **US 1.1** — View 3D building map coloured by solar potential
- **US 1.2** — Filter buildings by roof type and solar potential tier
- **US 2.1** — Click a building to inspect detailed solar metrics
- **US 2.2** — Compare two buildings side-by-side
