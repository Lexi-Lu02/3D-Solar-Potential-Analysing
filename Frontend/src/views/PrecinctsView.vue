<template>
  <div class="map-page">
    <MainNavbar />
    <main id="main-content" class="main">
      <div id="precinct-map" role="application" aria-label="Interactive suburb solar map of Melbourne CBD">
        <div v-if="isLoading" class="loading" role="status" aria-live="polite" aria-atomic="true" :aria-label="loadingText">
          <div class="loading-spinner" aria-hidden="true"></div>
          <div class="loading-text">{{ loadingText }}</div>
        </div>

      </div>

      <aside class="sidebar" :class="{ 'sidebar--collapsed': !sidebarOpen }" aria-label="Suburb details panel">
        <button
          class="sidebar-strip-btn"
          @click="sidebarOpen = !sidebarOpen"
          :aria-label="sidebarOpen ? 'Collapse suburb details panel' : 'Expand suburb details panel'"
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
                <div class="sidebar-title">Suburb Solar Rankings</div>
              </div>
              <div style="display:flex;gap:8px;align-items:center;">
                <button
                  class="sidebar-export-btn"
                  @click="guideStep = 0; showGuide = true"
                  aria-label="Open page guide"
                  title="How to use this page"
                >Guide</button>
                <button
                  class="sidebar-export-btn"
                  @click="exportPrecinctsCsv"
                  aria-label="Export suburb data as CSV"
                >Export CSV</button>
              </div>
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
              </div>

              <div class="section-title">Suburb Info</div>
              <div class="info-row">
                <span class="info-key">Suburb ID</span>
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
                  <div class="metric-sub">Est. electricity generated per year</div>
                </div>
                <div class="metric-card">
                  <div class="metric-val">{{ formatArea(selectedPrecinct.total_area) }}</div>
                  <div class="metric-label">Total Usable Roof Area</div>
                  <div class="metric-sub">Solar-viable rooftop space</div>
                </div>
                <div class="metric-card">
                  <div class="metric-val">{{ formatKw(selectedPrecinct.installed_capacity_kw) }}</div>
                  <div class="metric-label">Installed Capacity</div>
                  <div class="metric-sub">Solar already deployed</div>
                </div>
                <div class="metric-card">
                  <div class="metric-val">{{ formatKw(selectedPrecinct.potential_capacity_kw) }}</div>
                  <div class="metric-label">Potential Capacity</div>
                  <div class="metric-sub">Maximum achievable solar capacity</div>
                </div>
                <div class="metric-card metric-card--wide">
                  <div class="metric-val">{{ selectedPrecinct.adoption_gap_kw != null ? formatKw(selectedPrecinct.adoption_gap_kw) : formatKwh(selectedPrecinct.adoption_gap) }}</div>
                  <div class="metric-label">Adoption Gap</div>
                  <div class="metric-sub">Untapped capacity still available</div>
                </div>
              </div>

              <button class="share-btn" @click="selectedPrecinct = null" style="margin-top: 4px;">← Back to Rankings</button>
            </div>

            <!-- Ranked table -->
            <div v-else>
              <div v-if="sortedPrecincts.length === 0 && !isLoading" class="empty-state">
                <div class="empty-icon">☀</div>
                <div class="empty-text">No suburb data available</div>
              </div>

              <template v-else>
                <!-- Column headers — active sort column highlighted -->
                <div class="precinct-table-head">
                  <div class="pt-col-name">Suburb Name</div>
                  <div class="pt-col-kwh"       :class="{ 'col-active': sortBy === 'kwh'       }">Annual kWh</div>
                  <div class="pt-col-area"      :class="{ 'col-active': sortBy === 'area'      }">Roof Area</div>
                  <div class="pt-col-bldg"      :class="{ 'col-active': sortBy === 'buildings' }">Buildings</div>
                  <div class="pt-col-stat"      :class="{ 'col-active': sortBy === 'gap'       }">Adoption Rate</div>
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

    <!-- User guide overlay -->
    <Transition name="onboarding-fade">
      <div v-if="showGuide" class="onboarding-overlay" role="dialog" aria-modal="true" :aria-labelledby="`guide-title-${guideStep}`">
        <div class="onboarding-card guide-card">

          <div class="guide-header-row">
            <span class="guide-counter">{{ guideStep + 1 }} / {{ PRECINCT_GUIDE_STEPS.length }}</span>
            <button class="onboarding-skip" @click="dismissGuide" aria-label="Close guide">✕ Skip guide</button>
          </div>

          <div class="guide-body">
            <div class="guide-icon" aria-hidden="true" v-html="PRECINCT_GUIDE_STEPS[guideStep].icon"></div>
            <h2 class="guide-title" :id="`guide-title-${guideStep}`">{{ PRECINCT_GUIDE_STEPS[guideStep].title }}</h2>
            <p class="guide-desc">{{ PRECINCT_GUIDE_STEPS[guideStep].desc }}</p>
            <div v-if="PRECINCT_GUIDE_STEPS[guideStep].tip" class="guide-tip">
              <span class="guide-tip-label">Tip</span>
              {{ PRECINCT_GUIDE_STEPS[guideStep].tip }}
            </div>
          </div>

          <div class="guide-dots" role="tablist" aria-label="Guide progress">
            <button
              v-for="(_, i) in PRECINCT_GUIDE_STEPS"
              :key="i"
              class="guide-dot"
              :class="{ 'guide-dot--active': i === guideStep, 'guide-dot--done': i < guideStep }"
              @click="guideStep = i"
              :aria-label="`Go to step ${i + 1}`"
              role="tab"
              :aria-selected="i === guideStep"
            ></button>
          </div>

          <div class="guide-nav">
            <button class="guide-nav-back" :disabled="guideStep === 0" @click="guideStep--" aria-label="Previous step">← Back</button>
            <button
              v-if="guideStep < PRECINCT_GUIDE_STEPS.length - 1"
              class="onboarding-cta guide-nav-next"
              @click="guideStep++"
            >Next →</button>
            <button
              v-else
              class="onboarding-cta guide-nav-next"
              @click="dismissGuide"
            >Explore Suburbs →</button>
          </div>

        </div>
      </div>
    </Transition>
  </div>
</template>

<script>
// This extra <script> block (not <script setup>) is needed to set the component name.
// The name 'PrecinctsView' matches the string in KeepAlive in App.vue, which is what
// keeps this map page alive in memory when you navigate away.
export default { name: 'PrecinctsView' }
</script>

<script setup>
// ─────────────────────────────────────────────────────────────────────────────
// PrecinctsView.vue — The Precincts page.
//
// This page shows Melbourne CBD split into named precincts (neighbourhoods).
// Each precinct is coloured on the map by its solar ranking (green = best, red = worst).
//
// How it works:
//   1. Load the GeoJSON file of precinct boundaries (polygon shapes on the map).
//   2. Load the GeoJSON file of all buildings (40,000+ points).
//   3. For each building, use a point-in-polygon algorithm to figure out which
//      precinct it belongs to, then sum up the kWh and roof area per precinct.
//   4. Fetch additional data from the API (installed capacity, adoption gap).
//   5. Rank precincts and colour the map accordingly.
//
// The sidebar on the right shows a ranked table that the user can sort by:
//   Annual kWh / Roof Area / Number of Buildings / Adoption Gap
// ─────────────────────────────────────────────────────────────────────────────

// Vue's reactivity and lifecycle functions.
// computed   → creates a value that auto-updates when its inputs change
// onMounted  → runs once after the page is displayed on screen
// onUnmounted → runs before the page is hidden (used to clean up the map)
// ref        → creates a reactive variable
// watch      → runs a function whenever a reactive value changes
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'

// MapLibre GL JS — the library that renders the interactive map.
import maplibregl from 'maplibre-gl'

// Shared top navigation bar.
import MainNavbar from '../components/MainNavbar.vue'

// ── URL configuration ─────────────────────────────────────────────────────────
// These come from the .env file so they can point to different servers in
// development vs production. The || fallback is used when the env var isn't set.
const BUILDINGS_PATH  = import.meta.env.VITE_GEOJSON_URL   || '/combined-buildings.geojson'
const PRECINCTS_PATH  = import.meta.env.VITE_PRECINCTS_URL || '/melbourne_cbd_precincts.geojson'
const API_BASE        = import.meta.env.VITE_API_BASE_URL  || '/api/v1'

// ── GeoJSON fetch helper ──────────────────────────────────────────────────────
// Fetches a GeoJSON file and validates the response is actually JSON (not an HTML
// error page that the server returned with a 200 status by mistake).
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

// ── Module-level data caches ──────────────────────────────────────────────────
// These variables are stored OUTSIDE the component (at module level), which means
// they survive when the user navigates away and comes back.
//
// Without caching: every time you visit /precincts, it would re-download the
// multi-MB GeoJSON files and redo the point-in-polygon calculation (~10 seconds).
// With caching: the second visit is nearly instant.
let _cachedPrecinctGeoJSON = null   // the GeoJSON of precinct boundary polygons
let _cachedBuildingData    = null   // the GeoJSON of all buildings
let _cachedAggregation     = null   // the calculated per-precinct totals
let _cachedApiData         = null   // { precinct_id → PrecinctSummary } from the API

// ── Map colour constants ──────────────────────────────────────────────────────
// MapLibre GL paint specs only accept hex literals — they cannot read CSS variables.
// Every value here has a matching CSS variable in style.css :root for reference.
const MAP_COLORS = {
  solarExcellent: '#D55E00',
  solarGood:      '#E69F00',
  solarModerate:  '#F0E442',
  solarPoor:      '#56B4E9',
  solarVeryPoor:  '#0072B2',
  buildingBase:   '#2A2A26',
  top5Outline:    '#D4743A',
  selectedOutline:'#FFD966',
  defaultOutline: '#3E3E3A',
  lineStroke:     '#1C1710',
}

// ── 14-step colour gradient for precinct ranking ──────────────────────────────
// Rank 1 (best precinct) gets the darkest green; rank 14 (worst) gets the deepest red.
// Each precinct's rank maps to one of these 14 colours via quintileTier() below.
const TIER_COLORS = [
  '#D55E00',  // rank 1  — Excellent (orange-red)
  '#DA7200',  // rank 2
  '#DF8600',  // rank 3
  '#E59A00',  // rank 4
  '#E8AF0F',  // rank 5
  '#EBC424',  // rank 6
  '#EED938',  // rank 7
  '#D8DD5C',  // rank 8
  '#A9CE8F',  // rank 9
  '#7ABFC2',  // rank 10
  '#4FAFE5',  // rank 11
  '#359BD4',  // rank 12
  '#1B86C3',  // rank 13
  '#0072B2',  // rank 14 — Very Poor (dark blue)
]
const TIER_LABELS = [
  'Rank 1','Rank 2','Rank 3','Rank 4','Rank 5','Rank 6','Rank 7',
  'Rank 8','Rank 9','Rank 10','Rank 11','Rank 12','Rank 13','Rank 14',
]

// ── Helper functions ──────────────────────────────────────────────────────────

// Converts a rank (1 = best) into one of the 14 colour indices.
// Example: if there are 14 precincts, rank 1 → index 0, rank 14 → index 13.
function quintileTier(rank, total) {
  if (total <= 0) return 6  // default to middle colour if no data
  return Math.min(13, Math.floor((rank - 1) / total * 14))
}

// Returns the hex colour for a given tier index (0–13).
function tierColor(tier) { return TIER_COLORS[tier] ?? MAP_COLORS.solarModerate }

// Returns the human-readable label for a tier index ("Rank 1", "Rank 2", …).
function tierLabel(tier) { return TIER_LABELS[tier] ?? `Rank ${tier + 1}` }

// ── Reactive state (variables that update the UI when they change) ────────────

// ── Guide state ───────────────────────────────────────────────────────────────
const showGuide = ref(true)
const guideStep = ref(0)

const PRECINCT_GUIDE_STEPS = [
  {
    icon: `<svg width="52" height="52" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="4" stroke="var(--city-light)" stroke-width="1.8"/><path d="M12 2v2.5M12 19.5V22M2 12h2.5M19.5 12H22M4.2 4.2l1.8 1.8M18 18l1.8 1.8M18 6l1.8-1.8M4.2 19.8l1.8-1.8" stroke="var(--city-light)" stroke-width="1.6" stroke-linecap="round"/></svg>`,
    title: 'Welcome to Suburb Solar Rankings',
    desc: 'This page lets you explore the solar potential of every Melbourne CBD suburb at a glance. The map is colour-coded by solar rank, and the sidebar shows a ranked table you can sort and export.',
  },
  {
    icon: `<svg width="52" height="52" viewBox="0 0 24 24" fill="none"><path d="M3 6h18M3 12h18M3 18h18" stroke="var(--city-light)" stroke-width="2" stroke-linecap="round"/><circle cx="8" cy="6" r="2" fill="var(--city-light)"/><circle cx="16" cy="12" r="2" fill="var(--city-light)"/><circle cx="10" cy="18" r="2" fill="var(--city-light)"/></svg>`,
    title: 'Sort the Rankings',
    desc: 'Use the sort tabs at the top of the sidebar to reorder suburbs by Annual Output, Roof Area, Buildings, or Adoption Gap. The map and list update together so you always see the same ranking.',
    tip: 'Sort by Adoption Gap to find suburbs with the most untapped solar capacity — ideal for targeting policy interventions.',
  },
  {
    icon: `<svg width="52" height="52" viewBox="0 0 24 24" fill="none"><path d="M5 9c0-3.87 3.13-7 7-7s7 3.13 7 7c0 4.5-5.5 11-7 13C10.5 20 5 13.5 5 9z" stroke="var(--city-light)" stroke-width="1.8"/><circle cx="12" cy="9" r="2.5" stroke="var(--city-light)" stroke-width="1.6"/></svg>`,
    title: 'Explore the Map',
    desc: 'Each suburb polygon on the map is shaded from orange (highest solar potential) to blue (lowest). Click any suburb to select it, or click a row in the sidebar list. The map zooms in and highlights your selection.',
    tip: 'Drag and scroll to navigate the map. The colour gradient across all 14 suburbs shows you the spread of solar opportunity at a glance.',
  },
  {
    icon: `<svg width="52" height="52" viewBox="0 0 24 24" fill="none"><rect x="3" y="3" width="18" height="18" rx="2" stroke="var(--city-light)" stroke-width="1.8"/><path d="M7 8h10M7 12h7M7 16h5" stroke="var(--city-light)" stroke-width="1.4" stroke-linecap="round"/></svg>`,
    title: 'Suburb Detail Panel',
    desc: 'Clicking a suburb opens its full detail view in the sidebar. You\'ll see its rank, a solar capacity breakdown (installed vs potential), total annual output, usable roof area, building count, and the adoption gap.',
    tip: 'The adoption gap bar shows how much potential capacity is still untapped — a small installed segment means a big opportunity.',
  },
  {
    icon: `<svg width="52" height="52" viewBox="0 0 24 24" fill="none"><path d="M12 3L3 9v12h6v-6h6v6h6V9L12 3z" stroke="var(--city-light)" stroke-width="1.8" stroke-linejoin="round"/></svg>`,
    title: 'Export Data',
    desc: 'Click Export CSV in the sidebar header to download the full ranked suburb dataset — or just the selected suburb\'s detail — as a spreadsheet. Use it in planning tools, reports, or presentations.',
    tip: 'When a suburb is selected the export covers just that suburb\'s stats. Return to the rankings list first to export all suburbs.',
  },
]

function dismissGuide() { showGuide.value = false }

// true while data is being loaded or calculated — shows the loading spinner overlay.
const isLoading     = ref(true)
// Message shown under the loading spinner (e.g. "Aggregating buildings… 42%").
const loadingText   = ref('Loading building data…')
// true = the right sidebar is visible, false = collapsed to a narrow strip.
const sidebarOpen   = ref(true)
// Which column the precinct table is currently sorted by.
const sortBy        = ref('kwh')
// Array of enriched precinct objects — filled after aggregation completes.
const precincts     = ref([])
// The precinct the user clicked on — triggers the detail view in the sidebar.
const selectedPrecinct = ref(null)
// Short status message shown in a toast popup (e.g. "CSV exported").
const toastMessage  = ref('')
// true when the toast is visible (auto-hides after 1.8 seconds).
const toastVisible  = ref(false)
let toastTimer      = null   // stores the setTimeout handle so we can cancel it
let map             = null   // the MapLibre GL map instance

// ── Sort options for the sidebar tabs ─────────────────────────────────────────
// Each option has:
//   id    → the key used in `sortBy` to identify this sort
//   label → the text shown on the tab button
const sortOptions = [
  { id: 'kwh',       label: 'Annual kWh'   },
  { id: 'area',      label: 'Roof Area'    },
  { id: 'buildings', label: 'Buildings'    },
  { id: 'gap',       label: 'Adoption Rate' },
]

// ── Sorted / ranked list (computed) ──────────────────────────────────────────
// `sortedPrecincts` is a computed value — Vue recalculates it automatically
// whenever `sortBy` or `precincts` changes.
//
// It takes the raw precincts array, sorts by the selected column (kwh/area/buildings/gap),
// filters out precincts with no buildings, and assigns each precinct a `rank` and `tier`.
const sortedPrecincts = computed(() => {
  const isGap = sortBy.value === 'gap'
  const key = sortBy.value === 'kwh' ? 'total_kwh'
            : sortBy.value === 'area' ? 'total_area'
            : sortBy.value === 'buildings' ? 'building_count'
            : 'total_kwh'
  const sorted = [...precincts.value]
    .filter(p => p.building_count > 0)
    .sort((a, b) => {
      if (isGap) {
        const aRatio = (a.installed_capacity_kw ?? 0) / Math.max(1, a.potential_capacity_kw ?? 1)
        const bRatio = (b.installed_capacity_kw ?? 0) / Math.max(1, b.potential_capacity_kw ?? 1)
        return bRatio - aRatio  // descending: most installed (least gap) first
      }
      return (b[key] ?? 0) - (a[key] ?? 0)
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

// Whenever the sorted list changes (user switches sort tab), re-colour the map.
// `watch` runs the callback every time `sortedPrecincts` produces a new value.
watch(sortedPrecincts, () => updateMapLayers(), { deep: false })

// ── Number formatting helpers ─────────────────────────────────────────────────
// These convert raw numbers into human-readable strings with units.
// They automatically pick the best unit (kWh, MWh, GWh) based on the size.

// Format a kWh value for the detail view (full precision).
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
  if (p.potential_capacity_kw > 0) return Math.round((p.installed_capacity_kw ?? 0) / p.potential_capacity_kw * 1000) / 10
  if (!p.max_kwh) return 0
  return Math.round((p.total_kwh / p.max_kwh) * 100)
}
const currentSortLabel = computed(() => sortOptions.find(s => s.id === sortBy.value)?.label ?? '')

// ── Toast notification ────────────────────────────────────────────────────────
// Shows a brief popup message at the bottom of the screen (e.g. after CSV export).
// The toast auto-hides after 1.8 seconds.
function showToast(msg) {
  if (toastTimer) clearTimeout(toastTimer)
  toastMessage.value = msg
  toastVisible.value = true
  toastTimer = setTimeout(() => { toastVisible.value = false }, 1800)
}

// ── Select a precinct ─────────────────────────────────────────────────────────
// Called when the user clicks a row in the sidebar or a precinct on the map.
// It:
//   1. Sets selectedPrecinct (switches the sidebar to the detail view)
//   2. Highlights the precinct boundary on the map with a yellow outline
//   3. Flies the camera to fit the precinct polygon in view
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

// ── Point-in-polygon (ray casting algorithm) ──────────────────────────────────
// Determines whether a GPS coordinate (px, py) is inside a polygon shape.
//
// How it works (the "ray casting" method):
//   Imagine firing an infinite horizontal ray from the point to the right.
//   Count how many times the ray crosses a polygon edge.
//   If the count is ODD  → the point is INSIDE the polygon.
//   If the count is EVEN → the point is OUTSIDE the polygon.
//
// This is used to assign each building (a point) to the correct precinct (a polygon).
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

// ── Bounding box pre-computation ──────────────────────────────────────────────
// Calculates the min/max longitude and latitude for a polygon shape.
//
// Why? The point-in-polygon check is slow. We first do a fast "is this point even
// inside the bounding rectangle?" check. If the building is clearly outside the
// rectangle, we skip the expensive ray-cast entirely.
// This makes the aggregation much faster (skip ~90% of checks).
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

// ── Building aggregation ──────────────────────────────────────────────────────
// This is the main data processing step — it assigns every building to a precinct
// and sums up the annual kWh, usable roof area, and building count per precinct.
//
// Because we have 40,000+ buildings and 14 precincts, this takes ~10 seconds.
// To avoid freezing the browser tab, we process buildings in chunks of 2,000
// and use `await new Promise(r => setTimeout(r, 0))` between chunks to "yield"
// control back to the browser, allowing the loading spinner to keep animating.
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

// ── Update map colours ────────────────────────────────────────────────────────
// Called whenever the sort changes or new data arrives.
// Applies the rank-based colour gradient to each precinct polygon on the map,
// and draws an orange outline around the top 5 precincts.
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

// ── Map initialisation ────────────────────────────────────────────────────────
// Creates the MapLibre GL map and adds all the layers.
// Called once when the page first loads (not on every visit — see KeepAlive in App.vue).
//
// Layer order (bottom to top):
//   1. building-extrusion  → grey 3D boxes for context (low opacity)
//   2. precinct-fill       → coloured polygon fill per precinct
//   3. precinct-outline    → thin grey border around each precinct
//   4. precinct-top5-outline → orange border for the top 5 precincts
//   5. precinct-selected   → yellow border for the clicked precinct
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
        loadingText.value = 'Buildings unavailable — showing suburb outlines only'
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
    // Fetch the /api/v1/precincts endpoint to get installed_capacity_kw, potential_capacity_kw,
    // and adoption_gap_kw from the real CER database records.
    // If the API is unreachable we just skip this step — the sidebar still shows kWh/area/count.
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
// Generates and downloads a CSV file.
// If a precinct is selected → exports just that precinct's details.
// If no precinct is selected → exports the full ranked table.
//
// How browser-side CSV download works:
//   1. Build the CSV string in memory.
//   2. Create a Blob (a file-like object).
//   3. Generate a temporary URL for the Blob.
//   4. Programmatically click a hidden <a> link to trigger the browser's download.
//   5. Clean up the temporary URL.

// Wraps a value in double-quotes and escapes any existing quotes (RFC 4180 CSV format).
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
      ['Suburb Name', p.name],
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
    rows = [['Rank', 'Suburb Name', 'Annual Output', 'Usable Roof Area', 'Installed Capacity', 'Potential Capacity', 'Adoption Gap', 'Tier', 'Buildings']]
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

// ── Lifecycle hooks ───────────────────────────────────────────────────────────
// onMounted runs once after the page is first rendered on screen.
// It loads the data and initialises the map.
onMounted(async () => {
  // If we already have aggregated data from a previous visit (cached), show the sidebar
  // immediately and suppress the loading overlay — MapLibre initialises in the background.
  // This makes the second visit feel near-instant.
  if (_cachedAggregation) {
    precincts.value = _cachedAggregation
    isLoading.value = false
  }

  let precinctGeoJSON
  if (_cachedPrecinctGeoJSON) {
    precinctGeoJSON = _cachedPrecinctGeoJSON
  } else {
    loadingText.value = 'Loading suburb boundaries…'
    try {
      const res = await fetchGeoJson(PRECINCTS_PATH)
      precinctGeoJSON = await res.json()
      _cachedPrecinctGeoJSON = precinctGeoJSON
    } catch (err) {
      loadingText.value = `Failed to load suburbs: ${err.message}`
      return
    }
  }

  setTimeout(() => { if (!map) initMap(precinctGeoJSON) }, 50)
})

// onUnmounted runs before the component is removed from the DOM.
// We use it to:
//   1. Clear any pending toast timers (prevents them from firing after the component is gone)
//   2. Destroy the MapLibre map to free memory
//      (Note: with KeepAlive in App.vue, this only runs if the component is actually destroyed)
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
.sidebar { width: 720px; }
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
  font-size: 13px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.9px; color: var(--city-light); margin-bottom: 5px;
}

/* ── Sort tabs (full-width underline tab style) ───────────── */
.sort-tabs {
  display: flex; border-bottom: 2px solid var(--border);
  background: var(--surface);
}
.sort-tab {
  flex: 1; padding: 13px 8px; text-align: center;
  font-size: 14px; font-weight: 500; color: var(--text-muted);
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
  font-size: 13px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.7px; color: var(--text-muted); transition: color 0.15s;
  justify-content: flex-end; white-space: nowrap; overflow: hidden;
}
.precinct-table-head .col-active { color: var(--city-light); }
.precinct-table-head .pt-col-name { justify-content: flex-start; }

/* ── Column widths ────────────────────────────────────────── */
.pt-col-name { flex: 1; min-width: 0; display: flex; align-items: center; gap: 10px; justify-content: flex-start; text-align: left; }
.pt-col-kwh  { width: 120px; flex-shrink: 0; text-align: right; padding-right: 16px; }
.pt-col-area { width: 110px; flex-shrink: 0; text-align: right; padding-right: 16px; }
.pt-col-bldg { width: 100px; flex-shrink: 0; text-align: right; padding-right: 16px; }
.pt-col-stat { width: 140px; flex-shrink: 0; display: flex; align-items: center; justify-content: flex-end; gap: 6px; }

/* ── Rows ─────────────────────────────────────────────────── */
.precinct-row {
  display: flex; align-items: center;
  padding: 13px 20px; cursor: pointer;
  border-bottom: 1px solid var(--border); transition: background 0.15s;
}
.precinct-row:hover { background: var(--surface2); }
.precinct-row--top5 { background: rgba(var(--city-light-rgb), 0.05); }
.precinct-row--top5:hover { background: rgba(var(--city-light-rgb), 0.10); }

/* Rank badge */
.p-rank {
  width: 28px; height: 28px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  border-radius: 8px; font-size: 13px; font-weight: 700;
  color: var(--text-muted); background: var(--surface2); border: 1px solid var(--border);
}
.p-rank--top5 { background: var(--ink); color: var(--white); border-color: var(--ink); }

/* Tier color dot */
.p-dot { width: 13px; height: 13px; border-radius: 4px; flex-shrink: 0; }

/* Precinct name */
.p-name {
  font-size: 14px; font-weight: 600; color: var(--text-primary);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}

/* Data values — default muted, active sort column stands out */
.pt-col-kwh, .pt-col-area, .pt-col-bldg {
  font-size: 14px; color: var(--text-secondary); white-space: nowrap;
}
.pt-col-stat { font-size: 14px; color: var(--text-secondary); }
.p-val-active {
  font-size: 14px !important; font-weight: 700 !important;
  color: var(--text-primary) !important;
}
.p-val-active .mini-pct { font-weight: 700 !important; color: var(--text-primary); }

/* Mini bar */
.mini-bar-track {
  width: 60px; flex-shrink: 0; height: 6px; background: var(--border);
  border-radius: 3px; overflow: hidden;
}
.mini-bar { height: 100%; border-radius: 3px; transition: width 0.4s ease; }
.mini-bar--gap { background: var(--danger); }
.mini-pct { font-size: 13px; font-weight: 600; color: var(--text-muted); white-space: nowrap; width: 42px; text-align: right; flex-shrink: 0; }

/* ── Precinct detail panel ────────────────────────────────── */
.precinct-detail-panel { padding: 0 20px 16px; }

/* ── Toast ────────────────────────────────────────────────── */
.toast {
  position: fixed; bottom: 24px; left: 50%;
  transform: translateX(-50%) translateY(12px);
  background: var(--ink); color: var(--nav-text);
  border: 1px solid var(--ink-border); border-radius: 8px;
  padding: 9px 18px; font-size: 14px;
  opacity: 0; pointer-events: none;
  transition: opacity 0.2s ease, transform 0.2s ease; z-index: 9999;
}
.toast.show { opacity: 1; transform: translateX(-50%) translateY(0); }
</style>
