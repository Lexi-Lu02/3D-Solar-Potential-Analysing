# SolarMap — Melbourne CBD 3D Solar Platform

> An interactive 3D map that shows the rooftop solar potential of every building in Melbourne's CBD. Find out how much solar energy a building can generate, compare buildings side-by-side, and explore which precincts have the most untapped solar opportunity.

**Live site:** http://3dsolarcbd.me/  
**Access code:** `tp06888`  
**E-Portfolio:** https://bit.ly/SolarMapTP06

---

## Table of Contents

1. [Getting Started — Logging In](#1-getting-started--logging-in)
2. [Home Page](#2-home-page)
3. [3D Explore — The Main Map](#3-3d-explore--the-main-map)
   - [Navigating the Map](#navigating-the-map)
   - [Searching for a Building or Address](#searching-for-a-building-or-address)
   - [Using the Filter Panel](#using-the-filter-panel)
   - [Selecting a Building and Reading the Solar Panel](#selecting-a-building-and-reading-the-solar-panel)
   - [Monthly Output Chart](#monthly-output-chart)
   - [Sun Path & Shadow Analysis](#sun-path--shadow-analysis)
   - [Financial & Environmental Impact](#financial--environmental-impact)
   - [Comparing Two Buildings](#comparing-two-buildings)
   - [Sharing a Building](#sharing-a-building)
   - [Exporting Data](#exporting-data)
4. [Precincts — Neighbourhood Rankings](#4-precincts--neighbourhood-rankings)
5. [Understanding the Solar Score](#5-understanding-the-solar-score)
6. [Tips & Shortcuts](#6-tips--shortcuts)
7. [FAQ](#7-faq)
8. [Developer Setup](#8-developer-setup)

---

## 1. Getting Started — Logging In

1. Open **http://3dsolarcbd.me/** in your browser (Chrome or Firefox recommended).
2. You will be redirected to the login page automatically.
3. Type the access code **`tp06888`** and press **Enter** or click **Unlock**.
4. Once unlocked, you will not be asked again unless you clear your browser storage.

> If the page is blank or shows a loading spinner for more than 10 seconds, try a hard refresh with `Ctrl + Shift + R` (Windows) or `Cmd + Shift + R` (Mac).

---

## 2. Home Page

The home page gives you a quick overview of what the platform covers and live statistics pulled from the building database.

| Stat card | What it means |
|---|---|
| **Buildings Analysed** | Total number of Melbourne CBD buildings with solar data |
| **Usable Roof Area** | Combined m² of roof space rated Good or Excellent for solar across all buildings |
| **Annual Solar Yield** | Estimated combined kWh that could be generated per year if all usable space had panels |
| **High-Potential Sites** | Buildings with a solar score of 4 or above (out of 5) |

From the home page, click **Explore the 3D Map** or **Explore the Map** to jump straight into the interactive map. You can also use the navigation bar at the top to jump to any section.

---

## 3. 3D Explore — The Main Map

This is the core of the platform. Every building in Melbourne CBD is rendered as a 3D block and coloured by its solar potential score.

**Colour key (on the map):**

| Colour | Tier | Score Range |
|---|---|---|
| Dark green | Excellent | 4.5 – 5 / 5 |
| Bright green | Good | 3.5 – 4.4 / 5 |
| Yellow-green | Moderate | 2.5 – 3.4 / 5 |
| Pink | Poor | 1.5 – 2.4 / 5 |
| Red | Very Poor | 1 – 1.4 / 5 |

### Navigating the Map

| Action | How to do it |
|---|---|
| **Pan** | Click and drag |
| **Zoom in/out** | Scroll wheel, or pinch on touchscreen |
| **Tilt (3D view)** | Right-click and drag, or two-finger drag on touchscreen |
| **Rotate** | Hold `Ctrl` and drag, or use the compass button |
| **Reset north** | Click the compass button (top-right of map) to cycle through 8 compass bearings |
| **Zoom buttons** | Use the `+` / `−` buttons on the map if you prefer clicking |

### Searching for a Building or Address

1. Click the **search bar** at the top-left of the map (or press `/` on your keyboard).
2. Start typing a street name or number — suggestions appear as you type.
3. Click a suggestion to fly the map to that building and open its solar panel automatically.

> The search covers all ~19,000 buildings with a known street address. If you don't see a result, try a shorter query (e.g. `"Collins"` instead of `"123 Collins Street"`).

### Using the Filter Panel

Click the **Filters** button (top-left, with the sliders icon) to open the filter sidebar.

**Solar Potential filter** lets you show only buildings in a specific tier:

1. Expand the **Solar Potential** section by clicking its header.
2. Click a tier button (e.g. *Good*) — the map immediately hides all buildings outside that tier.
3. Click the same tier again, or click the **×** chip at the top of the filter panel, to clear the filter.

**Roof Type filter** lets you highlight buildings by their roof shape:

1. Expand the **Roof Type** section.
2. Toggle one or more roof types (Flat, Hip, Gable, Pyramid, Shed) — each type gets a distinct dash pattern drawn on its roof outline.
3. Toggle **Colour by Solar Potential** to keep the solar colour-coding visible while roof outlines are shown.

Both filters can be active at the same time and stack on top of each other.

### Selecting a Building and Reading the Solar Panel

Click any building on the map. A panel opens on the right side with:

| Section | What you see |
|---|---|
| **Solar Score** | A rating from 1 to 5 (from the City of Melbourne rooftop solar survey). Shows **No Data** if the building has no survey record. |
| **Solar Tier** | Excellent / Good / Moderate / Poor / Very Poor — derived from the score. |
| **Address** | Street address (reverse-geocoded). |
| **Roof Type** | Flat, Hip, Gable, etc. |
| **Building Height** | Total height in metres. |
| **Usable Ratio** | Percentage of the roof rated Good or Excellent. |
| **Max Solar Panels** | Maximum number of panels the roof can physically fit. |
| **Annual Electricity Generation** | Estimated kWh the building could produce per year. |
| **Sun Intensity** | Average solar energy hitting the roof per m² per day (kWh/m²/day). |
| **Roof Footprint** | Total surveyed roof area in m². |
| **Usable Roof Area** | Area actually suitable for panels (m²). |

Click the **?** button next to "Solar Score" to read a plain-language explanation of how the score is calculated.

> **No Data** means the City of Melbourne survey did not include that building's roof. The building is still shown on the map in grey.

### Monthly Output Chart

Below the building details, a **bar chart** shows how electricity production varies across the 12 months of the year.

- Hover over any bar to see the exact kWh value for that month.
- Production is highest in summer (December–February) and lowest in winter (June–August) due to longer daylight hours.
- The annual total shown in the panel equals the sum of all 12 bars.

### Sun Path & Shadow Analysis

This tool shows how the sun moves across the sky for this building on any day of the year and estimates how much of its roof is in shadow.

1. In the right panel, scroll to the **Sun Path** section.
2. Use the **date slider** to pick a date (defaults to today).
3. Use the **time slider** to move the sun position hour by hour.
4. The **shadow coverage** percentage updates to estimate what fraction of the roof is shaded by nearby buildings at that exact time.
5. A coloured overlay appears on the map showing shaded vs. unobstructed roof sections.

> Shadow coverage is an estimate based on building footprint geometry. It is most accurate at midday.

### Financial & Environmental Impact

Scroll to the **Financial Impact** and **Environmental Impact** sections in the right panel:

**Financial Impact**

| Field | What it means |
|---|---|
| Installation Cost | Estimated upfront cost of panels sized for this roof |
| Annual Savings | Estimated electricity bill savings per year |
| Payback Period | How many years until savings cover the install cost |
| Lifetime Net Savings | Total savings over 25 years minus install cost |

**Environmental Impact**

| Field | What it means |
|---|---|
| Annual CO₂ Reduction | Tonnes of CO₂ avoided per year compared to grid electricity |
| Equivalent Trees | Trees needed to absorb the same CO₂ |
| Equivalent Petrol | Litres of petrol whose combustion equals the CO₂ saved |

Use the **Season selector** to see how output and savings change across Summer, Autumn, Winter, Spring, and Annually.

### Comparing Two Buildings

You can compare any two buildings side-by-side:

1. Select a building by clicking it on the map.
2. Click **Add to Compare** in the right panel.
3. Click a second building on the map and click **Add to Compare** again.
4. The **comparison panel** slides in from the bottom showing both buildings' key metrics next to each other.
5. The metric where one building clearly wins is marked with a **★**.
6. To swap in a different building, select it and click **Add to Compare** — it replaces the oldest one in the pair.
7. Click the **×** on either building card to remove it from the comparison.

### Sharing a Building

1. Select any building.
2. Click **Copy Shareable Link** in the right panel.
3. Share the copied URL — anyone who opens it will land directly on that building with the solar panel open.

### Exporting Data

1. Select a building.
2. Click **Export CSV** in the right panel.
3. A `.csv` file downloads with all visible metrics for that building (solar score, kWh, roof area, financial estimates, assumptions used, etc.).

---

## 4. Precincts — Neighbourhood Rankings

The **Precincts** page (accessible from the top navigation bar) ranks Melbourne CBD's neighbourhoods by their solar opportunity.

**What you see:**

- A map showing precinct boundaries, colour-coded by solar potential.
- A ranked list on the left showing each precinct's key numbers.

**Sorting options** — click the sort buttons at the top of the list to rank by:

| Sort key | What it ranks by |
|---|---|
| Annual Output | Total estimated kWh per year across all buildings in the precinct |
| Usable Roof Area | Total m² of roof area rated Good or Excellent |
| Adoption Gap | Difference between potential solar capacity (kW) and currently installed capacity (kW) — higher gap = more untapped opportunity |
| Buildings | Number of buildings in the precinct |

**Clicking a precinct** on the map or in the list opens a detail panel showing:

- Installed vs. potential solar capacity (kW)
- Adoption gap (how much more could be installed)
- Total usable roof area
- Building count
- Annual output estimate

The **top 5 precincts** by the current sort key are highlighted in the list.

---

## 5. Understanding the Solar Score

The solar score (1–5) comes from the **City of Melbourne Rooftop Solar Survey**. Each building's roof is divided into patches, and each patch is rated:

| Rating | Meaning |
|---|---|
| 5 — Excellent | Maximum solar suitability; minimal shading, ideal orientation |
| 4 — Good | Strong solar suitability |
| 3 — Moderate | Average — some shading or suboptimal angle |
| 2 — Poor | Limited suitability |
| 1 — Very Poor | Heavily shaded or unsuitable orientation |

The score shown in the app is the **average** of all patch ratings on that building's roof.

Buildings with **No Data** were not included in the survey. They are still shown on the map but are not included in any solar yield calculations.

The **map colour-coding** is based on this same 1–5 scale, mapped visually so dark green = Excellent and red = Very Poor.

---

## 6. Tips & Shortcuts

| Tip | How |
|---|---|
| Jump to search | Press `/` anywhere on the Explore page |
| Reset map bearing | Click the compass icon to cycle to north-up |
| Clear all filters | Click the **×** chip in the filter panel header |
| Check a specific address without clicking | Use the search bar — it opens the panel automatically |
| Compare buildings from different areas | Pan the map after adding the first building, then click the second |
| See the full year's data | Scroll to the monthly chart; hover each bar for exact values |
| Find high-potential buildings fast | Apply the **Excellent** Solar Potential filter, then click any dark-green building |
| Share the exact view | Use Copy Shareable Link — the URL includes the building ID |

---

## 7. FAQ

**Q: Why does a building show "No Data" for the solar score?**  
A: That building was not included in the City of Melbourne rooftop solar survey. The building is still shown on the map but we cannot calculate its score or yield.

**Q: Why is the annual kWh estimate different from what my solar installer quoted?**  
A: Our estimate uses a standardised formula (20% panel efficiency × 75% performance ratio × NASA POWER monthly sun data for Melbourne). A real installer quote accounts for your specific panel brand, shading from chimneys and trees, inverter losses, and local council rules.

**Q: The map is slow or not loading — what should I do?**  
A: The map loads ~19,000 building polygons at once. On a slow connection this can take 10–20 seconds. Wait for the loading bar to complete. If buildings never appear, try a hard refresh (`Ctrl + Shift + R`).

**Q: Can I use this on a phone or tablet?**  
A: Yes. Use pinch-to-zoom and two-finger drag to tilt the 3D view. The layout adjusts for smaller screens, though the comparison panel works best on a wider display.

**Q: Does the site save my session?**  
A: The login state is saved in your browser's session storage. It persists until you close the tab or clear browser data. You will not need to re-enter the password if you navigate between pages.

**Q: Why do some buildings look grey with no colour?**  
A: Grey buildings have no survey data. If a Solar Potential filter is active, buildings outside the selected tier are also hidden, which can make many buildings disappear.

**Q: What does the Adoption Gap on the Precincts page mean?**  
A: It is the difference between the total solar capacity that *could* be installed (kW) and what is *currently* installed in that area. A large gap means the precinct has a lot of untapped solar potential.

---

## 8. Developer Setup

### Prerequisites

- Node.js 18+
- Python 3.11+ (only needed to run the backend locally or regenerate GeoJSON)

### Run the frontend dev server

```bash
# Install dependencies (from repo root)
npm install

# Start Vite dev server
npm run dev
# → http://localhost:5173
# Password: tp06888
```

### Frontend environment variables

Create `Frontend/.env`:

```env
VITE_API_BASE_URL=http://<ec2-ip>/api/v1
VITE_GEOJSON_URL=http://<ec2-ip>/combined-buildings.geojson
VITE_PRECINCTS_URL=http://<ec2-ip>/melbourne_cbd_precincts.geojson
VITE_SOLAR_API_KEY=<your-google-solar-api-key>
```

In production these are set in `Frontend/.env.production` using relative paths so nginx serves them same-origin.

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
# → Swagger docs: http://localhost:8000/api/v1/docs
```

### Build for production

```bash
npm run build
# → outputs to dist/
```

### Project structure

```
3D_Solar_Modelling/
├── Frontend/
│   ├── src/
│   │   ├── views/
│   │   │   ├── HomeView.vue              # Landing page with live stats
│   │   │   ├── ExploreView.vue           # Main 3D map, sidebar, filters, comparison
│   │   │   ├── PrecinctsView.vue         # Precinct rankings map
│   │   │   ├── PasswordView.vue          # Access code gate
│   │   │   └── FeaturePlaceholderView.vue # Coming-soon stub (AI Insights)
│   │   ├── components/
│   │   │   ├── MainNavbar.vue            # Shared top navigation bar
│   │   │   └── FilterPanel.vue           # Solar + roof type filter sidebar
│   │   ├── router/index.js               # Routes: /, /explore, /precincts, /insights, /login
│   │   ├── pictures/                     # PNG icons
│   │   ├── main.js
│   │   └── style.css                     # Global styles and CSS custom properties
│   └── vite.config.js
│
├── Backend/
│   ├── combined-buildings.geojson        # ~19,000 buildings (served as static asset)
│   └── app/
│       ├── main.py                       # FastAPI app factory
│       ├── models/schemas.py             # Pydantic response models
│       ├── routers/                      # FastAPI route handlers
│       ├── services/                     # Business logic (yield calc, building queries)
│       └── sql/                          # Raw SQL files
│
└── Data wrangling/
    ├── build_geojson.py                  # Joins CSVs → combined-buildings.geojson
    └── MelSolar.py                       # Raw shapefile → cleaned CSVs
```

### Backend API reference

Base URL (production): `https://<ec2-host>/api/v1`  
Interactive docs: `/api/v1/docs`

| Endpoint | Description |
|---|---|
| `GET /health` | Liveness + DB readiness check |
| `GET /buildings/search?q=` | Address autocomplete (up to 20 results) |
| `GET /buildings/by-structure/{id}/address` | Street address by structure_id |
| `GET /buildings/structure/{id}/yield` | Monthly + annual kWh, solar_score_avg |
| `GET /buildings/{id}/solar` | Solar cache data (panels, usable area, kWh, address) |
| `GET /buildings/{id}` | Full building record (geometry, height, roof type, solar) |
| `GET /precincts` | List of precincts with installed/potential capacity and adoption gap |
| `GET /sun/position` | Sun altitude and azimuth for a given date/time |
| `GET /sun/path` | Full day arc of sun positions |
| `GET /buildings/{id}/impact` | Financial and environmental impact estimates |

### Data sources

| Dataset | Source | Licence |
|---|---|---|
| Building footprints | [City of Melbourne — 2023 Building Footprints](https://data.melbourne.vic.gov.au/explore/dataset/building-footprints) | CC BY 4.0 |
| Rooftop solar survey | [City of Melbourne — Green Roof & Solar Potential](https://data.melbourne.vic.gov.au/explore/dataset/green-roofs-and-solar-potential-on-buildings) | CC BY 4.0 |
| Per-building solar data | [Google Solar API](https://developers.google.com/maps/documentation/solar) — pre-fetched and cached | Google Maps Platform ToS |
| Monthly PSH | NASA POWER API (2001–2020 climatology), calibrated to BOM station 086338 (4.1 PSH/day) | Public domain |
| Base map tiles | [CartoDB Light](https://carto.com/basemaps/) via OpenStreetMap | ODbL |
| Reverse geocoding | [Nominatim / OpenStreetMap](https://nominatim.openstreetmap.org/) | ODbL |

### Solar yield formula

```
solar_score_avg    = mean of patch ratings (Very Poor=1 … Excellent=5)
usable_roof_area   = total roof area × fraction of patches rated Good or Excellent
kwh_annual         = usable_roof_area × 0.20 (panel efficiency)
                                       × 0.75 (performance ratio)
                                       × monthly PSH values (NASA POWER / BOM)
```

Monthly kWh uses per-month PSH values so `sum(kwh_monthly) == kwh_annual` exactly.
