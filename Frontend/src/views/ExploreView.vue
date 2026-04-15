<template>
  <div class="map-page">
    <MainNavbar />
    <div class="main">
      <div id="map">
        <div v-if="isLoading" class="loading">
          <div class="loading-spinner"></div>
          <div class="loading-text">{{ loadingText }}</div>
        </div>
        <div class="map-controls">
          <div class="control-card">
            <button class="control-card-toggle" @click="solarFilterOpen = !solarFilterOpen">
              <span class="control-title">Filter by Solar Potential</span>
              <svg class="chevron-icon" :class="{ 'chevron-up': solarFilterOpen }" width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M3 5l4 4 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </button>
            <div v-show="solarFilterOpen" class="filter-group">
              <button
                v-for="t in solarTiers"
                :key="t.id"
                class="filter-btn"
                :class="{ active: activeSolarFilter === t.id }"
                @click="filterSolar(t.id)"
              >
                <div class="legend-dot" :style="{ background: t.color }"></div>
                {{ t.label }}<span class="tier-range">&nbsp;({{ t.range }})</span>
              </button>
            </div>
          </div>
          <div class="control-card">
            <button class="control-card-toggle" @click="roofFilterOpen = !roofFilterOpen">
              <span class="control-title">Filter by Roof Type</span>
              <svg class="chevron-icon" :class="{ 'chevron-up': roofFilterOpen }" width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M3 5l4 4 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </button>
            <div v-show="roofFilterOpen" class="filter-group">
              <button
                v-for="f in filters"
                :key="f.type"
                class="filter-btn"
                :class="{ active: activeFilter === f.type }"
                @click="filterRoof(f.type)"
              >
                <svg width="28" height="12" class="filter-dash-icon" aria-hidden="true">
                  <line
                    x1="2"
                    y1="6"
                    x2="26"
                    y2="6"
                    stroke="#374151"
                    stroke-width="2.5"
                    :stroke-dasharray="f.svgDash || 'none'"
                    stroke-linecap="round"
                  />
                </svg>
                {{ f.label }}
              </button>
            </div>
          </div>
        </div>

        <!-- Comparison panel — slides up from bottom of map area -->
        <Transition name="compare-slide">
          <div v-if="compareVisible" class="comparison-panel">
            <div class="comparison-header">
              <span class="comparison-title">
                Compare Buildings
                <span class="comparison-count">{{ compareBuildings.length }}/2</span>
              </span>
              <button class="comparison-close-btn" @click="clearCompare" title="Close">✕</button>
            </div>
            <div class="comparison-body">
              <div
                v-for="(item, col) in compareBuildings"
                :key="item.building.structure_id"
                class="comparison-col"
              >
                <div class="comparison-col-header">
                  <span class="comparison-building-id">Structure {{ item.building.structure_id }}</span>
                  <button class="comparison-remove-btn" @click="removeFromCompare(col)" title="Remove">✕</button>
                </div>
                <!-- Score bar -->
                <div class="comparison-score-row">
                  <div class="comparison-score-val" :style="{ color: scoreColor(item.building.solar_score) }">
                    {{ item.building.solar_score }}
                  </div>
                  <div class="comparison-score-bar-wrap">
                    <div class="comparison-score-bar">
                      <div class="comparison-score-fill" :style="{ width: Math.min(100, item.building.solar_score || 0) + '%', background: scoreColor(item.building.solar_score) }"></div>
                    </div>
                    <div class="comparison-tier-label" :style="{ color: scoreColor(item.building.solar_score) }">{{ scoreTier(item.building.solar_score) }}</div>
                  </div>
                </div>
                <!-- Metric rows -->
                <div
                  v-for="(metric, mi) in compareMetrics(item)"
                  :key="metric.label"
                  class="comparison-metric-row"
                  :class="{ 'comparison-winner': compareWinners[mi]?.[col] }"
                >
                  <span class="comparison-metric-label">{{ metric.label }}</span>
                  <span class="comparison-metric-val">
                    {{ metric.display }}
                    <span v-if="compareWinners[mi]?.[col]" class="comparison-winner-badge">▲</span>
                  </span>
                </div>
              </div>
              <!-- Empty slot when only 1 building added -->
              <div v-if="compareBuildings.length < 2" class="comparison-empty-col">
                <div class="comparison-empty-hint">
                  Click a building,<br>then "Add to Compare"
                </div>
              </div>
            </div>
          </div>
        </Transition>
      </div>

      <aside class="sidebar" :class="{ 'sidebar--collapsed': !sidebarOpen }">
        <button
          class="sidebar-strip-btn"
          @click="sidebarOpen = !sidebarOpen"
          :title="sidebarOpen ? 'Collapse panel' : 'Expand panel'"
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path
              :d="sidebarOpen ? 'M10 4l-4 4 4 4' : 'M6 4l4 4-4 4'"
              stroke="currentColor"
              stroke-width="1.5"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
        </button>
        <div class="sidebar-body">
          <div class="sidebar-header">
            <div class="sidebar-title">Building Details</div>
            <div class="sidebar-sub">
              {{ selectedBuilding ? `Structure ${selectedBuilding.structure_id || '—'}` : 'Click any building on the map' }}
            </div>
            <div class="search-row">
              <input
                v-model="searchId"
                type="text"
                class="search-input"
                placeholder="Search by Structure ID…"
                @keyup.enter="searchBuilding"
              />
              <button class="search-btn" @click="searchBuilding">→</button>
            </div>
            <div v-if="searchError" class="search-error">{{ searchError }}</div>
          </div>
          <div class="sidebar-content">
            <div v-if="!selectedBuilding" class="empty-state">
              <div class="empty-icon">Building</div>
              <div class="empty-text">Select a building on the map to view its solar potential analysis</div>
            </div>
            <div v-else class="building-panel visible">
              <div class="panel-id">BUILDING {{ selectedBuilding.structure_id || selectedBuilding.objectid || '—' }}</div>
              <div class="score-bar-wrap">
                <div class="score-header">
                  <span class="score-label">Solar Score</span>
                  <span class="score-value">{{ score }}</span>
                </div>
                <div class="score-bar">
                  <div class="score-fill" :style="{ width: Math.min(100, Math.max(0, score)) + '%', background: tierColor }"></div>
                </div>
                <div class="score-tier" :style="{ color: tierColor }">{{ tier }}</div>
              </div>
              <div class="metrics-grid">
                <div class="metric-card">
                  <div class="metric-val">
                    {{ solarApiData?.kwhAnnual != null
                        ? solarApiData.kwhAnnual.toLocaleString()
                        : (selectedBuilding.has_solar_data ? Math.round(selectedBuilding.kwh_annual || 0).toLocaleString() : '—') }}
                    {{ (solarApiData?.kwhAnnual != null || selectedBuilding.has_solar_data) ? ' kWh' : '' }}
                  </div>
                  <div class="metric-label">Est. Annual kWh</div>
                </div>
                <div class="metric-card">
                  <div class="metric-val">
                    {{ solarApiData?.usableAreaM2 != null
                        ? solarApiData.usableAreaM2.toFixed(1) + ' m²'
                        : (selectedBuilding.has_solar_data ? (selectedBuilding.usable_roof_area || 0).toFixed(1) + ' m²' : 'No data') }}
                  </div>
                  <div class="metric-label">Usable Roof Area</div>
                </div>
                <div class="metric-card">
                  <div class="metric-val">
                    {{ solarApiData?.roofAreaM2 != null
                        ? solarApiData.roofAreaM2.toFixed(1) + ' m²'
                        : (selectedBuilding.footprint_area || 0).toFixed(1) + ' m²' }}
                  </div>
                  <div class="metric-label">Roof Footprint</div>
                </div>
                <div class="metric-card">
                  <div class="metric-val">{{ (selectedBuilding.building_height || 0).toFixed(1) }} m</div>
                  <div class="metric-label">Building Height</div>
                </div>
              </div>
              <div class="section-title">Building Info</div>
              <div class="info-row"><span class="info-key">Structure ID</span><span class="info-val">{{ selectedBuilding.structure_id || '—' }}</span></div>
              <div class="info-row"><span class="info-key">Roof Type</span><span class="info-val">{{ selectedBuilding.roof_type || 'Unknown' }}</span></div>
              <div class="info-row">
                <span class="info-key">Usable Ratio</span>
                <span class="info-val">
                  {{ solarApiData?.usableAreaM2 != null
                      ? Math.round(solarApiData.usableAreaM2 / (solarApiData.roofAreaM2 ?? selectedBuilding.footprint_area) * 100) + '%'
                      : selectedBuilding.has_solar_data ? Math.round(selectedBuilding.usable_ratio * 100) + '%' : '—' }}
                </span>
              </div>
              <div class="info-row"><span class="info-key">Max Solar Panels</span><span class="info-val">{{ solarApiData?.maxPanels != null ? solarApiData.maxPanels.toLocaleString() : '—' }}</span></div>
              <div class="section-title">Monthly Output</div>
              <div v-if="monthlyOutput.length === 0" class="monthly-no-data">No solar data available for this building</div>
              <div v-else class="monthly-chart">
                <div class="monthly-bars">
                  <div
                    v-for="(m, i) in monthlyOutput"
                    :key="m.month"
                    class="monthly-bar-col"
                    :class="{ 'monthly-bar-col--hovered': hoveredMonthIdx === i }"
                    @mouseenter="hoveredMonthIdx = i"
                    @mouseleave="hoveredMonthIdx = null"
                  >
                    <div class="monthly-tooltip" v-if="hoveredMonthIdx === i">
                      {{ m.kwh.toLocaleString() }} kWh
                    </div>
                    <div class="monthly-bar-wrap">
                      <div class="monthly-bar" :style="{ height: m.pct + '%' }"></div>
                    </div>
                    <div class="monthly-bar-label">{{ m.month }}</div>
                  </div>
                </div>
              </div>
              <div class="compare-section">
                <div class="compare-header">
                  <span class="compare-title">Comparison</span>
                  <button v-if="compareBuildings.length > 0" class="compare-clear" @click="clearCompare">Clear all</button>
                </div>
                <div v-if="compareBuildings.length === 0" style="font-size:12px;color:var(--text-muted);padding:4px 0 8px;">
                  Add up to 2 buildings to compare side by side
                </div>
                <div v-else class="compare-slots-mini">
                  <div v-for="(item, i) in compareBuildings" :key="item.building.structure_id" class="compare-slot-mini">
                    <span class="compare-slot-mini-id">#{{ item.building.structure_id }}</span>
                    <span class="compare-slot-mini-score" :style="{ color: scoreColor(item.building.solar_score) }">{{ item.building.solar_score }}</span>
                    <button class="compare-slot-remove" @click="removeFromCompare(i)">✕</button>
                  </div>
                </div>
                <button
                  class="compare-add-btn"
                  @click="addToCompare"
                  :disabled="!selectedBuilding || compareBuildings.some(c => c.building.structure_id === selectedBuilding.structure_id)"
                >
                  {{ compareBuildings.some(c => c.building.structure_id === selectedBuilding?.structure_id) ? '✓ Already in comparison' : '+ Add to Compare' }}
                </button>
              </div>
              <button class="share-btn" @click="shareBuilding">Copy Shareable Link</button>
            </div>
          </div>
        </div>
      </aside>
    </div>

    <div class="toast" :class="{ show: toastVisible }">{{ toastMessage }}</div>
  </div>
</template>

<script>
export default { name: 'ExploreView' }
</script>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import maplibregl from 'maplibre-gl'
import MainNavbar from '../components/MainNavbar.vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const GEOJSON_PATH = '/combined-buildings.geojson'
const SELECTED_BUILDING_COLOR = '#7F93B2'
const SELECTED_BUILDING_OPACITY = 0.82

// Google Solar API — key loaded from .env (VITE_SOLAR_API_KEY).
// If blank the app works entirely on local data at no cost.
const SOLAR_API_KEY = import.meta.env.VITE_SOLAR_API_KEY || ''
const SOLAR_API_BASE = 'https://solar.googleapis.com/v1/buildingInsights:findClosest'

// Session cache: structure_id → result object | null (null = known failure, skip retry)
const solarApiCache = new Map()

const isLoading = ref(true)
const loadingText = ref('Loading Melbourne building data...')
const selectedBuilding = ref(null)
const activeFilter = ref('all')
const activeSolarFilter = ref('all')
const toastMessage = ref('')
const toastVisible = ref(false)
const solarApiData = ref(null)   // { maxPanels, usableAreaM2, kwhAnnual } | null
const solarApiLoading = ref(false)
const searchId = ref('')
const searchError = ref('')
const sidebarOpen = ref(true)
const solarFilterOpen = ref(true)
const roofFilterOpen = ref(true)
const compareBuildings = ref([]) // [{ building, apiData }] — max 2

const compareVisible = computed(() => compareBuildings.value.length > 0)
const hoveredMonthIdx = ref(null)

// NASA POWER monthly PSH scaled to BOM annual baseline of 4.1 PSH/day
const MONTHLY_PSH = [
  { month: 'Jan', days: 31, psh: 6.56 },
  { month: 'Feb', days: 28, psh: 5.71 },
  { month: 'Mar', days: 31, psh: 4.59 },
  { month: 'Apr', days: 30, psh: 3.18 },
  { month: 'May', days: 31, psh: 2.16 },
  { month: 'Jun', days: 30, psh: 1.69 },
  { month: 'Jul', days: 31, psh: 1.86 },
  { month: 'Aug', days: 31, psh: 2.61 },
  { month: 'Sep', days: 30, psh: 3.72 },
  { month: 'Oct', days: 31, psh: 4.92 },
  { month: 'Nov', days: 30, psh: 5.78 },
  { month: 'Dec', days: 31, psh: 6.49 },
]

const monthlyOutput = computed(() => {
  if (!selectedBuilding.value) return []

  // Prefer API annual total (consistent with the kWh card above);
  // fall back to the pre-computed kwh_annual already in the GeoJSON.
  const annualKwh = solarApiData.value?.kwhAnnual
    ?? Number(selectedBuilding.value.kwh_annual) ?? 0

  if (annualKwh <= 0) return []

  // Distribute annual total proportionally using NASA POWER monthly PSH weights
  const weights = MONTHLY_PSH.map(({ month, days, psh }) => ({ month, w: psh * days }))
  const totalWeight = weights.reduce((s, m) => s + m.w, 0)
  const months = weights.map(({ month, w }) => ({
    month,
    kwh: Math.round((w / totalWeight) * annualKwh),
  }))
  const maxKwh = Math.max(...months.map(m => m.kwh))
  return months.map(m => ({ ...m, pct: Math.round(m.kwh / maxKwh * 100) }))
})

let map = null
let toastTimer = null
let compassIdx = 0
let buildingIndex = new Map() // structure_id (number) → feature properties

const COMPASS_BEARINGS = [0, 45, 90, 135, 180, 225, 270, 315]
const filters = [
  { type: 'Flat', label: 'Flat Roofs', svgDash: 'none', mapDash: null },
  { type: 'Hip', label: 'Hip Roofs', svgDash: '8,4', mapDash: [6, 3] },
  { type: 'Gable', label: 'Gable Roofs', svgDash: '4,4', mapDash: [3, 3] },
  { type: 'Pyramid', label: 'Pyramid Roofs', svgDash: '1.5,4', mapDash: [1, 3] },
  { type: 'Shed', label: 'Shed Roofs', svgDash: '10,4,2,4', mapDash: [7, 3, 1, 3] },
]
const ROOF_TYPES = ['Flat', 'Hip', 'Gable', 'Pyramid', 'Shed']

const solarTiers = [
  { id: 'very-high', label: 'Excellent',  range: '80-100', color: '#5B1F0A', min: 80, max: null },
  { id: 'high',      label: 'Good',       range: '60-79',  color: '#9A3412', min: 60, max: 80 },
  { id: 'medium',    label: 'Moderate',   range: '40-59',  color: '#F97316', min: 40, max: 60 },
  { id: 'low',       label: 'Poor',       range: '20-39',  color: '#F59E0B', min: 20, max: 40 },
  { id: 'very-low',  label: 'Very Poor',  range: '0-19',   color: '#FEF3C7', min: 0,  max: 20 },
]

const score = computed(() => {
  if (!selectedBuilding.value) return 0
  return Number(selectedBuilding.value.solar_score || 0)
})

const tier = computed(() => {
  const s = score.value
  if (s >= 80) return 'Excellent'
  if (s >= 60) return 'Good'
  if (s >= 40) return 'Moderate'
  if (s >= 20) return 'Poor'
  return 'Very Poor'
})

const tierColor = computed(() => {
  const s = score.value
  if (s >= 80) return 'var(--solar-very-high)'
  if (s >= 60) return 'var(--solar-high)'
  if (s >= 40) return 'var(--solar-med)'
  if (s >= 20) return 'var(--solar-low)'
  return 'var(--solar-very-low)'
})

// Fetch live solar data for one building from Google Solar API.
// Returns { maxPanels, usableAreaM2, kwhAnnual } on success, null on any failure.
// Results are cached for the session so the same building is never billed twice.
async function fetchSolarApiData(structureId, lat, lng) {
  if (!SOLAR_API_KEY) return null                          // no key → free fallback
  if (solarApiCache.has(structureId)) return solarApiCache.get(structureId)

  try {
    const url = `${SOLAR_API_BASE}?location.latitude=${lat}&location.longitude=${lng}&requiredQuality=LOW&key=${SOLAR_API_KEY}`
    const res = await fetch(url)

    if (!res.ok) {
      // 404 = building not in Google's coverage; 429 = quota hit — both are silent fallbacks
      solarApiCache.set(structureId, null)
      return null
    }

    const body = await res.json()
    const solar = body.solarPotential
    if (!solar) { solarApiCache.set(structureId, null); return null }

    // solarPanelConfigs is sorted ascending by panel count; last entry = maximum config
    const maxConfig = solar.solarPanelConfigs?.at(-1)

    const result = {
      maxPanels:    solar.maxArrayPanelsCount  ?? null,
      usableAreaM2: solar.maxArrayAreaMeters2  != null ? Math.round(solar.maxArrayAreaMeters2 * 10) / 10 : null,
      roofAreaM2:   solar.wholeRoofStats?.areaMeters2 != null ? Math.round(solar.wholeRoofStats.areaMeters2 * 10) / 10 : null,
      kwhAnnual:    maxConfig?.yearlyEnergyDcKwh != null ? Math.round(maxConfig.yearlyEnergyDcKwh) : null,
    }
    solarApiCache.set(structureId, result)
    return result
  } catch {
    // Network error, CORS, parse failure — never crash the UI
    solarApiCache.set(structureId, null)
    return null
  }
}

function showToast(message) {
  if (toastTimer) clearTimeout(toastTimer)
  toastMessage.value = message
  toastVisible.value = true
  toastTimer = setTimeout(() => {
    toastVisible.value = false
  }, 1800)
}

function buildCombinedFilter(roofType, solarTierId) {
  const conditions = []
  if (roofType !== 'all') {
    conditions.push(['==', ['get', 'roof_type'], roofType])
  }
  if (solarTierId !== 'all') {
    const selectedTier = solarTiers.find((item) => item.id === solarTierId)
    if (selectedTier) {
      conditions.push(['>=', ['get', 'solar_score'], selectedTier.min])
      if (selectedTier.max !== null) {
        conditions.push(['<', ['get', 'solar_score'], selectedTier.max])
      }
    }
  }
  if (conditions.length === 0) return null
  if (conditions.length === 1) return conditions[0]
  return ['all', ...conditions]
}

function applyFilters() {
  if (!map) return
  map.setFilter('building-extrusion', buildCombinedFilter(activeFilter.value, activeSolarFilter.value))
  ROOF_TYPES.forEach((roofType) => {
    const visible = activeFilter.value === 'all' || activeFilter.value === roofType
    map.setLayoutProperty(`roof-outline-${roofType}`, 'visibility', visible ? 'visible' : 'none')
    if (visible) map.setFilter(`roof-outline-${roofType}`, buildCombinedFilter(roofType, activeSolarFilter.value))
  })
}

function filterRoof(type) {
  activeFilter.value = activeFilter.value === type ? 'all' : type
  applyFilters()
}

function filterSolar(tierId) {
  activeSolarFilter.value = activeSolarFilter.value === tierId ? 'all' : tierId
  applyFilters()
}

async function searchBuilding() {
  const id = parseInt(searchId.value.trim(), 10)
  if (isNaN(id)) { searchError.value = 'Please enter a valid Structure ID'; return }

  const props = buildingIndex.get(id)
  if (!props) { searchError.value = `Structure ${id} not found`; return }

  searchError.value = ''
  selectedBuilding.value = props
  solarApiData.value = null
  solarApiLoading.value = true

  if (map) {
    map.setFilter('building-selected', ['==', ['get', 'structure_id'], id])
    const lng = Number(props.lng)
    const lat = Number(props.lat)
    if (lat && lng) {
      map.flyTo({
        center: [lng, lat],
        zoom: Math.max(map.getZoom(), 15.5),
        pitch: 55,
        duration: 1200,
        easing: (t) => (t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t),
      })
    }
    solarApiData.value = await fetchSolarApiData(id, Number(props.lat), Number(props.lng))
  }
  solarApiLoading.value = false
}

function scoreColor(score) {
  const s = Number(score) || 0
  if (s >= 80) return 'var(--solar-very-high)'
  if (s >= 60) return 'var(--solar-high)'
  if (s >= 40) return 'var(--solar-med)'
  if (s >= 20) return 'var(--solar-low)'
  return 'var(--solar-very-low)'
}

function scoreTier(score) {
  const s = Number(score) || 0
  if (s >= 80) return 'Excellent'
  if (s >= 60) return 'Good'
  if (s >= 40) return 'Moderate'
  if (s >= 20) return 'Poor'
  return 'Very Poor'
}

// Returns the 4 comparable metrics for a compare entry
function compareMetrics(item) {
  const b = item.building
  const api = item.apiData
  const kwh = api?.kwhAnnual ?? (b.has_solar_data ? Math.round(Number(b.kwh_annual) || 0) : null)
  const area = api?.usableAreaM2 ?? (b.has_solar_data ? Number(b.usable_roof_area) : null)
  return [
    { label: 'Annual kWh',  display: kwh  != null ? Number(kwh).toLocaleString()         + ' kWh' : '—', raw: kwh  ?? 0 },
    { label: 'Usable Area', display: area != null ? Number(area).toFixed(1)               + ' m²'  : '—', raw: area ?? 0 },
    { label: 'Roof Type',   display: b.roof_type || '—',                                              raw: null },
    { label: 'Height',      display: b.building_height ? Number(b.building_height).toFixed(1) + ' m' : '—', raw: Number(b.building_height) || 0 },
  ]
}

// For each metric index: [isWinner_col0, isWinner_col1]
const compareWinners = computed(() => {
  if (compareBuildings.value.length < 2) return []
  const m0 = compareMetrics(compareBuildings.value[0])
  const m1 = compareMetrics(compareBuildings.value[1])
  return m0.map((_, i) => {
    if (m0[i].raw === null || m1[i].raw === null) return [false, false]
    if (m0[i].raw > m1[i].raw) return [true, false]
    if (m1[i].raw > m0[i].raw) return [false, true]
    return [false, false]
  })
})

function addToCompare() {
  if (!selectedBuilding.value) return
  const sid = selectedBuilding.value.structure_id
  if (compareBuildings.value.some(c => c.building.structure_id === sid)) {
    showToast('Already in comparison')
    return
  }
  const entry = {
    building: { ...selectedBuilding.value },
    apiData:  solarApiData.value ? { ...solarApiData.value } : null,
  }
  if (compareBuildings.value.length >= 2) compareBuildings.value.shift() // replace oldest
  compareBuildings.value.push(entry)
  showToast('Added to comparison')
}

function removeFromCompare(idx) {
  compareBuildings.value.splice(idx, 1)
}

function clearCompare() {
  compareBuildings.value = []
}
// Generates a shareable URL for the currently selected building and copies it to clipboard
function shareBuilding() {
  if (!selectedBuilding.value) {
    showToast('Select a building first')
    return
  }

  const id = selectedBuilding.value.structure_id
  const url = `${window.location.origin}/explore?buildingId=${id}`

  navigator.clipboard.writeText(url).then(() => {
    showToast('Shareable link copied!')
  })
}
// On page load, check if URL has ?buildingId= and if so open that building's details
async function openBuildingFromUrl() {
  const buildingId = route.query.buildingId
  if (!buildingId) return

  const id = Number(buildingId)
  const props = buildingIndex.get(id)

  if (!props) return

  selectedBuilding.value = props
  solarApiData.value = null
  solarApiLoading.value = true

  // highlight
  if (map) {
    map.setFilter('building-selected', ['==', ['get', 'structure_id'], id])

    const lng = Number(props.lng)
    const lat = Number(props.lat)

    if (lat && lng) {
      map.flyTo({
        center: [lng, lat],
        zoom: 16,
        pitch: 55,
        duration: 1200,
      })
    }

    solarApiData.value = await fetchSolarApiData(id, lat, lng)
  }

  solarApiLoading.value = false
}

function initMap() {
  map = new maplibregl.Map({
    container: 'map',
    style: {
      version: 8,
      sources: {
        osm: {
          type: 'raster',
          tiles: [
            'https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png',
            'https://b.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png',
            'https://c.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png',
            'https://d.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png',
          ],
          tileSize: 256,
          attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors © <a href="https://carto.com/attributions">CARTO</a>',
        },
      },
      layers: [{ id: 'osm', type: 'raster', source: 'osm' }],
    },
    center: [144.9631, -37.814],
    zoom: 12.2,
    pitch: 48,
    bearing: -17,
    antialias: true,
  })

  map.addControl(new maplibregl.NavigationControl(), 'top-right')

  setTimeout(() => {
    const compassBtn = document.querySelector('.maplibregl-ctrl-compass')
    if (!compassBtn || !map) return
    compassBtn.addEventListener(
      'click',
      (event) => {
        event.stopImmediatePropagation()
        compassIdx = (compassIdx + 1) % COMPASS_BEARINGS.length
        map.easeTo({
          bearing: COMPASS_BEARINGS[compassIdx],
          duration: 900,
          easing: (t) => (t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t),
        })
      },
      true
    )
  }, 0)

  map.on('load', () => {
    fetch(GEOJSON_PATH)
      .then((response) => {
        if (!response.ok) throw new Error(`Failed to load GeoJSON: ${response.statusText}`)
        return response.json()
      })
      .then(async (data) => {
        isLoading.value = false
        // Build lookup index for the search box
        data.features.forEach(f => buildingIndex.set(Number(f.properties.structure_id), f.properties))
        map.addSource('melbourne-buildings', { type: 'geojson', data })

        map.addLayer({
          id: 'building-extrusion',
          type: 'fill-extrusion',
          source: 'melbourne-buildings',
          paint: {
            'fill-extrusion-color': ['step', ['get', 'solar_score'], '#FEF3C7', 20, '#F59E0B', 40, '#F97316', 60, '#9A3412', 80, '#5B1F0A'],
            'fill-extrusion-height': ['coalesce', ['get', 'building_height'], 4],
            'fill-extrusion-base': 0,
            'fill-extrusion-opacity': 0.85,
          },
        })

        // Selected building highlight
        map.addLayer({
          id: 'building-selected',
          type: 'fill-extrusion',
          source: 'melbourne-buildings',
          filter: ['==', ['get', 'structure_id'], -1],
          paint: {
            'fill-extrusion-color': SELECTED_BUILDING_COLOR,
            'fill-extrusion-height': ['coalesce', ['get', 'building_height'], 4],
            'fill-extrusion-base': 0,
            'fill-extrusion-opacity': SELECTED_BUILDING_OPACITY,
          },
        })

        filters.slice(1).forEach((roofFilter) => {
          const paint = {
            'line-color': '#1C1917',
            'line-width': 1.2,
            'line-opacity': 0.55,
          }
          if (roofFilter.mapDash) paint['line-dasharray'] = roofFilter.mapDash
          map.addLayer({
            id: `roof-outline-${roofFilter.type}`,
            type: 'line',
            source: 'melbourne-buildings',
            filter: ['==', ['get', 'roof_type'], roofFilter.type],
            paint,
          })
        })

        map.on('click', 'building-extrusion', async (event) => {
          if (!event.features?.length) return
          const props = event.features[0].properties
          selectedBuilding.value = props
          solarApiData.value = null
          solarApiLoading.value = true

          // Highlight the clicked building
          map.setFilter('building-selected', ['==', ['get', 'structure_id'], Number(props.structure_id)])

          // Fly to building centre
          const lng = Number(props.lng)
          const lat = Number(props.lat)
          if (lat && lng) {
            map.flyTo({
              center: [lng, lat],
              zoom: Math.max(map.getZoom(), 15.5),
              pitch: 55,
              duration: 1200,
              easing: (t) => (t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t),
            })
          }

          // Fetch live data — falls back silently if API key missing or call fails
          solarApiData.value = await fetchSolarApiData(Number(props.structure_id), lat, lng)
          solarApiLoading.value = false
        })

        map.on('mouseenter', 'building-extrusion', () => {
          map.getCanvas().style.cursor = 'pointer'
        })
        map.on('mouseleave', 'building-extrusion', () => {
          map.getCanvas().style.cursor = ''
        })
        // Add flat roof outlines as a separate layer on top of all others, so they remain visible when any roof filter is active
        await openBuildingFromUrl()
      })
      .catch((err) => {
        console.error(err)
        loadingText.value = `Error loading buildings: ${err.message}`
      })
  })
}

onMounted(() => {
  setTimeout(() => {
    if (!map) initMap()
  }, 50)
})

onUnmounted(() => {
  if (toastTimer) clearTimeout(toastTimer)
  if (map) {
    map.remove()
    map = null
  }
})
</script>
