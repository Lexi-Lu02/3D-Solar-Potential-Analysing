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
      @show-guide="showGuide"
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
                <button class="planning-action-btn planning-action-btn--primary" @click="exportBuildingCsv">Export CSV</button>
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

                <div class="panel-id">BUILDING {{ selectedBuilding.structure_id || selectedBuilding.objectid || '—' }}</div>
                <div class="panel-address">
                  <span class="panel-address-label">Address</span>
                  <span class="panel-address-val">{{ shortAddress(selectedAddress) || selectedAddress || '—' }}</span>
                </div>

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
                        <div class="fin-tooltip-box">Annual Generation × $0.2575/kWh Victorian electricity tariff (avoided grid purchase cost).</div>
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

                <!-- Assumptions (editable) -->
                <div class="fin-assumptions">
                  <div class="fin-assumptions-title-row">
                    <span class="fin-assumptions-title">Assumptions</span>
                    <button class="fin-assumptions-reset" @click="resetAssumptions" title="Restore default values">Reset</button>
                  </div>
                  <div class="fin-assumption-row fin-assumption-row--input">
                    <span>Panel capacity</span>
                    <span class="fin-assumption-input-wrap">
                      <input type="number" v-model.number="assumptionPanelCap" min="100" max="1000" step="10" class="fin-assumption-input" />
                      <span class="fin-assumption-unit">W each</span>
                    </span>
                  </div>
                  <div class="fin-assumption-row fin-assumption-row--input">
                    <span>Install cost</span>
                    <span class="fin-assumption-input-wrap">
                      <span class="fin-assumption-unit fin-assumption-unit--pre">$</span>
                      <input type="number" v-model.number="assumptionCostPerWatt" min="0.5" max="5" step="0.05" class="fin-assumption-input" />
                      <span class="fin-assumption-unit">/ W</span>
                    </span>
                  </div>
                  <div class="fin-assumption-row fin-assumption-row--input">
                    <span>Electricity tariff</span>
                    <span class="fin-assumption-input-wrap">
                      <span class="fin-assumption-unit fin-assumption-unit--pre">$</span>
                      <input type="number" v-model.number="assumptionTariff" min="0.05" max="1" step="0.01" class="fin-assumption-input" />
                      <span class="fin-assumption-unit">/ kWh</span>
                    </span>
                  </div>
                  <div class="fin-assumption-row">
                    <span>Panel efficiency</span>
                    <span>20%</span>
                  </div>
                  <div class="fin-assumption-row">
                    <span>Performance ratio</span>
                    <span>75%</span>
                  </div>
                </div>

                <div class="section-title">Planning Actions</div>
                <div class="planning-actions">
                  <button class="planning-action-btn planning-action-btn--primary" @click="shareBuilding">Copy Shareable Link</button>
                  <button class="planning-action-btn planning-action-btn--primary" @click="addToCompare">Comparison</button>
                  <button class="planning-action-btn planning-action-btn--primary" @click="exportBuildingCsv">Export CSV</button>
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

                <div class="panel-id">BUILDING {{ selectedBuilding.structure_id || selectedBuilding.objectid || '—' }}</div>
                <div class="panel-address">
                  <span class="panel-address-label">Address</span>
                  <span class="panel-address-val">{{ shortAddress(selectedAddress) || selectedAddress || '—' }}</span>
                </div>

                <!-- CO₂ hero -->
                <div class="fin-hero fin-hero--green">
                  <div class="fin-hero-top">
                    <span class="fin-hero-label">Est. Annual CO₂ Reduction</span>
                    <div class="fin-tooltip-wrap">
                      <button class="fin-info-btn" aria-label="CO₂ reduction assumptions">i</button>
                      <div class="fin-tooltip-box">Annual Generation × {{ envMetrics.carbonKgPerKwh.toFixed(3) }} kg CO₂e/kWh Victorian grid emission factor.</div>
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
                        <div class="fin-tooltip-box">CO₂ Reduction ÷ 2,190 kg CO₂/yr average car emissions.</div>
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
                        <div class="fin-tooltip-box">Annual Generation ÷ 4,615 kWh average annual Victorian household consumption.</div>
                      </div>
                    </div>
                    <div class="fin-metric-val">{{ envMetrics.homesPowered.toLocaleString() }}</div>
                    <div class="fin-metric-unit">homes / yr</div>
                  </div>

                  <div class="fin-metric-card env-metric-card--full">
                    <div class="fin-metric-header">
                      <span class="fin-metric-label">Lifetime CO₂ Savings</span>
                      <div class="fin-tooltip-wrap">
                        <button class="fin-info-btn" aria-label="Lifetime CO₂ assumptions">i</button>
                        <div class="fin-tooltip-box">Annual CO₂ Reduction × 25 years (standard commercial solar panel lifespan), expressed in tonnes.</div>
                      </div>
                    </div>
                    <div class="fin-metric-val">{{ envMetrics.lifetimeCo2T.toLocaleString() }}</div>
                    <div class="fin-metric-unit">tonnes CO₂ over system life</div>
                  </div>

                </div>

                <!-- Conversion factors (3 adjustable, 3 static) -->
                <div class="fin-assumptions">
                  <div class="fin-assumptions-title-row">
                    <span class="fin-assumptions-title">Conversion Factors</span>
                    <button class="fin-assumptions-reset" @click="resetConversionFactors" title="Restore default values">Reset</button>
                  </div>
                  <div class="fin-assumption-row">
                    <span>Grid emission factor</span>
                    <span>{{ envMetrics.carbonKgPerKwh.toFixed(3) }} kg CO₂e / kWh</span>
                  </div>
                  <div class="fin-assumption-row"><span>Tree CO₂ absorption</span><span>21.77 kg CO₂ / yr</span></div>
                  <div class="fin-assumption-row"><span>Petrol energy equivalent</span><span>8.9 kWh / litre</span></div>
                  <div class="fin-assumption-row"><span>Average car emissions</span><span>2,190 kg CO₂ / yr</span></div>
                  <div class="fin-assumption-row fin-assumption-row--input">
                    <span>Vic. household consumption</span>
                    <span class="fin-assumption-input-wrap">
                      <input type="number" v-model.number="convHomeKwh" min="1000" max="20000" step="100" class="fin-assumption-input" />
                      <span class="fin-assumption-unit">kWh / yr</span>
                    </span>
                  </div>
                  <div class="fin-assumption-row fin-assumption-row--input">
                    <span>System lifespan</span>
                    <span class="fin-assumption-input-wrap">
                      <input type="number" v-model.number="convSystemLife" min="10" max="40" step="1" class="fin-assumption-input" />
                      <span class="fin-assumption-unit">years</span>
                    </span>
                  </div>
                </div>

                <div class="section-title">Planning Actions</div>
                <div class="planning-actions">
                  <button class="planning-action-btn planning-action-btn--primary" @click="shareBuilding">Copy Shareable Link</button>
                  <button class="planning-action-btn planning-action-btn--primary" @click="addToCompare">Comparison</button>
                  <button class="planning-action-btn planning-action-btn--primary" @click="exportBuildingCsv">Export CSV</button>
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

    <!-- User guide overlay — shown on every page load and on demand -->
    <Transition name="onboarding-fade">
      <div v-if="showOnboarding" class="onboarding-overlay" role="dialog" aria-modal="true" :aria-labelledby="`guide-title-${guideStep}`">
        <div class="onboarding-card guide-card">

          <!-- Header row: step counter + skip -->
          <div class="guide-header-row">
            <span class="guide-counter">{{ guideStep + 1 }} / {{ GUIDE_STEPS.length }}</span>
            <button class="onboarding-skip" @click="dismissOnboarding" aria-label="Close guide">✕ Skip guide</button>
          </div>

          <!-- Step content -->
          <div class="guide-body">
            <div class="guide-icon" aria-hidden="true" v-html="GUIDE_STEPS[guideStep].icon"></div>
            <h2 class="guide-title" :id="`guide-title-${guideStep}`">{{ GUIDE_STEPS[guideStep].title }}</h2>
            <p class="guide-desc">{{ GUIDE_STEPS[guideStep].desc }}</p>
            <div v-if="GUIDE_STEPS[guideStep].tip" class="guide-tip">
              <span class="guide-tip-label">Tip</span>
              {{ GUIDE_STEPS[guideStep].tip }}
            </div>
          </div>

          <!-- Progress dots -->
          <div class="guide-dots" role="tablist" aria-label="Guide progress">
            <button
              v-for="(_, i) in GUIDE_STEPS"
              :key="i"
              class="guide-dot"
              :class="{ 'guide-dot--active': i === guideStep, 'guide-dot--done': i < guideStep }"
              @click="guideStep = i"
              :aria-label="`Go to step ${i + 1}`"
              role="tab"
              :aria-selected="i === guideStep"
            ></button>
          </div>

          <!-- Navigation buttons -->
          <div class="guide-nav">
            <button
              class="guide-nav-back"
              :disabled="guideStep === 0"
              @click="guideStep--"
              aria-label="Previous step"
            >← Back</button>

            <button
              v-if="guideStep < GUIDE_STEPS.length - 1"
              class="onboarding-cta guide-nav-next"
              @click="guideStep++"
            >Next →</button>
            <button
              v-else
              class="onboarding-cta guide-nav-next"
              @click="dismissOnboarding"
            >Start Exploring →</button>
          </div>

        </div>
      </div>
    </Transition>
  </div>
</template>

<script>
// Named export — required for KeepAlive in App.vue to keep the map alive
// when navigating to other pages and back.
export default { name: 'ExploreView' }
</script>

<script setup>
// ─────────────────────────────────────────────────────────────────────────────
// ExploreView.vue — The main 3D interactive map page.
//
// This is the most complex page in the app. It:
//   • Renders 19,000+ Melbourne CBD buildings as 3D extrusions on a MapLibre map
//   • Colours each building by its solar score (green = great, red = poor)
//   • Opens a 3-tab sidebar when a building is clicked:
//       Tab 1 — Solar Potential: score, area, monthly chart, formula breakdown
//       Tab 2 — Financial Analysis: payback period, installation cost, annual savings
//       Tab 3 — Environmental Impact: CO₂ saved, trees equivalent, homes powered
//   • Provides an address search bar with dropdown results
//   • Allows filtering buildings by roof type and solar tier
//   • Supports side-by-side comparison of up to 2 buildings
//   • Simulates sun position and shadow on the map for any time of day
//   • Shows a first-time onboarding modal
//
// Data flow:
//   1. Load combined-buildings.geojson (40k+ building footprints + scores)
//   2. On building click → fetch detailed solar/yield data from the backend API
//   3. Calculate financial and environmental metrics from the energy estimate
// ─────────────────────────────────────────────────────────────────────────────

// Vue's reactivity helpers.
import { computed, onActivated, onMounted, onUnmounted, ref } from 'vue'

// MapLibre GL JS — the open-source map rendering engine.
import maplibregl from 'maplibre-gl'

// Shared components used on this page.
import MainNavbar     from '../components/MainNavbar.vue'
import MonthlyChart   from '../components/MonthlyChart.vue'   // bar chart of monthly kWh
import FormulaCard    from '../components/FormulaCard.vue'    // collapsible formula breakdown
import SubnavToolbar  from '../components/SubnavToolbar.vue'  // sub-navigation toolbar with search
import ComparisonPanel from '../components/ComparisonPanel.vue' // bottom comparison panel
import FilterPanel    from '../components/FilterPanel.vue'    // floating filter card

// Icon images used in the sidebar.
import iconCompare     from '../pictures/Compare.png'
import iconSearch      from '../pictures/Search.png'
import iconSolarCell   from '../pictures/solar-cell.png'
import iconProfits     from '../pictures/profits.png'
import iconPlanetEarth from '../pictures/planet-earth.png'

// useRoute gives us access to the current URL (used to read ?building= query parameter
// that is set when someone shares a direct link to a building's analysis).
import { useRoute } from 'vue-router'

const route = useRoute()

// ── URL configuration ─────────────────────────────────────────────────────────
// These come from the .env file so they can point to different servers/paths in
// development vs production. The || is the fallback if the env var isn't set.
const GEOJSON_PATH   = import.meta.env.VITE_GEOJSON_URL   || '/combined-buildings.geojson'
const PRECINCTS_PATH = import.meta.env.VITE_PRECINCTS_URL || '/melbourne_cbd_precincts.geojson'

// ── GeoJSON fetch helper ──────────────────────────────────────────────────────
// Fetches a GeoJSON file and validates that the server actually returned JSON
// (not an HTML error page that looks like a 200 response).
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

// ── Map colour constants ──────────────────────────────────────────────────────
// MapLibre paint properties only accept literal hex values — they cannot read CSS variables.
// These colours are intentionally kept in sync with the :root palette in style.css.
// Changing a colour here should also be changed in the matching CSS variable.
const MAP_COLORS = {
  solarExcellent:  '#D55E00',
  solarGood:       '#E69F00',
  solarModerate:   '#F0E442',
  solarPoor:       '#56B4E9',
  solarVeryPoor:   '#0072B2',
  selected:        '#E83E8C',
  compare:         '#8CA28F',
  lineStroke:      '#1C1710',
}

const SELECTED_BUILDING_COLOR = MAP_COLORS.selected
const SELECTED_BUILDING_OPACITY = 0.98
const COMPARE_BUILDING_COLOR = MAP_COLORS.compare
const COMPARE_BUILDING_OPACITY = 0.90
const SOLAR_DISABLED_EXTRUSION_COLOR = '#DED8CA'
const SOLAR_EXTRUSION_COLOR = [
  'case',
  ['==', ['coalesce', ['get', 'solar_score'], 0], 0],
  SOLAR_DISABLED_EXTRUSION_COLOR,
  ['step', ['get', 'solar_score'],
    MAP_COLORS.solarVeryPoor, 20, MAP_COLORS.solarPoor, 40, MAP_COLORS.solarModerate, 60, MAP_COLORS.solarGood, 80, MAP_COLORS.solarExcellent,
  ],
]

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1'

// ── API response caches ───────────────────────────────────────────────────────
// Each Map stores API responses keyed by structure_id (or date for sun path).
// When the user clicks the same building again, we return the cached result
// instead of making another network request (faster, reduces server load).
const solarApiCache   = new Map()   // Google Solar API data per building
const yieldCache      = new Map()   // annual kWh + monthly breakdown per building
const shadowImpactCache = new Map() // shadow analysis per building+date+hour
const sunPathCache    = new Map()   // full-day sun position data per season

// Fixed calendar dates used for the three sun simulation seasons.
const SUN_PATH_DATES = {
  summer: '2025-12-21',
  equinox: '2025-03-21',
  winter: '2025-06-21',
}
const NEARBY_SHADOW_RADIUS_M = 100

// ── Reactive state ────────────────────────────────────────────────────────────
// All these ref() variables are reactive — when you change .value,
// Vue automatically re-renders the relevant parts of the template.

// Loading overlay state — shown while the GeoJSON is being downloaded.
const isLoading   = ref(true)
const loadingText = ref('Loading Melbourne building data...')

// The building the user last clicked on the map.
// null = no building selected (sidebar shows the "click a building" placeholder).
const selectedBuilding = ref(null)

// Currently active filter values — arrays of selected ids (empty = show all).
const activeFilter       = ref([])   // selected roof types, e.g. ['Flat', 'Hip']
const activeSolarFilter  = ref([])   // selected solar tier ids, e.g. ['very-high', 'high']

// Whether the solar colour gradient / roof type effect are currently painted on the map.
const solarPotentialColorOn = ref(true)
const roofTypeEffectOn      = ref(true)

// Toast notification state (the brief popup message).
const toastMessage = ref('')
const toastVisible = ref(false)

// Data fetched from the backend API for the selected building.
const solarApiData  = ref(null)   // Google Solar API data (panels, area, sunshine hours)
const yieldData     = ref(null)   // City of Melbourne survey data (annual kWh, score)
const solarApiLoading = ref(false)  // true while API requests are in progress

// The street address of the selected building (fetched separately from /address endpoint).
const selectedAddress = ref(null)

// Address search state.
const searchId           = ref('')      // the current text typed in the search box
const searchError        = ref('')      // error message if the search API fails
const searchResults      = ref([])      // array of matching building objects
const searchLoading      = ref(false)   // true while waiting for search results
const searchFocusedIdx   = ref(-1)      // which dropdown item is keyboard-highlighted (-1 = none)
const searchDropdownOpen = ref(false)   // whether the results dropdown is visible
let searchDebounceTimer  = null         // timer handle to delay API calls while typing

// Guide overlay — shown on every page load and whenever the user clicks "Guide" in the subnav.
const showOnboarding = ref(true)   // always show on mount
const guideStep      = ref(0)      // current step index (0-based)
const sidebarOpen    = ref(false)
const filtersOpen    = ref(false)

// 8-step guide content. icon is an inline SVG string.
const GUIDE_STEPS = [
  {
    icon: `<svg width="52" height="52" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="4" stroke="var(--city-light)" stroke-width="1.8"/><path d="M12 2v2.5M12 19.5V22M2 12h2.5M19.5 12H22M4.2 4.2l1.8 1.8M18 18l1.8 1.8M18 6l1.8-1.8M4.2 19.8l1.8-1.8" stroke="var(--city-light)" stroke-width="1.6" stroke-linecap="round"/></svg>`,
    title: 'Welcome to 3D Explore',
    desc: 'This interactive map visualises the solar potential of 19,000+ Melbourne CBD buildings in real time. This quick guide walks you through every feature so you can get the most out of it.',
  },
  {
    icon: `<svg width="52" height="52" viewBox="0 0 24 24" fill="none"><path d="M5 9c0-3.87 3.13-7 7-7s7 3.13 7 7c0 4.5-5.5 11-7 13C10.5 20 5 13.5 5 9z" stroke="var(--city-light)" stroke-width="1.8"/><circle cx="12" cy="9" r="2.5" stroke="var(--city-light)" stroke-width="1.6"/></svg>`,
    title: 'Navigate the 3D Map',
    desc: 'Drag to pan across the city. Scroll or pinch to zoom in and out. Hold Ctrl and drag (or right-click drag) to rotate and tilt the 3D perspective. Double-click to zoom into a specific spot.',
    tip: 'Hold Shift while scrolling to tilt the map without rotating.',
  },
  {
    icon: `<svg width="52" height="52" viewBox="0 0 24 24" fill="none"><circle cx="11" cy="11" r="7" stroke="var(--city-light)" stroke-width="1.8"/><path d="M20 20l-3-3" stroke="var(--city-light)" stroke-width="2" stroke-linecap="round"/></svg>`,
    title: 'Search by Address',
    desc: 'Use the search bar at the top of the screen to jump straight to any building by street address. Results appear as you type — click one to fly the camera directly to that building.',
    tip: 'You only need to type 2 or more characters before results appear.',
  },
  {
    icon: `<svg width="52" height="52" viewBox="0 0 24 24" fill="none"><rect x="3" y="7" width="18" height="13" rx="2" stroke="var(--city-light)" stroke-width="1.8"/><path d="M8 7V5a4 4 0 0 1 8 0v2" stroke="var(--city-light)" stroke-width="1.8" stroke-linecap="round"/><circle cx="12" cy="13.5" r="1.5" fill="var(--city-light)"/></svg>`,
    title: 'Select a Building',
    desc: 'Click any 3D building on the map to select it. The building highlights in blue and its detailed solar profile opens in the right-hand panel. Buildings are coloured green (high potential) to red (low potential).',
    tip: 'Use the Filter tool to show only high-potential buildings so they are easier to find.',
  },
  {
    icon: `<svg width="52" height="52" viewBox="0 0 24 24" fill="none"><rect x="3" y="3" width="18" height="18" rx="2" stroke="var(--city-light)" stroke-width="1.8"/><path d="M15 3v18" stroke="var(--city-light)" stroke-width="1.8"/><path d="M7 8h4M7 12h4M7 16h4" stroke="var(--city-light)" stroke-width="1.4" stroke-linecap="round"/></svg>`,
    title: 'Building Info Panel',
    desc: 'The right-hand panel has three tabs. Solar Potential shows the score, usable roof area, peak sun hours, and a monthly generation chart. Financial Analysis shows installation cost, annual savings, and payback period. Environmental Impact shows CO₂ saved and homes powered.',
    tip: 'Click "Building Info" in the toolbar if the panel is closed.',
  },
  {
    icon: `<svg width="52" height="52" viewBox="0 0 24 24" fill="none"><path d="M4 6h16M7 12h10M10 18h4" stroke="var(--city-light)" stroke-width="2" stroke-linecap="round"/></svg>`,
    title: 'Filter Buildings',
    desc: 'Click Filter in the toolbar to open the filter panel. Filter buildings by solar score tier — High, Medium, or Low — or by roof type. Buildings that don\'t match your filter fade out on the map so the candidates stand out.',
    tip: 'Combine a High tier filter with the Sun Path tool to find shade-free, high-potential rooftops.',
  },
  {
    icon: `<svg width="52" height="52" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="4" stroke="var(--city-light)" stroke-width="1.8"/><path d="M12 2v2.5M12 19.5V22M2 12h2.5M19.5 12H22" stroke="var(--city-light)" stroke-width="1.6" stroke-linecap="round"/><path d="M6 18l8-12" stroke="var(--city-light)" stroke-width="1.4" stroke-linecap="round" opacity="0.55"/></svg>`,
    title: 'Sun Path & Shadow Simulation',
    desc: 'Click Sun Path in the toolbar to open the simulation panel. Set any time of day and month to see where the sun is in the sky and how shadows fall across the buildings. This reveals how much shade affects a roof throughout the year.',
    tip: 'Try midwinter (June) at noon versus midsummer (December) to see the dramatic difference in shadow length.',
  },
  {
    icon: `<svg width="52" height="52" viewBox="0 0 24 24" fill="none"><rect x="2" y="5" width="9" height="14" rx="2" stroke="var(--city-light)" stroke-width="1.8"/><rect x="13" y="5" width="9" height="14" rx="2" stroke="var(--city-light)" stroke-width="1.8"/></svg>`,
    title: 'Compare Buildings',
    desc: 'Click Comparison in the toolbar to open the compare panel at the bottom of the screen. Select a building on the map, then click "Add to Compare". Add a second building the same way. Their scores, energy output, costs, and CO₂ savings appear side-by-side.',
    tip: 'You can compare up to 2 buildings at once. Click the × on a card to remove it.',
  },
]

// Comparison panel state.
const comparePanelOpen = ref(false)     // whether the comparison panel is visible
const compareBuildings = ref([])        // array of up to 2 buildings being compared

// Sun path & shadow simulation state.
const sunPathOpen     = ref(false)      // whether the sun path panel is visible
const sunPathSeason   = ref('summer')  // selected season: 'summer', 'equinox', or 'winter'
const sunPathTime     = ref(12)         // selected hour (6–18, supports 0.5 steps for :30)
const sunAnimating    = ref(false)      // true when the "Play" animation is running
const sunAnimationTimer = ref(null)     // setInterval handle for the animation loop
const shadowCoveragePct = ref(0)        // estimated % of the selected building's roof that is shaded
const shadowCasterCount = ref(0)        // number of nearby buildings casting shadows
const shadowOverlayFeatures = ref([])   // GeoJSON features used to draw shadow polygons
const unobstructedUsableAreaM2 = ref(null)  // roof area not covered by shadow (m²)

// Sidebar state.
const compareVisible = computed(() => comparePanelOpen.value)  // alias for template clarity
const scoreExplOpen  = ref(false)     // whether the solar score explanation tooltip is open
const activeTab      = ref('details') // which sidebar tab is active: 'details', 'finance', or 'env'

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
  const eff = assumptionEfficiency.value / 100
  const pr  = assumptionPerfRatio.value  / 100
  if (psh) return Math.round(area * eff * pr * psh)
  return Math.round(area * eff * pr * 4.1 * 365)
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

// Financial assumption defaults — Melbourne 2024 commercial averages.
const DEFAULT_COST_PER_WATT  = 1.20
const DEFAULT_PANEL_CAPACITY = 400
const DEFAULT_TARIFF         = 0.2575
const DEFAULT_EFFICIENCY     = 20    // percent
const DEFAULT_PERF_RATIO     = 75    // percent

// User-adjustable assumption refs (bound to inputs in the Assumptions card).
const assumptionCostPerWatt  = ref(DEFAULT_COST_PER_WATT)
const assumptionPanelCap     = ref(DEFAULT_PANEL_CAPACITY)
const assumptionTariff       = ref(DEFAULT_TARIFF)
const assumptionEfficiency   = ref(DEFAULT_EFFICIENCY)
const assumptionPerfRatio    = ref(DEFAULT_PERF_RATIO)

function resetAssumptions() {
  assumptionCostPerWatt.value = DEFAULT_COST_PER_WATT
  assumptionPanelCap.value    = DEFAULT_PANEL_CAPACITY
  assumptionTariff.value      = DEFAULT_TARIFF
  assumptionEfficiency.value  = DEFAULT_EFFICIENCY
  assumptionPerfRatio.value   = DEFAULT_PERF_RATIO
}

// Environmental conversion factors — static scientific constants.
const TREE_CO2_KG_PER_YEAR  = 21.77  // kg CO₂ absorbed per mature tree per year (U.S. Forest Service)
const PETROL_KWH_PER_LITRE  = 8.9    // energy equivalent of 1 litre of petrol
const CAR_CO2_KG_PER_YEAR   = 2190   // average car emissions for temporary display

// User-adjustable environmental conversion factors.
const DEFAULT_GRID_EMISSION  = 0.86   // kg CO₂e/kWh, Victorian grid factor for temporary display
const DEFAULT_HOME_KWH       = 4615   // average Victorian household annual consumption for temporary display
const DEFAULT_SYSTEM_LIFE    = 25     // typical commercial solar panel lifespan

const convGridEmission = ref(DEFAULT_GRID_EMISSION)
const convHomeKwh      = ref(DEFAULT_HOME_KWH)
const convSystemLife   = ref(DEFAULT_SYSTEM_LIFE)

function resetConversionFactors() {
  convGridEmission.value = DEFAULT_GRID_EMISSION
  convHomeKwh.value      = DEFAULT_HOME_KWH
  convSystemLife.value   = DEFAULT_SYSTEM_LIFE
}

const envMetrics = computed(() => {
  const annualKwh = formulaKwhAnnual.value
  if (!selectedBuilding.value || annualKwh <= 0) return null
  // Temporary display uses the Victorian grid factor from the assumptions panel.
  const carbonKgPerKwh  = convGridEmission.value
  const co2Kg          = Math.round(annualKwh * carbonKgPerKwh)
  const treesEquiv     = Math.round(co2Kg / TREE_CO2_KG_PER_YEAR)
  const petrolLitres   = Math.round(annualKwh / PETROL_KWH_PER_LITRE)
  const carsOffRoad    = Math.round((co2Kg / CAR_CO2_KG_PER_YEAR) * 10) / 10
  const homesPowered   = Math.round((annualKwh / convHomeKwh.value) * 10) / 10
  const lifetimeCo2T   = Math.round(co2Kg * convSystemLife.value / 100) / 10
  return { co2Kg, treesEquiv, petrolLitres, carsOffRoad, homesPowered, lifetimeCo2T, annualKwh, carbonKgPerKwh }
})

// Calculates the financial metrics for the Finance Analysis tab.
// All numbers are estimates — they appear in the sidebar and the CSV export.
const financialMetrics = computed(() => {
  if (!selectedBuilding.value) return null
  const annualKwh = formulaKwhAnnual.value
  if (!annualKwh || annualKwh <= 0) return null
  // Use the Google Solar API panel count if available; otherwise null so the cost shows "—"
  const maxPanels       = solarApiData.value?.maxPanels ?? null
  // Some buildings have a non-standard panel size from the Solar API — fall back to user assumption
  const panelCapacityW  = solarApiData.value?.panelCapacityWatts ?? assumptionPanelCap.value
  // installCost = number of panels × watts per panel × cost per watt
  const installCost     = maxPanels != null ? Math.round(maxPanels * panelCapacityW * assumptionCostPerWatt.value) : null
  // annualSavings = energy we'd have to buy from the grid × electricity tariff
  const annualSavings = Math.round(annualKwh * assumptionTariff.value)
  // paybackYears = how many years of savings it takes to recover the installation cost
  // Rounded to 1 decimal place (e.g., 7.3 years)
  const paybackYears  = installCost && annualSavings > 0 ? Math.round((installCost / annualSavings) * 10) / 10 : null
  return { annualKwh, installCost, annualSavings, paybackYears, maxPanels, panelCapacityW }
})

// ── Map instance and non-reactive helpers ─────────────────────────────────────
// These are plain JavaScript variables, NOT Vue refs.
// They're outside Vue's reactivity system because the map object and lookup tables
// don't need to trigger re-renders — they're only used inside functions.

let map = null           // the MapLibre map instance (assigned in initMap)
let toastTimer = null    // setTimeout handle for auto-hiding the toast
let compassIdx = 0       // tracks which compass heading we're currently on

// Quick lookup tables built once when GeoJSON loads — avoids scanning all 40k features on every click.
// Using a Map (key-value store) gives O(1) lookup by structure_id, much faster than find().
let buildingIndex = new Map()        // structure_id → properties (for the sidebar panels)
let buildingFeatureIndex = new Map() // structure_id → full GeoJSON feature (needed for shadow geometry)

// When the user clicks the compass button, cycle through these 8 cardinal/intercardinal headings
// so they can quickly snap the map to a clean orientation.
const COMPASS_BEARINGS = [0, 45, 90, 135, 180, 225, 270, 315]

// Each entry describes one roof type button shown in the FilterPanel.
// `pattern` and `patternId` are used by createRoofPatternImage() to draw distinct hatching on the map.
const filters = [
  { type: 'Flat', label: 'Flat Roofs', pattern: 'flat', patternId: 'roof-pattern-flat' },
  { type: 'Hip', label: 'Hip Roofs', pattern: 'diagonal', patternId: 'roof-pattern-hip' },
  { type: 'Gable', label: 'Gable Roofs', pattern: 'cross', patternId: 'roof-pattern-gable' },
  { type: 'Pyramid', label: 'Pyramid Roofs', pattern: 'triangles', patternId: 'roof-pattern-pyramid' },
  { type: 'Shed', label: 'Shed Roofs', pattern: 'horizontal', patternId: 'roof-pattern-shed' },
]
// Plain list of type strings — used when we need to loop over all roof types without the extra metadata.
const ROOF_TYPES = ['Flat', 'Hip', 'Gable', 'Pyramid', 'Shed']

// Defines the 5 solar quality tiers shown in FilterPanel and the sidebar score card.
// `min`/`max` are the solar_score thresholds (0–100 scale used in the GeoJSON).
// `bars` controls how many signal-strength bars to draw in the UI (1–5).
const solarTiers = [
  { id: 'very-high', label: 'Excellent',  range: '4.5-5',   color: MAP_COLORS.solarExcellent,        min: 80,   max: null, bars: 5 },
  { id: 'high',      label: 'Good',       range: '3.5-4.4', color: MAP_COLORS.solarGood,             min: 60,   max: 80,   bars: 4 },
  { id: 'medium',    label: 'Moderate',   range: '2.5-3.4', color: MAP_COLORS.solarModerate,         min: 40,   max: 60,   bars: 3 },
  { id: 'low',       label: 'Poor',       range: '1.5-2.4', color: MAP_COLORS.solarPoor,             min: 20,   max: 40,   bars: 2 },
  { id: 'very-low',  label: 'Very Poor',  range: '1-1.4',   color: MAP_COLORS.solarVeryPoor,         min: 1,    max: 20,   bars: 1 },
  { id: 'no-data',   label: 'No Data',    range: '—',        color: SOLAR_DISABLED_EXTRUSION_COLOR,  min: null, max: null, bars: 0 },
]

// ── Solar score display helpers ───────────────────────────────────────────────
// The "solar score" (1–5) comes from the City of Melbourne rooftop solar survey.
// It measures average irradiance across the roof area — 5 means excellent solar potential.
// ~31% of buildings have this data; the rest show "No Data".

// Reads the score from the yield API response for the selected building.
// Returns null if no building is selected OR if the survey data doesn't cover this building.
const score = computed(() => {
  if (!selectedBuilding.value) return null
  return yieldData.value?.solar_score_avg ?? null
})

// Converts a numeric score (1–5) into a human-readable tier label for the sidebar.
const tier = computed(() => {
  const s = score.value
  if (s === null) return 'No Data'
  if (s >= 4.5) return 'Excellent'
  if (s >= 3.5) return 'Good'
  if (s >= 2.5) return 'Moderate'
  if (s >= 1.5) return 'Poor'
  return 'Very Poor'
})

// Returns the CSS variable name for the tier's colour.
// Uses CSS custom properties (defined in style.css :root) so the design system stays consistent.
const tierColor = computed(() => {
  const s = score.value
  if (s === null) return 'var(--text-secondary)'
  if (s >= 4.5) return 'var(--solar-very-high)'
  if (s >= 3.5) return 'var(--solar-high)'
  if (s >= 2.5) return 'var(--solar-med)'
  if (s >= 1.5) return 'var(--solar-low)'
  return 'var(--solar-very-low)'
})

// Some tier colours (yellow/orange) are light — we swap to a darker card background
// so the white score number stays readable (WCAG colour contrast requirement).
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

// Formats the shadow coverage percentage for display in the sun path panel.
// Shows "Select a building" when nothing is clicked, otherwise e.g. "34%".
const shadowCoverageLabel = computed(() => {
  if (!selectedBuilding.value) return 'Select a building'
  return `${Math.round(shadowCoveragePct.value)}%`
})

// Formats the unobstructed usable area (roof area not covered by shadow) for display.
// null means the calculation is still running or hasn't been triggered yet.
const unobstructedUsableAreaLabel = computed(() => {
  if (!selectedBuilding.value) return 'Select a building'
  if (unobstructedUsableAreaM2.value == null) return 'Calculating...'
  return `${Number(unobstructedUsableAreaM2.value).toFixed(1)} m²`
})

// Converts a raw coverage percentage into a 3-level impact word shown in the sun path panel.
// < 10% = Low, 10–35% = Moderate, > 35% = High
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

// Fetches the shadow impact analysis for one building at a specific date and time.
// The backend calculates which nearby buildings cast shadows on the selected building's roof
// and returns the coverage percentage and a GeoJSON overlay for the map.
// Results are cached by (structureId, date, hour) so scrubbing the time slider
// only fetches each unique combination once.
async function fetchShadowImpact(structureId, season, hour) {
  const date = SUN_PATH_DATES[season] || SUN_PATH_DATES.summer
  const normalizedHour = Number(hour)
  const cacheKey = `shadow_${structureId}_${date}_${normalizedHour}`

  // Return from in-memory cache if we've already fetched this combination
  if (shadowImpactCache.has(cacheKey)) return shadowImpactCache.get(cacheKey)

  // Build the query string, e.g. "?date=2025-12-21&hour=14"
  const params = new URLSearchParams({
    date,
    hour: String(normalizedHour),
  })
  const res = await fetch(`${API_BASE}/buildings/by-structure/${structureId}/shadow-impact?${params}`)

  // 404 means the backend has no shadow data for this building — cache null to avoid retrying
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

// The sun path API returns hourly data points (e.g., 6:00, 6:30, 7:00 … 18:00).
// The time slider can be dragged to any 30-minute increment.
// This function finds the sample whose hour value is numerically closest to the slider value
// so we always display a real data point, not an interpolated guess.
// Uses Array.reduce to scan all samples in one pass and return the winner.
function findClosestSunSample(samples, hour) {
  if (!Array.isArray(samples) || samples.length === 0) return null

  return samples.reduce((closest, item) => {
    return Math.abs(Number(item.hour) - hour) < Math.abs(Number(closest.hour) - hour)
      ? item
      : closest
  }, samples[0])
}

// Fetches annual kWh output and monthly breakdown from the City of Melbourne survey API.
// Returns null if this building has no survey data (the most common case — only ~31% are covered).
// Cached by structure_id so clicking the same building twice is instant.
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

// Fetches the street address for a building from the backend.
// This is a separate API call because address lookup can be slow — we call it after the
// solar data is already displayed so the user sees data immediately while the address loads.
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

// Shows a brief pop-up notification ("toast") at the bottom of the screen.
// Clears any existing toast first so rapid calls don't stack up.
// The toast auto-hides after 1.8 seconds using setTimeout.
function showToast(message) {
  if (toastTimer) clearTimeout(toastTimer)
  toastMessage.value = message
  toastVisible.value = true
  toastTimer = setTimeout(() => {
    toastVisible.value = false
  }, 1800)
}

// Builds a MapLibre filter expression for arrays of selected roof types and solar tier ids.
// Returns null when no filters are active (tells MapLibre to show all buildings).
function buildCombinedFilter(roofTypes, solarTierIds) {
  const conditions = []

  if (roofTypes.length > 0) {
    const roofConds = roofTypes.map(t => ['==', ['get', 'roof_type'], t])
    conditions.push(roofConds.length === 1 ? roofConds[0] : ['any', ...roofConds])
  }

  if (solarTierIds.length > 0) {
    const tierConds = solarTierIds.flatMap(tierId => {
      if (tierId === 'no-data') {
        // Mirrors SOLAR_EXTRUSION_COLOR: score=0 or null both mean "no survey data"
        return [['==', ['coalesce', ['get', 'solar_score'], 0], 0]]
      }
      const tier = solarTiers.find(t => t.id === tierId)
      if (!tier) return []
      const tc = [['>=', ['get', 'solar_score'], tier.min]]
      if (tier.max !== null) tc.push(['<', ['get', 'solar_score'], tier.max])
      return [tc.length === 1 ? tc[0] : ['all', ...tc]]
    })
    if (tierConds.length > 0) {
      conditions.push(tierConds.length === 1 ? tierConds[0] : ['any', ...tierConds])
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

// Registers each roof type's hatching pattern as a named image inside MapLibre.
// MapLibre uses these image names in the 'fill-pattern' paint property to tile the pattern
// across rooftops. We skip registration if the image was already added (e.g., after a hot reload).
function addRoofTypePatternImages() {
  filters.forEach((roofFilter) => {
    if (map.hasImage?.(roofFilter.patternId)) return
    map.addImage(roofFilter.patternId, createRoofPatternImage(roofFilter.pattern), { pixelRatio: 2 })
  })
}

// Returns true if a roof type's pattern/outline layers should currently be shown.
// The layer is hidden if: (a) the roof type effect toggle is off, or
// (b) the user has filtered to a different roof type.
function roofTypeLayerVisible(roofType) {
  return roofTypeEffectOn.value && (activeFilter.value.length === 0 || activeFilter.value.includes(roofType))
}

// Synchronises the map's visual state with the current filter toggles.
// Called whenever solarPotentialColorOn, roofTypeEffectOn, activeFilter, or activeSolarFilter change.
// Does three things:
//   1. Switches the extrusion colour between the solar gradient and a plain grey
//   2. Shows/hides each roof type's hatch pattern layer
//   3. Applies the combined filter expression to each layer so hidden buildings disappear
function applyRoofTypeEffect() {
  if (!map?.getLayer('building-extrusion')) return

  // Toggle between the 5-colour solar gradient and a uniform grey
  map.setPaintProperty(
    'building-extrusion',
    'fill-extrusion-color',
    solarPotentialColorOn.value ? SOLAR_EXTRUSION_COLOR : SOLAR_DISABLED_EXTRUSION_COLOR
  )

  // Update each roof type's pattern and outline layers
  ROOF_TYPES.forEach((roofType) => {
    const visible = roofTypeLayerVisible(roofType)
    const filter = buildCombinedFilter([roofType], activeSolarFilter.value)

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

// One-stop shop to apply both the combined filter and the roof type effect to the map.
// Called by filterRoof() and filterSolar() after the filter state refs are updated.
function applyFilters() {
  if (!map) return
  map.setFilter('building-extrusion', buildCombinedFilter(activeFilter.value, activeSolarFilter.value))
  applyRoofTypeEffect()
}

// Trims a full address to its first 3 comma-separated parts (street number, street, suburb).
// "123 Collins Street, Melbourne, Victoria 3000" → "123 Collins Street, Melbourne, Victoria 3000"
// Returns '—' when no address is available (no data sentinel).
function shortAddress(addr) {
  if (!addr) return '—'
  const parts = addr.split(',')
  return parts.slice(0, 3).join(',').trim()
}

// Toggles a roof type filter on/off (clicking the same type twice clears it).
// After updating the ref, calls applyFilters() to push the change to the map immediately.
function filterRoof(type) {
  const cur = activeFilter.value
  activeFilter.value = cur.includes(type) ? cur.filter(t => t !== type) : [...cur, type]
  applyFilters()
}

function filterSolar(tierId) {
  const cur = activeSolarFilter.value
  activeSolarFilter.value = cur.includes(tierId) ? cur.filter(id => id !== tierId) : [...cur, tierId]
  applyFilters()
}

// Closes the guide and opens the filter panel so the user can start interacting.
function dismissOnboarding() {
  showOnboarding.value = false
  filtersOpen.value = true
}

// Re-opens the guide from step 1 (triggered by the Guide button in the subnav).
function showGuide() {
  guideStep.value = 0
  showOnboarding.value = true
}

// Toggles the comparison panel open/closed.
// Closes the sun path panel if it was open — the two bottom panels can't overlap.
function toggleComparePanel() {
  comparePanelOpen.value = !comparePanelOpen.value
  if (comparePanelOpen.value) sunPathOpen.value = false
}

// Toggles the sun path/shadow simulation panel open/closed.
// Closes the comparison panel to avoid overlap.
function toggleSunPathPanel() {
  sunPathOpen.value = !sunPathOpen.value
  if (sunPathOpen.value) comparePanelOpen.value = false
}

// Flips the solar colour gradient on or off and shows a short toast confirming the change.
function toggleSolarPotentialColor() {
  solarPotentialColorOn.value = !solarPotentialColorOn.value
  applyRoofTypeEffect()
  showToast(`Solar potential colors ${solarPotentialColorOn.value ? 'on' : 'off'}`)
}

// Flips the roof type hatching overlays on or off and confirms with a toast.
function toggleRoofTypeEffect() {
  roofTypeEffectOn.value = !roofTypeEffectOn.value
  applyRoofTypeEffect()
  showToast(`Roof type styling ${roofTypeEffectOn.value ? 'on' : 'off'}`)
}

// Resets both active filters to 'all' and refreshes the map so all buildings are visible again.
function clearAllFilters() {
  activeFilter.value = []
  activeSolarFilter.value = []
  applyFilters()
}

// Hides the search dropdown by clearing all related state.
// Called when the user presses Escape, clicks outside, or selects a result.
function closeSearchDropdown() {
  searchResults.value = []
  searchLoading.value = false
  searchFocusedIdx.value = -1
  searchDropdownOpen.value = false
}


// Handles keyboard navigation in the search dropdown.
// This makes the search accessible to keyboard-only users (required by WCAG 2.1):
//   Escape → close the dropdown
//   Arrow Down → highlight the next result (wraps around at the bottom)
//   Arrow Up   → highlight the previous result (wraps around at the top)
//   Enter      → select the highlighted result (or the first one if none highlighted)
// % len ensures the index wraps: going past the last item goes back to the first.
function onSearchKeydown(e) {
  const len = searchResults.value.length
  if (e.key === 'Escape') { closeSearchDropdown(); return }
  if (e.key === 'ArrowDown') {
    e.preventDefault()  // prevents the page from scrolling when pressing arrow keys
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

// Fires every time the user types in the search box.
// Uses a debounce pattern: we wait 250ms after the last keypress before sending the request.
// This prevents sending one API call per keystroke (which would be ~10 calls for "Collins St").
// Only starts searching once 2+ characters are typed (avoid overwhelming the API with single letters).
function onSearchInput() {
  searchFocusedIdx.value = -1
  clearTimeout(searchDebounceTimer)      // cancel any pending search from the previous keystroke
  const q = searchId.value.trim()
  if (q.length < 2) { closeSearchDropdown(); return }  // too short — wait for more input
  searchDropdownOpen.value = true
  searchLoading.value = true
  searchDebounceTimer = setTimeout(async () => {
    // This inner function runs 250ms after the user stops typing
    try {
      const res = await fetch(`${API_BASE}/buildings/search?q=${encodeURIComponent(searchId.value.trim())}`)
      // encodeURIComponent ensures special characters (spaces, "&") are URL-safe
      searchResults.value = res.ok ? await res.json() : []
    } catch {
      searchResults.value = []
    } finally {
      searchLoading.value = false   // hide the loading spinner regardless of success/failure
    }
  }, 250)
}

// Called when the user clicks a search result or presses Enter on a highlighted result.
// Steps:
//   1. Close the dropdown and fill the search input with the chosen address
//   2. Look up the building in our local index (avoids a round-trip network request)
//   3. Set the selected building in state (shows the sidebar)
//   4. Fly the camera to the building's coordinates with a smooth animation
//   5. Fetch solar API + yield data in parallel (Promise.all)
//   6. Refresh the sun simulation for the newly selected building
async function selectSearchResult(result) {
  searchResults.value = []
  searchDropdownOpen.value = false
  searchError.value = ''
  searchId.value = result.address || String(result.structure_id)

  // Look up the building's cached properties by structure_id
  const props = buildingIndex.get(Number(result.structure_id))
  if (!props) { searchError.value = 'Building not found in map data'; return }

  const sid = Number(props.structure_id)

  // Pre-populate the sidebar immediately with GeoJSON properties (no API wait)
  selectedBuilding.value = props
  solarApiData.value = null
  yieldData.value = null
  selectedAddress.value = result.address || null
  solarApiLoading.value = true

  if (map) {
    updateHighlights()  // immediately highlight this building on the map
    const lng = Number(result.lng) || Number(props.lng)
    const lat = Number(result.lat) || Number(props.lat)
    if (lat && lng) {
      // Smooth animated camera fly-to — easing function creates a natural acceleration/deceleration
      map.flyTo({
        center: [lng, lat],
        zoom: Math.max(map.getZoom(), 15.5),  // zoom in but never zoom OUT (Math.max)
        pitch: 55,
        duration: 1200,
        easing: (t) => (t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t),  // ease-in-out curve
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


// Updates the 'building-compare' map layer filter to highlight the 1–2 comparison buildings
// in the teal/green colour defined by COMPARE_BUILDING_COLOR.
// We use [-1] as a dummy filter when the list is empty — no real structure_id equals -1.
function updateCompareHighlight() {
  if (!map) return
  const ids = compareBuildings.value.map(c => c.building.structure_id)
  map.setFilter('building-compare', ['in', ['get', 'structure_id'], ['literal', ids.length ? ids : [-1]]])
  updateHighlights()
}

// Updates the 'building-selected' layer to highlight the currently selected building (blue)
// AND any buildings in the comparison list. We use a Set to deduplicate (in case the
// selected building is also in the comparison list).
function updateHighlights() {
  if (!map) return
  const ids = new Set()
  if (selectedBuilding.value) ids.add(Number(selectedBuilding.value.structure_id))
  for (const c of compareBuildings.value) ids.add(Number(c.building.structure_id))
  const idArr = [...ids]
  // ['in', field, ['literal', array]] is a MapLibre filter that matches any feature
  // whose `structure_id` property appears in the given array.
  map.setFilter('building-selected',
    idArr.length > 0
      ? ['in', ['get', 'structure_id'], ['literal', idArr]]
      : ['==', ['get', 'structure_id'], -1]  // match nothing when list is empty
  )
}

// Adds the currently selected building to the comparison list (max 2 buildings).
// Snapshots all the currently computed data (solar, financial, environmental) at this moment
// so the comparison panel stays stable even if the user clicks another building afterwards.
// If the list is already full (2 buildings), the oldest entry is removed first (.shift()).
function addToCompare() {
  if (!selectedBuilding.value) return
  const sid = selectedBuilding.value.structure_id
  if (compareBuildings.value.some(c => c.building.structure_id === sid)) {
    showToast('Already in comparison')
    return
  }
  // { ...object } creates a shallow copy — the comparison panel's data won't change
  // if the user selects a different building and those refs update.
  const entry = {
    building: { ...selectedBuilding.value },
    apiData: solarApiData.value ? { ...solarApiData.value } : null,
    analysis: {
      solar: {
        annualKwh: formulaKwhAnnual.value > 0 ? formulaKwhAnnual.value : null,
        usableAreaM2: solarApiData.value?.usableAreaM2 ?? null,
        roofAreaM2: solarApiData.value?.roofAreaM2 ?? null,
        sunshineHours: solarApiData.value?.sunshineHours ?? null,
        scoreAvg: yieldData.value?.solar_score_avg ?? null,   // 0–5 City of Melbourne score
      },
      finance: financialMetrics.value
        ? { ...financialMetrics.value }
        : null,
      env: envMetrics.value
        ? { ...envMetrics.value }
        : null,
    },
  }
  // Drop the oldest building when at capacity (acts like a queue with max size 2)
  if (compareBuildings.value.length >= 2) compareBuildings.value.shift()
  compareBuildings.value.push(entry)
  comparePanelOpen.value = true  // automatically open the comparison panel
  showToast('Added to comparison')
  updateCompareHighlight()
}

// Removes the comparison building at position `idx` (0 or 1) from the list.
// Called from the × buttons inside ComparisonPanel.
function removeFromCompare(idx) {
  compareBuildings.value.splice(idx, 1)
  updateCompareHighlight()
}

// Empties the entire comparison list and removes the highlight from the map.
function clearCompare() {
  compareBuildings.value = []
  updateCompareHighlight()
}

// Makes a single cell value safe to embed in a CSV file.
// Rule: wrap everything in double quotes, and escape any internal double quotes by doubling them.
// e.g., the value: She said "hello"  →  CSV cell: "She said ""hello"""
function toCsvSafe(value) {
  const stringValue = value == null ? '' : String(value)
  const escaped = stringValue.replace(/"/g, '""')
  return `"${escaped}"`
}

// Generates a .csv file from all the data shown in the sidebar and triggers a browser download.
// The file contains three sections: Building Details, Financial Analysis, Environmental Impact.
// Uses Blob + URL.createObjectURL() — a browser API that lets JavaScript create a downloadable
// file without any server involvement. The link is programmatically "clicked" to start the download,
// then immediately cleaned up.
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
      ['Assumption - Electricity Tariff', '$0.2575 / kWh'],
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
      ['Lifetime CO₂ Savings', em.lifetimeCo2T.toLocaleString() + ' tonnes CO₂'],
      ['Conversion - Grid Emission Factor', '0.86 kg CO₂e / kWh'],
      ['Conversion - Tree CO₂ Absorption', '21.77 kg CO₂ / yr'],
      ['Conversion - Petrol Energy Equiv.', '8.9 kWh / litre'],
      ['Conversion - Avg. Car Emissions', '2,190 kg CO₂ / yr'],
      ['Conversion - Vic. Household Consumption', '4,615 kWh / yr'],
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

// Reads the ?buildingId= query parameter from the current URL and, if present,
// automatically selects that building on the map and loads its data.
// This enables the "Copy Shareable Link" feature: someone pastes the link,
// the page loads, and this function immediately jumps to the building.
// Called inside initMap() after the GeoJSON has finished loading.
async function openBuildingFromUrl() {
  const buildingId = route.query.buildingId  // e.g. "12345" from ?buildingId=12345
  if (!buildingId) return  // no deep-link parameter — do nothing

  const id = Number(buildingId)

  // Look up the building in the in-memory index (already populated from GeoJSON)
  const props = buildingIndex.get(id)
  if (!props) return  // building ID not found in the data — silently skip

  selectedBuilding.value = props
  solarApiData.value = null
  yieldData.value = null
  selectedAddress.value = null
  solarApiLoading.value = true
  sidebarOpen.value = true  // always open sidebar when deep-linking to a building

  // Map the ?panel= query value to the correct sidebar tab
  const panelMap = { solar: 'details', financial: 'finance', environment: 'env' }
  const requestedPanel = route.query.panel
  if (requestedPanel && panelMap[requestedPanel]) {
    activeTab.value = panelMap[requestedPanel]
  }

  if (map) {
    updateHighlights()  // immediately highlight the building before API data arrives

    const lng = Number(props.lng)
    const lat = Number(props.lat)

    if (lat && lng) {
      map.flyTo({ center: [lng, lat], zoom: 16, pitch: 55, duration: 1200 })
    }

    // Fetch both data sources in parallel — Promise.all waits for both before continuing
    ;[solarApiData.value, yieldData.value] = await Promise.all([
      fetchSolarApiData(id),
      fetchYieldData(id),
    ])
    selectedAddress.value = solarApiData.value?.address || await fetchAddressForBuilding(id)
  }

  solarApiLoading.value = false

  await updateSunSimulation()  // update the sun/shadow overlay for this building
}

// ── Sun path animation controls ───────────────────────────────────────────────

// Called when the user switches season (summer/equinox/winter).
// Resets the time to midday (12:00) and re-fetches the sun position for the new date.
async function applySeasonPreset() {
  sunPathTime.value = 12
  await updateSunSimulation()
}

// Resets the sun simulation to its default state: summer, midday, no animation.
async function resetSunSimulation() {
  sunPathSeason.value = 'summer'
  sunPathTime.value = 12
  stopSunAnimation()
  await updateSunSimulation()
}

// Starts or stops the animated time-lapse that steps through the day from 6:00 to 18:00.
// Uses setInterval to advance 30 minutes every 900ms, creating a "sun arc" animation.
// The time wraps from 18:00 back to 6:00 so the animation loops continuously.
function toggleSunAnimation() {
  if (sunAnimating.value) {
    stopSunAnimation()
    return
  }

  sunAnimating.value = true
  sunAnimationTimer.value = window.setInterval(async () => {
    const next = Number(sunPathTime.value) + 0.5  // advance by 30 minutes each tick
    sunPathTime.value = next > 18 ? 6 : next       // wrap around: after 18:00 → 6:00
    await updateSunSimulation()
  }, 900)  // 900ms per step = about 22 seconds per full day sweep
}

// Stops the time-lapse animation and clears the interval timer.
// clearInterval() is important — without it the timer would keep running even after the component unmounts.
function stopSunAnimation() {
  sunAnimating.value = false
  if (sunAnimationTimer.value) {
    clearInterval(sunAnimationTimer.value)
    sunAnimationTimer.value = null
  }
}

// ── Geometry helpers for shadow calculation ───────────────────────────────────
// These functions implement the trigonometry needed to project building shadows
// onto the ground plane given the sun's current altitude and azimuth angles.

// Returns the most reliable height estimate for a building.
// Priority: explicit building_height field → (max_elevation - base_height) → 20m fallback.
// The 20m default covers most low-rise Melbourne CBD buildings when data is missing.
function getEffectiveBuildingHeight(building) {
  const explicitHeight = Number(building?.building_height)
  if (Number.isFinite(explicitHeight) && explicitHeight > 0) return explicitHeight

  const base = Number(building?.base_height)
  const max = Number(building?.max_elevation)
  if (Number.isFinite(base) && Number.isFinite(max) && max > base) {
    return max - base
  }

  return 20  // fallback: assume ~6-storey building
}

// Calculates how far a building's shadow extends on the ground.
// Physics: shadow_length = height_difference / tan(sun_altitude)
// When the sun is very low (altitude near 0°), tan approaches 0 and shadows become extremely long.
// We cap at 8× building height to prevent unrealistically huge shadows.
// receiverHeight lets us account for buildings casting shadows onto elevated rooftops (not ground).
function getShadowLengthByHeightDifference(casterHeight, receiverHeight = 0) {
  const altitude = Number(currentSunData.value?.altitude_deg || 0)
  if (altitude <= 0) return 0  // sun is below horizon — no shadow

  const heightDiff = Math.max(0, casterHeight - receiverHeight)
  if (heightDiff <= 0) return 0  // caster isn't taller than receiver — no shadow falls on it

  const rad = altitude * Math.PI / 180  // convert degrees to radians (Math.tan requires radians)
  const tan = Math.tan(rad)
  if (tan <= 0.01) return casterHeight * 8  // near-horizon sun — use the cap

  return Math.min(heightDiff / tan, casterHeight * 8)  // normal shadow + apply cap
}

// Converts a displacement in meters (dx = east-west, dy = north-south) to a new
// longitude/latitude point. Used to shift a building's footprint in the direction
// of the shadow projection.
// The longitude correction (÷ cos(lat)) accounts for the fact that degrees of longitude
// represent fewer meters as you get further from the equator.
function shiftLngLat(lng, lat, dxMeters, dyMeters) {
  const dLat = dyMeters / 111320               // 111,320 meters per degree of latitude (constant)
  const dLng = dxMeters / (111320 * Math.cos(lat * Math.PI / 180))  // shrinks near poles
  return [lng + dLng, lat + dLat]
}

// Returns all ring arrays (outer boundary + holes) from a Polygon or MultiPolygon geometry.
// GeoJSON Polygon: coordinates = [outerRing, hole1, hole2, ...]
// GeoJSON MultiPolygon: coordinates = [polygon1, polygon2, ...] where each polygon has rings
function getPolygonRings(geometry) {
  if (!geometry) return []
  if (geometry.type === 'Polygon') return geometry.coordinates.map((ring) => ring)
  if (geometry.type === 'MultiPolygon') return geometry.coordinates.flatMap((poly) => poly.map((ring) => ring))
  return []
}

// Returns just the first (outer) ring of a polygon, which is the building footprint outline.
// Holes (interior rings) are ignored for shadow calculations.
function getMainOuterRing(geometry) {
  const rings = getPolygonRings(geometry)
  return rings.length ? rings[0] : null
}

// Computes the centroid (geographic centre) of a polygon by averaging all vertex coordinates.
// Used as a quick point-in-polygon seed check before doing more expensive full ray casting.
function getFeatureCenter(feature) {
  const ring = getMainOuterRing(feature?.geometry)
  if (!ring?.length) return null

  let lngSum = 0
  let latSum = 0

  ring.forEach(([lng, lat]) => {
    lngSum += Number(lng)
    latSum += Number(lat)
  })

  return [lngSum / ring.length, latSum / ring.length]  // simple arithmetic mean
}

// Ray casting algorithm: determines whether a 2D point is inside a polygon ring.
// Fires a conceptual ray from the point to the right (+x direction) and counts
// how many polygon edges it crosses. An odd count = inside, even count = outside.
// The tiny +0.0000000001 prevents division by zero when an edge is perfectly horizontal.
function pointInRing(point, ring) {
  const [px, py] = point
  let inside = false

  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [xi, yi] = ring[i]
    const [xj, yj] = ring[j]
    const intersects =
      ((yi > py) !== (yj > py)) &&
      (px < ((xj - xi) * (py - yi)) / (yj - yi + 0.0000000001) + xi)

    if (intersects) inside = !inside  // flip: odd crossings = inside
  }

  return inside
}

// Computes a bounding box (min/max lat/lng rectangle) for a polygon ring.
// Much faster to compare than doing full point-in-polygon on every nearby building —
// we first reject buildings whose bboxes don't overlap before running the expensive check.
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

// Returns true if two bounding boxes overlap.
// The condition reads: "they DON'T NOT-overlap" (double negation of the four non-overlap cases).
// a is fully left of b, b is fully left of a, a is fully below b, or a is fully above b.
function bboxIntersects(a, b) {
  return !(a.maxLng < b.minLng || a.minLng > b.maxLng || a.maxLat < b.minLat || a.minLat > b.maxLat)
}

// Expands a bounding box outward by a given number of meters in all directions.
// Used to create a search radius: e.g., "find all buildings within 260m of the selected building".
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

// Quick check: does a shadow polygon potentially overlap with the receiver building?
// Uses three increasingly expensive tests, stopping early when possible:
//   1. Bounding box check (cheapest — just compare 4 numbers)
//   2. Point-in-polygon: is the receiver's center inside the shadow? (fast for large overlaps)
//   3. Any vertex of the receiver's ring inside the shadow? (catches partial overlaps)
function polygonMayIntersectShadow(receiverFeature, shadowRing) {
  const receiverRing = getMainOuterRing(receiverFeature?.geometry)
  if (!receiverRing?.length || !shadowRing?.length) return false

  const receiverBox = bboxFromRing(receiverRing)
  const shadowBox = bboxFromRing(shadowRing)
  if (!bboxIntersects(receiverBox, shadowBox)) return false  // no overlap possible

  const receiverCenter = getFeatureCenter(receiverFeature)
  if (receiverCenter && pointInRing(receiverCenter, shadowRing)) return true

  return receiverRing.some((point) => pointInRing(point, shadowRing))
}

// Estimates what percentage of a building's roof is covered by shadows.
// Uses a Monte Carlo-style sampling grid: we place 18×18 = 324 test points across the
// bounding box of the roof, check which ones are inside the roof AND inside a shadow,
// then compute shadedSamples / roofSamples as the coverage fraction.
// 18 steps gives ~5% precision — fast enough for real-time slider updates.
function estimateShadowCoveragePct(receiverRing, shadowRings) {
  if (!receiverRing?.length || !shadowRings.length) return 0

  const box = bboxFromRing(receiverRing)
  const steps = 18   // grid resolution — 18×18 = 324 sample points
  let roofSamples = 0
  let shadedSamples = 0

  for (let x = 0; x < steps; x += 1) {
    for (let y = 0; y < steps; y += 1) {
      // Place point at the centre of each grid cell (+0.5 avoids testing on the exact boundary)
      const lng = box.minLng + ((x + 0.5) / steps) * (box.maxLng - box.minLng)
      const lat = box.minLat + ((y + 0.5) / steps) * (box.maxLat - box.minLat)
      const point = [lng, lat]

      if (!pointInRing(point, receiverRing)) continue  // skip: this point is outside the roof

      roofSamples += 1
      if (shadowRings.some((ring) => pointInRing(point, ring))) shadedSamples += 1
    }
  }

  if (!roofSamples) return 0
  return Math.round((shadedSamples / roofSamples) * 100)  // e.g., 34%
}

// Returns the best available usable roof area estimate for a building.
// Priority: survey usable_roof_area → total footprint_area → null (no data).
function getEstimatedUsableRoofArea(building) {
  const usableArea = Number(building?.usable_roof_area)
  if (Number.isFinite(usableArea) && usableArea > 0) return usableArea

  const footprintArea = Number(building?.footprint_area)
  if (Number.isFinite(footprintArea) && footprintArea > 0) return footprintArea

  return null
}

// Updates the "unobstructed usable area" display when the backend shadow API doesn't have data.
// Formula: unobstructed = usable_area × (1 - shadow_coverage%)
// This is a rough estimate — the backend's value (when available) is more accurate.
function updateFallbackUnobstructedUsableArea() {
  const area = getEstimatedUsableRoofArea(selectedBuilding.value)
  unobstructedUsableAreaM2.value = area == null
    ? null
    : Math.round(area * Math.max(0, 1 - shadowCoveragePct.value / 100) * 10) / 10
}

// Creates a GeoJSON LineString feature representing the sun's direction arrow
// drawn on the map (the amber/yellow line radiating from the selected building).
// The line is 80 meters long and points in the direction the sun is located
// (azimuth = compass bearing clockwise from North).
function buildSunDirectionFeature() {
  if (!selectedBuilding.value?.lng || !selectedBuilding.value?.lat) return null

  const lng = Number(selectedBuilding.value.lng)
  const lat = Number(selectedBuilding.value.lat)
  const az = sunMetrics.value.azimuth

  const lineLengthMeters = 80
  const rad = az * Math.PI / 180           // convert azimuth degrees → radians
  const dxMeters = Math.sin(rad) * lineLengthMeters  // east component of the line
  const dyMeters = Math.cos(rad) * lineLengthMeters  // north component of the line
  const [endLng, endLat] = shiftLngLat(lng, lat, dxMeters, dyMeters)

  return {
    type: 'Feature',
    geometry: {
      type: 'LineString',
      coordinates: [
        [lng, lat],        // starts at the building centre
        [endLng, endLat],  // ends 80m in the sun's direction
      ],
    },
    properties: {},
  }
}

// 2D convex hull via Andrew's monotone chain. Input: array of [x, y]. Output: closed
// CCW ring (first point repeated at the end). Operates directly on [lng, lat] — the
// spatial extent of a single building's shadow is small enough that treating degrees
// as planar coordinates does not change which vertices end up on the hull.
function convexHull2D(points) {
  if (points.length < 3) return points.slice()

  const pts = points
    .map(([x, y]) => [Number(x), Number(y)])
    .filter(([x, y]) => Number.isFinite(x) && Number.isFinite(y))
    .sort((a, b) => (a[0] - b[0]) || (a[1] - b[1]))

  // Cross product of vectors OA and OB. Positive = CCW turn.
  const cross = (o, a, b) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

  const lower = []
  for (const p of pts) {
    while (lower.length >= 2 && cross(lower[lower.length - 2], lower[lower.length - 1], p) <= 0) lower.pop()
    lower.push(p)
  }

  const upper = []
  for (let i = pts.length - 1; i >= 0; i -= 1) {
    const p = pts[i]
    while (upper.length >= 2 && cross(upper[upper.length - 2], upper[upper.length - 1], p) <= 0) upper.pop()
    upper.push(p)
  }

  lower.pop()
  upper.pop()
  const hull = lower.concat(upper)
  hull.push(hull[0])  // close the ring
  return hull
}

// Builds the ground-level shadow polygon swept out by translating `ring` along
// (dxMeters, dyMeters). The correct shape is the Minkowski sum of the footprint
// with the translation segment; for the convex / near-convex footprints in this
// dataset we approximate it as the convex hull of the original + shifted vertices,
// which avoids the self-intersecting "two footprints joined by a seam" artifact
// produced by naively concatenating the two rings.
function buildSweptShadowRing(ring, dxMeters, dyMeters) {
  if (!ring?.length) return null

  // Rings from GeoJSON are closed (last == first); drop the duplicate before hashing.
  const open = ring.length > 1 && ring[0][0] === ring[ring.length - 1][0] && ring[0][1] === ring[ring.length - 1][1]
    ? ring.slice(0, -1)
    : ring.slice()

  const shifted = open.map(([lng, lat]) => shiftLngLat(lng, lat, dxMeters, dyMeters))
  return convexHull2D([...open, ...shifted])
}

// Creates the GeoJSON polygon for a "shadow volume" cast by a caster building
// in the direction AWAY from the sun (shadow azimuth = sun azimuth + 180°).
// Used for VISUAL display of all nearby buildings' shadows (the dark overlay layer).
function buildSelectedBuildingShadowFeature(casterFeature, casterHeight) {
  const ring = getMainOuterRing(casterFeature?.geometry)
  if (!ring?.length) return null

  const shadowAzimuth = (sunMetrics.value.azimuth + 180) % 360  // opposite direction to sun
  const shadowLength = getShadowLengthByHeightDifference(casterHeight, 0)
  if (shadowLength <= 0) return null

  const rad = shadowAzimuth * Math.PI / 180
  const dxMeters = Math.sin(rad) * shadowLength
  const dyMeters = Math.cos(rad) * shadowLength
  const shadowRing = buildSweptShadowRing(ring, dxMeters, dyMeters)
  if (!shadowRing) return null

  return {
    type: 'Feature',
    geometry: {
      type: 'Polygon',
      coordinates: [shadowRing],
    },
    properties: {
      kind: 'shadow-volume',
    },
  }
}

// Similar to buildSelectedBuildingShadowFeature but accounts for the height of the RECEIVER
// (the building whose roof we're analysing). A short building near a tall tower only has
// a shadow cast on it if the shadow falls at or above the receiver's roof height.
// Used to find which buildings ACTUALLY affect the selected building (not just nearby ones).
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
  const shadowRing = buildSweptShadowRing(ring, dxMeters, dyMeters)
  if (!shadowRing) return null

  return {
    type: 'Feature',
    geometry: {
      type: 'Polygon',
      coordinates: [shadowRing],
    },
    properties: {
      kind: 'shadow-volume',
      caster_structure_id: casterFeature.properties?.structure_id,
    },
  }
}

// Creates a GeoJSON polygon for the SELECTED building's own footprint, tagged as
// 'shadow-receiver'. This triggers the red outline and fill shown on the selected building
// when it is in shadow, making it obvious which roof is being analysed.
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

// Orchestrates the full shadow calculation for the selected building.
// Steps:
//   1. Reset all shadow state
//   2. Get the selected building's footprint from the feature index
//   3. Build a 260m search box around it
//   4. For every building inside that box, project its shadow and check if it hits the receiver
//   5. Count how many casters actually affect the receiver (shadowCasterCount)
//   6. Estimate what % of the roof is in shadow (shadowCoveragePct) using the sampling grid
//   7. Return the list of GeoJSON features to draw on the map
// This runs entirely in the browser — no server request needed for the visual overlay.
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

// Master function called whenever the sun slider moves or the season changes.
// Coordinates all the shadow-related updates:
//   1. Fetch the sun position data for the current season (cached after first load)
//   2. Find the closest hourly sample to the slider's current time
//   3. Update currentSunData (altitude, azimuth) — this is read by sunMetrics computed
//   4. Build the client-side shadow geometry (visual overlays for all nearby buildings)
//   5. Try to fetch the backend's more accurate shadow analysis for the selected building
//   6. Update both the sun direction source and the shadow projection source on the map
// The backend data (step 5) takes priority over our client-side estimate (step 4).
async function updateSunSimulation() {
  try {
    const path = await fetchSunPath(sunPathSeason.value)
    const sample = findClosestSunSample(path.samples, Number(sunPathTime.value))

    if (sample) currentSunData.value = sample  // triggers re-render of altitude/azimuth display
  } catch (err) {
    console.error('Sun path API failed:', err)
    showToast('Sun path unavailable')
  }

  if (!map) return

  // Build client-side shadow geometry (fast, purely local computation)
  const sunFeature = buildSunDirectionFeature()     // the amber direction arrow
  const shadowFeatures = buildShadowInteractionFeatures()  // dark shadow polygons

  if (selectedBuilding.value?.structure_id) {
    try {
      // Try the backend API for a more accurate shadow analysis
      const impact = await fetchShadowImpact(
        selectedBuilding.value.structure_id,
        sunPathSeason.value,
        Number(sunPathTime.value),
      )
      if (impact) {
        // Use server values — override the client-side estimates
        shadowCoveragePct.value = Number(impact.shadow_coverage_pct || 0)
        shadowCasterCount.value = Number(impact.shadow_caster_count || 0)
        unobstructedUsableAreaM2.value = impact.unobstructed_usable_area_m2 ?? null
        if (unobstructedUsableAreaM2.value == null) updateFallbackUnobstructedUsableArea()
        shadowOverlayFeatures.value = impact.overlay_geojson?.features || []  // rooftop segments
      } else {
        // Backend has no data for this building — keep the client-side estimates
        updateFallbackUnobstructedUsableArea()
        shadowOverlayFeatures.value = []
      }
    } catch (err) {
      console.error('Shadow impact API failed:', err)
      updateFallbackUnobstructedUsableArea()
      shadowOverlayFeatures.value = []
    }
  }

  // Push updated GeoJSON to the map's live data sources
  // setData() replaces the entire FeatureCollection and MapLibre re-renders the layer immediately
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
        ...shadowFeatures,              // client-side geometry (visual shadow volumes)
        ...shadowOverlayFeatures.value, // server-side rooftop segment overlay
      ],
    })
  }
}

// ── Precinct helpers (mirror of PrecinctsView) ────────────────────────────────
// These are lightweight versions of the point-in-polygon helpers from PrecinctsView.
// They're used here to determine which precincts have at least one building with solar data,
// so only those precincts get the boundary outline on the Explore map.
// Prefixed with _p to distinguish them from the full-featured versions above.

// Computes the bounding box of a GeoJSON polygon or multipolygon feature.
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

// Ray-casting point-in-polygon test for a single ring (no holes).
function _pInRing(px, py, ring) {
  let inside = false
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [xi, yi] = ring[i], [xj, yj] = ring[j]
    if (((yi > py) !== (yj > py)) && (px < ((xj - xi) * (py - yi) / (yj - yi)) + xi)) inside = !inside
  }
  return inside
}

// Tests whether a point is inside a GeoJSON feature (supports Polygon and MultiPolygon).
function _pInFeature(px, py, f) {
  const g = f.geometry
  if (!g) return false
  const rings = g.type === 'Polygon' ? [g.coordinates[0]] : g.coordinates.map(p => p[0])
  return rings.some(r => _pInRing(px, py, r))
}

// ── Map initialisation ────────────────────────────────────────────────────────
// Creates the MapLibre map, registers all data sources and layers, and wires up
// all click/hover event listeners. Called once from onMounted.
//
// Layer rendering order (bottom → top — later layers paint on top of earlier ones):
//   1. building-extrusion   — main 3D buildings, coloured by solar score
//   2. roof-pattern-{type}  — hatching overlays per roof type (one per type)
//   3. building-compare     — teal highlight for comparison buildings
//   4. building-selected    — blue highlight for the clicked building
//   5. sun-direction-line   — amber arrow showing sun direction
//   6. shadow-projection-fill — dark shadow polygons on the ground
//   7. shadow-rooftop-overlay — coloured rooftop segments (shaded = red, clear = green)
//   8. shadow-receiver-outline — red border on the analysed building
//   9. roof-outline-{type}  — thin borders matching each roof type's hatching
//  10. precinct-boundary    — green district outlines
function initMap() {
  // Create the map and point it at Melbourne CBD
  map = new maplibregl.Map({
    container: 'map',    // the id of the <div> in the template
    style: 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',  // light basemap
    center: [144.9631, -37.814],  // Melbourne CBD coordinates [longitude, latitude]
    zoom: 12.2,          // roughly the CBD at ~1:10,000 scale
    pitch: 48,           // degrees of tilt (0 = top-down, 60 = nearly horizontal)
    bearing: -17,        // rotate slightly counter-clockwise (makes Collins St horizontal)
    antialias: true,     // smooth edges on buildings (uses WebGL MSAA)
  })

  // Add the built-in zoom/rotate controls in the top-right corner
  map.addControl(new maplibregl.NavigationControl(), 'top-right')

  // Customise the compass button: instead of resetting to North, cycle through 8 headings.
  // setTimeout(fn, 0) delays execution until after MapLibre has rendered the controls to the DOM.
  setTimeout(() => {
    const compassBtn = document.querySelector('.maplibregl-ctrl-compass')
    if (!compassBtn || !map) return
    // useCapture: true lets us intercept the click before MapLibre's own handler runs
    compassBtn.addEventListener(
      'click',
      (event) => {
        event.stopImmediatePropagation()  // prevent MapLibre's default "reset to North" behaviour
        compassIdx = (compassIdx + 1) % COMPASS_BEARINGS.length  // advance to next preset
        map.easeTo({
          bearing: COMPASS_BEARINGS[compassIdx],
          duration: 900,
          easing: (t) => (t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t),  // ease-in-out
        })
      },
      true
    )
  }, 0)

  // map.on('load') fires after the basemap tiles have finished loading.
  // Everything that adds sources/layers must happen inside this callback.
  map.on('load', () => {
    fetchGeoJson(GEOJSON_PATH)
      .then((response) => response.json())
      .then(async (data) => {
        isLoading.value = false  // hide the loading overlay

        // Build the two in-memory lookup tables from the GeoJSON features
        // This is the O(n) scan we do ONCE — after this all lookups are O(1)
        data.features.forEach(f => {
          buildingIndex.set(Number(f.properties.structure_id), f.properties)
          buildingFeatureIndex.set(Number(f.properties.structure_id), f)
        })

        // Register the GeoJSON as a named source — all layers will reference this source by name
        map.addSource('melbourne-buildings', { type: 'geojson', data })
        addRoofTypePatternImages()  // pre-register the hatch pattern images

        // Layer 1: main 3D building extrusions coloured by solar score
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

        // Layers 2a-2e: roof type hatching — one fill layer per roof type
        // Each layer uses the registered pattern image as its 'fill-pattern'
        // These are 2D flat overlays on top of the 3D extrusions
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

        // Layer 3: comparison buildings (teal/green colour)
        // Starts with a filter that matches nothing (structure_id = -1 never exists)
        // Updated by updateCompareHighlight() when buildings are added to comparison
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

        // Layer 4: selected building (blue) — also starts matching nothing
        // Updated by updateHighlights() on every building click/search
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

        // Sun direction and shadow layers use separate GeoJSON sources
        // that are updated dynamically by updateSunSimulation()
        map.addSource('sun-direction', {
          type: 'geojson',
          data: {
            type: 'FeatureCollection',
            features: [],
          },
        })

        // Layer 5: the amber arrow pointing in the direction of the sun
        map.addLayer({
          id: 'sun-direction-line',
          type: 'line',
          source: 'sun-direction',
          paint: {
            'line-color': '#F59E0B',  // amber/yellow — matches sun icon colour
            'line-width': 3,
            'line-opacity': 0.95,
          },
        })

        // Source for all shadow-related polygons — updated by updateSunSimulation()
        map.addSource('shadow-projection', {
          type: 'geojson',
          data: {
            type: 'FeatureCollection',
            features: [],
          },
        })

        // Layer 6: ground-level shadow fills (dark grey for normal shadows, red tint on receiver)
        // The MapLibre 'match' expression works like a switch statement on feature properties:
        //   if kind === 'shadow-receiver' → red fill
        //   otherwise → dark grey fill (shadow-volume)
        map.addLayer({
          id: 'shadow-projection-fill',
          type: 'fill',
          source: 'shadow-projection',
          filter: [
            'match',
            ['get', 'kind'],
            ['shadow-volume', 'shadow-receiver'],
            true,    // show these kinds
            false,   // hide everything else
          ],
          paint: {
            'fill-color': [
              'match',
              ['get', 'kind'],
              'shadow-receiver', '#DC2626',  // red for the analysed building
              '#1F2937',                     // dark grey for shadow volumes
            ],
            'fill-opacity': [
              'match',
              ['get', 'kind'],
              'shadow-receiver', 0.32,  // slightly more opaque on the receiver
              0.18,                     // semi-transparent shadow volumes
            ],
          },
        })

        // Layer 7: server-provided rooftop segment overlay (3D extrusions on the roof)
        // Red segments = shaded, Green segments = direct sunlight
        // Offset slightly above roof height (base + 0.25, height + 0.55) to sit on top of 3D buildings
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
              'rooftop-shaded', '#DC2626',       // red = in shadow
              'rooftop-unobstructed', '#16A34A', // green = clear sky
              '#16A34A',
            ],
            'fill-extrusion-base': ['+', ['coalesce', ['get', 'roof_height'], 0], 0.25],
            'fill-extrusion-height': ['+', ['coalesce', ['get', 'roof_height'], 0], 0.55],
            'fill-extrusion-opacity': 0.62,
          },
        })

        // Layer 8: red outline around the selected (receiver) building when in shadow
        // The opacity expression hides the outline for non-receiver features (avoids all shadows getting outlined)
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
              'shadow-receiver', 0.9,  // visible for the analysed building
              0,                        // invisible for shadow volumes
            ],
          },
        })

        // Layers 9a-9e: thin outlines matching each roof type's hatch — reinforces the visual grouping
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

        // Apply the current filter state (in case the user had filters active before the map loaded)
        applyFilters()

        try {
          // Layer 10 (optional): precinct boundary outlines in dark green.
          // Only draw boundaries for precincts that have at least one building with data.
          // Algorithm:
          //   1. Pre-compute bounding boxes for all precinct polygons (cheap initial filter)
          //   2. Loop through building features — for each, check which precinct it falls in
          //   3. Once we've found one building per precinct, stop early (Set.size === pFeatures.length)
          // This is the same algorithm used in PrecinctsView.aggregateBuildings().
          const pRes = await fetchGeoJson(PRECINCTS_PATH).catch(() => null)
          if (pRes) {
            const precinctData = await pRes.json()
            const pFeatures = precinctData.features
            const bboxes = pFeatures.map(_pBBox)  // pre-compute one bounding box per precinct

            const hasData = new Set()  // set of precinct_ids that have at least one building
            for (const bf of data.features) {
              if (hasData.size === pFeatures.length) break  // early exit: all precincts found
              const px = bf.properties.lng, py = bf.properties.lat
              if (!px || !py) continue  // skip buildings without coordinates
              for (let pi = 0; pi < pFeatures.length; pi++) {
                if (hasData.has(pFeatures[pi].properties.precinct_id)) continue  // already found
                const bb = bboxes[pi]
                // Bounding box pre-filter: skip if the building can't possibly be in this precinct
                if (!bb || px < bb.minX || px > bb.maxX || py < bb.minY || py > bb.maxY) continue
                if (!_pInFeature(px, py, pFeatures[pi])) continue  // precise point-in-polygon check
                hasData.add(pFeatures[pi].properties.precinct_id)
                break  // this building is in precinct pi — move to the next building
              }
            }

            map.addSource('melbourne-precincts-explore', { type: 'geojson', data: precinctData })
            map.addLayer({
              id: 'precinct-boundary',
              type: 'line',
              source: 'melbourne-precincts-explore',
              // Only draw outlines for precincts in our hasData set
              filter: ['in', ['get', 'precinct_id'], ['literal', [...hasData]]],
              paint: {
                'line-color': '#1B5E20',  // dark green — matches the solar theme palette
                'line-width': 1.5,
                'line-opacity': 0.85,
              },
            })
          }
        } catch { /* silently skip if precinct file unavailable */ }

        // Map click handler: fires when the user clicks on a building extrusion.
        // event.features[0] contains the GeoJSON properties of the clicked building.
        map.on('click', 'building-extrusion', async (event) => {
          if (!event.features?.length) return
          const props = event.features[0].properties

          // Update reactive state immediately so the sidebar shows a loading placeholder
          selectedBuilding.value = props
          solarApiData.value = null    // clear old building's data right away
          yieldData.value = null
          selectedAddress.value = null
          solarApiLoading.value = true
          sidebarOpen.value = true     // ensure the sidebar is visible

          updateHighlights()  // immediately colour this building blue on the map

          const lng = Number(props.lng)
          const lat = Number(props.lat)
          if (lat && lng) {
            map.flyTo({
              center: [lng, lat],
              zoom: Math.max(map.getZoom(), 15.5),  // zoom in to at least 15.5 (building-level)
              pitch: 55,
              duration: 1200,
              easing: (t) => (t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t),
            })
          }

          // Fetch solar and yield data simultaneously — Promise.all waits for both
          const sid = Number(props.structure_id)
          ;[solarApiData.value, yieldData.value] = await Promise.all([
            fetchSolarApiData(sid),
            fetchYieldData(sid),
          ])
          // Address may already be in the Solar API response; only hit the address endpoint if not
          selectedAddress.value = solarApiData.value?.address || await fetchAddressForBuilding(sid)
          solarApiLoading.value = false

          updateSunSimulation()  // update shadow overlay for the newly selected building
        })

        // Show a pointer cursor when hovering over a clickable building
        map.on('mouseenter', 'building-extrusion', () => {
          map.getCanvas().style.cursor = 'pointer'
        })
        map.on('mouseleave', 'building-extrusion', () => {
          map.getCanvas().style.cursor = ''  // restore default cursor
        })

        // Check if the URL has a ?buildingId= parameter and auto-select that building
        await openBuildingFromUrl()
      })
      .catch((err) => {
        console.error(err)
        loadingText.value = `Error loading buildings: ${err.message}`  // shown in the loading overlay
      })
  })
}

// onMounted runs once, immediately after Vue has attached this component's <template>
// to the actual webpage. The 50ms setTimeout is a small safety margin to ensure the
// #map <div> has been fully painted by the browser before MapLibre tries to attach to it.
// Without this delay, MapLibre's canvas resize logic can misread the container dimensions.
onMounted(() => {
  setTimeout(() => {
    if (!map) initMap()  // guard against React StrictMode / hot-reload double-mounting
  }, 50)
})

// onActivated fires every time the user navigates back to this page while it is
// kept alive in memory. onMounted only fires once (on first creation), so we need
// this hook to respond to fresh deep-link parameters set by the Home page CTAs.
onActivated(() => {
  if (route.query.buildingId) {
    openBuildingFromUrl()
  }
})

// onUnmounted runs when the user navigates away from this page.
// IMPORTANT: because App.vue wraps this component in <KeepAlive>, this component is NOT
// actually destroyed when you click to another tab — it stays mounted. onUnmounted only
// fires when the app is fully closed or the route is permanently removed.
// We still clean up timers and the map to release GPU memory and prevent leaks.
onUnmounted(() => {
  if (toastTimer) clearTimeout(toastTimer)

  stopSunAnimation()  // stop the setInterval timer if the animation was running

  if (map) {
    map.remove()  // releases the WebGL context and frees GPU memory
    map = null
  }
})
</script>
