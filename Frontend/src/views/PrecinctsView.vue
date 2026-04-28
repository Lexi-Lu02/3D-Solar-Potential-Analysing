<template>
  <div class="map-page">
    <MainNavbar />
    <main id="main-content" class="main">
      <div id="precinct-map" role="application" aria-label="Interactive precinct solar map of Melbourne CBD">
        <div v-if="isLoading" class="loading" role="status" aria-live="polite" aria-atomic="true" :aria-label="loadingText">
          <div class="loading-spinner" aria-hidden="true"></div>
          <div class="loading-text">{{ loadingText }}</div>
        </div>

      </div>

      <aside class="sidebar" :class="{ 'sidebar--collapsed': !sidebarOpen }" aria-label="Precinct details panel">
        <button
          class="sidebar-strip-btn"
          @click="sidebarOpen = !sidebarOpen"
          :aria-label="sidebarOpen ? 'Collapse precinct details panel' : 'Expand precinct details panel'"
          :aria-expanded="sidebarOpen"
          aria-controls="sidebar-body"
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
            <path
              :d="sidebarOpen ? 'M10 4l-4 4 4 4' : 'M6 4l4 4-4 4'"
              stroke="currentColor"
              stroke-width="1.5"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
        </button>

        <div id="sidebar-body" class="sidebar-body">
          <!-- Header -->
          <div class="sidebar-header">
            <div class="sidebar-title-row">
              <div>
                <div class="rankings-label">Rankings</div>
                <div class="sidebar-title">Precinct Solar Rankings</div>
              </div>
              <button
                class="sidebar-export-btn"
                @click="exportPrecinctsCsv"
                aria-label="Export precinct data as CSV"
              >
                Export CSV
              </button>
            </div>
          </div>

          <!-- Sort tabs — full width, one per sort option -->
          <div class="sort-tabs" role="group" aria-label="Sort options">
            <button
              v-for="s in sortOptions"
              :key="s.id"
              class="sort-tab"
              :class="{ active: sortBy === s.id }"
              :aria-pressed="sortBy === s.id"
              @click="sortBy = s.id"
            >{{ s.label }}</button>
          </div>

          <div class="sidebar-content">
            <!-- Selected precinct detail -->
            <div v-if="selectedPrecinct" class="building-panel visible precinct-detail-panel">
              <div class="panel-id">{{ selectedPrecinct.name.toUpperCase() }}</div>

              <div class="score-bar-wrap">
                <div class="score-header">
                  <span class="score-label">Rank</span>
                  <span class="score-value">#{{ selectedPrecinct.rank }}</span>
                </div>
                <div class="score-bar">
                  <div
                    class="score-fill"
                    :style="{ width: Math.max(4, 100 - ((selectedPrecinct.rank - 1) / Math.max(1, sortedPrecincts.length - 1)) * 100) + '%', background: tierColor(selectedPrecinct.tier) }"
                  ></div>
                </div>
                <div class="score-tier" :style="{ color: tierColor(selectedPrecinct.tier) }">
                  {{ tierLabel(selectedPrecinct.tier) }}
                </div>
              </div>

              <div class="section-title">Precinct Info</div>
              <div class="info-row">
                <span class="info-key">Precinct ID</span>
                <span class="info-val">{{ selectedPrecinct.precinct_id }}</span>
              </div>
              <div class="info-row">
                <span class="info-key">Name</span>
                <span class="info-val">{{ selectedPrecinct.name }}</span>
              </div>
              <div class="info-row">
                <span class="info-key">Postcode</span>
                <span class="info-val">{{ selectedPrecinct.postcode || '—' }}</span>
              </div>
              <div class="info-row">
                <span class="info-key">Buildings</span>
                <span class="info-val">{{ selectedPrecinct.building_count.toLocaleString() }}</span>
              </div>

              <div class="section-title">Solar Capacity</div>
              <div class="metrics-grid">
                <div class="metric-card">
                  <div class="metric-val">{{ formatKwh(selectedPrecinct.total_kwh) }}</div>
                  <div class="metric-label">Total Annual Output</div>
                  <div class="metric-sub">total_kwh_annual</div>
                </div>
                <div class="metric-card">
                  <div class="metric-val">{{ formatArea(selectedPrecinct.total_area) }}</div>
                  <div class="metric-label">Total Usable Roof Area</div>
                  <div class="metric-sub">total_usable_area_m2</div>
                </div>
                <div class="metric-card">
                  <div class="metric-val">{{ formatKw(selectedPrecinct.installed_capacity_kw) }}</div>
                  <div class="metric-label">Installed Capacity</div>
                  <div class="metric-sub">installed_capacity_kw</div>
                </div>
                <div class="metric-card">
                  <div class="metric-val">{{ formatKw(selectedPrecinct.potential_capacity_kw) }}</div>
                  <div class="metric-label">Potential Capacity</div>
                  <div class="metric-sub">potential_capacity_kw</div>
                </div>
                <div class="metric-card metric-card--wide">
                  <div class="metric-val">{{ selectedPrecinct.adoption_gap_kw != null ? formatKw(selectedPrecinct.adoption_gap_kw) : formatKwh(selectedPrecinct.adoption_gap) }}</div>
                  <div class="metric-label">Adoption Gap</div>
                  <div class="metric-sub">adoption_gap_kw</div>
                </div>
              </div>

              <button class="share-btn" @click="selectedPrecinct = null" style="margin-top: 4px;">← Back to Rankings</button>
            </div>

            <!-- Ranked table -->
            <div v-else>
              <div v-if="sortedPrecincts.length === 0 && !isLoading" class="empty-state">
                <div class="empty-icon">☀</div>
                <div class="empty-text">No precinct data available</div>
              </div>

              <template v-else>
                <!-- Column headers — active sort column highlighted -->
                <div class="precinct-table-head">
                  <div class="pt-col-name">Precinct Name</div>
                  <div class="pt-col-kwh"       :class="{ 'col-active': sortBy === 'kwh'       }">Annual kWh</div>
                  <div class="pt-col-area"      :class="{ 'col-active': sortBy === 'area'      }">Roof Area</div>
                  <div class="pt-col-bldg"      :class="{ 'col-active': sortBy === 'buildings' }">Buildings</div>
                  <div class="pt-col-stat"      :class="{ 'col-active': sortBy === 'gap'       }">Adoption Gap</div>
                </div>

                <!-- Rows -->
                <div
                  v-for="p in sortedPrecincts"
                  :key="p.precinct_id"
                  class="precinct-row"
                  :class="{ 'precinct-row--top5': p.rank <= 5 }"
                  role="button"
                  tabindex="0"
                  :aria-label="`${p.name}, rank ${p.rank}`"
                  @click="selectPrecinct(p)"
                  @keydown.enter="selectPrecinct(p)"
                  @keydown.space.prevent="selectPrecinct(p)"
                >
                  <!-- Precinct name + rank -->
                  <div class="pt-col-name">
                    <div class="p-rank" :class="{ 'p-rank--top5': p.rank <= 5 }">{{ p.rank }}</div>
                    <div class="p-dot" :style="{ background: tierColor(p.tier) }"></div>
                    <div class="p-name">{{ p.name }}</div>
                  </div>
                  <!-- kWh -->
                  <div class="pt-col-kwh" :class="{ 'p-val-active': sortBy === 'kwh' }">
                    {{ formatKwhCompact(p.total_kwh) }}
                  </div>
                  <!-- Area -->
                  <div class="pt-col-area" :class="{ 'p-val-active': sortBy === 'area' }">
                    {{ formatAreaCompact(p.total_area) }}
                  </div>
                  <!-- Buildings -->
                  <div class="pt-col-bldg" :class="{ 'p-val-active': sortBy === 'buildings' }">
                    {{ p.building_count.toLocaleString() }}
                  </div>
                  <!-- Gap bar -->
                  <div class="pt-col-stat" :class="{ 'p-val-active': sortBy === 'gap' }">
                    <div class="mini-bar-track">
                      <div class="mini-bar mini-bar--gap" :style="{ width: gapPct(p) + '%' }"></div>
                    </div>
                    <span class="mini-pct">{{ gapPct(p) }}%</span>
                  </div>
                </div>
              </template>
            </div>
          </div>
        </div>
      </aside>
    </main>

    <div class="toast" role="status" aria-live="polite" aria-atomic="true" :class="{ show: toastVisible }">{{ toastMessage }}</div>
  </div>
</template>

<script>
export default { name: 'PrecinctsView' }
</script>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import maplibregl from 'maplibre-gl'
import MainNavbar from '../components/MainNavbar.vue'

const BUILDINGS_PATH  = import.meta.env.VITE_GEOJSON_URL   || '/combined-buildings.geojson'
const PRECINCTS_PATH  = import.meta.env.VITE_PRECINCTS_URL || '/melbourne_cbd_precincts.geojson'
const API_BASE        = import.meta.env.VITE_API_BASE_URL  || '/api/v1'

async function fetchGeoJson(url) {
  const isJson = (res) => (res.headers.get('content-type') || '').includes('json')
  const acceptsGeoJsonFile = (url, res) => url.endsWith('.geojson') && res.ok

  const res = await fetch(url)
  if (!res.ok) throw new Error(`Server returned ${res.status} for ${url}`)
  if (!isJson(res) && !acceptsGeoJsonFile(url, res)) {
    throw new Error(`Unexpected content type for ${url}: ${res.headers.get('content-type') || 'unknown'}`)
  }
  return res
}

// Module-level session caches — survive component unmount/remount within the same tab.
// Avoids re-fetching large GeoJSON files and re-running the expensive PIP aggregation.
let _cachedPrecinctGeoJSON = null
let _cachedBuildingData    = null
let _cachedAggregation     = null
let _cachedApiData         = null   // { precinct_id → PrecinctSummary } from /api/v1/precincts

// MapLibre hex colours (mirrors CSS variables — GL paint doesn't accept CSS vars)
const MAP_COLORS = {
  solarExcellent: '#09332C',
  solarGood:      '#5A9072',
  solarModerate:  '#BED4C7',
  solarPoor:      '#F8AB90',
  solarVeryPoor:  '#FA1029',
  buildingBase:   '#2A2A26',
  top5Outline:    '#D4743A',
  selectedOutline:'#FFD966',
  defaultOutline: '#3E3E3A',
  lineStroke:     '#1C1710',
}

const TIER_COLORS = [
  MAP_COLORS.solarExcellent,
  MAP_COLORS.solarGood,
  MAP_COLORS.solarModerate,
  MAP_COLORS.solarPoor,
  MAP_COLORS.solarVeryPoor,
]
const TIER_LABELS = ['Excellent', 'Good', 'Moderate', 'Poor', 'Very Poor']

// Returns 0-based tier index (0 = best) based on rank quintile
function quintileTier(rank, total) {
  if (total <= 0) return 2
  return Math.min(4, Math.floor((rank - 1) / total * 5))
}
function tierColor(tier) { return TIER_COLORS[tier] ?? MAP_COLORS.solarModerate }
function tierLabel(tier) { return TIER_LABELS[tier] ?? 'Moderate' }

const isLoading     = ref(true)
const loadingText   = ref('Loading building data…')
const sidebarOpen   = ref(true)
const sortBy        = ref('kwh')
const precincts     = ref([])   // enriched precinct objects
const selectedPrecinct = ref(null)
const toastMessage  = ref('')
const toastVisible  = ref(false)
let toastTimer      = null
let map             = null

const sortOptions = [
  { id: 'kwh',       label: 'Annual kWh'   },
  { id: 'area',      label: 'Roof Area'    },
  { id: 'buildings', label: 'Buildings'    },
  { id: 'gap',       label: 'Adoption Gap' },
]

// ── Sorted / ranked list ──────────────────────────────────────────────────────
const sortedPrecincts = computed(() => {
  const isGap = sortBy.value === 'gap'
  const key = sortBy.value === 'kwh' ? 'total_kwh'
            : sortBy.value === 'area' ? 'total_area'
            : sortBy.value === 'buildings' ? 'building_count'
            : 'adoption_gap_kw'
  const sorted = [...precincts.value]
    .filter(p => p.building_count > 0)
    .sort((a, b) => {
      const aVal = isGap ? (a.adoption_gap_kw ?? a.adoption_gap ?? 0) : (a[key] ?? 0)
      const bVal = isGap ? (b.adoption_gap_kw ?? b.adoption_gap ?? 0) : (b[key] ?? 0)
      return bVal - aVal
    })
  const total = sorted.length
  const maxVal = sorted[0]?.[key] ?? 1
  return sorted.map((p, i) => {
    const rank = i + 1
    const tier = quintileTier(rank, total)
    return {
      ...p,
      rank,
      tier,
      norm_score: maxVal > 0 ? (p[key] ?? 0) / maxVal : 0,
    }
  })
})

// Update map layer paint + top-5 outline whenever sort changes
watch(sortedPrecincts, () => updateMapLayers(), { deep: false })

// ── Formatting helpers ────────────────────────────────────────────────────────
function formatKwh(val) {
  if (val == null || val === 0) return '—'
  if (val >= 1_000_000) return (val / 1_000_000).toFixed(2) + ' GWh'
  if (val >= 1_000)     return Math.round(val / 1_000).toLocaleString() + ' MWh'
  return Math.round(val).toLocaleString() + ' kWh'
}
function formatArea(val) {
  if (val == null || val === 0) return '—'
  if (val >= 1_000_000) return (val / 1_000_000).toFixed(2) + ' km²'
  return Math.round(val).toLocaleString() + ' m²'
}
function formatRowMetric(p) {
  if (sortBy.value === 'kwh')  return formatKwh(p.total_kwh)
  if (sortBy.value === 'area') return formatArea(p.total_area)
  return formatKwh(p.adoption_gap)
}
function formatKwhCompact(val) {
  if (!val) return '—'
  if (val >= 1_000_000_000) return (val / 1_000_000_000).toFixed(1) + ' TWh'
  if (val >= 1_000_000)     return (val / 1_000_000).toFixed(1) + ' GWh'
  if (val >= 1_000)         return (val / 1_000).toFixed(1) + ' MWh'
  return Math.round(val) + ' kWh'
}
function formatAreaCompact(val) {
  if (!val) return '—'
  if (val >= 1_000_000) return (val / 1_000_000).toFixed(1) + 'M m²'
  if (val >= 1_000)     return Math.round(val / 1_000) + 'K m²'
  return Math.round(val) + ' m²'
}
function formatKw(val) {
  if (val == null || val === 0) return '—'
  if (val >= 1_000_000) return (val / 1_000_000).toFixed(2) + ' GW'
  if (val >= 1_000)     return (val / 1_000).toFixed(1) + ' MW'
  return Math.round(val).toLocaleString() + ' kW'
}
function adoptionPct(p) {
  if (!p.max_kwh) return 0
  return Math.round((p.total_kwh / p.max_kwh) * 100)
}
function gapPct(p) {
  if (p.potential_capacity_kw > 0) return Math.round(((p.adoption_gap_kw ?? 0) / p.potential_capacity_kw) * 100)
  if (!p.max_kwh) return 0
  return Math.round((p.adoption_gap / p.max_kwh) * 100)
}
const currentSortLabel = computed(() => sortOptions.find(s => s.id === sortBy.value)?.label ?? '')

// ── Toast ─────────────────────────────────────────────────────────────────────
function showToast(msg) {
  if (toastTimer) clearTimeout(toastTimer)
  toastMessage.value = msg
  toastVisible.value = true
  toastTimer = setTimeout(() => { toastVisible.value = false }, 1800)
}

// ── Select a precinct (sidebar + map highlight) ───────────────────────────────
function selectPrecinct(p) {
  selectedPrecinct.value = p
  if (!map) return
  map.setFilter('precinct-selected', ['==', ['get', 'precinct_id'], p.precinct_id])
  const feature = map.querySourceFeatures('melbourne-precincts').find(
    f => f.properties.precinct_id === p.precinct_id
  )
  if (feature?.geometry) {
    const coords = feature.geometry.coordinates[0]
    const lngs = coords.map(c => c[0])
    const lats = coords.map(c => c[1])
    map.fitBounds(
      [[Math.min(...lngs), Math.min(...lats)], [Math.max(...lngs), Math.max(...lats)]],
      { padding: 80, maxZoom: 15, duration: 900 }
    )
  }
}

// ── Point-in-polygon (ray casting) ───────────────────────────────────────────
function pointInPolygon(px, py, ring) {
  let inside = false
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const xi = ring[i][0], yi = ring[i][1]
    const xj = ring[j][0], yj = ring[j][1]
    if (((yi > py) !== (yj > py)) && (px < ((xj - xi) * (py - yi)) / (yj - yi) + xi)) {
      inside = !inside
    }
  }
  return inside
}

function pointInFeature(px, py, feature) {
  const geom = feature.geometry
  if (!geom) return false
  const rings = geom.type === 'Polygon' ? [geom.coordinates[0]] : geom.coordinates.map(p => p[0])
  return rings.some(ring => pointInPolygon(px, py, ring))
}

// ── Build bounding boxes for fast pre-filter ─────────────────────────────────
function getBBox(feature) {
  const geom = feature.geometry
  if (!geom) return null
  const rings = geom.type === 'Polygon' ? [geom.coordinates[0]] : geom.coordinates.map(p => p[0])
  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity
  for (const ring of rings) {
    for (const [x, y] of ring) {
      if (x < minX) minX = x; if (x > maxX) maxX = x
      if (y < minY) minY = y; if (y > maxY) maxY = y
    }
  }
  return { minX, maxX, minY, maxY }
}

// ── Aggregate buildings into precincts (chunked to keep UI responsive) ────────
async function aggregateBuildings(buildingFeatures, precinctFeatures) {
  const bboxes = precinctFeatures.map(getBBox)
  const accum  = precinctFeatures.map(() => ({
    total_kwh: 0, total_area: 0, max_kwh: 0, building_count: 0,
  }))

  const CHUNK = 2000
  for (let start = 0; start < buildingFeatures.length; start += CHUNK) {
    await new Promise(r => setTimeout(r, 0))   // yield to browser
    const end = Math.min(start + CHUNK, buildingFeatures.length)
    loadingText.value = `Aggregating buildings… ${Math.round((start / buildingFeatures.length) * 100)}%`

    for (let bi = start; bi < end; bi++) {
      const feat = buildingFeatures[bi]
      const p = feat.properties
      const px = Number(p.lng ?? p.longitude ?? feat.geometry?.coordinates?.[0])
      const py = Number(p.lat ?? p.latitude  ?? feat.geometry?.coordinates?.[1])
      if (!px || !py) continue

      const kwh  = Number(p.kwh_annual || 0)
      const area = Number(p.usable_roof_area || 0)

      for (let pi = 0; pi < precinctFeatures.length; pi++) {
        const bb = bboxes[pi]
        if (!bb || px < bb.minX || px > bb.maxX || py < bb.minY || py > bb.maxY) continue
        if (!pointInFeature(px, py, precinctFeatures[pi])) continue
        accum[pi].total_kwh      += kwh
        accum[pi].total_area     += area
        accum[pi].max_kwh        += area * 0.20 * 0.75 * 4.1 * 365  // theoretical max using yield formula: η × PR × PSH × days
        accum[pi].building_count += 1
        break  // a building belongs to one precinct only
      }
    }
  }

  return precinctFeatures.map((feat, i) => ({
    precinct_id:    feat.properties.precinct_id,
    name:           feat.properties.name || feat.properties.precinct_id,
    total_kwh:      Math.round(accum[i].total_kwh),
    total_area:     Math.round(accum[i].total_area),
    max_kwh:        Math.round(accum[i].max_kwh),
    adoption_gap:   Math.round(Math.max(0, accum[i].max_kwh - accum[i].total_kwh)),
    building_count: accum[i].building_count,
  }))
}

// ── Update map fill colour and top-5 outline after sort changes ───────────────
function updateMapLayers() {
  if (!map || sortedPrecincts.value.length === 0) return

  const withDataIds = sortedPrecincts.value.map(p => p.precinct_id)
  const hasDataFilter = ['in', ['get', 'precinct_id'], ['literal', withDataIds]]

  // Colour expression: match precinct_id → quintile tier fill colour
  const matchExpr = ['match', ['get', 'precinct_id']]
  sortedPrecincts.value.forEach(p => {
    matchExpr.push(p.precinct_id, tierColor(p.tier))
  })
  matchExpr.push(MAP_COLORS.solarModerate)  // fallback

  if (map.getLayer('precinct-fill')) {
    map.setFilter('precinct-fill', hasDataFilter)
    map.setPaintProperty('precinct-fill', 'fill-color', matchExpr)
    map.setPaintProperty('precinct-fill', 'fill-opacity', 0.55)
  }
  if (map.getLayer('precinct-outline')) {
    map.setFilter('precinct-outline', hasDataFilter)
  }

  // Top-5 outline: set filter on precinct-top5-outline layer
  const top5Ids = sortedPrecincts.value.filter(p => p.rank <= 5).map(p => p.precinct_id)
  if (map.getLayer('precinct-top5-outline')) {
    map.setFilter('precinct-top5-outline', ['in', ['get', 'precinct_id'], ['literal', top5Ids]])
  }
}

// ── Map init ──────────────────────────────────────────────────────────────────
function initMap(precinctGeoJSON) {
  map = new maplibregl.Map({
    container: 'precinct-map',
    style: 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',
    center: [144.9631, -37.814],
    zoom: 12.2,
    pitch: 20,
    bearing: -17,
    antialias: true,
  })

  map.addControl(new maplibregl.NavigationControl(), 'top-right')

  map.on('load', async () => {
    // ── Precinct layers ───────────────────────────────────────────────────────
    map.addSource('melbourne-precincts', { type: 'geojson', data: precinctGeoJSON })

    map.addLayer({
      id: 'precinct-fill',
      type: 'fill',
      source: 'melbourne-precincts',
      filter: ['==', ['get', 'precinct_id'], ''],
      paint: {
        'fill-color': MAP_COLORS.solarModerate,
        'fill-opacity': 0.55,
      },
    })

    map.addLayer({
      id: 'precinct-outline',
      type: 'line',
      source: 'melbourne-precincts',
      filter: ['==', ['get', 'precinct_id'], ''],
      paint: {
        'line-color': MAP_COLORS.defaultOutline,
        'line-width': 1,
        'line-opacity': 0.6,
      },
    })

    map.addLayer({
      id: 'precinct-top5-outline',
      type: 'line',
      source: 'melbourne-precincts',
      filter: ['in', ['get', 'precinct_id'], ['literal', []]],
      paint: {
        'line-color': MAP_COLORS.top5Outline,
        'line-width': 2.5,
        'line-opacity': 0.9,
      },
    })

    map.addLayer({
      id: 'precinct-selected',
      type: 'line',
      source: 'melbourne-precincts',
      filter: ['==', ['get', 'precinct_id'], ''],
      paint: {
        'line-color': MAP_COLORS.selectedOutline,
        'line-width': 3.5,
        'line-opacity': 1,
      },
    })

    // ── Load buildings (background) ───────────────────────────────────────────
    let buildingData
    if (_cachedBuildingData) {
      buildingData = _cachedBuildingData
    } else {
      loadingText.value = 'Loading buildings…'
      try {
        const res = await fetchGeoJson(BUILDINGS_PATH)
        buildingData = await res.json()
        _cachedBuildingData = buildingData
      } catch (err) {
        console.error('Failed to load buildings:', err)
        loadingText.value = 'Buildings unavailable — showing precinct outlines only'
        isLoading.value = false
        updateMapLayers()
        return
      }
    }

    // Add building extrusions (low opacity background context)
    map.addSource('melbourne-buildings', { type: 'geojson', data: buildingData })
    map.addLayer({
      id: 'building-extrusion',
      type: 'fill-extrusion',
      source: 'melbourne-buildings',
      paint: {
        'fill-extrusion-color': MAP_COLORS.buildingBase,
        'fill-extrusion-height': ['coalesce', ['get', 'building_height'], 4],
        'fill-extrusion-base': 0,
        'fill-extrusion-opacity': 0.30,
      },
    }, 'precinct-fill')   // insert below precinct layers

    // ── Aggregate ─────────────────────────────────────────────────────────────
    let enriched
    if (_cachedAggregation) {
      enriched = _cachedAggregation
    } else {
      loadingText.value = 'Aggregating solar data…'
      enriched = await aggregateBuildings(buildingData.features, precinctGeoJSON.features)
      _cachedAggregation = enriched
    }
    // ── Fetch DB capacity data and merge ─────────────────────────────────────
    if (!_cachedApiData) {
      try {
        const apiRes = await fetch(`${API_BASE}/precincts`)
        if (apiRes.ok) {
          const apiJson = await apiRes.json()
          const list = Array.isArray(apiJson) ? apiJson : (apiJson.precincts ?? [])
          const apiMap = {}
          list.forEach(ap => { apiMap[ap.precinct_id] = ap })
          _cachedApiData = apiMap
        }
      } catch { /* API unreachable — use local aggregation only */ }
    }
    if (_cachedApiData) {
      enriched = enriched.map(p => {
        const ap = _cachedApiData[p.precinct_id]
        if (!ap) return p
        return {
          ...p,
          name: ap.name || p.name,
          postcode: ap.postcode ?? p.postcode,
          total_kwh: Math.round(ap.total_kwh_annual ?? p.total_kwh),
          total_area: Math.round(ap.total_usable_area_m2 ?? p.total_area),
          installed_capacity_kw: ap.installed_capacity_kw,
          potential_capacity_kw: ap.potential_capacity_kw,
          adoption_gap_kw:       ap.adoption_gap_kw,
          building_count:        ap.building_count ?? p.building_count,
        }
      })
      _cachedAggregation = enriched
    }

    precincts.value = enriched
    isLoading.value = false
    updateMapLayers()
  })

  // Click handler on precinct fill
  map.on('click', 'precinct-fill', (e) => {
    if (!e.features?.length) return
    const pid = e.features[0].properties.precinct_id
    const p = sortedPrecincts.value.find(x => x.precinct_id === pid)
    if (p) selectPrecinct(p)
  })

  map.on('mouseenter', 'precinct-fill', () => { map.getCanvas().style.cursor = 'pointer' })
  map.on('mouseleave', 'precinct-fill', () => { map.getCanvas().style.cursor = '' })
}

// ── CSV Export ────────────────────────────────────────────────────────────────
function toCsvSafe(value) {
  const s = value == null ? '' : String(value)
  return `"${s.replace(/"/g, '""')}"`
}

function exportPrecinctsCsv() {
  let rows, filename

  if (selectedPrecinct.value) {
    const p = selectedPrecinct.value
    rows = [
      ['Field', 'Value'],
      ['Precinct Name', p.name],
      ['Rank', `#${p.rank}`],
      ['Tier', tierLabel(p.tier)],
      ['Annual Output', formatKwh(p.total_kwh)],
      ['Usable Roof Area', formatArea(p.total_area)],
      ['Installed Capacity', formatKw(p.installed_capacity_kw)],
      ['Potential Capacity', formatKw(p.potential_capacity_kw)],
      ['Adoption Gap', p.adoption_gap_kw != null ? formatKw(p.adoption_gap_kw) : formatKwh(p.adoption_gap)],
      ['Buildings', p.building_count.toLocaleString()],
    ]
    filename = `precinct_${p.name.replace(/[^a-z0-9]+/gi, '_').toLowerCase()}.csv`
  } else {
    rows = [['Rank', 'Precinct Name', 'Annual Output', 'Usable Roof Area', 'Installed Capacity', 'Potential Capacity', 'Adoption Gap', 'Tier', 'Buildings']]
    sortedPrecincts.value.forEach(p => {
      rows.push([
        p.rank,
        p.name,
        formatKwh(p.total_kwh),
        formatArea(p.total_area),
        formatKw(p.installed_capacity_kw),
        formatKw(p.potential_capacity_kw),
        p.adoption_gap_kw != null ? formatKw(p.adoption_gap_kw) : formatKwh(p.adoption_gap),
        tierLabel(p.tier),
        p.building_count.toLocaleString(),
      ])
    })
    filename = 'precinct_solar_rankings.csv'
  }

  const csvText = rows.map(row => row.map(toCsvSafe).join(',')).join('\n')
  const blob = new Blob([csvText], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', filename)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
  showToast('CSV exported')
}

// ── Lifecycle ─────────────────────────────────────────────────────────────────
onMounted(async () => {
  // If we already have aggregated data from a previous visit, show the sidebar
  // immediately and suppress the loading overlay — MapLibre initialises in the background.
  if (_cachedAggregation) {
    precincts.value = _cachedAggregation
    isLoading.value = false
  }

  let precinctGeoJSON
  if (_cachedPrecinctGeoJSON) {
    precinctGeoJSON = _cachedPrecinctGeoJSON
  } else {
    loadingText.value = 'Loading precinct boundaries…'
    try {
      const res = await fetchGeoJson(PRECINCTS_PATH)
      precinctGeoJSON = await res.json()
      _cachedPrecinctGeoJSON = precinctGeoJSON
    } catch (err) {
      loadingText.value = `Failed to load precincts: ${err.message}`
      return
    }
  }

  setTimeout(() => { if (!map) initMap(precinctGeoJSON) }, 50)
})

onUnmounted(() => {
  if (toastTimer) clearTimeout(toastTimer)
  if (map) { map.remove(); map = null }
})
</script>

<style scoped>
/* ── Layout ───────────────────────────────────────────────── */
.map-page { display: flex; flex-direction: column; height: 100vh; overflow: hidden; }
.main { display: flex; flex: 1; overflow: hidden; }
#precinct-map { flex: 1; position: relative; overflow: hidden; }

/* Loading overlay — inherits from global style.css .loading / .loading-spinner / .loading-text */
@keyframes spin { to { transform: rotate(360deg); } }

/* ── Sidebar width ────────────────────────────────────────── */
.sidebar { width: 640px; }
.sidebar--collapsed { width: 28px; }

/* Override global sticky sidebar-header — precincts header is not inside sidebar-content */
.sidebar-header {
  position: static;
  padding: 18px 20px 12px;
  margin-bottom: 0;
  flex-shrink: 0;
}

/* ── Header: rankings label + title ──────────────────────── */
.rankings-label {
  font-size: 11px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.9px; color: var(--city-light); margin-bottom: 5px;
}

/* ── Sort tabs (full-width underline tab style) ───────────── */
.sort-tabs {
  display: flex; border-bottom: 2px solid var(--border);
  background: var(--surface);
}
.sort-tab {
  flex: 1; padding: 13px 8px; text-align: center;
  font-size: 13px; font-weight: 500; color: var(--text-muted);
  background: none; border: none; border-bottom: 2px solid transparent;
  margin-bottom: -2px; cursor: pointer; transition: color 0.15s, border-color 0.15s;
  font-family: 'DM Sans', sans-serif; white-space: nowrap;
}
.sort-tab:hover:not(.active) { color: var(--city-light); }
.sort-tab.active {
  color: var(--city-light); font-weight: 700;
  border-bottom-color: var(--city-light);
}

/* ── Sidebar content: rows span full width ────────────────── */
.sidebar-content { padding: 0; }
.precinct-detail-panel { margin-top: 22px; }

/* ── Column header row ────────────────────────────────────── */
.precinct-table-head {
  display: flex; align-items: center;
  padding: 8px 20px; border-bottom: 1px solid var(--border);
  background: var(--surface2); position: sticky; top: 0; z-index: 1;
}
.precinct-table-head > div {
  font-size: 10px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.7px; color: var(--text-muted); transition: color 0.15s;
  justify-content: flex-end;
}
.precinct-table-head .col-active { color: var(--city-light); }
.precinct-table-head .pt-col-name { justify-content: flex-start; }

/* ── Column widths ────────────────────────────────────────── */
.pt-col-name { flex: 1; min-width: 0; display: flex; align-items: center; gap: 10px; justify-content: flex-start; text-align: left; }
.pt-col-kwh  { width: 94px; flex-shrink: 0; text-align: right; padding-right: 14px; }
.pt-col-area { width: 86px; flex-shrink: 0; text-align: right; padding-right: 14px; }
.pt-col-bldg { width: 80px; flex-shrink: 0; text-align: right; padding-right: 14px; }
.pt-col-stat { width: 110px; flex-shrink: 0; display: flex; align-items: center; justify-content: flex-end; gap: 6px; }

/* ── Rows ─────────────────────────────────────────────────── */
.precinct-row {
  display: flex; align-items: center;
  padding: 13px 20px; cursor: pointer;
  border-bottom: 1px solid var(--border); transition: background 0.15s;
}
.precinct-row:hover { background: var(--surface2); }
.precinct-row--top5 { background: rgba(212, 116, 58, 0.05); }
.precinct-row--top5:hover { background: rgba(212, 116, 58, 0.10); }

/* Rank badge */
.p-rank {
  width: 28px; height: 28px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  border-radius: 8px; font-size: 12px; font-weight: 700;
  color: var(--text-muted); background: var(--surface2); border: 1px solid var(--border);
}
.p-rank--top5 { background: var(--ink); color: #fff; border-color: var(--ink); }

/* Tier color dot */
.p-dot { width: 13px; height: 13px; border-radius: 4px; flex-shrink: 0; }

/* Precinct name */
.p-name {
  font-size: 14px; font-weight: 600; color: var(--text-primary);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}

/* Data values — default muted, active sort column stands out */
.pt-col-kwh, .pt-col-area, .pt-col-bldg {
  font-size: 13px; color: var(--text-secondary); white-space: nowrap;
}
.pt-col-stat { font-size: 13px; color: var(--text-secondary); }
.p-val-active {
  font-size: 14px !important; font-weight: 700 !important;
  color: var(--text-primary) !important;
}

/* Mini bar */
.mini-bar-track {
  flex: 1; height: 6px; background: var(--border);
  border-radius: 3px; overflow: hidden;
}
.mini-bar { height: 100%; border-radius: 3px; transition: width 0.4s ease; }
.mini-bar--gap { background: #C0392B; }
.mini-pct { font-size: 12px; font-weight: 600; color: var(--text-muted); white-space: nowrap; }

/* ── Precinct detail panel ────────────────────────────────── */
.precinct-detail-panel { padding: 0 20px 16px; }

/* ── Toast ────────────────────────────────────────────────── */
.toast {
  position: fixed; bottom: 24px; left: 50%;
  transform: translateX(-50%) translateY(12px);
  background: var(--ink); color: var(--nav-text);
  border: 1px solid var(--ink-border); border-radius: 8px;
  padding: 9px 18px; font-size: 13px;
  opacity: 0; pointer-events: none;
  transition: opacity 0.2s ease, transform 0.2s ease; z-index: 9999;
}
.toast.show { opacity: 1; transform: translateX(-50%) translateY(0); }
</style>
