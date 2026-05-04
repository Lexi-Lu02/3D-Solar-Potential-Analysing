<template>
  <div class="comparison-panel" role="region" aria-label="Building comparison panel" aria-live="polite">

    <!-- Header -->
    <div class="comparison-header">
      <div class="comparison-header-left">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true" class="comparison-header-icon">
          <rect x="1" y="3" width="6" height="10" rx="1.5" stroke="currentColor" stroke-width="1.5"/>
          <rect x="9" y="3" width="6" height="10" rx="1.5" stroke="currentColor" stroke-width="1.5"/>
        </svg>
        <span class="comparison-title" id="compare-panel-title">Building Comparison</span>
        <span class="comparison-count" :aria-label="`${compareBuildings.length} of 2 buildings selected`">
          {{ compareBuildings.length }} / 2
        </span>

        <button
          class="compare-add-btn"
          @click="$emit('add')"
          :disabled="!selectedBuilding || isAlreadyAdded"
          :class="{ 'compare-add-btn--added': isAlreadyAdded }"
          :aria-label="isAlreadyAdded ? 'Building already in comparison' : 'Add selected building to comparison'"
        >
          <svg v-if="isAlreadyAdded" width="13" height="13" viewBox="0 0 13 13" fill="none" aria-hidden="true">
            <path d="M2 6.5l3.5 3.5 5.5-6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <svg v-else width="13" height="13" viewBox="0 0 13 13" fill="none" aria-hidden="true">
            <path d="M6.5 2v9M2 6.5h9" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
          </svg>
          {{ isAlreadyAdded ? 'Added to Compare' : 'Add to Compare' }}
        </button>

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

      <button class="comparison-close-btn" @click="$emit('close')" aria-label="Close comparison panel">
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
          <path d="M2 2l10 10M12 2L2 12" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
        </svg>
      </button>
    </div>

    <!-- Body -->
    <div class="comparison-body" aria-labelledby="compare-panel-title">

      <!-- Building columns -->
      <div
        v-for="(item, col) in compareBuildings"
        :key="item.building.structure_id"
        class="comparison-col"
      >
        <div class="comparison-col-header">
          <div class="comparison-col-label">Building {{ col + 1 }}</div>
          <div class="comparison-building-id">
            {{ shortAddress(item.apiData?.address) || '#' + item.building.structure_id }}
          </div>
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

        <!-- Score hero -->
        <div class="comparison-score-hero">
          <div class="comparison-score-circle" :style="{ '--score-color': scoreColor(item.building.solar_score) }">
            <span class="comparison-score-num">{{ item.building.solar_score ?? '—' }}</span>
            <span class="comparison-score-unit">/100</span>
          </div>
          <div class="comparison-score-meta">
            <div
              class="comparison-tier-badge"
              :style="{
                background:   scoreColor(item.building.solar_score) + '22',
                color:        scoreColor(item.building.solar_score),
                borderColor:  scoreColor(item.building.solar_score) + '55',
              }"
            >
              {{ scoreTier(item.building.solar_score) }}
            </div>
            <div class="comparison-score-bar-track">
              <div
                class="comparison-score-bar-fill"
                :style="{ width: Math.min(100, item.building.solar_score || 0) + '%', background: scoreColor(item.building.solar_score) }"
              ></div>
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

      <!-- VS divider -->
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
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  compareBuildings: { type: Array,  required: true },
  selectedBuilding: { type: Object, default: null },
  activePanel: { type: String, default: 'details' },
})

defineEmits(['add', 'remove', 'clear', 'close'])

const isAlreadyAdded = computed(() =>
  props.selectedBuilding != null &&
  props.compareBuildings.some(c => c.building.structure_id === props.selectedBuilding.structure_id)
)

const compareWinners = computed(() => {
  if (props.compareBuildings.length < 2) return []
  const m0 = compareMetrics(props.compareBuildings[0])
  const m1 = compareMetrics(props.compareBuildings[1])
  return m0.map((_, i) => {
    if (m0[i].better === 'none') return [false, false]
    if (m0[i].raw === null || m1[i].raw === null) return [false, false]
    if (m0[i].better === 'lower') {
      if (m0[i].raw < m1[i].raw) return [true, false]
      if (m1[i].raw < m0[i].raw) return [false, true]
      return [false, false]
    }
    if (m0[i].raw > m1[i].raw) return [true, false]
    if (m1[i].raw > m0[i].raw) return [false, true]
    return [false, false]
  })
})

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

function shortAddress(addr) {
  if (!addr) return '—'
  return addr.split(',').slice(0, 3).join(',').trim()
}

function compareMetrics(item) {
  if (props.activePanel === 'finance') return compareFinanceMetrics(item)
  if (props.activePanel === 'env') return compareEnvMetrics(item)
  return compareSolarMetrics(item)
}

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
    { label: 'Roof Type',        display: b.roof_type || '—',                                             raw: null,                   better: 'none' },
    { label: 'Sun Intensity',    display: sunIntensity != null ? sunIntensity.toFixed(1) + ' kWh/m²/day' : '—', raw: sunIntensity,          better: 'higher' },
    { label: 'Annual kWh',       display: kwh != null ? Number(kwh).toLocaleString() + ' kWh' : '—',      raw: kwh,                    better: 'higher' },
    { label: 'Usable Area',      display: area != null ? Number(area).toFixed(1) + ' m²' : '—',           raw: area,                   better: 'higher' },
    { label: 'Usable Ratio',     display: usableRatio != null ? usableRatio + '%' : '—',                   raw: usableRatio,            better: 'higher' },
    { label: 'Max Solar Panels', display: maxPanels != null ? Number(maxPanels).toLocaleString() : '—',   raw: maxPanels,              better: 'higher' },
  ]
}

function compareFinanceMetrics(item) {
  const f = item.analysis?.finance
  return [
    { label: 'Est. Payback',      display: f?.paybackYears != null ? `${f.paybackYears} yrs` : '—',              raw: f?.paybackYears ?? null, better: 'lower' },
    { label: 'Annual Savings',    display: f?.annualSavings != null ? `$${f.annualSavings.toLocaleString()}` : '—', raw: f?.annualSavings ?? null, better: 'higher' },
    { label: 'Installation Cost', display: f?.installCost != null ? `$${f.installCost.toLocaleString()}` : '—',     raw: f?.installCost ?? null,   better: 'lower' },
    { label: 'Annual Generation', display: f?.annualKwh != null ? `${f.annualKwh.toLocaleString()} kWh` : '—',      raw: f?.annualKwh ?? null,      better: 'higher' },
    { label: 'Max Solar Panels',  display: f?.maxPanels != null ? f.maxPanels.toLocaleString() : '—',               raw: f?.maxPanels ?? null,      better: 'higher' },
  ]
}

function compareEnvMetrics(item) {
  const e = item.analysis?.env
  return [
    { label: 'CO₂ Reduction',      display: e?.co2Kg != null ? `${e.co2Kg.toLocaleString()} kg/yr` : '—',       raw: e?.co2Kg ?? null,        better: 'higher' },
    { label: 'Trees Equivalent',   display: e?.treesEquiv != null ? `${e.treesEquiv.toLocaleString()} /yr` : '—', raw: e?.treesEquiv ?? null,    better: 'higher' },
    { label: 'Cars Off Road',      display: e?.carsOffRoad != null ? `${e.carsOffRoad.toLocaleString()} /yr` : '—', raw: e?.carsOffRoad ?? null,   better: 'higher' },
    { label: 'Homes Powered',      display: e?.homesPowered != null ? `${e.homesPowered.toLocaleString()} /yr` : '—', raw: e?.homesPowered ?? null, better: 'higher' },
    { label: 'Lifetime CO₂ Saved', display: e?.lifetimeCo2T != null ? `${e.lifetimeCo2T.toLocaleString()} t` : '—', raw: e?.lifetimeCo2T ?? null,  better: 'higher' },
  ]
}
</script>

<style scoped>
.comparison-panel {
  position: absolute; bottom: 0; left: 0; right: 0;
  background: var(--ink);
  border-top: 2px solid var(--ink-active-border);
  box-shadow: 0 -8px 32px rgba(0,0,0,0.45);
  z-index: 20;
  padding: 16px 24px 20px;
}

/* Header */
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

/* Add / Clear buttons */
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
.compare-add-btn--added { background: var(--solar-very-high); box-shadow: none; }
.compare-add-btn--added:hover:not(:disabled) { background: var(--solar-high); box-shadow: none; }
.compare-add-btn:disabled { opacity: 0.45; cursor: not-allowed; box-shadow: none; }
.compare-add-btn:focus-visible { outline: 3px solid var(--accent); outline-offset: 2px; }

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

/* Body */
.comparison-body {
  display: flex; gap: 32px; align-items: stretch; position: relative;
}

/* Building column */
.comparison-col {
  flex: 1;
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

/* Score hero */
.comparison-score-hero {
  display: flex; align-items: center; gap: 14px;
  background: rgba(0,0,0,0.25); border-radius: 10px; padding: 10px 14px;
}
.comparison-score-circle {
  display: flex; flex-direction: column; align-items: center;
  width: 52px; height: 52px; border-radius: 50%;
  border: 3px solid var(--score-color, #BE3820);
  background: rgba(0,0,0,0.3); justify-content: center; flex-shrink: 0;
  box-shadow: 0 0 12px color-mix(in srgb, var(--score-color, #BE3820) 30%, transparent);
}
.comparison-score-num {
  font-family: 'DM Serif Display', serif;
  font-size: 18px; line-height: 1; color: var(--nav-text); font-weight: 700;
}
.comparison-score-unit { font-size: 8px; color: var(--nav-text-muted); margin-top: 1px; }
.comparison-score-meta { flex: 1; display: flex; flex-direction: column; gap: 8px; }
.comparison-tier-badge {
  font-size: 13px; font-weight: 700; padding: 3px 10px;
  border-radius: 20px; border: 1px solid; display: inline-block; align-self: flex-start;
}
.comparison-score-bar-track {
  height: 5px; background: rgba(255,255,255,0.08); border-radius: 3px; overflow: hidden;
}
.comparison-score-bar-fill { height: 100%; border-radius: 3px; transition: width 0.5s ease; }

/* Metrics */
.comparison-metrics { display: flex; flex-direction: column; gap: 0; }
.comparison-metric-row {
  display: flex; justify-content: space-between; align-items: center;
  font-size: 14px; padding: 7px 8px; border-radius: 6px; transition: background 0.15s;
}
.comparison-metric-label { color: var(--nav-link); }
.comparison-metric-val { font-weight: 600; color: var(--nav-text); display: flex; align-items: center; gap: 5px; }
.comparison-winner { background: rgba(190,56,32,0.12); border: 1px solid rgba(190,56,32,0.20); }
.comparison-winner .comparison-metric-label { color: var(--nav-link); }
.comparison-winner .comparison-metric-val { color: var(--nav-active-color); }
.comparison-winner-badge { font-size: 13px; color: #FBBF24; filter: drop-shadow(0 0 4px rgba(251,191,36,0.6)); }

/* VS divider */
.comparison-vs {
  position: absolute; left: 50%; top: 50%;
  transform: translate(-50%, -50%);
  width: 32px; height: 32px;
  display: flex; align-items: center; justify-content: center;
  font-size: 13px; font-weight: 800; color: var(--nav-text-muted); letter-spacing: 1px;
  background: var(--ink); border: 1px solid var(--ink-border); border-radius: 50%;
  z-index: 2; pointer-events: none;
}

/* Empty slot */
.comparison-empty-col {
  flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 10px; border: 2px dashed rgba(255,255,255,0.12);
  border-radius: 12px; min-height: 120px; padding: 20px;
}
.comparison-empty-icon { color: rgba(255,255,255,0.20); }
.comparison-empty-hint { font-size: 13px; color: var(--nav-text-muted); text-align: center; line-height: 1.7; }
.comparison-empty-hint strong { color: var(--nav-link); }
</style>
