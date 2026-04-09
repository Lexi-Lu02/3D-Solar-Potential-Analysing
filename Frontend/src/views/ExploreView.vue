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
            <div class="control-title">Filter by Solar Potential</div>
            <div class="filter-group">
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
            <div class="control-title">Filter by Roof Type</div>
            <div class="filter-group">
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
      </div>

      <aside class="sidebar">
        <div class="sidebar-header">
          <div class="sidebar-title">Building Details</div>
          <div class="sidebar-sub">
            {{ selectedBuilding ? `Structure ${selectedBuilding.structure_id || '—'}` : 'Click any building on the map' }}
          </div>
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
                <div class="metric-val">{{ selectedBuilding.has_solar_data ? Math.round(selectedBuilding.kwh_annual || 0).toLocaleString() : '—' }} {{ selectedBuilding.has_solar_data ? 'kWh' : '' }}</div>
                <div class="metric-label">Est. Annual kWh</div>
              </div>
              <div class="metric-card">
                <div class="metric-val">{{ selectedBuilding.has_solar_data ? (selectedBuilding.usable_roof_area || 0).toFixed(1) + ' m²' : 'No data' }}</div>
                <div class="metric-label">Usable Roof Area</div>
              </div>
              <div class="metric-card">
                <div class="metric-val">{{ (selectedBuilding.footprint_area || 0).toFixed(1) }} m²</div>
                <div class="metric-label">Roof Footprint</div>
              </div>
              <div class="metric-card">
                <div class="metric-val">{{ (selectedBuilding.building_height || 0).toFixed(1) }} m</div>
                <div class="metric-label">Building Height</div>
              </div>
            </div>
            <div class="section-title">Building Info</div>
            <div class="info-row"><span class="info-key">Roof Type</span><span class="info-val">{{ selectedBuilding.roof_type || 'Unknown' }}</span></div>
            <div class="info-row"><span class="info-key">Solar Rating</span><span class="info-val">{{ selectedBuilding.dominant_rating || 'No data' }}</span></div>
            <div class="info-row"><span class="info-key">Usable Ratio</span><span class="info-val">{{ selectedBuilding.has_solar_data ? Math.round(selectedBuilding.usable_ratio * 100) + '%' : '—' }}</span></div>
            <div class="info-row"><span class="info-key">Structure ID</span><span class="info-val">{{ selectedBuilding.structure_id || '—' }}</span></div>
            <div class="info-row"><span class="info-key">Data Source</span><span class="info-val" style="font-size:11px;">City of Melbourne 2023</span></div>
            <div class="assumptions">
              <strong>Calculation assumptions</strong>
              Usable Area x 20% efficiency x 0.75 PR x 4.1 PSH x 365 days<br />
              Melbourne CBD avg: 4.1 peak sun hours/day (BOM validated)
            </div>
            <div class="compare-section">
              <div class="compare-header">
                <span class="compare-title">Comparison</span>
                <button class="compare-clear" @click="clearCompare">Clear</button>
              </div>
              <div style="font-size:12px;color:var(--text-muted);text-align:center;padding:8px 0;">Select a second building to compare</div>
            </div>
            <button class="share-btn" @click="shareBuilding">Copy Shareable Link</button>
          </div>
        </div>
      </aside>
    </div>

    <div class="toast" :class="{ show: toastVisible }">{{ toastMessage }}</div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import maplibregl from 'maplibre-gl'
import MainNavbar from '../components/MainNavbar.vue'

const GEOJSON_PATH = '/combined-buildings.geojson'

const isLoading = ref(true)
const loadingText = ref('Loading Melbourne building data...')
const selectedBuilding = ref(null)
const activeFilter = ref('all')
const activeSolarFilter = ref('all')
const toastMessage = ref('')
const toastVisible = ref(false)

let map = null
let toastTimer = null
let compassIdx = 0

const COMPASS_BEARINGS = [0, 45, 90, 135, 180, 225, 270, 315]
const filters = [
  { type: 'all', label: 'All Types', svgDash: 'none', mapDash: null },
  { type: 'Flat', label: 'Flat Roofs', svgDash: 'none', mapDash: null },
  { type: 'Hip', label: 'Hip Roofs', svgDash: '8,4', mapDash: [6, 3] },
  { type: 'Gable', label: 'Gable Roofs', svgDash: '4,4', mapDash: [3, 3] },
  { type: 'Pyramid', label: 'Pyramid Roofs', svgDash: '1.5,4', mapDash: [1, 3] },
  { type: 'Shed', label: 'Shed Roofs', svgDash: '10,4,2,4', mapDash: [7, 3, 1, 3] },
]
const ROOF_TYPES = ['Flat', 'Hip', 'Gable', 'Pyramid', 'Shed']

const solarTiers = [
  { id: 'very-high', label: 'Very High', range: '80-100', color: '#9A3412', min: 80, max: null },
  { id: 'high', label: 'High', range: '60-79', color: '#EA580C', min: 60, max: 80 },
  { id: 'medium', label: 'Medium', range: '40-59', color: '#F97316', min: 40, max: 60 },
  { id: 'low', label: 'Low', range: '20-39', color: '#FB923C', min: 20, max: 40 },
  { id: 'very-low', label: 'Very Low', range: '0-19', color: '#FED7AA', min: 0, max: 20 },
]

const score = computed(() => {
  if (!selectedBuilding.value) return 0
  return Number(selectedBuilding.value.solar_score || 0)
})

const tier = computed(() => {
  const s = score.value
  if (s >= 80) return 'Very High'
  if (s >= 60) return 'High'
  if (s >= 40) return 'Medium'
  if (s >= 20) return 'Low'
  return 'Very Low'
})

const tierColor = computed(() => {
  const s = score.value
  if (s >= 80) return 'var(--solar-very-high)'
  if (s >= 60) return 'var(--solar-high)'
  if (s >= 40) return 'var(--solar-med)'
  if (s >= 20) return 'var(--solar-low)'
  return 'var(--solar-very-low)'
})

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
  activeFilter.value = type
  applyFilters()
}

function filterSolar(tierId) {
  activeSolarFilter.value = activeSolarFilter.value === tierId ? 'all' : tierId
  applyFilters()
}

function clearCompare() {}

function shareBuilding() {
  if (!selectedBuilding.value) {
    showToast('Select a building first')
    return
  }
  const id = selectedBuilding.value.structure_id || '-'
  navigator.clipboard.writeText(`SolarMap Building ${id}`).then(() => showToast('Copied to clipboard'))
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
      .then((data) => {
        isLoading.value = false
        map.addSource('melbourne-buildings', { type: 'geojson', data })

        map.addLayer({
          id: 'building-extrusion',
          type: 'fill-extrusion',
          source: 'melbourne-buildings',
          paint: {
            'fill-extrusion-color': ['step', ['get', 'solar_score'], '#FED7AA', 20, '#FB923C', 40, '#F97316', 60, '#EA580C', 80, '#9A3412'],
            'fill-extrusion-height': ['coalesce', ['get', 'building_height'], 4],
            'fill-extrusion-base': 0,
            'fill-extrusion-opacity': 0.85,
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

        map.on('click', 'building-extrusion', (event) => {
          if (!event.features?.length) return
          selectedBuilding.value = event.features[0].properties
        })

        map.on('mouseenter', 'building-extrusion', () => {
          map.getCanvas().style.cursor = 'pointer'
        })
        map.on('mouseleave', 'building-extrusion', () => {
          map.getCanvas().style.cursor = ''
        })
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
