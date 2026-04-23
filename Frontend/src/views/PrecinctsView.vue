<template>
  <div class="map-page">
    <MainNavbar />
    <main id="main-content" class="main">
      <div id="precinct-map" role="application" aria-label="Interactive precinct solar map of Melbourne CBD">
        <div v-if="isLoading" class="loading" role="status" aria-live="polite" aria-atomic="true" :aria-label="loadingText">
          <div class="loading-spinner" aria-hidden="true"></div>
          <div class="loading-text">{{ loadingText }}</div>
        </div>

        <!-- Sort controls overlay -->
        <div class="map-controls" role="group" aria-label="Precinct sort controls">
          <div class="control-card">
            <div class="control-title" style="margin-bottom: 8px;">Sort Precincts By</div>
            <div class="filter-group" role="group" aria-label="Sort options">
              <button
                v-for="s in sortOptions"
                :key="s.id"
                class="filter-btn"
                :class="{ active: sortBy === s.id }"
                :aria-pressed="sortBy === s.id"
                @click="sortBy = s.id"
              >{{ s.label }}</button>
            </div>
          </div>
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
          <div class="sidebar-header">
            <div class="sidebar-title">Precinct Rankings</div>
            <div class="sidebar-sub">{{ isLoading ? loadingText : `${sortedPrecincts.length} precincts with data · Melbourne CBD` }}</div>
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

              <div class="metrics-grid">
                <div class="metric-card">
                  <div class="metric-val">{{ formatKwh(selectedPrecinct.total_kwh) }}</div>
                  <div class="metric-label">Annual kWh</div>
                </div>
                <div class="metric-card">
                  <div class="metric-val">{{ formatArea(selectedPrecinct.total_area) }}</div>
                  <div class="metric-label">Usable Roof Area</div>
                </div>
                <div class="metric-card">
                  <div class="metric-val">{{ formatKwh(selectedPrecinct.adoption_gap) }}</div>
                  <div class="metric-label">Adoption Gap (kWh)</div>
                </div>
                <div class="metric-card">
                  <div class="metric-val">{{ selectedPrecinct.building_count.toLocaleString() }}</div>
                  <div class="metric-label">Buildings</div>
                </div>
              </div>

              <button class="share-btn" @click="selectedPrecinct = null" style="margin-top: 4px;">← Back to Rankings</button>
            </div>

            <!-- Ranked list -->
            <div v-else>
              <div v-if="sortedPrecincts.length === 0 && !isLoading" class="empty-state">
                <div class="empty-icon">Precinct</div>
                <div class="empty-text">No precinct data available</div>
              </div>

              <div
                v-for="p in sortedPrecincts"
                :key="p.precinct_id"
                class="precinct-row"
                :class="{ 'precinct-row--top5': p.rank <= 5, 'precinct-row--selected': selectedPrecinct?.precinct_id === p.precinct_id }"
                role="button"
                tabindex="0"
                :aria-label="`${p.name}, rank ${p.rank}`"
                @click="selectPrecinct(p)"
                @keydown.enter="selectPrecinct(p)"
                @keydown.space.prevent="selectPrecinct(p)"
              >
                <div class="precinct-rank" :class="{ 'precinct-rank--top5': p.rank <= 5 }">
                  <span v-if="p.rank <= 5">★</span>
                  <span v-else>#{{ p.rank }}</span>
                </div>
                <div class="precinct-row-info">
                  <div class="precinct-row-name">{{ p.name }}</div>
                  <div class="precinct-row-metric">{{ formatRowMetric(p) }}</div>
                </div>
                <div class="precinct-row-bar-wrap">
                  <div
                    class="precinct-row-bar"
                    :style="{ width: Math.max(4, (p.norm_score * 100)) + '%', background: tierColor(p.tier) }"
                  ></div>
                </div>
              </div>
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

const BUILDINGS_PATH  = import.meta.env.VITE_GEOJSON_URL || '/combined-buildings.geojson'
const PRECINCTS_PATH  = import.meta.env.VITE_PRECINCTS_URL || '/melbourne_cbd_precincts.geojson'

// Module-level session caches — survive component unmount/remount within the same tab.
// Avoids re-fetching large GeoJSON files and re-running the expensive PIP aggregation.
let _cachedPrecinctGeoJSON = null
let _cachedBuildingData    = null
let _cachedAggregation     = null

// MapLibre hex colours (mirrors CSS variables — GL paint doesn't accept CSS vars)
const MAP_COLORS = {
  solarExcellent: '#09332C',
  solarGood:      '#5A9072',
  solarModerate:  '#BED4C7',
  solarPoor:      '#F8AB90',
  solarVeryPoor:  '#F0531C',
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
  { id: 'kwh',  label: 'Annual kWh' },
  { id: 'area', label: 'Roof Area'  },
  { id: 'gap',  label: 'Adoption Gap' },
]

// ── Sorted / ranked list ──────────────────────────────────────────────────────
const sortedPrecincts = computed(() => {
  const key = sortBy.value === 'kwh' ? 'total_kwh' : sortBy.value === 'area' ? 'total_area' : 'adoption_gap'
  const sorted = [...precincts.value]
    .filter(p => p.building_count > 0)
    .sort((a, b) => (b[key] ?? 0) - (a[key] ?? 0))
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
        accum[pi].max_kwh        += area * 0.18 * 4.1 * 365  // theoretical max: 180 W/m² × PSH
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
        const res = await fetch(BUILDINGS_PATH)
        if (!res.ok) throw new Error(res.statusText)
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
      const res = await fetch(PRECINCTS_PATH)
      if (!res.ok) throw new Error(res.statusText)
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
/* Reuse map-page / main / sidebar layout identical to ExploreView */
.map-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
}
.main {
  display: flex;
  flex: 1;
  overflow: hidden;
}
#precinct-map {
  flex: 1;
  position: relative;
  overflow: hidden;
}

/* Loading overlay */
.loading {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(26, 26, 24, 0.72);
  z-index: 20;
  gap: 16px;
}
.loading-spinner {
  width: 36px;
  height: 36px;
  border: 3px solid rgba(255, 255, 255, 0.15);
  border-top-color: var(--city-light);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
.loading-text { color: var(--nav-text); font-size: 14px; }
@keyframes spin { to { transform: rotate(360deg); } }

/* Controls overlay (top-left) */
.map-controls {
  position: absolute;
  top: 12px;
  left: 12px;
  z-index: 10;
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: calc(100% - 24px);
  overflow-y: auto;
}
.control-card {
  background: var(--ink);
  border: 1px solid var(--ink-border);
  border-radius: 10px;
  padding: 12px 14px;
  min-width: 200px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.35);
}
.control-title {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.7px;
  color: var(--nav-text-muted);
}
.filter-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.filter-btn {
  background: none;
  border: 1px solid transparent;
  border-radius: 7px;
  padding: 6px 10px;
  font-size: 13px;
  font-weight: 500;
  color: var(--nav-link);
  cursor: pointer;
  font-family: 'DM Sans', sans-serif;
  text-align: left;
  transition: background 0.15s, color 0.15s, border-color 0.15s;
}
.filter-btn:hover { background: var(--ink2); color: var(--nav-text); }
.filter-btn.active {
  background: var(--ink-active);
  border-color: var(--ink-active-border);
  color: var(--nav-active-color);
  font-weight: 600;
}

/* Sidebar */
.sidebar {
  width: 320px;
  flex-shrink: 0;
  background: var(--surface);
  border-left: 1px solid var(--border);
  display: flex;
  overflow: hidden;
  transition: width 0.25s ease;
  position: relative;
}
.sidebar--collapsed { width: 32px; }
.sidebar-strip-btn {
  position: absolute;
  top: 50%;
  left: 0;
  transform: translateY(-50%);
  width: 32px;
  height: 48px;
  background: var(--surface2);
  border: none;
  border-right: 1px solid var(--border);
  cursor: pointer;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2;
  flex-shrink: 0;
}
.sidebar-strip-btn:hover { background: var(--border); color: var(--text-primary); }
.sidebar-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  margin-left: 32px;
}
.sidebar--collapsed .sidebar-body { visibility: hidden; }
.sidebar-header {
  padding: 16px 16px 12px;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}
.sidebar-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 2px;
}
.sidebar-sub { font-size: 12px; color: var(--text-muted); }
.sidebar-content {
  flex: 1;
  overflow-y: auto;
  padding: 12px 0;
}

/* Precinct ranked rows */
.precinct-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 16px;
  cursor: pointer;
  border-bottom: 1px solid var(--border);
  transition: background 0.15s;
}
.precinct-row:hover { background: var(--surface2); }
.precinct-row--top5 { background: rgba(212, 116, 58, 0.06); }
.precinct-row--top5:hover { background: rgba(212, 116, 58, 0.12); }
.precinct-row--selected { background: rgba(255, 217, 102, 0.12); }
.precinct-rank {
  width: 28px;
  flex-shrink: 0;
  font-size: 11px;
  font-weight: 700;
  color: var(--text-muted);
  text-align: center;
}
.precinct-rank--top5 { color: var(--city-light); font-size: 14px; }
.precinct-row-info { flex: 1; min-width: 0; }
.precinct-row-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.precinct-row-metric { font-size: 11px; color: var(--text-muted); margin-top: 1px; }
.precinct-row-bar-wrap {
  width: 48px;
  height: 4px;
  background: var(--surface2);
  border-radius: 2px;
  overflow: hidden;
  flex-shrink: 0;
}
.precinct-row-bar { height: 100%; border-radius: 2px; transition: width 0.4s ease; }

/* Detail panel (reuses ExploreView metric styles via global css) */
.precinct-detail-panel { padding: 0 16px 16px; }
.panel-id {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 1px;
  color: var(--text-muted);
  text-transform: uppercase;
  margin-bottom: 12px;
  padding-top: 12px;
}
.score-bar-wrap { margin-bottom: 16px; }
.score-header { display: flex; justify-content: space-between; margin-bottom: 6px; }
.score-label { font-size: 12px; color: var(--text-secondary); }
.score-value { font-size: 13px; font-weight: 700; color: var(--text-primary); }
.score-bar {
  height: 6px;
  background: var(--surface2);
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 4px;
}
.score-fill { height: 100%; border-radius: 3px; transition: width 0.5s ease; }
.score-tier { font-size: 11px; font-weight: 600; }
.metrics-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-bottom: 12px;
}
.metric-card {
  background: var(--surface2);
  border-radius: 8px;
  padding: 10px 12px;
  border: 1px solid var(--border);
}
.metric-val { font-size: 14px; font-weight: 700; color: var(--text-primary); line-height: 1.2; }
.metric-label { font-size: 10px; color: var(--text-muted); margin-top: 3px; text-transform: uppercase; letter-spacing: 0.4px; }

/* Empty state */
.empty-state {
  padding: 48px 24px;
  text-align: center;
}
.empty-icon { font-size: 32px; margin-bottom: 12px; opacity: 0.3; }
.empty-text { font-size: 13px; color: var(--text-muted); line-height: 1.5; }

/* Share / back button */
.share-btn {
  width: 100%;
  padding: 9px 14px;
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  cursor: pointer;
  font-family: 'DM Sans', sans-serif;
  transition: background 0.15s, color 0.15s;
}
.share-btn:hover { background: var(--border); color: var(--text-primary); }

/* Toast */
.toast {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%) translateY(12px);
  background: var(--ink);
  color: var(--nav-text);
  border: 1px solid var(--ink-border);
  border-radius: 8px;
  padding: 9px 18px;
  font-size: 13px;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.2s ease, transform 0.2s ease;
  z-index: 9999;
}
.toast.show { opacity: 1; transform: translateX(-50%) translateY(0); }
</style>
