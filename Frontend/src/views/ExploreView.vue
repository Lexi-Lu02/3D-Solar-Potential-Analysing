<template>
  <div class="map-page">
    <MainNavbar />

    <!-- Sub-navigation bar for Explore page -->
    <div class="explore-subnav" role="toolbar" aria-label="Explore controls">
      <!-- Right: panel toggles -->
      <div class="subnav-actions">
        <button
          class="subnav-btn"
          :class="{ 'subnav-btn--active': filtersOpen }"
          @click="filtersOpen = !filtersOpen"
          :aria-pressed="filtersOpen"
          aria-label="Toggle map filters"
        >
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
            <path d="M1 3h12M3 7h8M5 11h4" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
          </svg>
          Filter
        </button>
        <button
          class="subnav-btn"
          :class="{ 'subnav-btn--active': comparePanelOpen }"
          @click="comparePanelOpen = !comparePanelOpen"
          :aria-pressed="comparePanelOpen"
          aria-label="Toggle comparison panel"
        >
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
            <rect x="1" y="3" width="5" height="8" rx="1" stroke="currentColor" stroke-width="1.5"/>
            <rect x="8" y="3" width="5" height="8" rx="1" stroke="currentColor" stroke-width="1.5"/>
          </svg>
          Comparison
          <span v-if="compareBuildings.length > 0" class="subnav-badge">{{ compareBuildings.length }}</span>
        </button>
        <button
          class="subnav-btn"
          :class="{ 'subnav-btn--active': sidebarOpen }"
          @click="sidebarOpen = !sidebarOpen"
          :aria-pressed="sidebarOpen"
          aria-label="Toggle building info panel"
        >
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
            <rect x="1" y="1" width="12" height="12" rx="2" stroke="currentColor" stroke-width="1.5"/>
            <path d="M9 1v12" stroke="currentColor" stroke-width="1.5"/>
          </svg>
          Building Info

        <!-- MOD: Sun Path button -->
        <button
          class="subnav-btn"
          :class="{ 'subnav-btn--active': sunPathOpen }"
          @click="sunPathOpen = !sunPathOpen"
          :aria-pressed="sunPathOpen"
          aria-label="Toggle sun path and shadow simulation panel"
        >
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
            <circle cx="7" cy="7" r="2.2" stroke="currentColor" stroke-width="1.4"/>
            <path d="M7 1.2v1.6M7 11.2v1.6M1.2 7h1.6M11.2 7h1.6M2.8 2.8l1.1 1.1M10.1 10.1l1.1 1.1M10.1 3.9l1.1-1.1M2.8 11.2l1.1-1.1" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
          </svg>
          Sun Path
        </button>
      </div>

      <!-- Search by Address -->
      <div class="subnav-search-wrap" ref="searchWrapRef" role="search">
        <label for="search-address" class="visually-hidden">Search buildings by address</label>
        <div class="subnav-search-inner">
          <img :src="iconSearch" alt="" aria-hidden="true" class="subnav-search-icon" />
          <input
            id="search-address"
            v-model="searchId"
            type="text"
            class="subnav-search-input"
            placeholder="Search by address…"
            autocomplete="off"
            role="combobox"
            :aria-expanded="searchResults.length > 0 || searchLoading"
            aria-autocomplete="list"
            aria-controls="search-listbox"
            :aria-activedescendant="searchFocusedIdx >= 0 ? `search-option-${searchFocusedIdx}` : undefined"
            @input="onSearchInput"
            @keydown="onSearchKeydown"
          />
          <button
            class="subnav-search-clear"
            v-if="searchId.length"
            @click="searchId = ''; closeSearchDropdown()"
            aria-label="Clear search"
            type="button"
          >
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true"><path d="M1 1l10 10M11 1L1 11" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>
          </button>
        </div>
        <!-- Dropdown: loading -->
        <ul v-if="searchLoading" class="search-dropdown subnav-dropdown" role="listbox" id="search-listbox">
          <li class="search-dropdown-loading" aria-live="polite">
            <span class="search-loading-dot"></span>
            <span class="search-loading-dot"></span>
            <span class="search-loading-dot"></span>
          </li>
        </ul>
        <!-- Dropdown: results -->
        <ul v-else-if="searchResults.length" class="search-dropdown subnav-dropdown" role="listbox" id="search-listbox" aria-label="Address search results">
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
        <ul v-else-if="searchDropdownOpen && searchId.trim().length >= 2 && !searchLoading" class="search-dropdown subnav-dropdown" role="listbox" id="search-listbox">
          <li class="search-dropdown-empty">No matching addresses found</li>
        </ul>
        <div v-if="searchError" id="search-error-msg" class="search-error subnav-search-error" role="alert" aria-live="assertive">{{ searchError }}</div>
      </div>
    </div>

    <main id="main-content" class="main">
      <div class="map-area">
        <div id="map" role="application" aria-label="Interactive 3D solar map of Melbourne buildings">
          <div v-if="isLoading" class="loading" role="status" aria-live="polite" aria-atomic="true" :aria-label="loadingText">
            <div class="loading-spinner" aria-hidden="true"></div>
            <div class="loading-text">{{ loadingText }}</div>
          </div>
        </div>

        <div v-show="filtersOpen" class="map-controls" role="group" aria-label="Map filters">
          <div class="control-card">
            <!-- Panel header -->
            <div class="filter-panel-header">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
                <path d="M1 3h12M3 7h8M5 11h4" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
              </svg>
              <span class="filter-panel-title">Filters</span>
              <button class="filter-panel-close" @click="filtersOpen = false" aria-label="Close filter panel">
                <svg width="13" height="13" viewBox="0 0 14 14" fill="none" aria-hidden="true">
                  <path d="M10 4l-4 4 4 4" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </button>
            </div>

            <!-- Applied filters -->
            <div v-if="activeFilter !== 'all' || activeSolarFilter !== 'all'" class="applied-filters-section">
              <div class="applied-filters-row">
                <span class="applied-filters-label">Applied filters</span>
                <button class="filter-clear-all" @click="clearAllFilters" aria-label="Clear all filters">
                  Clear all
                  <svg width="10" height="10" viewBox="0 0 10 10" fill="none" aria-hidden="true"><path d="M1 1l8 8M9 1L1 9" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
                </button>
              </div>
              <div class="applied-chips" role="list" aria-label="Active filters">
                <span v-if="activeSolarFilter !== 'all'" class="filter-chip" role="listitem">
                  <span class="filter-chip-dot" :style="{ background: solarTiers.find(t => t.id === activeSolarFilter)?.color }"></span>
                  {{ solarTiers.find(t => t.id === activeSolarFilter)?.label }}
                  <button class="filter-chip-remove" @click="filterSolar(activeSolarFilter)" :aria-label="`Remove ${solarTiers.find(t => t.id === activeSolarFilter)?.label} filter`">×</button>
                </span>
                <span v-if="activeFilter !== 'all'" class="filter-chip" role="listitem">
                  {{ filters.find(f => f.type === activeFilter)?.label }}
                  <button class="filter-chip-remove" @click="filterRoof(activeFilter)" :aria-label="`Remove ${filters.find(f => f.type === activeFilter)?.label} filter`">×</button>
                </span>
              </div>
            </div>

            <!-- Solar Potential section -->
            <div class="filter-section-divider" v-if="activeFilter !== 'all' || activeSolarFilter !== 'all'"></div>
            <button
              class="control-card-toggle"
              @click="solarFilterOpen = !solarFilterOpen"
              :aria-expanded="solarFilterOpen"
              aria-controls="solar-filter-group"
            >
              <span class="control-title">Solar Potential</span>
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

            <!-- Roof Type section -->
            <div class="filter-section-divider"></div>
            <button
              class="control-card-toggle"
              @click="roofFilterOpen = !roofFilterOpen"
              :aria-expanded="roofFilterOpen"
              aria-controls="roof-filter-group"
            >
              <span class="control-title">Roof Type</span>
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
                  <line x1="2" y1="6" x2="26" y2="6" stroke="currentColor" stroke-width="2.5" :stroke-dasharray="f.svgDash || 'none'" stroke-linecap="round"/>
                </svg>
                {{ f.label }}
              </button>
            </div>
          </div>
        </div>

        <!-- MOD: Sun Path panel -->
        <div v-show="sunPathOpen" class="sunpath-controls" role="group" aria-label="Sun path and shadow simulation controls">
          <div class="control-card sunpath-card">
            <div class="filter-panel-header">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
                <circle cx="7" cy="7" r="2.2" stroke="currentColor" stroke-width="1.4"/>
                <path d="M7 1.2v1.6M7 11.2v1.6M1.2 7h1.6M11.2 7h1.6" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
              </svg>
              <span class="filter-panel-title">Sun Path</span>
              <button class="filter-panel-close" @click="sunPathOpen = false" aria-label="Close sun path panel">
                <svg width="13" height="13" viewBox="0 0 14 14" fill="none" aria-hidden="true">
                  <path d="M10 4l-4 4 4 4" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </button>
            </div>

            <div class="sunpath-section">
              <label class="sunpath-label" for="sunpath-season">Season</label>
              <select id="sunpath-season" v-model="sunPathSeason" class="sunpath-select" @change="applySeasonPreset">
                <option value="summer">Summer Solstice</option>
                <option value="equinox">Equinox</option>
                <option value="winter">Winter Solstice</option>
              </select>
            </div>

            <div class="sunpath-section">
              <label class="sunpath-label" for="sunpath-time">
                Time: <strong>{{ formattedSunTime }}</strong>
              </label>
              <input
                id="sunpath-time"
                v-model="sunPathTime"
                class="sunpath-range"
                type="range"
                min="6"
                max="18"
                step="0.5"
                @input="updateSunSimulation"
              />
              <div class="sunpath-range-labels">
                <span>6:00</span>
                <span>12:00</span>
                <span>18:00</span>
              </div>
            </div>

            <div class="sunpath-section sunpath-actions">
              <button class="sunpath-play-btn" @click="toggleSunAnimation">
                {{ sunAnimating ? 'Pause' : 'Play' }}
              </button>
              <button class="sunpath-play-btn sunpath-play-btn--ghost" @click="resetSunSimulation">
                Reset
              </button>
            </div>

            <div class="sunpath-section">
              <div class="sunpath-stat-row">
                <span class="sunpath-stat-label">Sun altitude</span>
                <span class="sunpath-stat-value">{{ sunMetrics.altitude }}°</span>
              </div>
              <div class="sunpath-stat-row">
                <span class="sunpath-stat-label">Sun azimuth</span>
                <span class="sunpath-stat-value">{{ sunMetrics.azimuth }}°</span>
              </div>
              <div class="sunpath-stat-row">
                <span class="sunpath-stat-label">Shadow length factor</span>
                <span class="sunpath-stat-value">{{ sunMetrics.shadowFactor }}</span>
              </div>
            </div>

            <p class="sunpath-help">
              Select a building, then use the slider to simulate sunlight and shadow changes across the day.
            </p>
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
                <button
                  class="compare-add-btn"
                  @click="addToCompare"
                  :disabled="!selectedBuilding || compareBuildings.some(c => c.building.structure_id === selectedBuilding.structure_id)"
                  :class="{ 'compare-add-btn--added': compareBuildings.some(c => c.building.structure_id === selectedBuilding?.structure_id) }"
                  :aria-label="compareBuildings.some(c => c.building.structure_id === selectedBuilding?.structure_id) ? 'Building already in comparison' : 'Add selected building to comparison'"
                >
                  <svg v-if="compareBuildings.some(c => c.building.structure_id === selectedBuilding?.structure_id)" width="13" height="13" viewBox="0 0 13 13" fill="none" aria-hidden="true"><path d="M2 6.5l3.5 3.5 5.5-6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
                  <svg v-else width="13" height="13" viewBox="0 0 13 13" fill="none" aria-hidden="true"><path d="M6.5 2v9M2 6.5h9" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>
                  {{ compareBuildings.some(c => c.building.structure_id === selectedBuilding?.structure_id) ? 'Added to Compare' : 'Add to Compare' }}
                </button>
              </div>
              <button class="comparison-close-btn" @click="comparePanelOpen = false" aria-label="Close comparison panel">
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
                    {{ shortAddress(item.apiData?.address) || '#' + item.building.structure_id }}
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
      </div><!-- end .map-area -->

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
          <div class="sidebar-content">
            <template v-if="activeTab === 'details'">
            <div class="sidebar-header">
              <div class="sidebar-title-row">
                <div class="sidebar-title" id="sidebar-title">Solar Potential</div>
                <button
                  class="sidebar-export-btn"
                  @click="exportBuildingCsv"
                  :disabled="!selectedBuilding"
                  :aria-disabled="!selectedBuilding"
                  aria-label="Export selected building details as CSV"
                >
                  Export CSV
                </button>
              </div>
              <div class="sidebar-sub" aria-live="polite">
                {{ selectedBuilding ? '' : 'Click any building on the map' }}
              </div>
            </div>
            <div v-if="!selectedBuilding" class="empty-state">
              <img :src="iconSolarCell" alt="" class="empty-icon-img" aria-hidden="true" />
              <div class="empty-text">Select a building on the map to view its solar potential analysis</div>
            </div>
            <div v-else class="building-panel visible">
              <div class="panel-id">BUILDING {{ selectedBuilding.structure_id || selectedBuilding.objectid || '—' }}</div>
              <div class="score-bar-wrap">
                <div class="score-header">
                  <span class="score-label-group">
                    <span class="score-label">Solar Score</span>
                    <button
                      class="score-info-btn"
                      @click="scoreExplOpen = !scoreExplOpen"
                      :aria-expanded="scoreExplOpen"
                      aria-label="Toggle solar score explanation"
                    >?</button>
                  </span>
                  <span class="score-value">{{ score }}</span>
                </div>
                <div class="score-bar">
                  <div class="score-fill" :style="{ width: Math.min(100, Math.max(0, score)) + '%', background: tierColor }"></div>
                </div>
                <div class="score-tier" :style="{ color: tierColor }">{{ tier }}</div>
                <Transition name="score-expl">
                  <div v-if="scoreExplOpen" class="score-explanation">
                    Composite of <strong>roof quality</strong> (sunshine intensity per m²)
                    and <strong>energy output</strong> (annual kWh), each normalised 0–100
                    and weighted equally.
                  </div>
                </Transition>
              </div>
              <div class="section-title">Building Info</div>
              <div class="info-row"><span class="info-key">Address</span><span class="info-val">{{ shortAddress(selectedAddress) }}</span></div>
              <div class="info-row"><span class="info-key">Roof Type</span><span class="info-val">{{ selectedBuilding.roof_type || 'Unknown' }}</span></div>
              <div class="info-row"><span class="info-key">Building Height</span><span class="info-val">{{ (selectedBuilding.building_height || 0).toFixed(1) }} m</span></div>
              <div class="info-row">
                <span class="info-key">Usable Ratio</span>
                <span class="info-val">
                  {{ solarApiData?.usableAreaM2 != null && solarApiData?.roofAreaM2 != null
                      ? Math.round(solarApiData.usableAreaM2 / solarApiData.roofAreaM2 * 100) + '%'
                      : (solarApiLoading ? '…' : '—') }}
                </span>
              </div>
              <div class="info-row"><span class="info-key">Max Solar Panels</span><span class="info-val">{{ solarApiData?.maxPanels != null ? solarApiData.maxPanels.toLocaleString() : '—' }}</span></div>
              <div class="metrics-grid">
                <div class="metric-card">
                  <div class="metric-label">Est. Annual Output</div>
                  <div class="metric-val">
                    {{ formulaKwhAnnual > 0
                        ? formulaKwhAnnual.toLocaleString() + ' kWh'
                        : '—' }}
                  </div>
                </div>
                <div class="metric-card">
                  <div class="metric-label">Sun Intensity</div>
                  <div class="metric-val">
                    {{ solarApiData?.sunshineHours != null
                        ? (Math.round(solarApiData.sunshineHours / 365 * 10) / 10).toFixed(1) + ' kWh/m²/day'
                        : (solarApiLoading ? '…' : '—') }}
                  </div>
                </div>
                <div class="metric-card">
                  <div class="metric-label">Roof Footprint</div>
                  <div class="metric-val">
                    {{ solarApiData?.roofAreaM2 != null
                        ? solarApiData.roofAreaM2.toFixed(1) + ' m²'
                        : (solarApiLoading ? '…' : '—') }}
                  </div>
                </div>
                <div class="metric-card">
                  <div class="metric-label">Usable Roof Area</div>
                  <div class="metric-val">
                    {{ solarApiData?.usableAreaM2 != null
                        ? solarApiData.usableAreaM2.toFixed(1) + ' m²'
                        : (solarApiLoading ? '…' : '—') }}
                  </div>
                </div>
              </div>

              <!-- MOD: Sun Path result -->
              <div v-if="selectedBuilding" class="sunpath-summary-card">
                <div class="section-title">Sun Path & Shadow</div>
                <div class="info-row">
                  <span class="info-key">Simulation Date</span>
                  <span class="info-val">{{ selectedSimulationDateLabel }}</span>
                </div>
                <div class="info-row">
                  <span class="info-key">Simulation Time</span>
                  <span class="info-val">{{ formattedSunTime }}</span>
                </div>
                <div class="info-row">
                  <span class="info-key">Sun Altitude</span>
                  <span class="info-val">{{ sunMetrics.altitude }}°</span>
                </div>
                <div class="info-row">
                  <span class="info-key">Sun Azimuth</span>
                  <span class="info-val">{{ sunMetrics.azimuth }}°</span>
                </div>
                <div class="info-row">
                  <span class="info-key">Estimated Shadow Impact</span>
                  <span class="info-val">{{ shadowImpactLabel }}</span>
                </div>
              </div>

              <!-- Formula explanation card -->
              <div v-if="formulaKwhAnnual > 0" class="formula-card">
                <button class="formula-card-toggle" @click="formulaCardOpen = !formulaCardOpen" :aria-expanded="formulaCardOpen">
                  <span class="formula-card-title">How We Calculate Annual Output</span>
                  <svg class="chevron-icon" :class="{ 'chevron-up': formulaCardOpen }" width="13" height="13" viewBox="0 0 14 14" fill="none" aria-hidden="true">
                    <path d="M3 5l4 4 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                </button>
                <Transition name="formula-collapse">
                <div v-if="formulaCardOpen" class="formula-rows">
                  <div class="formula-row">
                    <span class="formula-row-label">Usable Roof Area</span>
                    <span class="formula-row-val">
                      {{ (solarApiData?.usableAreaM2 ?? selectedBuilding?.usable_roof_area ?? 0).toLocaleString(undefined, { maximumFractionDigits: 1 }) }} m²
                    </span>
                  </div>
                  <div class="formula-row formula-row-op">
                    <span class="formula-row-label">Panel Efficiency</span>
                    <span class="formula-row-val">× 20%</span>
                  </div>
                  <div class="formula-row formula-row-op">
                    <span class="formula-row-label">Performance Ratio</span>
                    <span class="formula-row-val">× 75%</span>
                  </div>
                  <div class="formula-row formula-row-op">
                    <span class="formula-row-label">Peak Sun Hours/Day</span>
                    <span class="formula-row-val">
                      × {{ solarApiData?.sunshineHours != null
                            ? (Math.round(solarApiData.sunshineHours / 365 * 10) / 10).toFixed(1) + ' kWh/m²/day'
                            : '4.1 kWh/m²/day' }}
                    </span>
                  </div>
                  <div class="formula-row formula-row-op">
                    <span class="formula-row-label">Days per Year</span>
                    <span class="formula-row-val">× 365</span>
                  </div>
                  <div class="formula-row formula-result">
                    <span class="formula-row-label">Est. Annual Output</span>
                    <span class="formula-row-val">{{ formulaKwhAnnual.toLocaleString() }} kWh</span>
                  </div>
                </div>
                </Transition>
              </div>

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
              <button class="share-btn" @click="shareBuilding">Copy Shareable Link</button>
              <p class="share-btn-desc">Copies a direct link to this building's solar analysis — paste it to share with colleagues or save for later.</p>
            </div>
            </template>
            <template v-else-if="activeTab === 'finance'">
              <div class="sidebar-header">
                <div class="sidebar-title-row">
                  <div class="sidebar-title">Financial Analysis</div>
                  <button
                    class="sidebar-export-btn"
                    @click="exportBuildingCsv"
                    :disabled="!selectedBuilding"
                    :aria-disabled="!selectedBuilding"
                    aria-label="Export building details as CSV"
                  >Export CSV</button>
                </div>
                <div class="sidebar-sub">Estimated returns from solar installation</div>
              </div>

              <!-- No building selected -->
              <div v-if="!selectedBuilding" class="empty-state">
                <img :src="iconProfits" alt="" class="empty-icon-img" aria-hidden="true" />
                <div class="empty-text">Select a building on the map to view financial analysis</div>
              </div>

              <!-- Building selected but no energy data yet -->
              <div v-else-if="formulaKwhAnnual <= 0" class="empty-state">
                <div class="empty-icon">—</div>
                <div class="empty-text">Energy output data unavailable for this building</div>
              </div>

              <!-- Full financial panel -->
              <div v-else class="fin-panel">

                <!-- Payback hero -->
                <div class="fin-hero">
                  <div class="fin-hero-top">
                    <span class="fin-hero-label">Est. Payback Period</span>
                    <div class="fin-tooltip-wrap">
                      <button class="fin-info-btn" aria-label="Payback period assumptions">i</button>
                      <div class="fin-tooltip-box">Simple payback = Installation Cost ÷ Annual Savings. Excludes feed-in tariff, maintenance costs, and panel degradation.</div>
                    </div>
                  </div>
                  <div class="fin-hero-val">
                    {{ financialMetrics?.paybackYears != null ? financialMetrics.paybackYears + ' yrs' : '—' }}
                  </div>
                  <div class="fin-hero-sub">before the system pays for itself</div>
                </div>

                <!-- 4 metric cards -->
                <div class="fin-metrics-grid">

                  <div class="fin-metric-card">
                    <div class="fin-metric-header">
                      <span class="fin-metric-label">Annual Output</span>
                      <div class="fin-tooltip-wrap">
                        <button class="fin-info-btn" aria-label="Annual output assumptions">i</button>
                        <div class="fin-tooltip-box">Usable Roof Area × 20% panel efficiency × 75% performance ratio × peak sun hours × 365 days.</div>
                      </div>
                    </div>
                    <div class="fin-metric-val">{{ financialMetrics.annualKwh.toLocaleString() }}</div>
                    <div class="fin-metric-unit">kWh / yr</div>
                  </div>

                  <div class="fin-metric-card">
                    <div class="fin-metric-header">
                      <span class="fin-metric-label">Installation Cost</span>
                      <div class="fin-tooltip-wrap">
                        <button class="fin-info-btn" aria-label="Installation cost assumptions">i</button>
                        <div class="fin-tooltip-box">Max. panels × 400 W/panel × $1.20/W installed (Melbourne 2024 commercial average).</div>
                      </div>
                    </div>
                    <div class="fin-metric-val">
                      {{ financialMetrics.installCost != null ? '$' + financialMetrics.installCost.toLocaleString() : '—' }}
                    </div>
                    <div class="fin-metric-unit">AUD</div>
                  </div>

                  <div class="fin-metric-card">
                    <div class="fin-metric-header">
                      <span class="fin-metric-label">Annual Savings</span>
                      <div class="fin-tooltip-wrap">
                        <button class="fin-info-btn" aria-label="Annual savings assumptions">i</button>
                        <div class="fin-tooltip-box">Annual Output × $0.28/kWh Melbourne commercial electricity tariff (avoided grid purchase cost).</div>
                      </div>
                    </div>
                    <div class="fin-metric-val">${{ financialMetrics.annualSavings.toLocaleString() }}</div>
                    <div class="fin-metric-unit">AUD / yr</div>
                  </div>

                  <div class="fin-metric-card">
                    <div class="fin-metric-header">
                      <span class="fin-metric-label">Max Solar Panels</span>
                      <div class="fin-tooltip-wrap">
                        <button class="fin-info-btn" aria-label="Panel count source">i</button>
                        <div class="fin-tooltip-box">Maximum panel count sourced from Google Solar API based on usable roof geometry.</div>
                      </div>
                    </div>
                    <div class="fin-metric-val">
                      {{ financialMetrics.maxPanels != null ? financialMetrics.maxPanels.toLocaleString() : '—' }}
                    </div>
                    <div class="fin-metric-unit">panels</div>
                  </div>

                </div>

                <!-- Assumptions note -->
                <div class="fin-assumptions">
                  <div class="fin-assumptions-title">Assumptions</div>
                  <div class="fin-assumption-row"><span>Panel capacity</span><span>400 W each</span></div>
                  <div class="fin-assumption-row"><span>Install cost</span><span>$1.20 / W</span></div>
                  <div class="fin-assumption-row"><span>Electricity tariff</span><span>$0.28 / kWh</span></div>
                  <div class="fin-assumption-row"><span>Panel efficiency</span><span>20%</span></div>
                  <div class="fin-assumption-row"><span>Performance ratio</span><span>75%</span></div>
                </div>

              </div>
            </template>
            <template v-else-if="activeTab === 'env'">
              <div class="sidebar-header">
                <div class="sidebar-title-row">
                  <div class="sidebar-title">Environmental Impact</div>
                  <button
                    class="sidebar-export-btn"
                    @click="exportBuildingCsv"
                    :disabled="!selectedBuilding"
                    :aria-disabled="!selectedBuilding"
                    aria-label="Export building details as CSV"
                  >Export CSV</button>
                </div>
                <div class="sidebar-sub">Estimated sustainability benefits from solar installation</div>
              </div>

              <!-- No building selected -->
              <div v-if="!selectedBuilding" class="empty-state">
                <img :src="iconPlanetEarth" alt="" class="empty-icon-img" aria-hidden="true" />
                <div class="empty-text">Select a building on the map to view environmental impact</div>
              </div>

              <!-- Building selected but no energy data -->
              <div v-else-if="formulaKwhAnnual <= 0" class="empty-state">
                <div class="empty-icon">—</div>
                <div class="empty-text">Energy output data unavailable for this building</div>
              </div>

              <!-- Full environmental panel -->
              <div v-else class="fin-panel">

                <!-- CO₂ hero -->
                <div class="fin-hero fin-hero--green">
                  <div class="fin-hero-top">
                    <span class="fin-hero-label">Est. Annual CO₂ Reduction</span>
                    <div class="fin-tooltip-wrap">
                      <button class="fin-info-btn" aria-label="CO₂ reduction assumptions">i</button>
                      <div class="fin-tooltip-box">Annual Output × 0.79 kg CO₂e/kWh (Australian national grid emission factor, Clean Energy Regulator 2022).</div>
                    </div>
                  </div>
                  <div class="fin-hero-val">
                    {{ envMetrics.co2Kg.toLocaleString() }} <span class="fin-hero-unit">kg CO₂</span>
                  </div>
                  <div class="fin-hero-sub">avoided per year vs. coal-fired grid power</div>
                </div>

                <!-- 6 metric cards -->
                <div class="fin-metrics-grid">

                  <div class="fin-metric-card">
                    <div class="fin-metric-header">
                      <span class="fin-metric-label">Equivalent Trees Planted</span>
                      <div class="fin-tooltip-wrap">
                        <button class="fin-info-btn" aria-label="Trees equivalent assumptions">i</button>
                        <div class="fin-tooltip-box">CO₂ Reduction ÷ 21.77 kg CO₂ absorbed per mature tree per year (U.S. Forest Service average).</div>
                      </div>
                    </div>
                    <div class="fin-metric-val">{{ envMetrics.treesEquiv.toLocaleString() }}</div>
                    <div class="fin-metric-unit">trees / yr</div>
                  </div>

                  <div class="fin-metric-card">
                    <div class="fin-metric-header">
                      <span class="fin-metric-label">Petrol Fuel Saved</span>
                      <div class="fin-tooltip-wrap">
                        <button class="fin-info-btn" aria-label="Fuel savings assumptions">i</button>
                        <div class="fin-tooltip-box">Annual Output ÷ 8.9 kWh/litre energy equivalent of petrol (Australian standard fuel conversion).</div>
                      </div>
                    </div>
                    <div class="fin-metric-val">{{ envMetrics.petrolLitres.toLocaleString() }}</div>
                    <div class="fin-metric-unit">litres / yr</div>
                  </div>

                  <div class="fin-metric-card">
                    <div class="fin-metric-header">
                      <span class="fin-metric-label">Cars Off the Road</span>
                      <div class="fin-tooltip-wrap">
                        <button class="fin-info-btn" aria-label="Cars equivalent assumptions">i</button>
                        <div class="fin-tooltip-box">CO₂ Reduction ÷ 2,100 kg CO₂/yr (average Australian car at 180 g/km × 12,000 km/yr).</div>
                      </div>
                    </div>
                    <div class="fin-metric-val">{{ envMetrics.carsOffRoad.toLocaleString() }}</div>
                    <div class="fin-metric-unit">cars / yr</div>
                  </div>

                  <div class="fin-metric-card">
                    <div class="fin-metric-header">
                      <span class="fin-metric-label">Homes Powered</span>
                      <div class="fin-tooltip-wrap">
                        <button class="fin-info-btn" aria-label="Homes powered assumptions">i</button>
                        <div class="fin-tooltip-box">Annual Output ÷ 7,227 kWh average annual Victorian household consumption (AER 2023).</div>
                      </div>
                    </div>
                    <div class="fin-metric-val">{{ envMetrics.homesPowered.toLocaleString() }}</div>
                    <div class="fin-metric-unit">homes / yr</div>
                  </div>

                  <div class="fin-metric-card env-metric-card--full">
                    <div class="fin-metric-header">
                      <span class="fin-metric-label">Lifetime CO₂ Savings (25 yrs)</span>
                      <div class="fin-tooltip-wrap">
                        <button class="fin-info-btn" aria-label="Lifetime CO₂ assumptions">i</button>
                        <div class="fin-tooltip-box">Annual CO₂ Reduction × 25 years (standard commercial solar panel lifespan), expressed in tonnes.</div>
                      </div>
                    </div>
                    <div class="fin-metric-val">{{ envMetrics.lifetimeCo2T.toLocaleString() }}</div>
                    <div class="fin-metric-unit">tonnes CO₂ over system life</div>
                  </div>

                </div>

                <!-- Conversion assumptions -->
                <div class="fin-assumptions">
                  <div class="fin-assumptions-title">Conversion Factors</div>
                  <div class="fin-assumption-row"><span>Grid emission factor</span><span>0.79 kg CO₂e / kWh</span></div>
                  <div class="fin-assumption-row"><span>Tree CO₂ absorption</span><span>21.77 kg CO₂ / yr</span></div>
                  <div class="fin-assumption-row"><span>Petrol energy equivalent</span><span>8.9 kWh / litre</span></div>
                  <div class="fin-assumption-row"><span>Average car emissions</span><span>2,100 kg CO₂ / yr</span></div>
                  <div class="fin-assumption-row"><span>Vic. household consumption</span><span>7,227 kWh / yr</span></div>
                  <div class="fin-assumption-row"><span>System lifespan</span><span>25 years</span></div>
                </div>

              </div>
            </template>
          </div>
        </div>
        <!-- Vertical section tabs on right edge -->
        <div class="sidebar-tabs-v" role="tablist" aria-label="Sidebar sections">
          <button
            class="sidebar-tab-v"
            :class="{ active: activeTab === 'details' }"
            @click="activeTab = 'details'"
            role="tab"
            :aria-selected="activeTab === 'details'"
            aria-label="Solar Potential"
          ><span>Solar Potential</span></button>
          <button
            class="sidebar-tab-v"
            :class="{ active: activeTab === 'finance' }"
            @click="activeTab = 'finance'"
            role="tab"
            :aria-selected="activeTab === 'finance'"
            aria-label="Financial Analysis"
          ><span>Financial Analysis</span></button>
          <button
            class="sidebar-tab-v"
            :class="{ active: activeTab === 'env' }"
            @click="activeTab = 'env'"
            role="tab"
            :aria-selected="activeTab === 'env'"
            aria-label="Environmental Impact"
          ><span>Environmental Impact</span></button>
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
import iconCompare   from '../pictures/Compare.png'
import iconSearch    from '../pictures/Search.png'
import iconSolarCell from '../pictures/solar-cell.png'
import iconProfits     from '../pictures/profits.png'
import iconPlanetEarth from '../pictures/planet-earth.png'
import { useRoute } from 'vue-router'

const route = useRoute()

const GEOJSON_PATH = import.meta.env.VITE_GEOJSON_URL || '/combined-buildings.geojson'
const PRECINCTS_PATH = import.meta.env.VITE_PRECINCTS_URL || '/melbourne_cbd_precincts.geojson'

// MapLibre GL requires hex values — CSS variables are not supported in GL paint specs.
// These mirror the CSS variables defined in style.css :root for a single source of truth.
const MAP_COLORS = {
  solarExcellent:  '#09332C',
  solarGood:       '#5A9072',
  solarModerate:   '#BED4C7',
  solarPoor:       '#F8AB90',
  solarVeryPoor:   '#F0531C',
  selected:        '#FFD966',
  compare:         '#8CA28F',
  lineStroke:      '#1C1710',
}

const SELECTED_BUILDING_COLOR = MAP_COLORS.selected
const SELECTED_BUILDING_OPACITY = 0.98
const COMPARE_BUILDING_COLOR = MAP_COLORS.compare
const COMPARE_BUILDING_OPACITY = 0.90

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1'
const solarApiCache = new Map()

const isLoading = ref(true)
const loadingText = ref('Loading Melbourne building data...')
const selectedBuilding = ref(null)
const activeFilter = ref('all')
const activeSolarFilter = ref('all')
const toastMessage = ref('')
const toastVisible = ref(false)
const solarApiData = ref(null)
const solarApiLoading = ref(false)
const selectedAddress = ref(null)
const searchId = ref('')
const searchError = ref('')
const searchResults = ref([])
const searchLoading = ref(false)
const searchFocusedIdx = ref(-1)
const searchDropdownOpen = ref(false)
const searchWrapRef = ref(null)
let searchDebounceTimer = null
const sidebarOpen = ref(true)
const filtersOpen = ref(true)
const comparePanelOpen = ref(false)
const solarFilterOpen = ref(true)
const roofFilterOpen = ref(true)
const compareBuildings = ref([])

// MOD: Sun Path state
const sunPathOpen = ref(false)
const sunPathSeason = ref('summer')
const sunPathTime = ref(12)
const sunAnimating = ref(false)
const sunAnimationTimer = ref(null)

const compareVisible = computed(() => comparePanelOpen.value)
const hoveredMonthIdx = ref(null)
const scoreExplOpen = ref(false)
const formulaCardOpen = ref(false)
const activeTab = ref('details')

const formulaKwhAnnual = computed(() => {
  const area = solarApiData.value?.usableAreaM2 || selectedBuilding.value?.usable_roof_area
  if (!area || area <= 0) return 0
  const psh = solarApiData.value?.sunshineHours
  if (psh) return Math.round(area * 0.20 * 0.75 * psh)
  return Math.round(area * 0.20 * 0.75 * 4.1 * 365)
})

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

  const annualKwh = formulaKwhAnnual.value
  if (annualKwh <= 0) return []

  const weights = MONTHLY_PSH.map(({ month, days, psh }) => ({ month, w: psh * days }))
  const totalWeight = weights.reduce((s, m) => s + m.w, 0)
  const months = weights.map(({ month, w }) => ({
    month,
    kwh: Math.round((w / totalWeight) * annualKwh),
  }))
  const maxKwh = Math.max(...months.map(m => m.kwh))
  return months.map(m => ({ ...m, pct: Math.round(m.kwh / maxKwh * 100) }))
})

const COST_PER_WATT_AUD = 1.20
const PANEL_CAPACITY_W  = 400
const TARIFF_AUD_KWH    = 0.28

const GRID_EMISSION_KG_PER_KWH = 0.79   // kg CO₂e/kWh, Australian national avg (Clean Energy Regulator 2022)
const TREE_CO2_KG_PER_YEAR     = 21.77  // kg CO₂ absorbed per mature tree per year (U.S. Forest Service)
const PETROL_KWH_PER_LITRE     = 8.9    // energy equivalent of 1 litre of petrol
const CAR_CO2_KG_PER_YEAR      = 2100   // avg Australian car: 180 g/km × 12,000 km/yr
const VIC_HOME_KWH_PER_YEAR    = 7227   // average Victorian household annual consumption (AER 2023)
const SOLAR_SYSTEM_LIFE_YEARS  = 25     // typical commercial solar panel lifespan

const envMetrics = computed(() => {
  const annualKwh = formulaKwhAnnual.value
  if (!selectedBuilding.value || annualKwh <= 0) return null
  const co2Kg          = Math.round(annualKwh * GRID_EMISSION_KG_PER_KWH)
  const treesEquiv     = Math.round(co2Kg / TREE_CO2_KG_PER_YEAR)
  const petrolLitres   = Math.round(annualKwh / PETROL_KWH_PER_LITRE)
  const carsOffRoad    = Math.round((co2Kg / CAR_CO2_KG_PER_YEAR) * 10) / 10
  const homesPowered   = Math.round((annualKwh / VIC_HOME_KWH_PER_YEAR) * 10) / 10
  const lifetimeCo2T   = Math.round(co2Kg * SOLAR_SYSTEM_LIFE_YEARS / 100) / 10  // tonnes, 1dp
  return { co2Kg, treesEquiv, petrolLitres, carsOffRoad, homesPowered, lifetimeCo2T, annualKwh }
})

const financialMetrics = computed(() => {
  const annualKwh = formulaKwhAnnual.value
  if (!selectedBuilding.value || annualKwh <= 0) return null
  const maxPanels     = solarApiData.value?.maxPanels ?? null
  const installCost   = maxPanels != null ? Math.round(maxPanels * PANEL_CAPACITY_W * COST_PER_WATT_AUD) : null
  const annualSavings = Math.round(annualKwh * TARIFF_AUD_KWH)
  const paybackYears  = installCost && annualSavings > 0 ? Math.round((installCost / annualSavings) * 10) / 10 : null
  return { annualKwh, installCost, annualSavings, paybackYears, maxPanels }
})

let map = null
let toastTimer = null
let compassIdx = 0
let buildingIndex = new Map() // structure_id -> properties

// MOD: full feature index for geometry
let buildingFeatureIndex = new Map()

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

// MOD: Sun Path computed
const selectedSimulationDateLabel = computed(() => {
  if (sunPathSeason.value === 'summer') return '21 Dec'
  if (sunPathSeason.value === 'winter') return '21 Jun'
  return '21 Mar'
})

const formattedSunTime = computed(() => {
  const value = Number(sunPathTime.value)
  const hour = Math.floor(value)
  const minute = value % 1 === 0 ? '00' : '30'
  return `${String(hour).padStart(2, '0')}:${minute}`
})

const MELBOURNE_LAT = -37.8136

function getDayOfYearForSeason(season) {
  if (season === 'summer') return 355
  if (season === 'winter') return 172
  return 80
}

function solarDeclination(dayOfYear) {
  return 23.44 * Math.sin((2 * Math.PI / 365) * (dayOfYear - 81))
}

function calculateSolarPosition(latDeg, dayOfYear, timeHour) {
  const lat = latDeg * Math.PI / 180
  const decl = solarDeclination(dayOfYear) * Math.PI / 180
  const hourAngle = (15 * (timeHour - 12)) * Math.PI / 180

  const sinAlt =
    Math.sin(lat) * Math.sin(decl) +
    Math.cos(lat) * Math.cos(decl) * Math.cos(hourAngle)

  const altitude = Math.asin(sinAlt)

  const cosAz =
    (Math.sin(decl) - Math.sin(altitude) * Math.sin(lat)) /
    (Math.cos(altitude) * Math.cos(lat))

  let azimuth = Math.acos(Math.min(1, Math.max(-1, cosAz))) * 180 / Math.PI
  if (timeHour > 12) azimuth = 360 - azimuth

  return {
    altitude: Math.max(0, altitude * 180 / Math.PI),
    azimuth: Math.round(azimuth),
  }
}

const sunMetrics = computed(() => {
  const dayOfYear = getDayOfYearForSeason(sunPathSeason.value)
  const pos = calculateSolarPosition(MELBOURNE_LAT, dayOfYear, Number(sunPathTime.value))
  const altitude = Math.round(pos.altitude)
  const azimuth = pos.azimuth
  const shadowFactor = altitude > 0 ? (90 / altitude).toFixed(1) : '∞'

  return {
    altitude,
    azimuth,
    shadowFactor,
  }
})

const shadowImpactLabel = computed(() => {
  const altitude = sunMetrics.value.altitude
  if (altitude >= 60) return 'Low'
  if (altitude >= 35) return 'Moderate'
  return 'High'
})

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
      maxPanels: body.max_panels ?? null,
      usableAreaM2: body.max_array_area_m2 != null ? Math.round(body.max_array_area_m2 * 10) / 10 : null,
      roofAreaM2: body.whole_roof_area_m2 != null ? Math.round(body.whole_roof_area_m2 * 10) / 10 : null,
      kwhAnnual: body.max_panels_kwh_annual != null ? Math.round(body.max_panels_kwh_annual) : null,
      sunshineHours: body.max_sunshine_hours_per_year != null ? Math.round(body.max_sunshine_hours_per_year) : null,
      address: body.address || null,
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

function clearAllFilters() {
  activeFilter.value = 'all'
  activeSolarFilter.value = 'all'
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

  // MOD: update sun simulation after search select
  updateSunSimulation()
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

function compareMetrics(item) {
  const b = item.building
  const api = item.apiData
  const kwh = api?.kwhAnnual ?? null
  const area = api?.usableAreaM2 ?? null
  const roofArea = api?.roofAreaM2 ?? null
  const usableRatio = area != null && roofArea ? Math.round((area / roofArea) * 100) : null
  const maxPanels = api?.maxPanels ?? null
  const sunHours = api?.sunshineHours ?? null
  const sunIntensity = sunHours != null && roofArea ? Math.round(sunHours / roofArea * 10) / 10 : null
  return [
    { label: 'Roof Type',        display: b.roof_type || '—',                                                          raw: null },
    { label: 'Sun Hrs / m²',     display: sunIntensity != null ? sunIntensity + ' hrs/m²' : '—',                      raw: sunIntensity ?? 0 },
    { label: 'Annual kWh',       display: kwh != null ? Number(kwh).toLocaleString() + ' kWh' : '—',                 raw: kwh ?? 0 },
    { label: 'Usable Area',      display: area != null ? Number(area).toFixed(1) + ' m²' : '—',                      raw: area ?? 0 },
    { label: 'Usable Ratio',     display: usableRatio != null ? usableRatio + '%' : '—',                              raw: usableRatio ?? 0 },
    { label: 'Max Solar Panels', display: maxPanels != null ? Number(maxPanels).toLocaleString() : '—',               raw: maxPanels ?? 0 },
  ]
}

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
    apiData: solarApiData.value ? { ...solarApiData.value } : null,
  }
  if (compareBuildings.value.length >= 2) compareBuildings.value.shift()
  compareBuildings.value.push(entry)
  comparePanelOpen.value = true
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

function toCsvSafe(value) {
  const stringValue = value == null ? '' : String(value)
  const escaped = stringValue.replace(/"/g, '""')
  return `"${escaped}"`
}

function exportBuildingCsv() {
  if (!selectedBuilding.value) {
    showToast('Select a building first')
    return
  }

  const usableRatio = solarApiData.value?.usableAreaM2 != null && solarApiData.value?.roofAreaM2 != null
    ? Math.round((solarApiData.value.usableAreaM2 / solarApiData.value.roofAreaM2) * 100) + '%'
    : (solarApiLoading.value ? '…' : '—')

  const peakSunHours = solarApiData.value?.sunshineHours != null
    ? (Math.round(solarApiData.value.sunshineHours / 365 * 10) / 10).toFixed(1) + ' kWh/m²/day'
    : (solarApiLoading.value ? '…' : '—')

  const roofFootprint = solarApiData.value?.roofAreaM2 != null
    ? solarApiData.value.roofAreaM2.toFixed(1) + ' m²'
    : (solarApiLoading.value ? '…' : '—')

  const usableRoofArea = solarApiData.value?.usableAreaM2 != null
    ? solarApiData.value.usableAreaM2.toFixed(1) + ' m²'
    : (solarApiLoading.value ? '…' : '—')

  const formulaUsableArea = (solarApiData.value?.usableAreaM2 ?? selectedBuilding.value?.usable_roof_area ?? 0)
    .toLocaleString(undefined, { maximumFractionDigits: 1 }) + ' m²'

  const formulaPeakSun = solarApiData.value?.sunshineHours != null
    ? (Math.round(solarApiData.value.sunshineHours / 365 * 10) / 10).toFixed(1) + ' kWh/m²/day'
    : '4.1 kWh/m²/day'

  const fm = financialMetrics.value
  const em = envMetrics.value

  const rows = [
    ['Field', 'Value'],

    // ── Building Details ──────────────────────────────────────
    ['--- BUILDING DETAILS ---', ''],
    ['Building ID', selectedBuilding.value.structure_id || selectedBuilding.value.objectid || '—'],
    ['Address', shortAddress(selectedAddress.value)],
    ['Solar Score', score.value],
    ['Solar Tier', tier.value],
    ['Solar Score Explanation', 'Composite of roof quality (sunshine intensity per m²) and energy output (annual kWh), each normalised 0–100 and weighted equally.'],
    ['Roof Type', selectedBuilding.value.roof_type || 'Unknown'],
    ['Building Height', (selectedBuilding.value.building_height || 0).toFixed(1) + ' m'],
    ['Usable Ratio', usableRatio],
    ['Max Solar Panels', solarApiData.value?.maxPanels != null ? solarApiData.value.maxPanels.toLocaleString() : '—'],
    ['Est. Annual kWh', formulaKwhAnnual.value > 0 ? formulaKwhAnnual.value.toLocaleString() + ' kWh' : '—'],
    ['Peak Sun Hours/Day', peakSunHours],
    ['Roof Footprint', roofFootprint],
    ['Usable Roof Area', usableRoofArea],
    ['Formula - Usable Roof Area', formulaUsableArea],
    ['Formula - Panel Efficiency', '20%'],
    ['Formula - Performance Ratio', '75%'],
    ['Formula - Peak Sun Hours/Day', formulaPeakSun],
    ['Formula - Days per Year', '365'],
    ['Formula - Est. Annual Output', formulaKwhAnnual.value.toLocaleString() + ' kWh'],
  ]

  if (monthlyOutput.value.length > 0) {
    monthlyOutput.value.forEach((monthData) => {
      rows.push([`Monthly Output - ${monthData.month}`, monthData.kwh.toLocaleString() + ' kWh'])
    })
  } else {
    rows.push(['Monthly Output', 'No solar data available for this building'])
  }

  // ── Financial Analysis ────────────────────────────────────
  rows.push(['--- FINANCIAL ANALYSIS ---', ''])
  if (fm) {
    rows.push(
      ['Est. Payback Period', fm.paybackYears != null ? fm.paybackYears + ' yrs' : '—'],
      ['Annual Solar Output', fm.annualKwh.toLocaleString() + ' kWh'],
      ['Installation Cost', fm.installCost != null ? '$' + fm.installCost.toLocaleString() + ' AUD' : '—'],
      ['Annual Savings', '$' + fm.annualSavings.toLocaleString() + ' AUD'],
      ['Max Solar Panels', fm.maxPanels != null ? fm.maxPanels.toLocaleString() : '—'],
      ['Assumption - Panel Capacity', '400 W/panel'],
      ['Assumption - Install Cost Rate', '$1.20 / W'],
      ['Assumption - Electricity Tariff', '$0.28 / kWh'],
    )
  } else {
    rows.push(['Financial Analysis', 'No data — select a building with solar data'])
  }

  // ── Environmental Impact ──────────────────────────────────
  rows.push(['--- ENVIRONMENTAL IMPACT ---', ''])
  if (em) {
    rows.push(
      ['Annual CO₂ Reduction', em.co2Kg.toLocaleString() + ' kg CO₂/yr'],
      ['Equivalent Trees Planted', em.treesEquiv.toLocaleString() + ' trees/yr'],
      ['Petrol Fuel Saved', em.petrolLitres.toLocaleString() + ' litres/yr'],
      ['Cars Off the Road', em.carsOffRoad.toLocaleString() + ' cars/yr'],
      ['Homes Powered', em.homesPowered.toLocaleString() + ' homes/yr'],
      ['Lifetime CO₂ Savings (25 yrs)', em.lifetimeCo2T.toLocaleString() + ' tonnes CO₂'],
      ['Conversion - Grid Emission Factor', '0.79 kg CO₂e / kWh'],
      ['Conversion - Tree CO₂ Absorption', '21.77 kg CO₂ / yr'],
      ['Conversion - Petrol Energy Equiv.', '8.9 kWh / litre'],
      ['Conversion - Avg. Car Emissions', '2,100 kg CO₂ / yr'],
      ['Conversion - Vic. Household Consumption', '7,227 kWh / yr'],
      ['Conversion - System Lifespan', '25 years'],
    )
  } else {
    rows.push(['Environmental Impact', 'No data — select a building with solar data'])
  }

  const csvText = rows.map((row) => row.map(toCsvSafe).join(',')).join('\n')
  const blob = new Blob([csvText], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const addressPart = shortAddress(selectedAddress.value)
    .replace(/[^a-z0-9]+/gi, '_')
    .replace(/^_+|_+$/g, '')
    .toLowerCase()
  const fileName = `building_${selectedBuilding.value.structure_id || 'details'}${addressPart ? '_' + addressPart : ''}.csv`

  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', fileName)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
  showToast('CSV exported')
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

async function openBuildingFromUrl() {
  const buildingId = route.query.buildingId
  if (!buildingId) return

  const id = Number(buildingId)

  // MOD: buildingIndex stores properties, not full feature
  const props = buildingIndex.get(id)
  if (!props) return

  selectedBuilding.value = props
  solarApiData.value = null
  selectedAddress.value = null
  solarApiLoading.value = true

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

  // MOD: update sun simulation after deep link open
  updateSunSimulation()
}

// MOD: Sun Path controls
function applySeasonPreset() {
  sunPathTime.value = 12
  updateSunSimulation()
}

function resetSunSimulation() {
  sunPathSeason.value = 'summer'
  sunPathTime.value = 12
  stopSunAnimation()
  updateSunSimulation()
}

function toggleSunAnimation() {
  if (sunAnimating.value) {
    stopSunAnimation()
    return
  }

  sunAnimating.value = true
  sunAnimationTimer.value = window.setInterval(() => {
    const next = Number(sunPathTime.value) + 0.5
    sunPathTime.value = next > 18 ? 6 : next
    updateSunSimulation()
  }, 900)
}

function stopSunAnimation() {
  sunAnimating.value = false
  if (sunAnimationTimer.value) {
    clearInterval(sunAnimationTimer.value)
    sunAnimationTimer.value = null
  }
}

// MOD: geometry helpers + map source updater
function getEffectiveBuildingHeight(building) {
  const explicitHeight = Number(building?.building_height)
  if (Number.isFinite(explicitHeight) && explicitHeight > 0) return explicitHeight

  const base = Number(building?.base_height)
  const max = Number(building?.max_elevation)
  if (Number.isFinite(base) && Number.isFinite(max) && max > base) {
    return max - base
  }

  return 20
}

function getShadowLength(height, altitudeDeg) {
  const rad = altitudeDeg * Math.PI / 180
  const tan = Math.tan(rad)
  if (tan <= 0.01) return height * 8
  return Math.min(height / tan, height * 8)
}

function shiftLngLat(lng, lat, dxMeters, dyMeters) {
  const dLat = dyMeters / 111320
  const dLng = dxMeters / (111320 * Math.cos(lat * Math.PI / 180))
  return [lng + dLng, lat + dLat]
}

function buildSunDirectionFeature() {
  if (!selectedBuilding.value?.lng || !selectedBuilding.value?.lat) return null

  const lng = Number(selectedBuilding.value.lng)
  const lat = Number(selectedBuilding.value.lat)
  const az = sunMetrics.value.azimuth

  const lineLengthMeters = 60
  const rad = az * Math.PI / 180
  const dxMeters = Math.sin(rad) * lineLengthMeters
  const dyMeters = Math.cos(rad) * lineLengthMeters
  const [endLng, endLat] = shiftLngLat(lng, lat, dxMeters, dyMeters)

  return {
    type: 'Feature',
    geometry: {
      type: 'LineString',
      coordinates: [
        [lng, lat],
        [endLng, endLat],
      ],
    },
    properties: {},
  }
}

function buildShadowProjectionFeature() {
  if (!selectedBuilding.value?.structure_id) return null

  const feature = buildingFeatureIndex.get(Number(selectedBuilding.value.structure_id))
  if (!feature?.geometry || feature.geometry.type !== 'Polygon') return null

  const ring = feature.geometry.coordinates[0]
  const height = getEffectiveBuildingHeight(selectedBuilding.value)
  const altitude = sunMetrics.value.altitude
  const shadowAzimuth = (sunMetrics.value.azimuth + 180) % 360
  const shadowLength = getShadowLength(height, altitude)

  const rad = shadowAzimuth * Math.PI / 180
  const dxMeters = Math.sin(rad) * shadowLength
  const dyMeters = Math.cos(rad) * shadowLength

  const shiftedRing = ring.map(([lng, lat]) => shiftLngLat(lng, lat, dxMeters, dyMeters))

  return {
    type: 'Feature',
    geometry: {
      type: 'Polygon',
      coordinates: [[
        ...ring,
        ...shiftedRing.slice().reverse(),
        ring[0],
      ]],
    },
    properties: {},
  }
}

function updateSunSimulation() {
  if (!map) return

  const sunFeature = buildSunDirectionFeature()
  const shadowFeature = buildShadowProjectionFeature()

  const sunSource = map.getSource('sun-direction')
  if (sunSource) {
    sunSource.setData({
      type: 'FeatureCollection',
      features: sunFeature ? [sunFeature] : [],
    })
  }

  const shadowSource = map.getSource('shadow-projection')
  if (shadowSource) {
    shadowSource.setData({
      type: 'FeatureCollection',
      features: shadowFeature ? [shadowFeature] : [],
    })
  }
}

// ── Precinct helpers (mirror of PrecinctsView) ────────────────────────────────
function _pBBox(f) {
  const g = f.geometry; if (!g) return null
  const rings = g.type === 'Polygon' ? [g.coordinates[0]] : g.coordinates.map(p => p[0])
  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity
  for (const ring of rings) for (const [x, y] of ring) {
    if (x < minX) minX = x
    if (x > maxX) maxX = x
    if (y < minY) minY = y
    if (y > maxY) maxY = y
  }
  return { minX, maxX, minY, maxY }
}

function _pInRing(px, py, ring) {
  let inside = false
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [xi, yi] = ring[i], [xj, yj] = ring[j]
    if (((yi > py) !== (yj > py)) && (px < ((xj - xi) * (py - yi) / (yj - yi)) + xi)) inside = !inside
  }
  return inside
}

function _pInFeature(px, py, f) {
  const g = f.geometry
  if (!g) return false
  const rings = g.type === 'Polygon' ? [g.coordinates[0]] : g.coordinates.map(p => p[0])
  return rings.some(r => _pInRing(px, py, r))
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

        // MOD: keep both properties index and full feature index
        data.features.forEach(f => {
          buildingIndex.set(Number(f.properties.structure_id), f.properties)
          buildingFeatureIndex.set(Number(f.properties.structure_id), f)
        })

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

        // MOD: Sun Path sources and layers
        map.addSource('sun-direction', {
          type: 'geojson',
          data: {
            type: 'FeatureCollection',
            features: [],
          },
        })

        map.addLayer({
          id: 'sun-direction-line',
          type: 'line',
          source: 'sun-direction',
          paint: {
            'line-color': '#F59E0B',
            'line-width': 3,
            'line-opacity': 0.95,
          },
        })

        map.addSource('shadow-projection', {
          type: 'geojson',
          data: {
            type: 'FeatureCollection',
            features: [],
          },
        })

        map.addLayer({
          id: 'shadow-projection-fill',
          type: 'fill',
          source: 'shadow-projection',
          paint: {
            'fill-color': '#1F2937',
            'fill-opacity': 0.18,
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

        try {
          const pRes = await fetch(PRECINCTS_PATH)
          if (pRes.ok) {
            const precinctData = await pRes.json()
            const pFeatures = precinctData.features
            const bboxes = pFeatures.map(_pBBox)

            const hasData = new Set()
            for (const bf of data.features) {
              if (hasData.size === pFeatures.length) break
              const px = bf.properties.lng, py = bf.properties.lat
              if (!px || !py) continue
              for (let pi = 0; pi < pFeatures.length; pi++) {
                if (hasData.has(pFeatures[pi].properties.precinct_id)) continue
                const bb = bboxes[pi]
                if (!bb || px < bb.minX || px > bb.maxX || py < bb.minY || py > bb.maxY) continue
                if (!_pInFeature(px, py, pFeatures[pi])) continue
                hasData.add(pFeatures[pi].properties.precinct_id)
                break
              }
            }

            map.addSource('melbourne-precincts-explore', { type: 'geojson', data: precinctData })
            map.addLayer({
              id: 'precinct-boundary',
              type: 'line',
              source: 'melbourne-precincts-explore',
              filter: ['in', ['get', 'precinct_id'], ['literal', [...hasData]]],
              paint: {
                'line-color': '#1B5E20',
                'line-width': 1.5,
                'line-opacity': 0.85,
              },
            })
          }
        } catch { /* silently skip if precinct file unavailable */ }

        map.on('click', 'building-extrusion', async (event) => {
          if (!event.features?.length) return
          const props = event.features[0].properties
          selectedBuilding.value = props
          solarApiData.value = null
          selectedAddress.value = null
          solarApiLoading.value = true
          sidebarOpen.value = true

          map.setFilter('building-selected', ['==', ['get', 'structure_id'], Number(props.structure_id)])

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

          const sid = Number(props.structure_id)
          solarApiData.value = await fetchSolarApiData(sid)
          selectedAddress.value = solarApiData.value?.address || await fetchAddressForBuilding(sid)
          solarApiLoading.value = false

          // MOD: update sun simulation after map click
          updateSunSimulation()
        })

        map.on('mouseenter', 'building-extrusion', () => {
          map.getCanvas().style.cursor = 'pointer'
        })
        map.on('mouseleave', 'building-extrusion', () => {
          map.getCanvas().style.cursor = ''
        })

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

  // MOD: stop sun animation timer
  stopSunAnimation()

  if (map) {
    map.remove()
    map = null
  }
})
</script>