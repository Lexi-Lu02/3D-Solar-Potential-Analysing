<template>
  <div class="map-page">
    <MainNavbar />

    <!-- Sub-navigation bar for Explore page -->
    <SubnavToolbar
      :filters-open="filtersOpen"
      :compare-panel-open="comparePanelOpen"
      :sun-path-open="sunPathOpen"
      :sidebar-open="sidebarOpen"
      :compare-count="compareBuildings.length"
      :search-query="searchId"
      :search-results="searchResults"
      :search-loading="searchLoading"
      :search-dropdown-open="searchDropdownOpen"
      :search-focused-idx="searchFocusedIdx"
      :search-error="searchError"
      :icon-search="iconSearch"
      @toggle-filters="filtersOpen = !filtersOpen"
      @toggle-compare="toggleComparePanel"
      @toggle-sun-path="toggleSunPathPanel"
      @toggle-sidebar="sidebarOpen = !sidebarOpen"
      @update:search-query="searchId = $event"
      @search-input="onSearchInput"
      @search-keydown="onSearchKeydown"
      @select-result="selectSearchResult"
      @update:search-focused-idx="searchFocusedIdx = $event"
      @clear-search="searchId = ''; closeSearchDropdown()"
      @close-dropdown="closeSearchDropdown"
    />

    <main id="main-content" class="main">
      <div class="map-area">
        <div id="map" role="application" aria-label="Interactive 3D solar map of Melbourne buildings">
          <div v-if="isLoading" class="loading" role="status" aria-live="polite" aria-atomic="true" :aria-label="loadingText">
            <div class="loading-spinner" aria-hidden="true"></div>
            <div class="loading-text">{{ loadingText }}</div>
          </div>
        </div>

        <FilterPanel
          v-show="filtersOpen"
          :active-filter="activeFilter"
          :active-solar-filter="activeSolarFilter"
          :solar-potential-color-on="solarPotentialColorOn"
          :roof-type-effect-on="roofTypeEffectOn"
          :solar-tiers="solarTiers"
          :filters="filters"
          @close="filtersOpen = false"
          @clear-all="clearAllFilters"
          @filter-solar="filterSolar"
          @filter-roof="filterRoof"
          @toggle-solar-color="toggleSolarPotentialColor"
          @toggle-roof-type="toggleRoofTypeEffect"
        />

        <!-- Updated: Sun Path panel -->
        <div
          v-show="sunPathOpen"
          class="sunpath-controls"
          :class="{ 'sunpath-controls--beside-filters': filtersOpen }"
          role="group"
          aria-label="Sun path and shadow simulation controls"
        >
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
              <div class="sunpath-stat-row">
                <span class="sunpath-stat-label">Rooftop shaded</span>
                <span class="sunpath-stat-value">{{ shadowCoverageLabel }}</span>
              </div>
              <div class="sunpath-stat-row">
                <span class="sunpath-stat-label">Unobstructed usable roof</span>
                <span class="sunpath-stat-value">{{ unobstructedUsableAreaLabel }}</span>
              </div>
            </div>

            <p class="sunpath-help">
              Select a building, then use the slider to simulate sunlight and shadow changes across the day.
            </p>
          </div>
        </div>

        <!-- Comparison panel — slides up from bottom of map area -->
        <Transition name="compare-slide">
          <ComparisonPanel
            v-if="compareVisible"
            :compare-buildings="compareBuildings"
            :selected-building="selectedBuilding"
            :active-panel="activeTab"
            @add="addToCompare"
            @remove="removeFromCompare"
            @clear="clearCompare"
            @close="comparePanelOpen = false"
          />
        </Transition>

        <!-- Sun Path bottom panel -->
        <Transition name="sunpath-slide">
          <div v-if="sunPathOpen" class="sunpath-panel" role="region" aria-label="Sun path and shadow simulation">
            <div class="sunpath-panel-header">
              <div class="sunpath-panel-header-left">
                <svg width="16" height="16" viewBox="0 0 14 14" fill="none" aria-hidden="true" class="sunpath-panel-icon">
                  <circle cx="7" cy="7" r="2.2" stroke="currentColor" stroke-width="1.4"/>
                  <path d="M7 1.2v1.6M7 11.2v1.6M1.2 7h1.6M11.2 7h1.6M2.8 2.8l1.1 1.1M10.1 10.1l1.1 1.1M10.1 3.9l1.1-1.1M2.8 11.2l1.1-1.1" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
                </svg>
                <span class="sunpath-panel-title">Sun Path & Shadow</span>
              </div>
              <button class="comparison-close-btn" @click="sunPathOpen = false" aria-label="Close sun path panel">
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
                  <path d="M2 2l10 10M12 2L2 12" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
                </svg>
              </button>
            </div>
            <div class="sunpath-panel-body">
              <!-- Season + play controls -->
              <div class="sunpath-panel-col">
                <div class="sunpath-panel-col-label">Season</div>
                <select v-model="sunPathSeason" class="sunpath-select" @change="applySeasonPreset" aria-label="Select season">
                  <option value="summer">Summer Solstice</option>
                  <option value="equinox">Equinox</option>
                  <option value="winter">Winter Solstice</option>
                </select>
                <div class="sunpath-actions" style="margin-top:10px">
                  <button class="sunpath-play-btn" @click="toggleSunAnimation">{{ sunAnimating ? 'Pause' : 'Play' }}</button>
                  <button class="sunpath-play-btn sunpath-play-btn--ghost" @click="resetSunSimulation">Reset</button>
                </div>
              </div>
              <!-- Time slider -->
              <div class="sunpath-panel-col sunpath-panel-col--wide">
                <div class="sunpath-panel-col-label">Time: <strong>{{ formattedSunTime }}</strong></div>
                <input
                  v-model="sunPathTime"
                  class="sunpath-range"
                  type="range"
                  min="6"
                  max="18"
                  step="0.5"
                  aria-label="Simulation time"
                  @input="updateSunSimulation"
                />
                <div class="sunpath-range-labels">
                  <span>6:00</span><span>12:00</span><span>18:00</span>
                </div>
              </div>
              <!-- Sun metrics -->
              <div class="sunpath-panel-col">
                <div class="sunpath-panel-col-label">Sun Metrics</div>
                <div class="sunpath-stat-row"><span class="sunpath-stat-label">Date</span><span class="sunpath-stat-value">{{ selectedSimulationDateLabel }}</span></div>
                <div class="sunpath-stat-row"><span class="sunpath-stat-label">Altitude</span><span class="sunpath-stat-value">{{ sunMetrics.altitude }}°</span></div>
                <div class="sunpath-stat-row"><span class="sunpath-stat-label">Azimuth</span><span class="sunpath-stat-value">{{ sunMetrics.azimuth }}°</span></div>
                <div class="sunpath-stat-row"><span class="sunpath-stat-label">Shadow Factor</span><span class="sunpath-stat-value">{{ sunMetrics.shadowFactor }}</span></div>
              </div>
              <!-- Building shadow data (only when a building is selected) -->
              <div v-if="selectedBuilding" class="sunpath-panel-col">
                <div class="sunpath-panel-col-label">Building Shadow</div>
                <div class="sunpath-stat-row"><span class="sunpath-stat-label">Rooftop Shaded</span><span class="sunpath-stat-value">{{ shadowCoverageLabel }}</span></div>
                <div class="sunpath-stat-row"><span class="sunpath-stat-label">Unobstructed Roof</span><span class="sunpath-stat-value">{{ unobstructedUsableAreaLabel }}</span></div>
                <div class="sunpath-stat-row"><span class="sunpath-stat-label">Shadow Impact</span><span class="sunpath-stat-value">{{ shadowImpactLabel }}</span></div>
              </div>
              <div v-else class="sunpath-panel-col sunpath-panel-col--help">
                <p class="sunpath-help" style="margin:0;padding:0;font-size:12px;color:var(--text-muted);line-height:1.5">Select a building on the map to see shadow impact for the current sun position.</p>
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
              <div class="score-bar-wrap" :class="scoreCardClass">
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
                  <span class="score-value" :style="{ color: tierColor }">
                    {{ score !== null ? score.toFixed(1) + ' / 5' : 'No Data' }}
                  </span>
                </div>
                <div class="score-bar">
                  <div class="score-fill" :style="{ width: score !== null ? ((score / 5) * 100) + '%' : '0%', background: tierColor }"></div>
                </div>
                <div class="score-tier" :style="{ color: tierColor }">{{ tier }}</div>
                <Transition name="score-expl">
                  <div v-if="scoreExplOpen" class="score-explanation">
                    Rated <strong>1–5</strong> from the City of Melbourne rooftop solar survey.
                    5 = Excellent, 1 = Very Poor. Shows <strong>No Data</strong> when the
                    building has no survey record.
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
                  <div class="metric-label">Annual Electricity Generation</div>
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

              <!-- Formula explanation card -->
              <FormulaCard
                v-if="formulaKwhAnnual > 0"
                :formula-kwh-annual="formulaKwhAnnual"
                :solar-api-data="solarApiData"
                :selected-building="selectedBuilding"
              />

              <div class="section-title">Monthly Generation</div>
              <MonthlyChart :monthly-output="monthlyOutput" />
              <div class="section-title">Planning Actions</div>
              <div class="planning-actions">
                <button class="planning-action-btn planning-action-btn--primary" @click="shareBuilding">Copy Shareable Link</button>
                <button class="planning-action-btn planning-action-btn--primary" @click="addToCompare">Comparison</button>
                <button class="planning-action-btn planning-action-btn--primary" @click="exportBuildingCsv">Export Report</button>
              </div>
              <p class="planning-actions-note">Copies a direct link to this building's solar analysis — paste it to share with colleagues or save for later.</p>
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
                      <span class="fin-metric-label">Annual Generation</span>
                      <div class="fin-tooltip-wrap">
                        <button class="fin-info-btn" aria-label="Annual output assumptions">i</button>
                        <div class="fin-tooltip-box">Same as Solar Potential panel: Usable Roof Area × 20% efficiency × 75% performance ratio × peak sun hours × 365 days.</div>
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
                        <div class="fin-tooltip-box">Annual Generation × $0.28/kWh Melbourne commercial electricity tariff (avoided grid purchase cost).</div>
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
                  <div class="fin-assumption-row"><span>Panel capacity</span><span>{{ financialMetrics.panelCapacityW }} W each</span></div>
                  <div class="fin-assumption-row"><span>Install cost</span><span>$1.20 / W</span></div>
                  <div class="fin-assumption-row"><span>Electricity tariff</span><span>$0.28 / kWh</span></div>
                  <div class="fin-assumption-row"><span>Panel efficiency</span><span>20%</span></div>
                  <div class="fin-assumption-row"><span>Performance ratio</span><span>75%</span></div>
                </div>

                <div class="section-title">Planning Actions</div>
                <div class="planning-actions">
                  <button class="planning-action-btn planning-action-btn--primary" @click="shareBuilding">Copy Shareable Link</button>
                  <button class="planning-action-btn planning-action-btn--primary" @click="addToCompare">Comparison</button>
                  <button class="planning-action-btn planning-action-btn--primary" @click="exportBuildingCsv">Export Report</button>
                </div>
                <p class="planning-actions-note">Copies a direct link to this building's solar analysis — paste it to share with colleagues or save for later.</p>

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
                      <div class="fin-tooltip-box">Annual Generation × {{ envMetrics.carbonKgPerKwh.toFixed(3) }} kg CO₂e/kWh (sourced from Google Solar API carbon_offset_kg_per_mwh; falls back to 0.79 kg CO₂e/kWh Australian national average).</div>
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
                        <div class="fin-tooltip-box">Annual Generation ÷ 8.9 kWh/litre energy equivalent of petrol (Australian standard fuel conversion).</div>
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
                        <div class="fin-tooltip-box">Annual Generation ÷ 7,227 kWh average annual Victorian household consumption (AER 2023).</div>
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
                  <div class="fin-assumption-row"><span>Grid emission factor</span><span>{{ envMetrics.carbonKgPerKwh.toFixed(3) }} kg CO₂e / kWh</span></div>
                  <div class="fin-assumption-row"><span>Tree CO₂ absorption</span><span>21.77 kg CO₂ / yr</span></div>
                  <div class="fin-assumption-row"><span>Petrol energy equivalent</span><span>8.9 kWh / litre</span></div>
                  <div class="fin-assumption-row"><span>Average car emissions</span><span>2,100 kg CO₂ / yr</span></div>
                  <div class="fin-assumption-row"><span>Vic. household consumption</span><span>7,227 kWh / yr</span></div>
                  <div class="fin-assumption-row"><span>System lifespan</span><span>25 years</span></div>
                </div>

                <div class="section-title">Planning Actions</div>
                <div class="planning-actions">
                  <button class="planning-action-btn planning-action-btn--primary" @click="shareBuilding">Copy Shareable Link</button>
                  <button class="planning-action-btn planning-action-btn--primary" @click="addToCompare">Comparison</button>
                  <button class="planning-action-btn planning-action-btn--primary" @click="exportBuildingCsv">Export Report</button>
                </div>
                <p class="planning-actions-note">Copies a direct link to this building's solar analysis — paste it to share with colleagues or save for later.</p>

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

    <!-- Onboarding overlay — shown on first visit only -->
    <Transition name="onboarding-fade">
      <div v-if="showOnboarding" class="onboarding-overlay" role="dialog" aria-modal="true" aria-labelledby="onboarding-title">
        <div class="onboarding-card">
          <button class="onboarding-skip" @click="dismissOnboarding" aria-label="Skip introduction">✕</button>

          <div class="onboarding-header">
            <div class="onboarding-sun" aria-hidden="true">
              <svg width="40" height="40" viewBox="0 0 14 14" fill="none">
                <circle cx="7" cy="7" r="2.6" stroke="var(--city-light)" stroke-width="1.4"/>
                <path d="M7 1v1.6M7 11.4V13M1 7h1.6M11.4 7H13M2.8 2.8l1.1 1.1M10.1 10.1l1.1 1.1M10.1 3.9l1.1-1.1M2.8 11.2l1.1-1.1" stroke="var(--city-light)" stroke-width="1.2" stroke-linecap="round"/>
              </svg>
            </div>
            <h2 class="onboarding-title" id="onboarding-title">Welcome to SolarMap</h2>
            <p class="onboarding-sub">Explore rooftop solar potential across 19,000 Melbourne CBD buildings — free, open, no sign-up.</p>
          </div>

          <div class="onboarding-steps" role="list" aria-label="Getting started steps">
            <div class="onboarding-step" role="listitem">
              <div class="onboarding-step-num" aria-hidden="true">1</div>
              <div class="onboarding-step-icon" aria-hidden="true">
                <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
                  <path d="M3 6h18M7 12h10M10 18h4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                </svg>
              </div>
              <div class="onboarding-step-label">Filter</div>
              <div class="onboarding-step-desc">Use <strong>Filter</strong> to highlight buildings by solar potential tier or roof type</div>
            </div>

            <div class="onboarding-arrow" aria-hidden="true">→</div>

            <div class="onboarding-step" role="listitem">
              <div class="onboarding-step-num" aria-hidden="true">2</div>
              <div class="onboarding-step-icon" aria-hidden="true">
                <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
                  <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z" stroke="currentColor" stroke-width="2"/>
                  <circle cx="12" cy="9" r="2.5" stroke="currentColor" stroke-width="2"/>
                </svg>
              </div>
              <div class="onboarding-step-label">Click a Building</div>
              <div class="onboarding-step-desc">Click any 3D building on the map to select it and open its solar profile</div>
            </div>

            <div class="onboarding-arrow" aria-hidden="true">→</div>

            <div class="onboarding-step" role="listitem">
              <div class="onboarding-step-num" aria-hidden="true">3</div>
              <div class="onboarding-step-icon" aria-hidden="true">
                <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
                  <rect x="3" y="12" width="4" height="9" rx="1" stroke="currentColor" stroke-width="2"/>
                  <rect x="10" y="7" width="4" height="14" rx="1" stroke="currentColor" stroke-width="2"/>
                  <rect x="17" y="3" width="4" height="18" rx="1" stroke="currentColor" stroke-width="2"/>
                </svg>
              </div>
              <div class="onboarding-step-label">View Estimates</div>
              <div class="onboarding-step-desc">See annual energy output, financial payback, CO₂ savings, and shadow analysis</div>
            </div>
          </div>

          <div class="onboarding-actions">
            <button class="onboarding-cta" @click="dismissOnboarding">Start Exploring →</button>
          </div>
          <p class="onboarding-note">Tip: use the search bar above to jump straight to a street address</p>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script>
export default { name: 'ExploreView' }
</script>

<script setup>
// 3D Explore page — the main interactive map. Renders every Melbourne CBD building
// as a 3D extrusion colour-coded by solar score, and opens a three-panel analysis
// (Solar Potential / Financial / Environmental) when a building is clicked.
import { computed, onMounted, onUnmounted, ref } from 'vue'
import maplibregl from 'maplibre-gl'
import MainNavbar from '../components/MainNavbar.vue'
import MonthlyChart from '../components/MonthlyChart.vue'
import FormulaCard from '../components/FormulaCard.vue'
import SubnavToolbar from '../components/SubnavToolbar.vue'
import ComparisonPanel from '../components/ComparisonPanel.vue'
import FilterPanel from '../components/FilterPanel.vue'
import iconCompare   from '../pictures/Compare.png'
import iconSearch    from '../pictures/Search.png'
import iconSolarCell from '../pictures/solar-cell.png'
import iconProfits     from '../pictures/profits.png'
import iconPlanetEarth from '../pictures/planet-earth.png'
import { useRoute } from 'vue-router'

const route = useRoute()

// URLs come from .env so they can point at the EC2 server in production or a local file in dev.
const GEOJSON_PATH   = import.meta.env.VITE_GEOJSON_URL   || '/combined-buildings.geojson'
const PRECINCTS_PATH = import.meta.env.VITE_PRECINCTS_URL || '/melbourne_cbd_precincts.geojson'

// Fetches a GeoJSON file and validates that the server actually returned JSON (not an HTML error page).
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

// MapLibre paint properties only accept literal hex values — they can't read CSS variables.
// These colours are intentionally kept in sync with the :root palette in style.css.
const MAP_COLORS = {
  solarExcellent:  '#0A2E1F',
  solarGood:       '#5A9060',
  solarModerate:   '#C8D4A0',
  solarPoor:       '#F09090',
  solarVeryPoor:   '#E81040',
  selected:        '#4A90D9',
  compare:         '#8CA28F',
  lineStroke:      '#1C1710',
}

const SELECTED_BUILDING_COLOR = MAP_COLORS.selected
const SELECTED_BUILDING_OPACITY = 0.98
const COMPARE_BUILDING_COLOR = MAP_COLORS.compare
const COMPARE_BUILDING_OPACITY = 0.90
const SOLAR_EXTRUSION_COLOR = ['step', ['get', 'solar_score'], MAP_COLORS.solarVeryPoor, 20, MAP_COLORS.solarPoor, 40, MAP_COLORS.solarModerate, 60, MAP_COLORS.solarGood, 80, MAP_COLORS.solarExcellent]
const SOLAR_DISABLED_EXTRUSION_COLOR = '#DED8CA'

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1'

// In-memory caches keyed by structure_id (or season for sun path).
// Avoids re-fetching the same building data every time the user clicks the same building.
const solarApiCache = new Map()
const yieldCache = new Map()
const shadowImpactCache = new Map()
const sunPathCache = new Map()

// Fixed calendar dates used for the three sun simulation seasons.
const SUN_PATH_DATES = {
  summer: '2025-12-21',
  equinox: '2025-03-21',
  winter: '2025-06-21',
}
const NEARBY_SHADOW_RADIUS_M = 260

const isLoading = ref(true)
const loadingText = ref('Loading Melbourne building data...')
const selectedBuilding = ref(null)
const activeFilter = ref('all')
const activeSolarFilter = ref('all')
const solarPotentialColorOn = ref(true)
const roofTypeEffectOn = ref(true)
const toastMessage = ref('')
const toastVisible = ref(false)
const solarApiData = ref(null)
const yieldData = ref(null)
const solarApiLoading = ref(false)
const selectedAddress = ref(null)
const searchId = ref('')
const searchError = ref('')
const searchResults = ref([])
const searchLoading = ref(false)
const searchFocusedIdx = ref(-1)
const searchDropdownOpen = ref(false)
let searchDebounceTimer = null
const hasOnboarded = localStorage.getItem('SOLARMAP_ONBOARDED')
const showOnboarding = ref(!hasOnboarded)
const sidebarOpen = ref(!!hasOnboarded)
const filtersOpen = ref(!!hasOnboarded)
const comparePanelOpen = ref(false)
const compareBuildings = ref([])

// Updated: Sun Path state
const sunPathOpen = ref(false)
const sunPathSeason = ref('summer')
const sunPathTime = ref(12)
const sunAnimating = ref(false)
const sunAnimationTimer = ref(null)
const shadowCoveragePct = ref(0)
const shadowCasterCount = ref(0)
const shadowOverlayFeatures = ref([])
const unobstructedUsableAreaM2 = ref(null)

const compareVisible = computed(() => comparePanelOpen.value)
const scoreExplOpen = ref(false)
const activeTab = ref('details')

// kWh estimate with three fallback tiers, because not every building has every data source:
//   1. Backend yield API — from the City of Melbourne rooftop solar survey (~31% of buildings)
//   2. GeoJSON kwh_annual — also survey data, embedded in the map file
//   3. Formula: usable area × 20% panel efficiency × 75% system losses × peak sun hours
const formulaKwhAnnual = computed(() => {
  if (yieldData.value?.kwh_annual > 0) return yieldData.value.kwh_annual
  if (selectedBuilding.value?.kwh_annual > 0) return Number(selectedBuilding.value.kwh_annual)
  const area = solarApiData.value?.usableAreaM2
  if (!area || area <= 0) return 0
  const psh = solarApiData.value?.sunshineHours
  if (psh) return Math.round(area * 0.20 * 0.75 * psh)
  return Math.round(area * 0.20 * 0.75 * 4.1 * 365)
})

// Monthly peak sun hours for Melbourne from NASA POWER, used to split annual kWh into
// a per-month breakdown when the backend doesn't have actual monthly survey data.
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
  // Priority 1: per-month kWh direct from backend yield API
  const apiMonths = yieldData.value?.kwh_monthly
  if (apiMonths?.length) {
    const maxKwh = Math.max(...apiMonths.map(m => m.kwh))
    return apiMonths.map(m => ({ ...m, pct: Math.round(m.kwh / maxKwh * 100) }))
  }
  // Priority 2: distribute formulaKwhAnnual proportionally using NASA POWER PSH weights
  const annualKwh = formulaKwhAnnual.value
  if (!annualKwh || annualKwh <= 0) return []
  const weights = MONTHLY_PSH.map(({ month, days, psh }) => ({ month, w: psh * days }))
  const totalWeight = weights.reduce((s, m) => s + m.w, 0)
  const months = weights.map(({ month, w }) => ({
    month,
    kwh: Math.round((w / totalWeight) * annualKwh),
  }))
  const maxKwh = Math.max(...months.map(m => m.kwh))
  return months.map(m => ({ ...m, pct: Math.round(m.kwh / maxKwh * 100) }))
})

// Financial constants — Melbourne 2024 commercial averages used for the payback calculation.
const COST_PER_WATT_AUD = 1.20   // installed cost per watt (AUD)
const PANEL_CAPACITY_W  = 400    // standard panel wattage used when Google Solar API doesn't specify
const TARIFF_AUD_KWH    = 0.28   // electricity tariff (avoided cost per kWh)

// Environmental conversion factors — sources noted inline, used for the Impact panel.
const GRID_EMISSION_KG_PER_KWH = 0.79   // kg CO₂e/kWh, Australian national avg (Clean Energy Regulator 2022)
const TREE_CO2_KG_PER_YEAR     = 21.77  // kg CO₂ absorbed per mature tree per year (U.S. Forest Service)
const PETROL_KWH_PER_LITRE     = 8.9    // energy equivalent of 1 litre of petrol
const CAR_CO2_KG_PER_YEAR      = 2100   // avg Australian car: 180 g/km × 12,000 km/yr
const VIC_HOME_KWH_PER_YEAR    = 7227   // average Victorian household annual consumption (AER 2023)
const SOLAR_SYSTEM_LIFE_YEARS  = 25     // typical commercial solar panel lifespan

const envMetrics = computed(() => {
  const annualKwh = formulaKwhAnnual.value
  if (!selectedBuilding.value || annualKwh <= 0) return null
  // Use building-specific carbon offset factor from Google Solar API (kg/MWh → kg/kWh ÷ 1000)
  // Falls back to Australian national grid average when not available
  const carbonKgPerKwh  = solarApiData.value?.carbonOffsetKgPerMwh != null
    ? solarApiData.value.carbonOffsetKgPerMwh / 1000
    : GRID_EMISSION_KG_PER_KWH
  const co2Kg          = Math.round(annualKwh * carbonKgPerKwh)
  const treesEquiv     = Math.round(co2Kg / TREE_CO2_KG_PER_YEAR)
  const petrolLitres   = Math.round(annualKwh / PETROL_KWH_PER_LITRE)
  const carsOffRoad    = Math.round((co2Kg / CAR_CO2_KG_PER_YEAR) * 10) / 10
  const homesPowered   = Math.round((annualKwh / VIC_HOME_KWH_PER_YEAR) * 10) / 10
  const lifetimeCo2T   = Math.round(co2Kg * SOLAR_SYSTEM_LIFE_YEARS / 100) / 10  // tonnes, 1dp
  return { co2Kg, treesEquiv, petrolLitres, carsOffRoad, homesPowered, lifetimeCo2T, annualKwh, carbonKgPerKwh }
})

const financialMetrics = computed(() => {
  if (!selectedBuilding.value) return null
  const annualKwh = formulaKwhAnnual.value
  if (!annualKwh || annualKwh <= 0) return null
  const maxPanels       = solarApiData.value?.maxPanels ?? null
  const panelCapacityW  = solarApiData.value?.panelCapacityWatts ?? PANEL_CAPACITY_W
  const installCost     = maxPanels != null ? Math.round(maxPanels * panelCapacityW * COST_PER_WATT_AUD) : null
  const annualSavings = Math.round(annualKwh * TARIFF_AUD_KWH)
  const paybackYears  = installCost && annualSavings > 0 ? Math.round((installCost / annualSavings) * 10) / 10 : null
  return { annualKwh, installCost, annualSavings, paybackYears, maxPanels, panelCapacityW }
})

let map = null
let toastTimer = null
let compassIdx = 0
// Quick lookup tables built once when GeoJSON loads — avoids scanning all 40k features on every click.
let buildingIndex = new Map()        // structure_id → properties (for the sidebar panels)
let buildingFeatureIndex = new Map() // structure_id → full GeoJSON feature (needed for shadow geometry)

const COMPASS_BEARINGS = [0, 45, 90, 135, 180, 225, 270, 315]
const filters = [
  { type: 'Flat', label: 'Flat Roofs', pattern: 'flat', patternId: 'roof-pattern-flat' },
  { type: 'Hip', label: 'Hip Roofs', pattern: 'diagonal', patternId: 'roof-pattern-hip' },
  { type: 'Gable', label: 'Gable Roofs', pattern: 'cross', patternId: 'roof-pattern-gable' },
  { type: 'Pyramid', label: 'Pyramid Roofs', pattern: 'triangles', patternId: 'roof-pattern-pyramid' },
  { type: 'Shed', label: 'Shed Roofs', pattern: 'horizontal', patternId: 'roof-pattern-shed' },
]
const ROOF_TYPES = ['Flat', 'Hip', 'Gable', 'Pyramid', 'Shed']

const solarTiers = [
  { id: 'very-high', label: 'Excellent',  range: '4.5-5',   color: MAP_COLORS.solarExcellent, min: 80, max: null, bars: 5 },
  { id: 'high',      label: 'Good',       range: '3.5-4.4', color: MAP_COLORS.solarGood,      min: 60, max: 80,   bars: 4 },
  { id: 'medium',    label: 'Moderate',   range: '2.5-3.4', color: MAP_COLORS.solarModerate,  min: 40, max: 60,   bars: 3 },
  { id: 'low',       label: 'Poor',       range: '1.5-2.4', color: MAP_COLORS.solarPoor,      min: 20, max: 40,   bars: 2 },
  { id: 'very-low',  label: 'Very Poor',  range: '1-1.4',   color: MAP_COLORS.solarVeryPoor,  min: 0,  max: 20,   bars: 1 },
]

// solar_score_avg from rooftop_solar survey: 1 (worst) to 5 (best), null when no survey data.
const score = computed(() => {
  if (!selectedBuilding.value) return null
  return yieldData.value?.solar_score_avg ?? null
})

const tier = computed(() => {
  const s = score.value
  if (s === null) return 'No Data'
  if (s >= 4.5) return 'Excellent'
  if (s >= 3.5) return 'Good'
  if (s >= 2.5) return 'Moderate'
  if (s >= 1.5) return 'Poor'
  return 'Very Poor'
})

const tierColor = computed(() => {
  const s = score.value
  if (s === null) return 'var(--text-secondary)'
  if (s >= 4.5) return 'var(--solar-very-high)'
  if (s >= 3.5) return 'var(--solar-high)'
  if (s >= 2.5) return 'var(--solar-med)'
  if (s >= 1.5) return 'var(--solar-low)'
  return 'var(--solar-very-low)'
})

const scoreCardClass = computed(() => {
  const s = score.value
  // Light tier colors (Moderate/Poor) need a darker surface for contrast.
  const usesLightTierColor = s !== null && s >= 1.5 && s < 3.5
  return usesLightTierColor ? 'score-bar-wrap--light-tier' : 'score-bar-wrap--dark-tier'
})

// Updated: Sun Path computed
const formattedSunTime = computed(() => {
  const value = Number(sunPathTime.value)
  const hour = Math.floor(value)
  const minute = value % 1 === 0 ? '00' : '30'
  return `${String(hour).padStart(2, '0')}:${minute}`
})

const selectedSimulationDateLabel = computed(() => {
  if (sunPathSeason.value === 'summer') return '21 Dec'
  if (sunPathSeason.value === 'winter') return '21 Jun'
  return '21 Mar'
})

// Updated: Current sun data returned by the backend Sun Path API.
const currentSunData = ref({
  hour: 12,
  altitude_deg: 0,
  azimuth_deg: 0,
  shadow_factor: null,
})

// Updated: Display backend sun API values in the UI.
const sunMetrics = computed(() => {
  const altitude = Math.round(Number(currentSunData.value?.altitude_deg || 0))
  const azimuth = Math.round(Number(currentSunData.value?.azimuth_deg || 0))
  const factor = currentSunData.value?.shadow_factor

  return {
    altitude,
    azimuth,
    shadowFactor: factor == null ? '∞' : Number(factor).toFixed(1),
  }
})

const shadowCoverageLabel = computed(() => {
  if (!selectedBuilding.value) return 'Select a building'
  return `${Math.round(shadowCoveragePct.value)}%`
})

const unobstructedUsableAreaLabel = computed(() => {
  if (!selectedBuilding.value) return 'Select a building'
  if (unobstructedUsableAreaM2.value == null) return 'Calculating...'
  return `${Number(unobstructedUsableAreaM2.value).toFixed(1)} m²`
})

const shadowImpactLabel = computed(() => {
  if (!selectedBuilding.value) return 'Select a building'

  const coverage = Number(shadowCoveragePct.value || 0)
  if (coverage < 10) return 'Low'
  if (coverage < 35) return 'Moderate'
  return 'High'
})

// Loads a full day's sun position data from the backend for one of the three seasons.
// Caches in memory (Map) and also in sessionStorage so a page refresh doesn't re-fetch.
async function fetchSunPath(season) {
  const date = SUN_PATH_DATES[season] || SUN_PATH_DATES.summer
  const cacheKey = `sun_path_${season}`

  if (sunPathCache.has(cacheKey)) return sunPathCache.get(cacheKey)

  const cached = sessionStorage.getItem(cacheKey)
  if (cached) {
    const parsed = JSON.parse(cached)
    sunPathCache.set(cacheKey, parsed)
    return parsed
  }

  const res = await fetch(`${API_BASE}/sun/path?date=${encodeURIComponent(date)}`)

  if (!res.ok) {
    throw new Error(`Failed to fetch sun path: ${res.status}`)
  }

  const data = await res.json()
  sessionStorage.setItem(cacheKey, JSON.stringify(data))
  sunPathCache.set(cacheKey, data)

  return data
}

async function fetchShadowImpact(structureId, season, hour) {
  const date = SUN_PATH_DATES[season] || SUN_PATH_DATES.summer
  const normalizedHour = Number(hour)
  const cacheKey = `shadow_${structureId}_${date}_${normalizedHour}`

  if (shadowImpactCache.has(cacheKey)) return shadowImpactCache.get(cacheKey)

  const params = new URLSearchParams({
    date,
    hour: String(normalizedHour),
  })
  const res = await fetch(`${API_BASE}/buildings/by-structure/${structureId}/shadow-impact?${params}`)

  if (res.status === 404) {
    shadowImpactCache.set(cacheKey, null)
    return null
  }

  if (!res.ok) {
    throw new Error(`Failed to fetch shadow impact: ${res.status}`)
  }

  const data = await res.json()
  shadowImpactCache.set(cacheKey, data)
  return data
}

// Fetches Google Solar API data for a building from the backend cache table.
// Returns null if the building has no cached entry (saves the 404 from bubbling up as an error).
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
      panelCapacityWatts: body.panel_capacity_watts ?? null,
      carbonOffsetKgPerMwh: body.carbon_offset_kg_per_mwh ?? null,
      address: body.address || null,
    }
    solarApiCache.set(structureId, result)
    return result
  } catch {
    solarApiCache.set(structureId, null)
    return null
  }
}

// Updated: Pick the closest backend sample for the current slider time.
function findClosestSunSample(samples, hour) {
  if (!Array.isArray(samples) || samples.length === 0) return null

  return samples.reduce((closest, item) => {
    return Math.abs(Number(item.hour) - hour) < Math.abs(Number(closest.hour) - hour)
      ? item
      : closest
  }, samples[0])
}

async function fetchYieldData(structureId) {
  if (yieldCache.has(structureId)) return yieldCache.get(structureId)
  try {
    const res = await fetch(`${API_BASE}/buildings/structure/${structureId}/yield`)
    if (!res.ok) { yieldCache.set(structureId, null); return null }
    const body = await res.json()
    yieldCache.set(structureId, body)
    return body
  } catch {
    yieldCache.set(structureId, null)
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

// Builds a MapLibre filter expression that combines the active roof type and solar tier filters.
// Returns null when no filters are active (tells MapLibre to show all buildings).
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

// Draws a small texture onto a canvas and returns it as image data for MapLibre to use
// as a fill pattern on roof-type overlay layers (each roof type gets a distinct hatching style).
function createRoofPatternImage(pattern) {
  const size = 32
  const canvas = document.createElement('canvas')
  canvas.width = size
  canvas.height = size
  const ctx = canvas.getContext('2d')

  ctx.clearRect(0, 0, size, size)
  ctx.strokeStyle = 'rgba(17, 24, 39, 0.62)'
  ctx.fillStyle = 'rgba(17, 24, 39, 0.62)'
  ctx.lineWidth = 3
  ctx.lineCap = 'round'

  if (pattern === 'flat') {
    ctx.fillRect(6, 6, 5, 5)
    ctx.fillRect(22, 22, 5, 5)
  } else if (pattern === 'diagonal') {
    for (let x = -size; x <= size * 2; x += 12) {
      ctx.beginPath()
      ctx.moveTo(x, size)
      ctx.lineTo(x + size, 0)
      ctx.stroke()
    }
  } else if (pattern === 'cross') {
    for (let x = -size; x <= size * 2; x += 14) {
      ctx.beginPath()
      ctx.moveTo(x, size)
      ctx.lineTo(x + size, 0)
      ctx.stroke()
      ctx.beginPath()
      ctx.moveTo(x, 0)
      ctx.lineTo(x + size, size)
      ctx.stroke()
    }
  } else if (pattern === 'triangles') {
    for (let y = 7; y < size; y += 12) {
      for (let x = 7; x < size; x += 12) {
        ctx.beginPath()
        ctx.moveTo(x, y - 3)
        ctx.lineTo(x + 3, y + 2.5)
        ctx.lineTo(x - 3, y + 2.5)
        ctx.closePath()
        ctx.fill()
      }
    }
  } else if (pattern === 'horizontal') {
    for (let y = 6; y < size; y += 10) {
      ctx.beginPath()
      ctx.moveTo(2, y)
      ctx.lineTo(size - 2, y)
      ctx.stroke()
    }
  }

  return ctx.getImageData(0, 0, size, size)
}

function addRoofTypePatternImages() {
  filters.forEach((roofFilter) => {
    if (map.hasImage?.(roofFilter.patternId)) return
    map.addImage(roofFilter.patternId, createRoofPatternImage(roofFilter.pattern), { pixelRatio: 2 })
  })
}

function roofTypeLayerVisible(roofType) {
  return roofTypeEffectOn.value && (activeFilter.value === 'all' || activeFilter.value === roofType)
}

function applyRoofTypeEffect() {
  if (!map?.getLayer('building-extrusion')) return

  map.setPaintProperty(
    'building-extrusion',
    'fill-extrusion-color',
    solarPotentialColorOn.value ? SOLAR_EXTRUSION_COLOR : SOLAR_DISABLED_EXTRUSION_COLOR
  )

  ROOF_TYPES.forEach((roofType) => {
    const visible = roofTypeLayerVisible(roofType)
    const filter = buildCombinedFilter(roofType, activeSolarFilter.value)

    if (map.getLayer(`roof-pattern-${roofType}`)) {
      map.setLayoutProperty(`roof-pattern-${roofType}`, 'visibility', visible ? 'visible' : 'none')
      if (visible) map.setFilter(`roof-pattern-${roofType}`, filter)
    }

    if (map.getLayer(`roof-outline-${roofType}`)) {
      map.setLayoutProperty(`roof-outline-${roofType}`, 'visibility', visible ? 'visible' : 'none')
      if (visible) map.setFilter(`roof-outline-${roofType}`, filter)
    }
  })
}

function applyFilters() {
  if (!map) return
  map.setFilter('building-extrusion', buildCombinedFilter(activeFilter.value, activeSolarFilter.value))
  applyRoofTypeEffect()
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

function dismissOnboarding() {
  showOnboarding.value = false
  localStorage.setItem('SOLARMAP_ONBOARDED', '1')
  filtersOpen.value = true
}

function toggleComparePanel() {
  comparePanelOpen.value = !comparePanelOpen.value
  if (comparePanelOpen.value) sunPathOpen.value = false
}

function toggleSunPathPanel() {
  sunPathOpen.value = !sunPathOpen.value
  if (sunPathOpen.value) comparePanelOpen.value = false
}

function toggleSolarPotentialColor() {
  solarPotentialColorOn.value = !solarPotentialColorOn.value
  applyRoofTypeEffect()
  showToast(`Solar potential colors ${solarPotentialColorOn.value ? 'on' : 'off'}`)
}

function toggleRoofTypeEffect() {
  roofTypeEffectOn.value = !roofTypeEffectOn.value
  applyRoofTypeEffect()
  showToast(`Roof type styling ${roofTypeEffectOn.value ? 'on' : 'off'}`)
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
  yieldData.value = null
  selectedAddress.value = result.address || null
  solarApiLoading.value = true

  if (map) {
    updateHighlights()
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

  ;[solarApiData.value, yieldData.value] = await Promise.all([
    fetchSolarApiData(sid),
    fetchYieldData(sid),
  ])
  if (!selectedAddress.value) {
    selectedAddress.value = solarApiData.value?.address || await fetchAddressForBuilding(sid)
  }
  solarApiLoading.value = false

  // Updated: update sun simulation after search select
  updateSunSimulation()
}


function updateCompareHighlight() {
  if (!map) return
  const ids = compareBuildings.value.map(c => c.building.structure_id)
  map.setFilter('building-compare', ['in', ['get', 'structure_id'], ['literal', ids.length ? ids : [-1]]])
  updateHighlights()
}

function updateHighlights() {
  if (!map) return
  const ids = new Set()
  if (selectedBuilding.value) ids.add(Number(selectedBuilding.value.structure_id))
  for (const c of compareBuildings.value) ids.add(Number(c.building.structure_id))
  const idArr = [...ids]
  map.setFilter('building-selected',
    idArr.length > 0
      ? ['in', ['get', 'structure_id'], ['literal', idArr]]
      : ['==', ['get', 'structure_id'], -1]
  )
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
    analysis: {
      solar: {
        annualKwh: formulaKwhAnnual.value > 0 ? formulaKwhAnnual.value : null,
        usableAreaM2: solarApiData.value?.usableAreaM2 ?? null,
        roofAreaM2: solarApiData.value?.roofAreaM2 ?? null,
        sunshineHours: solarApiData.value?.sunshineHours ?? null,
      },
      finance: financialMetrics.value
        ? { ...financialMetrics.value }
        : null,
      env: envMetrics.value
        ? { ...envMetrics.value }
        : null,
    },
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
    ['Solar Score (1–5)', score.value !== null ? score.value.toFixed(1) : 'No Data'],
    ['Solar Tier', tier.value],
    ['Solar Score Explanation', 'Rated 1–5 from the City of Melbourne rooftop solar survey. 5 = Excellent, 1 = Very Poor.'],
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
    ['Formula - Annual Electricity Generation', formulaKwhAnnual.value.toLocaleString() + ' kWh'],
  ]

  if (monthlyOutput.value.length > 0) {
    monthlyOutput.value.forEach((monthData) => {
      rows.push([`Monthly Generation - ${monthData.month}`, monthData.kwh.toLocaleString() + ' kWh'])
    })
  } else {
    rows.push(['Monthly Generation', 'No solar data available for this building'])
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

  // Updated: buildingIndex stores properties, not full feature
  const props = buildingIndex.get(id)
  if (!props) return

  selectedBuilding.value = props
  solarApiData.value = null
  yieldData.value = null
  selectedAddress.value = null
  solarApiLoading.value = true

  if (map) {
    updateHighlights()

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

    ;[solarApiData.value, yieldData.value] = await Promise.all([
      fetchSolarApiData(id),
      fetchYieldData(id),
    ])
    selectedAddress.value = solarApiData.value?.address || await fetchAddressForBuilding(id)
  }

  solarApiLoading.value = false

  // Updated: update sun simulation after deep link open
  await updateSunSimulation()
}

// Updated: Sun Path controls
async function applySeasonPreset() {
  sunPathTime.value = 12
  await updateSunSimulation()
}

async function resetSunSimulation() {
  sunPathSeason.value = 'summer'
  sunPathTime.value = 12
  stopSunAnimation()
  await updateSunSimulation()
}

function toggleSunAnimation() {
  if (sunAnimating.value) {
    stopSunAnimation()
    return
  }

  sunAnimating.value = true
  sunAnimationTimer.value = window.setInterval(async () => {
    const next = Number(sunPathTime.value) + 0.5
    sunPathTime.value = next > 18 ? 6 : next
    await updateSunSimulation()
  }, 900)
}

function stopSunAnimation() {
  sunAnimating.value = false
  if (sunAnimationTimer.value) {
    clearInterval(sunAnimationTimer.value)
    sunAnimationTimer.value = null
  }
}

// Updated: geometry helpers + map source updater
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

function getShadowLengthByHeightDifference(casterHeight, receiverHeight = 0) {
  const altitude = Number(currentSunData.value?.altitude_deg || 0)
  if (altitude <= 0) return 0

  const heightDiff = Math.max(0, casterHeight - receiverHeight)
  if (heightDiff <= 0) return 0

  const rad = altitude * Math.PI / 180
  const tan = Math.tan(rad)
  if (tan <= 0.01) return casterHeight * 8

  return Math.min(heightDiff / tan, casterHeight * 8)
}

function shiftLngLat(lng, lat, dxMeters, dyMeters) {
  const dLat = dyMeters / 111320
  const dLng = dxMeters / (111320 * Math.cos(lat * Math.PI / 180))
  return [lng + dLng, lat + dLat]
}

function getPolygonRings(geometry) {
  if (!geometry) return []
  if (geometry.type === 'Polygon') return geometry.coordinates.map((ring) => ring)
  if (geometry.type === 'MultiPolygon') return geometry.coordinates.flatMap((poly) => poly.map((ring) => ring))
  return []
}

function getMainOuterRing(geometry) {
  const rings = getPolygonRings(geometry)
  return rings.length ? rings[0] : null
}

function getFeatureCenter(feature) {
  const ring = getMainOuterRing(feature?.geometry)
  if (!ring?.length) return null

  let lngSum = 0
  let latSum = 0

  ring.forEach(([lng, lat]) => {
    lngSum += Number(lng)
    latSum += Number(lat)
  })

  return [lngSum / ring.length, latSum / ring.length]
}

function pointInRing(point, ring) {
  const [px, py] = point
  let inside = false

  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [xi, yi] = ring[i]
    const [xj, yj] = ring[j]
    const intersects =
      ((yi > py) !== (yj > py)) &&
      (px < ((xj - xi) * (py - yi)) / (yj - yi + 0.0000000001) + xi)

    if (intersects) inside = !inside
  }

  return inside
}

function bboxFromRing(ring) {
  let minLng = Infinity
  let minLat = Infinity
  let maxLng = -Infinity
  let maxLat = -Infinity

  ring.forEach(([lng, lat]) => {
    minLng = Math.min(minLng, lng)
    minLat = Math.min(minLat, lat)
    maxLng = Math.max(maxLng, lng)
    maxLat = Math.max(maxLat, lat)
  })

  return { minLng, minLat, maxLng, maxLat }
}

function bboxIntersects(a, b) {
  return !(a.maxLng < b.minLng || a.minLng > b.maxLng || a.maxLat < b.minLat || a.minLat > b.maxLat)
}

function expandBboxByMeters(box, metres) {
  const centerLat = (box.minLat + box.maxLat) / 2
  const latDelta = metres / 111320
  const lngDelta = metres / (111320 * Math.cos(centerLat * Math.PI / 180))

  return {
    minLng: box.minLng - lngDelta,
    minLat: box.minLat - latDelta,
    maxLng: box.maxLng + lngDelta,
    maxLat: box.maxLat + latDelta,
  }
}

function polygonMayIntersectShadow(receiverFeature, shadowRing) {
  const receiverRing = getMainOuterRing(receiverFeature?.geometry)
  if (!receiverRing?.length || !shadowRing?.length) return false

  const receiverBox = bboxFromRing(receiverRing)
  const shadowBox = bboxFromRing(shadowRing)
  if (!bboxIntersects(receiverBox, shadowBox)) return false

  const receiverCenter = getFeatureCenter(receiverFeature)
  if (receiverCenter && pointInRing(receiverCenter, shadowRing)) return true

  return receiverRing.some((point) => pointInRing(point, shadowRing))
}

function estimateShadowCoveragePct(receiverRing, shadowRings) {
  if (!receiverRing?.length || !shadowRings.length) return 0

  const box = bboxFromRing(receiverRing)
  const steps = 18
  let roofSamples = 0
  let shadedSamples = 0

  for (let x = 0; x < steps; x += 1) {
    for (let y = 0; y < steps; y += 1) {
      const lng = box.minLng + ((x + 0.5) / steps) * (box.maxLng - box.minLng)
      const lat = box.minLat + ((y + 0.5) / steps) * (box.maxLat - box.minLat)
      const point = [lng, lat]

      if (!pointInRing(point, receiverRing)) continue

      roofSamples += 1
      if (shadowRings.some((ring) => pointInRing(point, ring))) shadedSamples += 1
    }
  }

  if (!roofSamples) return 0
  return Math.round((shadedSamples / roofSamples) * 100)
}

function getEstimatedUsableRoofArea(building) {
  const usableArea = Number(building?.usable_roof_area)
  if (Number.isFinite(usableArea) && usableArea > 0) return usableArea

  const footprintArea = Number(building?.footprint_area)
  if (Number.isFinite(footprintArea) && footprintArea > 0) return footprintArea

  return null
}

function updateFallbackUnobstructedUsableArea() {
  const area = getEstimatedUsableRoofArea(selectedBuilding.value)
  unobstructedUsableAreaM2.value = area == null
    ? null
    : Math.round(area * Math.max(0, 1 - shadowCoveragePct.value / 100) * 10) / 10
}

function buildSunDirectionFeature() {
  if (!selectedBuilding.value?.lng || !selectedBuilding.value?.lat) return null

  const lng = Number(selectedBuilding.value.lng)
  const lat = Number(selectedBuilding.value.lat)
  const az = sunMetrics.value.azimuth

  const lineLengthMeters = 80
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

function buildSelectedBuildingShadowFeature(casterFeature, casterHeight) {
  const ring = getMainOuterRing(casterFeature?.geometry)
  if (!ring?.length) return null

  const shadowAzimuth = (sunMetrics.value.azimuth + 180) % 360
  const shadowLength = getShadowLengthByHeightDifference(casterHeight, 0)
  if (shadowLength <= 0) return null

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
    properties: {
      kind: 'shadow-volume',
    },
  }
}

function buildCasterShadowFeature(casterFeature, receiverHeight) {
  const ring = getMainOuterRing(casterFeature?.geometry)
  if (!ring?.length) return null

  const casterHeight = getEffectiveBuildingHeight(casterFeature.properties)
  const shadowLength = getShadowLengthByHeightDifference(casterHeight, receiverHeight)
  if (shadowLength <= 0) return null

  const shadowAzimuth = (sunMetrics.value.azimuth + 180) % 360
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
    properties: {
      kind: 'shadow-volume',
      caster_structure_id: casterFeature.properties?.structure_id,
    },
  }
}

function buildReceiverShadowFeature(receiverFeature) {
  const ring = getMainOuterRing(receiverFeature?.geometry)
  if (!ring?.length) return null

  return {
    type: 'Feature',
    geometry: {
      type: 'Polygon',
      coordinates: [ring],
    },
    properties: {
      kind: 'shadow-receiver',
      structure_id: receiverFeature.properties?.structure_id,
    },
  }
}

function buildShadowInteractionFeatures() {
  shadowCoveragePct.value = 0
  shadowCasterCount.value = 0
  shadowOverlayFeatures.value = []
  unobstructedUsableAreaM2.value = null

  if (!selectedBuilding.value?.structure_id) return []

  const selectedId = Number(selectedBuilding.value.structure_id)
  const receiverFeature = buildingFeatureIndex.get(selectedId)
  if (!receiverFeature?.geometry) return []

  const receiverRing = getMainOuterRing(receiverFeature.geometry)
  if (!receiverRing?.length) return []

  const receiverHeight = getEffectiveBuildingHeight(selectedBuilding.value)
  const receiverBox = bboxFromRing(receiverRing)
  const nearbyBox = expandBboxByMeters(receiverBox, NEARBY_SHADOW_RADIUS_M)
  const visualShadowFeatures = []
  const affectingShadowFeatures = []
  const affectingShadowRings = []

  buildingFeatureIndex.forEach((feature, structureId) => {
    if (Number(structureId) === selectedId) return
    if (!feature?.geometry) return

    const casterRing = getMainOuterRing(feature.geometry)
    if (!casterRing?.length) return
    if (!bboxIntersects(nearbyBox, bboxFromRing(casterRing))) return

    const casterHeight = getEffectiveBuildingHeight(feature.properties)
    const visualShadowFeature = buildSelectedBuildingShadowFeature(feature, casterHeight)
    if (visualShadowFeature) {
      visualShadowFeatures.push(visualShadowFeature)
    }

    const shadowFeature = buildCasterShadowFeature(feature, receiverHeight)
    if (!shadowFeature) return

    const shadowRing = getMainOuterRing(shadowFeature.geometry)
    if (!shadowRing?.length) return
    if (!bboxIntersects(receiverBox, bboxFromRing(shadowRing))) return

    if (polygonMayIntersectShadow(receiverFeature, shadowRing)) {
      affectingShadowFeatures.push(shadowFeature)
      affectingShadowRings.push(shadowRing)
    }
  })

  shadowCasterCount.value = affectingShadowRings.length
  shadowCoveragePct.value = estimateShadowCoveragePct(receiverRing, affectingShadowRings)
  updateFallbackUnobstructedUsableArea()

  const receiverShadowFeature = shadowCasterCount.value > 0
    ? buildReceiverShadowFeature(receiverFeature)
    : null

  return receiverShadowFeature
    ? [...visualShadowFeatures, ...affectingShadowFeatures, receiverShadowFeature]
    : visualShadowFeatures
}

async function updateSunSimulation() {
  try {
    const path = await fetchSunPath(sunPathSeason.value)
    const sample = findClosestSunSample(path.samples, Number(sunPathTime.value))

    if (sample) currentSunData.value = sample
  } catch (err) {
    console.error('Sun path API failed:', err)
    showToast('Sun path unavailable')
  }

  if (!map) return

  const sunFeature = buildSunDirectionFeature()
  const shadowFeatures = buildShadowInteractionFeatures()

  if (selectedBuilding.value?.structure_id) {
    try {
      const impact = await fetchShadowImpact(
        selectedBuilding.value.structure_id,
        sunPathSeason.value,
        Number(sunPathTime.value),
      )
      if (impact) {
        shadowCoveragePct.value = Number(impact.shadow_coverage_pct || 0)
        shadowCasterCount.value = Number(impact.shadow_caster_count || 0)
        unobstructedUsableAreaM2.value = impact.unobstructed_usable_area_m2 ?? null
        if (unobstructedUsableAreaM2.value == null) updateFallbackUnobstructedUsableArea()
        shadowOverlayFeatures.value = impact.overlay_geojson?.features || []
      } else {
        updateFallbackUnobstructedUsableArea()
        shadowOverlayFeatures.value = []
      }
    } catch (err) {
      console.error('Shadow impact API failed:', err)
      updateFallbackUnobstructedUsableArea()
      shadowOverlayFeatures.value = []
    }
  }

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
      features: [
        ...shadowFeatures,
        ...shadowOverlayFeatures.value,
      ],
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
    fetchGeoJson(GEOJSON_PATH)
      .then((response) => response.json())
      .then(async (data) => {
        isLoading.value = false

        // Updated: keep both properties index and full feature index
        data.features.forEach(f => {
          buildingIndex.set(Number(f.properties.structure_id), f.properties)
          buildingFeatureIndex.set(Number(f.properties.structure_id), f)
        })

        map.addSource('melbourne-buildings', { type: 'geojson', data })
        addRoofTypePatternImages()

        map.addLayer({
          id: 'building-extrusion',
          type: 'fill-extrusion',
          source: 'melbourne-buildings',
          paint: {
            'fill-extrusion-color': SOLAR_EXTRUSION_COLOR,
            'fill-extrusion-height': ['coalesce', ['get', 'building_height'], 4],
            'fill-extrusion-base': 0,
            'fill-extrusion-opacity': 0.85,
          },
        })

        filters.forEach((roofFilter) => {
          map.addLayer({
            id: `roof-pattern-${roofFilter.type}`,
            type: 'fill',
            source: 'melbourne-buildings',
            filter: ['==', ['get', 'roof_type'], roofFilter.type],
            layout: {
              visibility: roofTypeEffectOn.value ? 'visible' : 'none',
            },
            paint: {
              'fill-pattern': roofFilter.patternId,
              'fill-opacity': 1,
            },
          })
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

        // Updated: Sun Path sources and layers
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
          filter: [
            'match',
            ['get', 'kind'],
            ['shadow-volume', 'shadow-receiver'],
            true,
            false,
          ],
          paint: {
            'fill-color': [
              'match',
              ['get', 'kind'],
              'shadow-receiver', '#DC2626',
              '#1F2937',
            ],
            'fill-opacity': [
              'match',
              ['get', 'kind'],
              'shadow-receiver', 0.32,
              0.18,
            ],
          },
        })

        map.addLayer({
          id: 'shadow-rooftop-overlay',
          type: 'fill-extrusion',
          source: 'shadow-projection',
          filter: [
            'match',
            ['get', 'kind'],
            ['rooftop-shaded', 'rooftop-unobstructed'],
            true,
            false,
          ],
          paint: {
            'fill-extrusion-color': [
              'match',
              ['get', 'kind'],
              'rooftop-shaded', '#DC2626',
              'rooftop-unobstructed', '#16A34A',
              '#16A34A',
            ],
            'fill-extrusion-base': ['+', ['coalesce', ['get', 'roof_height'], 0], 0.25],
            'fill-extrusion-height': ['+', ['coalesce', ['get', 'roof_height'], 0], 0.55],
            'fill-extrusion-opacity': 0.62,
          },
        })

        map.addLayer({
          id: 'shadow-receiver-outline',
          type: 'line',
          source: 'shadow-projection',
          paint: {
            'line-color': '#DC2626',
            'line-width': 1.8,
            'line-opacity': [
              'match',
              ['get', 'kind'],
              'shadow-receiver', 0.9,
              0,
            ],
          },
        })

        filters.forEach((roofFilter) => {
          map.addLayer({
            id: `roof-outline-${roofFilter.type}`,
            type: 'line',
            source: 'melbourne-buildings',
            filter: ['==', ['get', 'roof_type'], roofFilter.type],
            layout: {
              visibility: roofTypeEffectOn.value ? 'visible' : 'none',
            },
            paint: {
              'line-color': 'rgba(17, 24, 39, 0.45)',
              'line-width': 1.2,
              'line-opacity': 0.7,
            },
          })
        })
        applyFilters()

        try {
          const pRes = await fetchGeoJson(PRECINCTS_PATH).catch(() => null)
          if (pRes) {
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
          yieldData.value = null
          selectedAddress.value = null
          solarApiLoading.value = true
          sidebarOpen.value = true

          updateHighlights()

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
          ;[solarApiData.value, yieldData.value] = await Promise.all([
            fetchSolarApiData(sid),
            fetchYieldData(sid),
          ])
          selectedAddress.value = solarApiData.value?.address || await fetchAddressForBuilding(sid)
          solarApiLoading.value = false

          // Updated: update sun simulation after map click
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
})

onUnmounted(() => {
  if (toastTimer) clearTimeout(toastTimer)

  // Updated: stop sun animation timer
  stopSunAnimation()

  if (map) {
    map.remove()
    map = null
  }
})
</script>
