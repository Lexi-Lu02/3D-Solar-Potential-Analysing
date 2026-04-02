<template>
  <nav class="topnav">
    <div class="logo">
      <div class="logo-icon">☀️</div>
      <div>
        <div class="logo-text">SolarMap Melbourne</div>
        <div class="logo-sub">3D City Solar Potential</div>
      </div>
    </div>
    <div class="nav-divider"></div>
    <div class="nav-stats">
      <div class="nav-stat">
        <span class="nav-stat-val">{{ buildingCount.toLocaleString() }}</span>
        <span class="nav-stat-label">Buildings</span>
      </div>
      <div class="nav-stat"><span class="nav-stat-val">169K m²</span><span class="nav-stat-label">Usable Rooftop</span></div>
      <div class="nav-stat"><span class="nav-stat-val">37.9 GWh</span><span class="nav-stat-label">Est. Annual Yield</span></div>
      <div class="nav-stat"><span class="nav-stat-val">237</span><span class="nav-stat-label">High Potential</span></div>
    </div>
    <div class="nav-spacer"></div>
    <div class="nav-badge">Iteration 1 · MVP</div>
  </nav>

  <div class="main">
    <div id="map">
      <div v-if="isLoading" class="loading">
        <div class="loading-spinner"></div>
        <div class="loading-text">{{ loadingText }}</div>
      </div>
      <div class="map-controls">
        <div class="control-card">
          <div class="control-title">Solar Potential</div>
          <div class="legend-items">
            <div class="legend-item"><div class="legend-dot" style="background:#16A34A"></div>High (score ≥ 60)</div>
            <div class="legend-item"><div class="legend-dot" style="background:#EAB308"></div>Medium (30–59)</div>
            <div class="legend-item"><div class="legend-dot" style="background:#DC2626"></div>Low (&lt; 30)</div>
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
              <span class="filter-dot" :style="{ background: f.color }"></span>
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
          <div class="empty-icon">🏢</div>
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
              <div class="metric-val">{{ Math.round(selectedBuilding.kwh_annual || 0).toLocaleString() }} kWh</div>
              <div class="metric-label">Est. Annual kWh</div>
            </div>
            <div class="metric-card">
              <div class="metric-val">{{ (selectedBuilding.usable_area || 0).toFixed(1) }} m²</div>
              <div class="metric-label">Usable Area (m²)</div>
            </div>
            <div class="metric-card">
              <div class="metric-val">{{ (selectedBuilding.computed_area || 0).toFixed(1) }} m²</div>
              <div class="metric-label">Total Footprint (m²)</div>
            </div>
            <div class="metric-card">
              <div class="metric-val">{{ (selectedBuilding.structure_max_elevation || selectedBuilding.structure_extrusion || 0).toFixed(1) }} m</div>
              <div class="metric-label">Building Height (m)</div>
            </div>
          </div>
          <div class="section-title">Building Info</div>
          <div class="info-row"><span class="info-key">Roof Type</span><span class="info-val">{{ selectedBuilding.roof_type || 'Unknown' }}</span></div>
          <div class="info-row"><span class="info-key">Shading Analysis</span><span class="info-val" style="color:#92400E;font-size:12px;">Pending shadow analysis (E4)</span></div>
          <div class="info-row"><span class="info-key">Structure ID</span><span class="info-val">{{ selectedBuilding.structure_id || '—' }}</span></div>
          <div class="info-row"><span class="info-key">Data Source</span><span class="info-val" style="font-size:11px;">City of Melbourne 2023</span></div>
          <div class="assumptions">
            <strong>⚡ Calculation Assumptions</strong>
            Usable Area × 20% efficiency × 0.75 PR × 4.1 PSH × 365 days<br>
            Melbourne CBD avg: 4.1 peak sun hours/day (BOM validated)
          </div>
          <div class="compare-section">
            <div class="compare-header">
              <span class="compare-title">Comparison</span>
              <button class="compare-clear" @click="clearCompare">Clear</button>
            </div>
            <div style="font-size:12px;color:var(--text-muted);text-align:center;padding:8px 0;">Select a second building to compare</div>
          </div>
          <button class="share-btn" @click="shareBuilding">🔗 Copy Shareable Link</button>
        </div>
      </div>
    </aside>
  </div>

  <div class="toast" :class="{ show: toastVisible }">{{ toastMessage }}</div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import maplibregl from 'maplibre-gl'

const GEOJSON_PATH = '/Backend/2023-building-footprints.geojson'

const isLoading = ref(true)
const loadingText = ref('Loading Melbourne building data…')
const buildingCount = ref(500)
const selectedBuilding = ref(null)
const activeFilter = ref('all')
const toastMessage = ref('')
const toastVisible = ref(false)
let map = null
let toastTimer = null

const filters = [
  { type: 'all',     label: 'All Types',     color: '#8A9BB0' },
  { type: 'Flat',    label: 'Flat Roofs',    color: '#4A86C8' },
  { type: 'Hip',     label: 'Hip Roofs',     color: '#4EA876' },
  { type: 'Gable',   label: 'Gable Roofs',   color: '#D97B4A' },
  { type: 'Pyramid', label: 'Pyramid Roofs', color: '#8B68C4' },
  { type: 'Shed',    label: 'Shed Roofs',    color: '#C9A93E' },
]

const score = computed(() => {
  if (!selectedBuilding.value) return 0
  const p = selectedBuilding.value
  return Number(p.solar_score ?? Math.round((p.structure_extrusion || p.footprint_extrusion || 1) * 6))
})

const tier = computed(() => score.value >= 60 ? 'High' : score.value >= 30 ? 'Medium' : 'Low')

const tierColor = computed(() => {
  if (score.value >= 60) return 'var(--solar-high)'
  if (score.value >= 30) return 'var(--solar-med)'
  return 'var(--solar-low)'
})

function showToast(message) {
  if (toastTimer) clearTimeout(toastTimer)
  toastMessage.value = message
  toastVisible.value = true
  toastTimer = setTimeout(() => { toastVisible.value = false }, 1800)
}

function filterRoof(type) {
  activeFilter.value = type
  if (!map) return
  if (type === 'all') {
    map.setFilter('building-extrusion', null)
  } else {
    map.setFilter('building-extrusion', ['==', ['get', 'roof_type'], type])
  }
}

function clearCompare() {
  // placeholder for future compare feature
}

function shareBuilding() {
  if (!selectedBuilding.value) {
    showToast('Select a building first')
    return
  }
  const id = selectedBuilding.value.structure_id || '—'
  navigator.clipboard.writeText(`SolarMap Building ${id}`).then(() => showToast('Copied to clipboard'))
}

onMounted(() => {
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
            'https://d.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png'
          ],
          tileSize: 256,
          attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors © <a href="https://carto.com/attributions">CARTO</a>'
        }
      },
      layers: [{ id: 'osm', type: 'raster', source: 'osm' }]
    },
    center: [144.9631, -37.814],
    zoom: 12.2,
    pitch: 48,
    bearing: -17,
    antialias: true
  })

  map.addControl(new maplibregl.NavigationControl(), 'top-right')

  map.on('load', () => {
    fetch(GEOJSON_PATH)
      .then(response => {
        if (!response.ok) throw new Error(`Failed to load GeoJSON: ${response.statusText}`)
        return response.json()
      })
      .then(data => {
        isLoading.value = false
        buildingCount.value = data.features?.length ?? 0

        map.addSource('melbourne-buildings', { type: 'geojson', data })

        map.addLayer({
          id: 'building-extrusion',
          type: 'fill-extrusion',
          source: 'melbourne-buildings',
          paint: {
            'fill-extrusion-color': [
              'match', ['get', 'roof_type'],
              'Flat',    '#4A86C8',
              'Hip',     '#4EA876',
              'Gable',   '#D97B4A',
              'Pyramid', '#8B68C4',
              'Shed',    '#C9A93E',
              '#8A9BB0'
            ],
            'fill-extrusion-height': ['coalesce', ['get', 'structure_extrusion'], ['get', 'footprint_extrusion'], 4],
            'fill-extrusion-base': ['coalesce', ['get', 'structure_min_elevation'], 0],
            'fill-extrusion-opacity': 0.8
          }
        })

        map.addLayer({
          id: 'building-outline',
          type: 'line',
          source: 'melbourne-buildings',
          paint: {
            'line-color': '#111827',
            'line-width': 0.8,
            'line-opacity': 0.5
          }
        })

        map.on('click', 'building-extrusion', e => {
          if (!e.features?.length) return
          selectedBuilding.value = e.features[0].properties
        })

        map.on('mouseenter', 'building-extrusion', () => { map.getCanvas().style.cursor = 'pointer' })
        map.on('mouseleave', 'building-extrusion', () => { map.getCanvas().style.cursor = '' })
      })
      .catch(err => {
        console.error(err)
        loadingText.value = `Error loading buildings: ${err.message}`
      })
  })
})
</script>
