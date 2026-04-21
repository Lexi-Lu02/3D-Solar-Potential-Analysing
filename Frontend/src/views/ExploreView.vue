<template>
  <div class="map-page">
    <MainNavbar />
    <main id="main-content" class="main">
      <div id="map" role="application" aria-label="Interactive 3D solar map of Melbourne buildings">
        <div v-if="isLoading" class="loading" role="status" aria-live="polite" aria-atomic="true" :aria-label="loadingText">
          <div class="loading-spinner" aria-hidden="true"></div>
          <div class="loading-text">{{ loadingText }}</div>
        </div>
        <div class="map-controls" role="group" aria-label="Map filters">
          <div class="control-card">
            <button
              class="control-card-toggle"
              @click="solarFilterOpen = !solarFilterOpen"
              :aria-expanded="solarFilterOpen"
              aria-controls="solar-filter-group"
            >
              <span class="control-title">Filter by Solar Potential</span>
              <svg class="chevron-icon" :class="{ 'chevron-up': solarFilterOpen }" width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
                <path d="M3 5l4 4 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </button>
            <div id="solar-filter-group" v-show="solarFilterOpen" class="filter-group" role="group" aria-label="Solar potential filter options">
              <button
                v-for="t in solarTiers"
                :key="t.id"
                class="filter-btn"
                :class="{ active: activeSolarFilter === t.id }"
                :aria-pressed="activeSolarFilter === t.id"
                :aria-label="`${t.label} solar potential, score range ${t.range}`"
                @click="filterSolar(t.id)"
              >
                <div class="legend-dot" :style="{ background: t.color }" aria-hidden="true"></div>
                {{ t.label }}<span class="tier-range">&nbsp;({{ t.range }})</span>
              </button>
            </div>
          </div>
          <div class="control-card">
            <button
              class="control-card-toggle"
              @click="roofFilterOpen = !roofFilterOpen"
              :aria-expanded="roofFilterOpen"
              aria-controls="roof-filter-group"
            >
              <span class="control-title">Filter by Roof Type</span>
              <svg class="chevron-icon" :class="{ 'chevron-up': roofFilterOpen }" width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
                <path d="M3 5l4 4 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </button>
            <div id="roof-filter-group" v-show="roofFilterOpen" class="filter-group" role="group" aria-label="Roof type filter options">
              <button
                v-for="f in filters"
                :key="f.type"
                class="filter-btn"
                :class="{ active: activeFilter === f.type }"
                :aria-pressed="activeFilter === f.type"
                :aria-label="`${f.label} filter`"
                @click="filterRoof(f.type)"
              >
                <svg width="28" height="12" class="filter-dash-icon" aria-hidden="true">
                  <line
                    x1="2"
                    y1="6"
                    x2="26"
                    y2="6"
                    stroke="currentColor"
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
          <div v-if="compareVisible" class="comparison-panel" role="region" aria-label="Building comparison panel" aria-live="polite">
            <div class="comparison-header">
              <div class="comparison-header-left">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true" class="comparison-header-icon">
                  <rect x="1" y="3" width="6" height="10" rx="1.5" stroke="currentColor" stroke-width="1.5"/>
                  <rect x="9" y="3" width="6" height="10" rx="1.5" stroke="currentColor" stroke-width="1.5"/>
                </svg>
                <span class="comparison-title" id="compare-panel-title">Building Comparison</span>
                <span class="comparison-count" :aria-label="`${compareBuildings.length} of 2 buildings selected`">{{ compareBuildings.length }} / 2</span>
              </div>
              <button class="comparison-close-btn" @click="clearCompare" aria-label="Close comparison panel">
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
                  <path d="M2 2l10 10M12 2L2 12" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
                </svg>
              </button>
            </div>

            <div class="comparison-body" aria-labelledby="compare-panel-title">
              <!-- Building columns -->
              <div
                v-for="(item, col) in compareBuildings"
                :key="item.building.structure_id"
                class="comparison-col"
              >
                <!-- Column header -->
                <div class="comparison-col-header">
                  <div class="comparison-col-label">Building {{ col + 1 }}</div>
                  <div class="comparison-building-id">
                    {{ item.building.structure_id }}
                  </div>
                  <button class="comparison-remove-btn" @click="removeFromCompare(col)" :aria-label="`Remove Structure ${item.building.structure_id} from comparison`">
                    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true"><path d="M1.5 1.5l9 9M10.5 1.5l-9 9" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>
                  </button>
                </div>

                <!-- Score hero -->
                <div class="comparison-score-hero">
                  <div class="comparison-score-circle" :style="{ '--score-color': scoreColor(item.building.solar_score) }">
                    <span class="comparison-score-num">{{ item.building.solar_score ?? '—' }}</span>
                    <span class="comparison-score-unit">/100</span>
                  </div>
                  <div class="comparison-score-meta">
                    <div class="comparison-tier-badge" :style="{ background: scoreColor(item.building.solar_score) + '22', color: scoreColor(item.building.solar_score), borderColor: scoreColor(item.building.solar_score) + '55' }">
                      {{ scoreTier(item.building.solar_score) }}
                    </div>
                    <div class="comparison-score-bar-track">
                      <div class="comparison-score-bar-fill" :style="{ width: Math.min(100, item.building.solar_score || 0) + '%', background: scoreColor(item.building.solar_score) }"></div>
                    </div>
                  </div>
                </div>

                <!-- Metric rows -->
                <div class="comparison-metrics">
                  <div
                    v-for="(metric, mi) in compareMetrics(item)"
                    :key="metric.label"
                    class="comparison-metric-row"
                    :class="{ 'comparison-winner': compareWinners[mi]?.[col] }"
                  >
                    <span class="comparison-metric-label">{{ metric.label }}</span>
                    <span class="comparison-metric-val">
                      {{ metric.display }}
                      <span v-if="compareWinners[mi]?.[col]" class="comparison-winner-badge" aria-label="Winner">★</span>
                    </span>
                  </div>
                </div>
              </div>

              <!-- VS divider (only when 2 buildings) -->
              <div v-if="compareBuildings.length === 2" class="comparison-vs" aria-hidden="true">VS</div>

              <!-- Empty slot -->
              <div v-if="compareBuildings.length < 2" class="comparison-empty-col">
                <svg width="28" height="28" viewBox="0 0 28 28" fill="none" aria-hidden="true" class="comparison-empty-icon">
                  <rect x="2" y="2" width="24" height="24" rx="4" stroke="currentColor" stroke-width="1.5" stroke-dasharray="4 3"/>
                  <path d="M14 9v10M9 14h10" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
                </svg>
                <div class="comparison-empty-hint">Click a building,<br>then <strong>Add to Compare</strong></div>
              </div>
            </div>
          </div>
        </Transition>
      </div>

      <aside class="sidebar" :class="{ 'sidebar--collapsed': !sidebarOpen }" aria-label="Building details panel">
        <button
          class="sidebar-strip-btn"
          @click="sidebarOpen = !sidebarOpen"
          :aria-label="sidebarOpen ? 'Collapse building details panel' : 'Expand building details panel'"
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
            <div class="sidebar-title" id="sidebar-title">Building Details</div>
            <div class="sidebar-sub" aria-live="polite">
              {{ selectedBuilding ? '' : 'Click any building on the map' }}
            </div>
            <div class="search-row" role="search">
              <label for="search-address" class="visually-hidden">Search buildings by address</label>
              <div class="search-input-wrap" ref="searchWrapRef">
                <input
                  id="search-address"
                  v-model="searchId"
                  type="text"
                  class="search-input"
                  placeholder="Search by address…"
                  autocomplete="off"
                  role="combobox"
                  :aria-expanded="searchResults.length > 0 || searchLoading"
                  aria-autocomplete="list"
                  aria-controls="search-listbox"
                  :aria-activedescendant="searchFocusedIdx >= 0 ? `search-option-${searchFocusedIdx}` : undefined"
                  :aria-describedby="searchError ? 'search-error-msg' : undefined"
                  @input="onSearchInput"
                  @keydown="onSearchKeydown"
                />
                <button
                  class="search-icon-btn"
                  @click="searchResults.length ? selectSearchResult(searchResults[searchFocusedIdx >= 0 ? searchFocusedIdx : 0]) : onSearchInput()"
                  aria-label="Search"
                  type="button"
                >
                  <img :src="iconSearch" alt="" aria-hidden="true" class="search-icon-img" />
                </button>
                <!-- Dropdown: loading -->
                <ul v-if="searchLoading" class="search-dropdown" role="listbox" id="search-listbox">
                  <li class="search-dropdown-loading" aria-live="polite">
                    <span class="search-loading-dot"></span>
                    <span class="search-loading-dot"></span>
                    <span class="search-loading-dot"></span>
                  </li>
                </ul>
                <!-- Dropdown: results -->
                <ul v-else-if="searchResults.length" class="search-dropdown" role="listbox" id="search-listbox" aria-label="Address search results">
                  <li
                    v-for="(result, i) in searchResults"
                    :key="result.structure_id"
                    :id="`search-option-${i}`"
                    class="search-dropdown-item"
                    :class="{ 'search-dropdown-item--focused': searchFocusedIdx === i }"
                    role="option"
                    :aria-selected="searchFocusedIdx === i"
                    @mousedown.prevent="selectSearchResult(result)"
                    @mouseover="searchFocusedIdx = i"
                  >
                    <svg class="search-result-pin" width="12" height="14" viewBox="0 0 12 14" fill="none" aria-hidden="true">
                      <path d="M6 0C3.24 0 1 2.24 1 5c0 3.75 5 9 5 9s5-5.25 5-9c0-2.76-2.24-5-5-5zm0 6.5A1.5 1.5 0 1 1 6 3.5a1.5 1.5 0 0 1 0 3z" fill="currentColor"/>
                    </svg>
                    <span class="search-result-address">{{ result.address }}</span>
                  </li>
                </ul>
                <!-- Dropdown: no results -->
                <ul v-else-if="searchDropdownOpen && searchId.trim().length >= 2 && !searchLoading" class="search-dropdown" role="listbox" id="search-listbox">
                  <li class="search-dropdown-empty">No matching addresses found</li>
                </ul>
              </div>
            </div>
            <div v-if="searchError" id="search-error-msg" class="search-error" role="alert" aria-live="assertive">{{ searchError }}</div>
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
              <div class="info-row"><span class="info-key">Address</span><span class="info-val">{{ shortAddress(selectedAddress) }}</span></div>
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
              <div v-else class="monthly-chart" role="img" :aria-label="`Monthly solar output chart. ${monthlyOutput.map(m => `${m.month}: ${m.kwh.toLocaleString()} kWh`).join(', ')}`">
                <div class="monthly-bars" role="list">
                  <div
                    v-for="(m, i) in monthlyOutput"
                    :key="m.month"
                    class="monthly-bar-col"
                    :class="{ 'monthly-bar-col--hovered': hoveredMonthIdx === i }"
                    role="listitem"
                    tabindex="0"
                    :aria-label="`${m.month}: ${m.kwh.toLocaleString()} kWh`"
                    @mouseenter="hoveredMonthIdx = i"
                    @mouseleave="hoveredMonthIdx = null"
                    @focus="hoveredMonthIdx = i"
                    @blur="hoveredMonthIdx = null"
                    @keydown.enter="hoveredMonthIdx = hoveredMonthIdx === i ? null : i"
                    @keydown.space.prevent="hoveredMonthIdx = hoveredMonthIdx === i ? null : i"
                  >
                    <div class="monthly-tooltip" v-if="hoveredMonthIdx === i" aria-hidden="true">
                      {{ m.kwh.toLocaleString() }} kWh
                    </div>
                    <div class="monthly-bar-wrap">
                      <div class="monthly-bar" :style="{ height: m.pct + '%' }" aria-hidden="true"></div>
                    </div>
                    <div class="monthly-bar-label" aria-hidden="true">{{ m.month }}</div>
                  </div>
                </div>
              </div>
              <div class="compare-section">
                <div class="compare-header">
                  <span class="compare-title">
                    <img :src="iconCompare" alt="" aria-hidden="true" class="compare-title-icon" />
                    Compare
                  </span>
                  <button v-if="compareBuildings.length > 0" class="compare-clear" @click="clearCompare" aria-label="Clear all comparison buildings">Clear all</button>
                </div>

                <div v-if="compareBuildings.length === 0" class="compare-empty-hint-sidebar">
                  Add up to 2 buildings to compare side by side
                </div>

                <div v-else class="compare-slots-mini" role="list" aria-label="Buildings in comparison">
                  <div
                    v-for="(item, i) in compareBuildings"
                    :key="item.building.structure_id"
                    class="compare-slot-mini"
                    role="listitem"
                  >
                    <div class="compare-slot-mini-label">B{{ i + 1 }}</div>
                    <div class="compare-slot-mini-info">
                      <span class="compare-slot-mini-id">#{{ item.building.structure_id }}</span>
                      <span class="compare-slot-mini-tier" :style="{ color: scoreColor(item.building.solar_score) }">{{ scoreTier(item.building.solar_score) }}</span>
                    </div>
                    <span class="compare-slot-mini-score" :style="{ color: scoreColor(item.building.solar_score) }" :aria-label="`Solar score: ${item.building.solar_score}`">{{ item.building.solar_score }}</span>
                    <button class="compare-slot-remove" @click="removeFromCompare(i)" :aria-label="`Remove Structure ${item.building.structure_id} from comparison`">
                      <svg width="10" height="10" viewBox="0 0 10 10" fill="none" aria-hidden="true"><path d="M1 1l8 8M9 1L1 9" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
                    </button>
                  </div>
                </div>

                <button
                  class="compare-add-btn"
                  @click="addToCompare"
                  :disabled="!selectedBuilding || compareBuildings.some(c => c.building.structure_id === selectedBuilding.structure_id)"
                  :aria-disabled="!selectedBuilding || compareBuildings.some(c => c.building.structure_id === selectedBuilding.structure_id)"
                  :aria-label="compareBuildings.some(c => c.building.structure_id === selectedBuilding?.structure_id) ? 'Building already in comparison' : 'Add current building to comparison'"
                  :class="{ 'compare-add-btn--added': compareBuildings.some(c => c.building.structure_id === selectedBuilding?.structure_id) }"
                >
                  <svg v-if="compareBuildings.some(c => c.building.structure_id === selectedBuilding?.structure_id)" width="13" height="13" viewBox="0 0 13 13" fill="none" aria-hidden="true"><path d="M2 6.5l3.5 3.5 5.5-6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
                  <svg v-else width="13" height="13" viewBox="0 0 13 13" fill="none" aria-hidden="true"><path d="M6.5 2v9M2 6.5h9" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>
                  {{ compareBuildings.some(c => c.building.structure_id === selectedBuilding?.structure_id) ? 'Added to Compare' : 'Add to Compare' }}
                </button>
              </div>
              <button class="share-btn" @click="shareBuilding">Copy Shareable Link</button>
            </div>
          </div>
        </div>
      </aside>
    </main>

    <div class="toast" role="status" aria-live="polite" aria-atomic="true" :class="{ show: toastVisible }">{{ toastMessage }}</div>
  </div>
</template>

<script>
export default { name: 'ExploreView' }
</script>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import maplibregl from 'maplibre-gl'
import MainNavbar from '../components/MainNavbar.vue'
import iconCompare from '../pictures/Compare.png'
import iconSearch  from '../pictures/Search.png'
import { useRoute } from 'vue-router'

const route = useRoute()

const GEOJSON_PATH = import.meta.env.VITE_GEOJSON_URL || '/combined-buildings.geojson'

// MapLibre GL requires hex values — CSS variables are not supported in GL paint specs.
// These mirror the CSS variables defined in style.css :root for a single source of truth.
const MAP_COLORS = {
  solarExcellent:  '#09332C',  // --solar-very-high
  solarGood:       '#5A9072',  // --solar-high
  solarModerate:   '#C8A870',  // --solar-med
  solarPoor:       '#F8AB90',  // --solar-low
  solarVeryPoor:   '#F0531C',  // --solar-very-low
  selected:        '#FFD966',  // warm gold highlight
  compare:         '#8CA28F',  // muted sage highlight
  lineStroke:      '#1C1710',  // --text-primary
}

const SELECTED_BUILDING_COLOR = MAP_COLORS.selected
const SELECTED_BUILDING_OPACITY = 0.98
const COMPARE_BUILDING_COLOR = MAP_COLORS.compare
const COMPARE_BUILDING_OPACITY = 0.90

// Backend API base URL (same-origin in production, localhost in dev)
const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1'

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
const selectedAddress = ref(null)
const searchId = ref('')
const searchError = ref('')
const searchResults = ref([])   // [{ id, structure_id, lat, lng, address }]
const searchLoading = ref(false)
const searchFocusedIdx = ref(-1)
const searchDropdownOpen = ref(false)
const searchWrapRef = ref(null)
let searchDebounceTimer = null
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
  { id: 'very-high', label: 'Excellent',  range: '80-100', color: MAP_COLORS.solarExcellent, min: 80, max: null },
  { id: 'high',      label: 'Good',       range: '60-79',  color: MAP_COLORS.solarGood,      min: 60, max: 80 },
  { id: 'medium',    label: 'Moderate',   range: '40-59',  color: MAP_COLORS.solarModerate,  min: 40, max: 60 },
  { id: 'low',       label: 'Poor',       range: '20-39',  color: MAP_COLORS.solarPoor,      min: 20, max: 40 },
  { id: 'very-low',  label: 'Very Poor',  range: '0-19',   color: MAP_COLORS.solarVeryPoor,  min: 0,  max: 20 },
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

// Fetch solar cache data from the backend for one building.
// Returns { maxPanels, usableAreaM2, roofAreaM2, kwhAnnual } on success, null on any failure.
// Results are session-cached so the same building is only fetched once.
async function fetchSolarApiData(structureId) {
  if (solarApiCache.has(structureId)) return solarApiCache.get(structureId)

  try {
    const res = await fetch(`${API_BASE}/buildings/structure/${structureId}/solar`)

    if (!res.ok) {
      solarApiCache.set(structureId, null)
      return null
    }

    const body = await res.json()
    const result = {
      maxPanels:    body.max_panels ?? null,
      usableAreaM2: body.max_array_area_m2 != null ? Math.round(body.max_array_area_m2 * 10) / 10 : null,
      roofAreaM2:   body.whole_roof_area_m2 != null ? Math.round(body.whole_roof_area_m2 * 10) / 10 : null,
      kwhAnnual:    body.max_panels_kwh_annual != null ? Math.round(body.max_panels_kwh_annual) : null,
      address:      body.address || null,
    }
    solarApiCache.set(structureId, result)
    return result
  } catch {
    solarApiCache.set(structureId, null)
    return null
  }
}

async function fetchAddressForBuilding(structureId) {
  try {
    const res = await fetch(`${API_BASE}/buildings/by-structure/${structureId}/address`)
    if (!res.ok) return null
    const data = await res.json()
    return data.address || null
  } catch {
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

function shortAddress(addr) {
  if (!addr) return '—'
  const parts = addr.split(',')
  return parts.slice(0, 3).join(',').trim()
}

function filterRoof(type) {
  activeFilter.value = activeFilter.value === type ? 'all' : type
  applyFilters()
}

function filterSolar(tierId) {
  activeSolarFilter.value = activeSolarFilter.value === tierId ? 'all' : tierId
  applyFilters()
}

function closeSearchDropdown() {
  searchResults.value = []
  searchLoading.value = false
  searchFocusedIdx.value = -1
  searchDropdownOpen.value = false
}

function onSearchClickOutside(e) {
  if (searchWrapRef.value && !searchWrapRef.value.contains(e.target)) {
    closeSearchDropdown()
  }
}

function onSearchKeydown(e) {
  const len = searchResults.value.length
  if (e.key === 'Escape') { closeSearchDropdown(); return }
  if (e.key === 'ArrowDown') {
    e.preventDefault()
    searchFocusedIdx.value = len ? (searchFocusedIdx.value + 1) % len : -1
    return
  }
  if (e.key === 'ArrowUp') {
    e.preventDefault()
    searchFocusedIdx.value = len ? (searchFocusedIdx.value - 1 + len) % len : -1
    return
  }
  if (e.key === 'Enter') {
    const idx = searchFocusedIdx.value >= 0 ? searchFocusedIdx.value : 0
    if (len) selectSearchResult(searchResults.value[idx])
    return
  }
}

function onSearchInput() {
  searchFocusedIdx.value = -1
  clearTimeout(searchDebounceTimer)
  const q = searchId.value.trim()
  if (q.length < 2) { closeSearchDropdown(); return }
  searchDropdownOpen.value = true
  searchLoading.value = true
  searchDebounceTimer = setTimeout(async () => {
    try {
      const res = await fetch(`${API_BASE}/buildings/search?q=${encodeURIComponent(searchId.value.trim())}`)
      searchResults.value = res.ok ? await res.json() : []
    } catch {
      searchResults.value = []
    } finally {
      searchLoading.value = false
    }
  }, 250)
}

async function selectSearchResult(result) {
  searchResults.value = []
  searchDropdownOpen.value = false
  searchError.value = ''
  searchId.value = result.address || String(result.structure_id)

  const props = buildingIndex.get(Number(result.structure_id))
  if (!props) { searchError.value = 'Building not found in map data'; return }

  // Use the structure_id from GeoJSON props (same source as map features) for the filter
  const sid = Number(props.structure_id)

  selectedBuilding.value = props
  solarApiData.value = null
  selectedAddress.value = result.address || null
  solarApiLoading.value = true

  if (map) {
    map.setFilter('building-selected', ['==', ['get', 'structure_id'], sid])
    const lng = Number(result.lng) || Number(props.lng)
    const lat = Number(result.lat) || Number(props.lat)
    if (lat && lng) {
      map.flyTo({
        center: [lng, lat],
        zoom: Math.max(map.getZoom(), 15.5),
        pitch: 55,
        duration: 1200,
        easing: (t) => (t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t),
      })
    }
  }

  solarApiData.value = await fetchSolarApiData(sid)
  if (!selectedAddress.value) {
    selectedAddress.value = solarApiData.value?.address || await fetchAddressForBuilding(sid)
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

// Returns the comparable metrics for a compare entry
function compareMetrics(item) {
  const b = item.building
  const api = item.apiData
  const kwh = api?.kwhAnnual ?? (b.has_solar_data ? Math.round(Number(b.kwh_annual) || 0) : null)
  const area = api?.usableAreaM2 ?? (b.has_solar_data ? Number(b.usable_roof_area) : null)
  const roofArea = api?.roofAreaM2 ?? Number(b.footprint_area) ?? null
  const usableRatio = area != null && roofArea ? Math.round((area / roofArea) * 100) : null
  const maxPanels = api?.maxPanels ?? null
  return [
    { label: 'Roof Type',       display: b.roof_type || '—',                                                         raw: null },
    { label: 'Annual kWh',      display: kwh        != null ? Number(kwh).toLocaleString()        + ' kWh' : '—',    raw: kwh        ?? 0 },
    { label: 'Usable Area',     display: area       != null ? Number(area).toFixed(1)              + ' m²'  : '—',    raw: area       ?? 0 },
    { label: 'Usable Ratio',    display: usableRatio != null ? usableRatio                         + '%'    : '—',    raw: usableRatio ?? 0 },
    { label: 'Max Solar Panels',display: maxPanels  != null ? Number(maxPanels).toLocaleString()              : '—',  raw: maxPanels  ?? 0 },
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

function updateCompareHighlight() {
  if (!map) return
  const ids = compareBuildings.value.map(c => c.building.structure_id)
  map.setFilter('building-compare', ['in', ['get', 'structure_id'], ['literal', ids.length ? ids : [-1]]])
}

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
  updateCompareHighlight()
}

function removeFromCompare(idx) {
  compareBuildings.value.splice(idx, 1)
  updateCompareHighlight()
}

function clearCompare() {
  compareBuildings.value = []
  updateCompareHighlight()
}
// Generates a shareable URL for the currently selected building and copies it to clipboard
async function shareBuilding() {
  if (!selectedBuilding.value) {
    showToast('Select a building first')
    return
  }

  const id = selectedBuilding.value.structure_id
  const url = `${window.location.origin}/explore?buildingId=${id}`

  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(url)
      showToast('Shareable link copied!')
      return
    }

    // fallback
    const textArea = document.createElement('textarea')
    textArea.value = url
    textArea.style.position = 'fixed'
    textArea.style.left = '-9999px'
    textArea.style.top = '-9999px'
    document.body.appendChild(textArea)
    textArea.focus()
    textArea.select()

    const success = document.execCommand('copy')
    document.body.removeChild(textArea)

    if (success) {
      showToast('Shareable link copied!')
    } else {
      showToast('Copy failed')
    }
  } catch (err) {
    console.error('Clipboard copy failed:', err)
    showToast('Copy failed')
  }
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
  selectedAddress.value = null
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

    solarApiData.value = await fetchSolarApiData(id)
    selectedAddress.value = solarApiData.value?.address || await fetchAddressForBuilding(id)
  }

  solarApiLoading.value = false
}

function initMap() {
  map = new maplibregl.Map({
    container: 'map',
    style: 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',
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
            'fill-extrusion-color': ['step', ['get', 'solar_score'], MAP_COLORS.solarVeryPoor, 20, MAP_COLORS.solarPoor, 40, MAP_COLORS.solarModerate, 60, MAP_COLORS.solarGood, 80, MAP_COLORS.solarExcellent],
            'fill-extrusion-height': ['coalesce', ['get', 'building_height'], 4],
            'fill-extrusion-base': 0,
            'fill-extrusion-opacity': 0.85,
          },
        })

        // Compare buildings highlight (rendered below selected so selected stays on top)
        map.addLayer({
          id: 'building-compare',
          type: 'fill-extrusion',
          source: 'melbourne-buildings',
          filter: ['in', ['get', 'structure_id'], ['literal', [-1]]],
          paint: {
            'fill-extrusion-color': COMPARE_BUILDING_COLOR,
            'fill-extrusion-height': ['coalesce', ['get', 'building_height'], 4],
            'fill-extrusion-base': 0,
            'fill-extrusion-opacity': COMPARE_BUILDING_OPACITY,
          },
        })

        // Selected building highlight (on top of compare layer)
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
            'line-color': MAP_COLORS.lineStroke,
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
          selectedAddress.value = null
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

          // Fetch solar cache data and address from backend
          const sid = Number(props.structure_id)
          solarApiData.value = await fetchSolarApiData(sid)
          selectedAddress.value = solarApiData.value?.address || await fetchAddressForBuilding(sid)
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
  document.addEventListener('mousedown', onSearchClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('mousedown', onSearchClickOutside)
  if (toastTimer) clearTimeout(toastTimer)
  if (map) {
    map.remove()
    map = null
  }
})
</script>
