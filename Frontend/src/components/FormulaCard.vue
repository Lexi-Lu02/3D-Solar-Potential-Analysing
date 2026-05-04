<template>
  <div class="formula-card">
    <button
      class="formula-card-toggle"
      @click="formulaCardOpen = !formulaCardOpen"
      :aria-expanded="formulaCardOpen"
    >
      <span class="formula-card-title">How We Calculate Annual Generation</span>
      <svg
        class="chevron-icon"
        :class="{ 'chevron-up': formulaCardOpen }"
        width="13" height="13" viewBox="0 0 14 14" fill="none" aria-hidden="true"
      >
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
          <span class="formula-row-label">Annual Electricity Generation</span>
          <span class="formula-row-val">{{ formulaKwhAnnual.toLocaleString() }} kWh</span>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  formulaKwhAnnual: { type: Number, required: true },
  solarApiData:     { type: Object, default: null },
  selectedBuilding: { type: Object, default: null },
})

const formulaCardOpen = ref(false)
</script>

<style scoped>
.formula-card {
  margin: 0 0 16px;
  padding: 12px 14px;
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: 8px;
}

.formula-card-toggle {
  width: 100%; display: flex; align-items: center; justify-content: space-between;
  background: none; border: none; cursor: pointer; padding: 0; gap: 6px;
  font-family: 'DM Sans', sans-serif;
}

.formula-card-toggle .chevron-icon { color: var(--text-muted); }

.formula-card-title {
  font-size: 12px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.07em; color: var(--text-muted);
}

.formula-collapse-enter-active,
.formula-collapse-leave-active {
  transition: opacity 0.2s ease, max-height 0.25s ease;
  overflow: hidden;
  max-height: 400px;
}
.formula-collapse-enter-from,
.formula-collapse-leave-to { opacity: 0; max-height: 0; }

.formula-rows { display: flex; flex-direction: column; gap: 0; margin-top: 10px; }

.formula-row {
  display: flex; justify-content: space-between; align-items: baseline;
  padding: 5px 0; border-bottom: 1px solid var(--border); font-size: 13px;
}
.formula-row:last-child { border-bottom: none; }

.formula-row-label { color: var(--text-secondary); }
.formula-row-val   { font-weight: 600; color: var(--ink); flex-shrink: 0; text-align: right; }

.formula-row-op .formula-row-label { color: var(--text-muted); padding-left: 10px; }
.formula-row-op .formula-row-val   { color: var(--text-secondary); font-weight: 500; }

.formula-result {
  margin-top: 2px; padding-top: 8px !important;
  border-top: 1.5px solid var(--ink) !important;
  border-bottom: none !important;
}
.formula-result .formula-row-label { font-weight: 700; color: var(--ink); }
.formula-result .formula-row-val   { font-size: 14px; font-weight: 700; color: var(--ink); }
</style>
