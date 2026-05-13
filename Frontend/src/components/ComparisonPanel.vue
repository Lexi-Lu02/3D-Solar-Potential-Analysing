<template>
  <!--
    ComparisonPanel.vue — A dark panel that slides up from the bottom of the map,
    showing two buildings side-by-side with their metrics compared.

    Layout:
      Header row: title | "Add to Compare" button | "Clear All" button | Close button
      Body row:   [Building 1 column]  VS  [Building 2 column / empty slot]

    Each building column shows:
      • A circle with its solar score and a tier badge
      • A list of metrics for the active tab (Solar / Finance / Environment)
      • The "winner" metric in each row is highlighted with a star ★

    When fewer than 2 buildings are in the list, an empty dashed slot is shown
    to invite the user to add another building.
  -->
  <div class="comparison-panel" role="region" aria-label="Building comparison panel" aria-live="polite">

    <!-- ── Header ── -->
    <div class="comparison-header">
      <div class="comparison-header-left">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true" class="comparison-header-icon">
          <rect x="1" y="3" width="6" height="10" rx="1.5" stroke="currentColor" stroke-width="1.5"/>
          <rect x="9" y="3" width="6" height="10" rx="1.5" stroke="currentColor" stroke-width="1.5"/>
        </svg>
        <span class="comparison-title" id="compare-panel-title">Building Comparison</span>

        <!-- Count badge: "1 / 2" or "2 / 2" -->
        <span class="comparison-count" :aria-label="`${compareBuildings.length} of 2 buildings selected`">
          {{ compareBuildings.length }} / 2
        </span>

        <!--
          "Add to Compare" button.
          :disabled="!selectedBuilding || isAlreadyAdded" disables it when:
            • No building is selected on the map, OR
            • The selected building is already in the comparison list.
          isAlreadyAdded is a computed property (see script section).
        -->
        <button
          class="compare-add-btn"
          @click="$emit('add')"
          :disabled="!selectedBuilding || isAlreadyAdded"
          :class="{ 'compare-add-btn--added': isAlreadyAdded }"
          :aria-label="isAlreadyAdded ? 'Building already in comparison' : 'Add selected building to comparison'"
        >
          <!-- Checkmark icon when already added -->
          <svg v-if="isAlreadyAdded" width="13" height="13" viewBox="0 0 13 13" fill="none" aria-hidden="true">
            <path d="M2 6.5l3.5 3.5 5.5-6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <!-- Plus icon when not yet added -->
          <svg v-else width="13" height="13" viewBox="0 0 13 13" fill="none" aria-hidden="true">
            <path d="M6.5 2v9M2 6.5h9" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
          </svg>
          {{ isAlreadyAdded ? 'Added to Compare' : 'Add to Compare' }}
        </button>

        <!--
          "Clear All" button — only shows when there's at least one building to clear.
          v-if="compareBuildings.length > 0" hides it when the list is empty.
        -->
        <button
          v-if="compareBuildings.length > 0"
          class="compare-clear-footer-btn"
          @click="$emit('clear')"
          aria-label="Clear all comparison buildings"
        >
          <svg width="13" height="13" viewBox="0 0 13 13" fill="none" aria-hidden="true">
            <path d="M2 2l9 9M11 2l-9 9" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
          </svg>
          Clear All
        </button>
      </div>

      <!-- Close the panel -->
      <button class="comparison-close-btn" @click="$emit('close')" aria-label="Close comparison panel">
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
          <path d="M2 2l10 10M12 2L2 12" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
        </svg>
      </button>
    </div>

    <!-- ── Body: Building columns ── -->
    <div class="comparison-body" aria-labelledby="compare-panel-title">

      <!--
        v-for loops over compareBuildings (max 2 items).
        Each `item` contains:  { building: {...}, apiData: {...}, analysis: {...} }
        `col` is 0 for Building 1, 1 for Building 2.
      -->
      <div
        v-for="(item, col) in compareBuildings"
        :key="item.building.structure_id"
        class="comparison-col"
      >
        <!-- Building label + address + remove button -->
        <div class="comparison-col-header">
          <div class="comparison-col-label">Building {{ col + 1 }}</div>
          <div class="comparison-building-id">
            <!--
              shortAddress() trims a long address to the first three comma-separated parts.
              Falls back to the structure_id if no address is available.
            -->
            {{ shortAddress(item.apiData?.address) || '#' + item.building.structure_id }}
          </div>
          <!-- Remove this building from the comparison -->
          <button
            class="comparison-remove-btn"
            @click="$emit('remove', col)"
            :aria-label="`Remove Structure ${item.building.structure_id} from comparison`"
          >
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true">
              <path d="M1.5 1.5l9 9M10.5 1.5l-9 9" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
            </svg>
          </button>
        </div>

        <!-- Score card — mirrors the sidebar's score-bar-wrap layout (0–5 scale) -->
        <div class="comparison-score-card">
          <div class="comparison-score-row">
            <span class="comparison-score-label">Solar Score</span>
            <span class="comparison-score-num" :style="{ color: scoreColor(item.analysis.solar.scoreAvg) }">
              {{ item.analysis.solar.scoreAvg != null ? item.analysis.solar.scoreAvg.toFixed(1) : '—' }}<span class="comparison-score-unit">/ 5</span>
            </span>
          </div>
          <div class="comparison-score-bar-track">
            <div
              class="comparison-score-bar-fill"
              :style="{
                width: item.analysis.solar.scoreAvg != null ? Math.min(100, (item.analysis.solar.scoreAvg / 5) * 100) + '%' : '0%',
                background: scoreColor(item.analysis.solar.scoreAvg)
              }"
            ></div>
          </div>
          <div
            class="comparison-tier-badge"
            :style="{
              background:  scoreColor(item.analysis.solar.scoreAvg) + '22',
              color:       scoreColor(item.analysis.solar.scoreAvg),
              borderColor: scoreColor(item.analysis.solar.scoreAvg) + '55',
            }"
          >{{ scoreTier(item.analysis.solar.scoreAvg) }}</div>
        </div>

        <!--
          Metric rows — content depends on which tab is active.
          compareMetrics(item) returns the correct set of metrics.
          compareWinners[mi]?.[col] is true when THIS building wins THIS metric.
        -->
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
              <!-- ★ star shown next to the winning building's value -->
              <span v-if="compareWinners[mi]?.[col]" class="comparison-winner-badge" aria-label="Winner">★</span>
            </span>
          </div>
        </div>
      </div>

      <!-- "VS" text shown between the two columns when both are filled -->
      <div v-if="compareBuildings.length === 2" class="comparison-vs" aria-hidden="true">VS</div>

      <!--
        Empty slot — shown when there is fewer than 2 buildings.
        Acts as a second "Add to Compare" button so the user can click the
        dashed area directly instead of using the header button.
      -->
      <button
        v-if="compareBuildings.length < 2"
        class="comparison-empty-col"
        :class="{ 'comparison-empty-col--active': selectedBuilding && !isAlreadyAdded }"
        @click="$emit('add')"
        :disabled="!selectedBuilding || isAlreadyAdded"
        :aria-label="isAlreadyAdded ? 'Building already added' : selectedBuilding ? 'Add selected building to comparison' : 'Select a building on the map first'"
      >
        <svg width="28" height="28" viewBox="0 0 28 28" fill="none" aria-hidden="true" class="comparison-empty-icon">
          <rect x="2" y="2" width="24" height="24" rx="4" stroke="currentColor" stroke-width="1.5" stroke-dasharray="4 3"/>
          <path d="M14 9v10M9 14h10" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
        </svg>
        <div class="comparison-empty-hint">Click a building,<br>then <strong>Add to Compare</strong></div>
      </button>
    </div>
  </div>
</template>

<script setup>
// ─────────────────────────────────────────────────────────────────────────────
// ComparisonPanel.vue — Script section
//
// This component receives up to two buildings from ExploreView and displays them
// side-by-side. It automatically determines which building "wins" each metric
// (higher kWh wins for energy, lower cost wins for payback, etc.)
// ─────────────────────────────────────────────────────────────────────────────

// computed creates a value that re-calculates automatically when its inputs change.
import { computed } from 'vue'

// ── Props — data passed in from ExploreView ────────────────────────────────────
const props = defineProps({
  // Array of up to 2 comparison items:
  // [{ building: {...geoJSON props}, apiData: {...Google Solar}, analysis: {...calculated} }]
  compareBuildings: { type: Array,  required: true },
  // The building currently selected on the map (used to enable/disable the Add button).
  selectedBuilding: { type: Object, default: null },
  // Which sidebar tab is active: 'details', 'finance', or 'env'.
  // Determines which metrics to show in the comparison.
  activePanel: { type: String, default: 'details' },
})

// Events this component can send back to ExploreView.
defineEmits(['add', 'remove', 'clear', 'close'])

// ── Computed: is the selected building already in the comparison? ────────────────
// Returns true if the currently-selected building's ID matches any building already
// in the compareBuildings list. Used to disable the "Add to Compare" button.
const isAlreadyAdded = computed(() =>
  props.selectedBuilding != null &&
  props.compareBuildings.some(c => c.building.structure_id === props.selectedBuilding.structure_id)
)

// ── Computed: which building wins each metric? ────────────────────────────────
// compareWinners is an array parallel to the metric rows.
// Each element is [col0Wins, col1Wins] — a boolean pair indicating which building
// is "better" for that metric.
//
// The "better" direction depends on the metric:
//   'higher' = bigger number is better (more kWh, more savings, more trees)
//   'lower'  = smaller number is better (shorter payback, cheaper cost)
//   'none'   = can't compare (e.g. roof type is a string, not a number)
const compareWinners = computed(() => {
  // Only calculate when we have exactly 2 buildings.
  if (props.compareBuildings.length < 2) return []

  const m0 = compareMetrics(props.compareBuildings[0])
  const m1 = compareMetrics(props.compareBuildings[1])

  return m0.map((_, i) => {
    // No comparison possible for this metric.
    if (m0[i].better === 'none') return [false, false]
    // Can't compare if either value is missing.
    if (m0[i].raw === null || m1[i].raw === null) return [false, false]

    if (m0[i].better === 'lower') {
      // Smaller value wins.
      if (m0[i].raw < m1[i].raw) return [true, false]
      if (m1[i].raw < m0[i].raw) return [false, true]
      return [false, false]  // tie
    }

    // Default: larger value wins.
    if (m0[i].raw > m1[i].raw) return [true, false]
    if (m1[i].raw > m0[i].raw) return [false, true]
    return [false, false]  // tie
  })
})

// ── Helper functions ──────────────────────────────────────────────────────────

// Returns the CSS colour for a 0–5 solar score (matches sidebar tierColor thresholds).
function scoreColor(score) {
  if (score == null) return 'var(--text-secondary)'
  const s = Number(score)
  if (s >= 4.5) return 'var(--solar-very-high)'
  if (s >= 3.5) return 'var(--solar-high)'
  if (s >= 2.5) return 'var(--solar-med)'
  if (s >= 1.5) return 'var(--solar-low)'
  return 'var(--solar-very-low)'
}

// Returns the human-readable tier label for a 0–5 solar score.
function scoreTier(score) {
  if (score == null) return 'No Data'
  const s = Number(score)
  if (s >= 4.5) return 'Excellent'
  if (s >= 3.5) return 'Good'
  if (s >= 2.5) return 'Moderate'
  if (s >= 1.5) return 'Poor'
  return 'Very Poor'
}

// Takes a full address like "123 Example Street, Melbourne, Victoria, 3000"
// and returns just the first three parts: "123 Example Street, Melbourne, Victoria"
function shortAddress(addr) {
  if (!addr) return '—'
  return addr.split(',').slice(0, 3).join(',').trim()
}

// ── Metric builders ────────────────────────────────────────────────────────────
// These functions return the correct set of metric rows depending on which tab is active.
// Each metric has:
//   label   → the display name
//   display → formatted string to show in the UI (e.g. "12,345 kWh")
//   raw     → the numeric value used for winner comparison (null = can't compare)
//   better  → 'higher', 'lower', or 'none'

function compareMetrics(item) {
  if (props.activePanel === 'finance') return compareFinanceMetrics(item)
  if (props.activePanel === 'env')     return compareEnvMetrics(item)
  return compareSolarMetrics(item)
}

// Solar Potential tab metrics.
function compareSolarMetrics(item) {
  const b = item.building
  const api = item.apiData
  const solar = item.analysis?.solar
  const kwh = solar?.annualKwh ?? api?.kwhAnnual ?? null
  const area = api?.usableAreaM2 ?? null
  const roofArea = api?.roofAreaM2 ?? null
  const usableRatio = area != null && roofArea ? Math.round((area / roofArea) * 100) : null
  const maxPanels = api?.maxPanels ?? null
  const sunHours = api?.sunshineHours ?? null
  const sunIntensity = sunHours != null ? Math.round((sunHours / 365) * 10) / 10 : null
  return [
    { label: 'Roof Type',        display: b.roof_type || '—',                                             raw: null,         better: 'none' },
    { label: 'Sun Intensity',    display: sunIntensity != null ? sunIntensity.toFixed(1) + ' kWh/m²/day' : '—', raw: sunIntensity, better: 'higher' },
    { label: 'Annual kWh',       display: kwh != null ? Number(kwh).toLocaleString() + ' kWh' : '—',      raw: kwh,          better: 'higher' },
    { label: 'Usable Area',      display: area != null ? Number(area).toFixed(1) + ' m²' : '—',           raw: area,         better: 'higher' },
    { label: 'Usable Ratio',     display: usableRatio != null ? usableRatio + '%' : '—',                   raw: usableRatio,  better: 'higher' },
    { label: 'Max Solar Panels', display: maxPanels != null ? Number(maxPanels).toLocaleString() : '—',   raw: maxPanels,    better: 'higher' },
  ]
}

// Financial Analysis tab metrics.
function compareFinanceMetrics(item) {
  const f = item.analysis?.finance
  return [
    { label: 'Est. Payback',      display: f?.paybackYears != null ? `${f.paybackYears} yrs` : '—',               raw: f?.paybackYears ?? null, better: 'lower' },  // fewer years = better
    { label: 'Annual Savings',    display: f?.annualSavings != null ? `$${f.annualSavings.toLocaleString()}` : '—', raw: f?.annualSavings ?? null, better: 'higher' },
    { label: 'Installation Cost', display: f?.installCost != null ? `$${f.installCost.toLocaleString()}` : '—',    raw: f?.installCost ?? null,   better: 'lower' },  // cheaper = better
    { label: 'Annual Generation', display: f?.annualKwh != null ? `${f.annualKwh.toLocaleString()} kWh` : '—',    raw: f?.annualKwh ?? null,     better: 'higher' },
    { label: 'Max Solar Panels',  display: f?.maxPanels != null ? f.maxPanels.toLocaleString() : '—',              raw: f?.maxPanels ?? null,     better: 'higher' },
  ]
}

// Environmental Impact tab metrics.
function compareEnvMetrics(item) {
  const e = item.analysis?.env
  return [
    { label: 'CO₂ Reduction',      display: e?.co2Kg != null ? `${e.co2Kg.toLocaleString()} kg/yr` : '—',        raw: e?.co2Kg ?? null,        better: 'higher' },
    { label: 'Trees Equivalent',   display: e?.treesEquiv != null ? `${e.treesEquiv.toLocaleString()} /yr` : '—', raw: e?.treesEquiv ?? null,    better: 'higher' },
    { label: 'Cars Off Road',      display: e?.carsOffRoad != null ? `${e.carsOffRoad.toLocaleString()} /yr` : '—', raw: e?.carsOffRoad ?? null,   better: 'higher' },
    { label: 'Homes Powered',      display: e?.homesPowered != null ? `${e.homesPowered.toLocaleString()} /yr` : '—', raw: e?.homesPowered ?? null, better: 'higher' },
    { label: 'Lifetime CO₂ Saved', display: e?.lifetimeCo2T != null ? `${e.lifetimeCo2T.toLocaleString()} t` : '—', raw: e?.lifetimeCo2T ?? null,  better: 'higher' },
  ]
}
</script>

<style scoped>
/* Dark panel anchored to the bottom of the map area */
.comparison-panel {
  position: absolute; bottom: 0; left: 0; right: 0;
  background: var(--ink);
  border-top: 2px solid var(--ink-active-border);  /* orange top border */
  box-shadow: 0 -8px 32px rgba(0,0,0,0.45);
  z-index: 20;
  padding: 16px 24px 20px;
}

/* Header row */
.comparison-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 14px;
}
.comparison-header-left { display: flex; align-items: center; gap: 10px; }
.comparison-header-icon { color: var(--nav-active-color); }
.comparison-title {
  font-size: 13px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.8px; color: var(--nav-text); white-space: nowrap;
}
.comparison-count {
  background: rgba(190,56,32,0.18); color: var(--nav-active-color);
  font-size: 13px; font-weight: 600;
  padding: 2px 9px; border-radius: 20px;
  border: 1px solid rgba(190,56,32,0.40);
}
.comparison-close-btn {
  background: rgba(255,255,255,0.06); border: 1px solid var(--ink-border);
  cursor: pointer; color: var(--nav-text-muted); padding: 5px 7px;
  border-radius: 6px; transition: background 0.15s, color 0.15s;
  display: flex; align-items: center;
}
.comparison-close-btn:hover { background: var(--ink2); color: var(--nav-text); }
.comparison-close-btn:focus-visible { outline: 3px solid var(--accent); outline-offset: 2px; }

/* Orange "Add to Compare" button */
.compare-add-btn {
  padding: 5px 12px;
  background: var(--city-light); color: #fff;
  border: none; border-radius: 8px;
  font-family: 'DM Sans', sans-serif; font-size: 13px; font-weight: 600;
  cursor: pointer; flex-shrink: 0;
  display: flex; align-items: center; gap: 7px;
  box-shadow: 0 2px 10px rgba(212,116,58,0.40);
  border-left: 1px solid var(--ink-border); padding-left: 16px; margin-left: 8px;
}
.compare-add-btn:hover:not(:disabled) { background: var(--city-light-dim); box-shadow: 0 4px 14px rgba(212,116,58,0.55); }
.compare-add-btn--added { background: var(--solar-very-high); box-shadow: none; }  /* green when already added */
.compare-add-btn--added:hover:not(:disabled) { background: var(--solar-high); box-shadow: none; }
.compare-add-btn:disabled { opacity: 0.45; cursor: not-allowed; box-shadow: none; }
.compare-add-btn:focus-visible { outline: 3px solid var(--accent); outline-offset: 2px; }

/* "Clear All" button */
.compare-clear-footer-btn {
  display: flex; align-items: center; gap: 6px;
  font-size: 13px; font-weight: 600; font-family: 'DM Sans', sans-serif;
  color: var(--nav-text-muted); cursor: pointer;
  background: rgba(255,255,255,0.06); border: 1px solid var(--ink-border); border-radius: 8px;
  padding: 5px 12px; flex-shrink: 0;
  transition: background 0.15s, color 0.15s;
}
.compare-clear-footer-btn:hover { background: var(--ink2); color: var(--nav-text); }
.compare-clear-footer-btn:focus-visible { outline: 3px solid var(--accent); outline-offset: 2px; }

/* Body containing the two building columns */
.comparison-body {
  display: flex; gap: 16px; align-items: stretch; position: relative;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch; /* smooth momentum scrolling on iOS */
  padding-bottom: 4px;              /* space for the scrollbar so it doesn't overlap content */
}

/* One building's column */
.comparison-col {
  flex: 1 1 260px;   /* grow to fill available space on wide screens, min 260px before scrolling */
  min-width: 260px;
  background: var(--ink2); border: 1px solid var(--ink-border);
  border-radius: 12px; padding: 16px 18px;
  display: flex; flex-direction: column; gap: 12px;
}
.comparison-col-header { display: flex; align-items: center; gap: 8px; margin-bottom: 2px; }
.comparison-col-label {
  font-size: 13px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.8px; color: var(--nav-active-color);
  background: rgba(190,56,32,0.15); border: 1px solid rgba(190,56,32,0.30);
  padding: 2px 7px; border-radius: 20px; flex-shrink: 0;
}
.comparison-building-id {
  display: flex; align-items: center; gap: 4px;
  font-size: 13px; font-weight: 600; color: var(--nav-text); flex: 1;
}
.comparison-remove-btn {
  background: rgba(255,255,255,0.05); border: 1px solid var(--ink-border);
  cursor: pointer; color: var(--nav-text-muted); padding: 4px;
  border-radius: 5px; display: flex; align-items: center;
  transition: background 0.15s, color 0.15s; flex-shrink: 0;
}
.comparison-remove-btn:hover { background: rgba(239,68,68,0.15); color: #FCA5A5; border-color: rgba(239,68,68,0.3); }
.comparison-remove-btn:focus-visible { outline: 3px solid var(--accent); outline-offset: 2px; }

/* Score card — mirrors sidebar score-bar-wrap */
.comparison-score-card {
  background: rgba(0,0,0,0.25);
  border-radius: 10px;
  padding: 10px 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.comparison-score-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}
.comparison-score-label {
  font-size: 12px; font-weight: 600; text-transform: uppercase;
  letter-spacing: 0.5px; color: var(--nav-text-muted);
}
.comparison-score-num {
  font-family: 'DM Serif Display', serif;
  font-size: 22px; font-weight: 700; line-height: 1;
}
.comparison-score-unit {
  font-size: 11px; color: var(--nav-text-muted);
  font-family: 'DM Sans', sans-serif; font-weight: 400; margin-left: 2px;
}
.comparison-score-bar-track {
  height: 7px; background: rgba(255,255,255,0.08); border-radius: 4px; overflow: hidden;
}
.comparison-score-bar-fill { height: 100%; border-radius: 4px; transition: width 0.5s ease; }
.comparison-tier-badge {
  font-size: 12px; font-weight: 700; padding: 2px 9px;
  border-radius: 20px; border: 1px solid; display: inline-block; align-self: flex-start;
}

/* Metric rows */
.comparison-metrics { display: flex; flex-direction: column; gap: 0; }
.comparison-metric-row {
  display: flex; justify-content: space-between; align-items: center;
  font-size: 14px; padding: 7px 8px; border-radius: 6px; transition: background 0.15s;
}
.comparison-metric-label { color: var(--nav-link); }
.comparison-metric-val { font-weight: 600; color: var(--nav-text); display: flex; align-items: center; gap: 5px; }

/* Highlighted row for the winning building */
.comparison-winner { background: rgba(190,56,32,0.12); border: 1px solid rgba(190,56,32,0.20); }
.comparison-winner .comparison-metric-label { color: var(--nav-link); }
.comparison-winner .comparison-metric-val { color: var(--nav-active-color); }

/* ★ star badge next to the winning value */
.comparison-winner-badge { font-size: 13px; color: #FBBF24; filter: drop-shadow(0 0 4px rgba(251,191,36,0.6)); }

/* "VS" circle between the two columns */
.comparison-vs {
  position: absolute; left: 50%; top: 50%;
  transform: translate(-50%, -50%);
  width: 32px; height: 32px;
  display: flex; align-items: center; justify-content: center;
  font-size: 13px; font-weight: 800; color: var(--nav-text-muted); letter-spacing: 1px;
  background: var(--ink); border: 1px solid var(--ink-border); border-radius: 50%;
  z-index: 2; pointer-events: none;
}

/* Empty dashed slot — now a <button> that triggers add-to-compare */
.comparison-empty-col {
  flex: 1 1 260px; min-width: 260px;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 10px; border: 2px dashed rgba(255,255,255,0.12);
  border-radius: 12px; min-height: 120px; padding: 20px;
  background: none; font-family: 'DM Sans', sans-serif;
  cursor: not-allowed;           /* disabled by default until a building is selected */
  transition: border-color 0.18s, background 0.18s;
}

/* When a building IS selected, show the slot as interactive */
.comparison-empty-col--active {
  cursor: pointer;
  border-color: rgba(212,116,58,0.40);   /* orange dashed border */
}
.comparison-empty-col--active:hover {
  background: rgba(212,116,58,0.08);
  border-color: var(--city-light);
}
.comparison-empty-col--active:hover .comparison-empty-icon {
  color: var(--city-light);
}
.comparison-empty-col:focus-visible {
  outline: 3px solid var(--city-light);
  outline-offset: 2px;
}

.comparison-empty-icon { color: rgba(255,255,255,0.20); transition: color 0.18s; }
.comparison-empty-hint { font-size: 13px; color: var(--nav-text-muted); text-align: center; line-height: 1.7; }
.comparison-empty-hint strong { color: var(--nav-link); }
</style>
