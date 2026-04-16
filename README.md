# 3D Solar Potential Analysing — Melbourne CBD

An interactive 3D web platform for exploring rooftop solar potential across Melbourne's CBD. Built for FIT5120 Industry Experience Studio.

Domain: http://3dsolarcbd.tech/explore 
Live: password-gated — use access code
E-Portfolio: https://bit.ly/SolarMapTP06

---

## Overview

The platform visualises every building in Melbourne CBD as a true-to-scale 3D extrusion coloured by solar potential score. Users can filter by roof type and solar rating, search buildings by address, inspect detailed solar metrics per building, and compare two buildings side-by-side. All solar data is served from a pre-populated PostgreSQL database on AWS EC2 — no live Google Solar API calls are made during normal use.

---

## Features

| Feature | Description |
|---|---|
| 3D Building Map | MapLibre GL extrusions for ~19,000 Melbourne CBD buildings, colour-coded by solar score (Excellent → Very Poor) |
| Solar Score | 0–100 score derived from City of Melbourne rooftop solar survey (1–5 patch ratings, linearly mapped) |
| Roof Type Filter | Filter by Flat, Hip, Gable, Pyramid, Shed — each type shown with a distinct dash pattern on outlines |
| Solar Potential Filter | Filter by score tier (Excellent / Good / Moderate / Poor / Very Poor) — combinable with roof type filter |
| Address Search | Autocomplete search bar finds buildings by street address; map flies to and highlights the result |
| Building Details | Click any building to see solar score, annual kWh, usable roof area, usable ratio, max solar panels, roof type, and street address |
| Monthly Output Chart | 12-bar chart distributing annual kWh across months using NASA POWER PSH data; hover for exact value |
| Building Comparison | Add up to 2 buildings to compare side-by-side; winning metrics highlighted with ★; third selection replaces oldest |
| Shareable Links | "Copy Shareable Link" copies a URL with `?buildingId=` so others open the same building directly |
| Compass Rotation | Clicking the compass cycles through 8 bearings (0° → 45° → … → 315°) with smooth animation |
| Home Page Stats | Live counts of buildings, usable roof area, annual yield, and high-potential sites from the GeoJSON |
| Password Gate | Site-wide access code gate at `/login` before any other page is accessible |
| WCAG 2.1 AA | Full keyboard navigation, focus-visible outlines, ARIA landmarks, live regions, and screen-reader labels throughout |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Vue 3 (Composition API), Vite 5 |
| Map | MapLibre GL JS 4.x |
| Routing | Vue Router 4 |
| Styling | Global CSS with CSS custom properties (no framework) |
| Backend API | FastAPI + psycopg3, deployed on AWS EC2 behind nginx + gunicorn |
| Database | PostgreSQL (AWS EC2) — buildings, rooftop_solar, solar_api_cache tables |
| Data pipeline | Python 3, pandas, geopandas, shapely |

---

## Project Structure

```
3D_Solar_Modelling/
├── Frontend/
│   ├── src/
│   │   ├── views/
│   │   │   ├── HomeView.vue              # Landing page with stats and feature cards
│   │   │   ├── ExploreView.vue           # Main 3D map, sidebar, filters, comparison
│   │   │   ├── PasswordView.vue          # Access code gate
│   │   │   └── FeaturePlaceholderView.vue # Coming-soon page for Precincts / AI Insights
│   │   ├── components/
│   │   │   └── MainNavbar.vue            # Shared navigation bar
│   │   ├── router/index.js               # Routes: /, /explore, /precincts, /insights, /login
│   │   ├── pictures/                     # PNG icons used in navbar and feature cards
│   │   ├── main.js
│   │   └── style.css                     # Global styles and CSS variables
│   ├── .env                              # Local env vars (not committed)
│   └── vite.config.js
│
├── Backend/
│   ├── combined-buildings.geojson        # ~19,000 buildings (served as static asset by Vite/nginx)
│   └── api/                              # FastAPI application
│       ├── app/
│       │   ├── main.py                   # App factory, router registration, middleware
│       │   ├── config.py                 # Settings via pydantic-settings (.env)
│       │   ├── db.py                     # psycopg3 connection pool
│       │   ├── models/schemas.py         # Pydantic response models
│       │   ├── routers/
│       │   │   ├── health.py             # GET /health
│       │   │   ├── buildings.py          # GET /buildings/search, /buildings/by-structure/{id}/address, /buildings/{id}
│       │   │   ├── solar.py              # GET /buildings/structure/{id}/solar, /buildings/{id}/solar
│       │   │   ├── yield_engine.py       # GET /buildings/{id}/yield
│       │   │   └── solar_cache.py        # GET /buildings/{id}/solar (cache-aside, calls Google Solar API — admin use only)
│       │   ├── services/
│       │   │   ├── building_query.py
│       │   │   ├── solar_query.py
│       │   │   ├── yield_calc.py
│       │   │   └── solar_api.py          # Google Solar API client (used only by solar_cache router)
│       │   ├── sql/                      # Raw .sql files loaded by services
│       │   └── constants/melbourne_psh.py # NASA POWER monthly PSH constants
│       ├── scripts/
│       │   ├── batch_solar_fetch.py      # Populates solar_api_cache from Google Solar API (run once)
│       │   └── reverse_geocode_addresses.py  # Writes addresses to solar_api_cache (run once)
│       └── pyproject.toml
│
├── Data wrangling/
│   ├── build_geojson.py                  # Joins CSVs → combined-buildings.geojson
│   └── MelSolar.py                       # Raw shapefile → cleaned buildings.csv + rooftop_solar.csv
│
├── scripts/
│   └── reverse_geocode_addresses.py      # Root-level geocoder (writes to solar_api_cache.address)
│
├── vite.config.js                        # root: ./Frontend, publicDir: ../Backend
└── package.json
```

---

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.11+ (only needed to regenerate the GeoJSON or run backend locally)

### Run the frontend dev server

```bash
# Install dependencies (from repo root)
npm install

# Start Vite dev server
npm run dev
# → http://localhost:5173
# Password: tp06888
```

### Environment variables

Create `Frontend/.env`:

```env
# URL of the backend API. Omit in production (nginx proxies /api/* same-origin).
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

If `VITE_API_BASE_URL` is not set, the frontend defaults to `/api/v1` (same-origin, used in production).

### Run the backend locally

```bash
cd Backend/api

# Create and activate virtualenv
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Create .env with DB credentials
cp .env.example .env
# Edit .env: DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

# Start the API
uvicorn app.main:app --reload --port 8000
# → http://localhost:8000/api/v1/docs
```

### Regenerate the GeoJSON

Run whenever `buildings.csv` or `rooftop_solar.csv` changes:

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

## Backend API

Base URL (production): `https://<ec2-host>/api/v1`  
Interactive docs: `/api/v1/docs`

| Endpoint | Description |
|---|---|
| `GET /health` | Liveness + DB readiness probe |
| `GET /buildings/search?q=` | Address autocomplete — partial, case-insensitive, returns up to 20 results |
| `GET /buildings/by-structure/{structure_id}/address` | Street address for a building by structure_id |
| `GET /buildings/structure/{structure_id}/solar` | Solar cache data (max panels, usable area, annual kWh, address) |
| `GET /buildings/{id}/solar` | Same as above, addressed by surrogate PK |
| `GET /buildings/{id}` | Full building record (geometry, height, roof type, solar summary, address) |
| `GET /buildings/{id}/yield` | Monthly kWh breakdown using NASA POWER PSH weights |

> **Note:** `GET /buildings/{structure_id}/solar` (no `structure/` prefix) is the admin cache-population route used by `batch_solar_fetch.py`. It calls the Google Solar API for cache misses. **The frontend does not use this route.**

---

## Database Population (one-time scripts)

These scripts are run once on the EC2 server to fill the database. They are not part of normal operation.

**1. Fetch solar data from Google Solar API into `solar_api_cache`:**

```bash
cd Backend/api
python scripts/batch_solar_fetch.py
# Processes buildings not yet in solar_api_cache
# Requires API running on localhost:8000
```

**2. Reverse-geocode addresses into `solar_api_cache.address`:**

```bash
cd scripts   # repo root /scripts/
python reverse_geocode_addresses.py --email your@email.com
# Calls Nominatim at 1 req/s for all buildings with missing addresses
# Progress is resumable — already-geocoded rows are skipped
```

---

## Data Sources

| Dataset | Source | Licence |
|---|---|---|
| Building footprints | [City of Melbourne — 2023 Building Footprints](https://data.melbourne.vic.gov.au/explore/dataset/building-footprints) | CC BY 4.0 |
| Rooftop solar survey | [City of Melbourne — Green Roof & Solar Potential](https://data.melbourne.vic.gov.au/explore/dataset/green-roofs-and-solar-potential-on-buildings) | CC BY 4.0 |
| Per-building solar data | [Google Solar API](https://developers.google.com/maps/documentation/solar) — max panels, usable array area, annual kWh, roof segment stats; pre-fetched and cached in PostgreSQL | Google Maps Platform ToS |
| Monthly PSH values | NASA POWER API (20-year climatology 2001–2020), scaled to BOM station 086338 baseline (4.1 PSH/day) | Public domain |
| Base map tiles | [CartoDB Light](https://carto.com/basemaps/) (via OpenStreetMap) | ODbL |
| Reverse geocoding | [Nominatim / OpenStreetMap](https://nominatim.openstreetmap.org/) | ODbL |

---

## Solar Score Methodology

```
solar_score_avg  =  mean of patch ratings across the building's roof segments
                    (Very Poor=1, Poor=2, Moderate=3, Good=4, Excellent=5)

solar_score (0–100)  =  round( (solar_score_avg − 1) / 4 × 100 )

usable_roof_area  =  footprint_area × usable_ratio
                     where usable_ratio = fraction of patches rated Good or Excellent

kwh_annual  =  usable_roof_area × 0.20 (efficiency) × 0.75 (PR) × 4.1 (PSH/day) × 365

max_solar_panels  =  from solar_api_cache.max_panels (Google Solar API, pre-fetched)
```

Monthly kWh is distributed using NASA POWER monthly PSH values (BOM-scaled), ensuring `sum(kwh_monthly) == kwh_annual`.

---

## Planned Features (Coming Soon)

- **Precincts** — group buildings into planning precincts for aggregate analysis
- **AI Insights** — explainable AI recommendations from building-level and precinct-level data