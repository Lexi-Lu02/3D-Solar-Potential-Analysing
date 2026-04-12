# Solar Map API

Read-only HTTP API for the **3D Solar Potential Analysing** project. It serves
Melbourne CBD building footprints, rooftop solar suitability data, and
per-building kWh estimates to the Vue + MapLibre frontend.

> **Status:** Phase A (project skeleton + `/health` endpoint). Phases B–E will
> add building details, kWh yield, address backfill, and EC2 deployment. See
> the implementation plan in `C:\Users\Flame\.claude\plans\` for the roadmap.

---

## 1. Overview

| | |
|---|---|
| **Stack** | FastAPI, psycopg3 (raw SQL), PostgreSQL, Pydantic v2 |
| **Mode** | Read-only (no POST/PUT/DELETE; DB user has SELECT only) |
| **Base URL (local)** | `http://localhost:8000/api/v1` |
| **Base URL (prod)**  | `https://<domain>/api/v1` (same EC2 as the frontend, behind nginx) |
| **Auth** | None — data is public (CC BY 4.0, City of Melbourne) |
| **Auto-generated docs** | Swagger UI at `/api/v1/docs`, ReDoc at `/api/v1/redoc` |

This README is the **narrative** documentation. For interactive
"Try it out" requests and machine-readable schemas, run the service and open
`http://localhost:8000/api/v1/docs` — that page is generated from the same
Pydantic models the API uses to validate responses, so it can never drift.

The API serves these epics from the project plan:

- **Epic 1** — 3D City Map (single-building data fetch)
- **Epic 2** — Building Details Panel
- **Epic 3** — kWh Energy Yield Calculation Engine

---

## 2. Quick Start

Requires Python **3.11+** (3.12 recommended).

```bash
# 1. clone & enter the API folder
cd Backend/api

# 2. create a virtualenv
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# 3. install the package and dev tools
pip install -e ".[dev]"

# 4. configure database credentials
cp .env.example .env        # Windows: copy .env.example .env
# then edit .env and fill in DB_HOST / DB_USER / DB_PASSWORD

# 5. run the API
uvicorn app.main:app --reload

# 6. verify
curl -sf http://localhost:8000/api/v1/health
# → {"status":"ok","db":"ok","buildings_count":40951}

# 7. run unit tests
pytest
```

Open `http://localhost:8000/api/v1/docs` in a browser for the auto-generated
Swagger UI.

---

## 3. Environment Variables

All settings are read from environment variables (and `.env` during local
development). The app refuses to start if a required variable is missing —
better to fail loud at boot than silently use a wrong DB.

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `DB_HOST` | ✅ | — | PostgreSQL host (e.g. `16.176.25.174`) |
| `DB_PORT` | ❌ | `5432` | PostgreSQL port |
| `DB_NAME` | ✅ | — | Database name (e.g. `melbourne_solar`) |
| `DB_USER` | ✅ | — | DB user. **Production must use the read-only role `solarmap_api_ro`.** |
| `DB_PASSWORD` | ✅ | — | DB password |
| `DB_POOL_MIN_SIZE` | ❌ | `1` | psycopg connection pool minimum |
| `DB_POOL_MAX_SIZE` | ❌ | `10` | psycopg connection pool maximum |
| `CORS_ORIGINS` | ❌ | `""` | Comma-separated allowed origins. **Leave empty in production** (frontend and API share the same nginx → same-origin → CORS not needed). Set to `http://localhost:5173` for local frontend dev. |
| `LOG_LEVEL` | ❌ | `INFO` | `DEBUG` / `INFO` / `WARNING` / `ERROR` |

`.env` must never be committed — it is already listed in `.gitignore`.

---

## 4. Authentication

**None.** All data is openly licensed (CC BY 4.0, City of Melbourne) and the
API exposes nothing user-specific. If a future iteration adds per-user state
(saved buildings, etc.) authentication will be documented here.

---

## 5. Endpoints

> The following are the endpoints currently implemented. The full list will
> grow as Phases B and C land.

### `GET /api/v1/health`

**Purpose:** Liveness probe + database readiness check. Used by systemd /
nginx / uptime monitors. Not consumed by the frontend.

**Epic:** Operations / monitoring

**Path parameters:** none
**Query parameters:** none

**Response 200**

```json
{
  "status": "ok",
  "db": "ok",
  "buildings_count": 40951
}
```

| Field | Type | Description |
|---|---|---|
| `status` | `"ok"` \| `"error"` | Overall service health |
| `db` | `"ok"` \| `"unreachable"` | Whether the API can SELECT from PostgreSQL |
| `buildings_count` | int | Live row count of the `buildings` table |

**Response 503** — DB unreachable or query failed:

```json
{
  "status": "error",
  "db": "unreachable",
  "buildings_count": 0
}
```

**Cache:** `no-store`
**Rate limit:** none

**curl example:**

```bash
curl -sf http://localhost:8000/api/v1/health | jq .
```

---

## 6. Error Format

Every non-2xx response has the same envelope, with a `request_id` you can
grep server logs for:

```json
{
  "error": "internal_error",
  "request_id": "9f8b3a-...",
  "detail": "Optional human-readable message"
}
```

| Status | `error` slug | Meaning |
|---|---|---|
| 400 | `bad_request` | Malformed request body / params |
| 404 | `not_found` | Resource (building) does not exist |
| 422 | `validation_error` | Input failed Pydantic validation (e.g. non-integer ID) |
| 429 | `rate_limited` | Too many requests from this IP |
| 500 | `internal_error` | Unhandled server-side error (Python tracebacks **never** leak; check logs by `request_id`) |
| 503 | `service_unavailable` | DB unreachable or other downstream failure |

The response also includes an `x-request-id` header on every response, set
either from the incoming `X-Request-ID` header (if provided by an upstream
proxy) or generated fresh.