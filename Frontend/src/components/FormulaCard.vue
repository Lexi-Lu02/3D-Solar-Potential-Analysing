<template>
  <!--
    FormulaCard.vue — A collapsible card that shows HOW the annual electricity
    generation number is calculated, step by step.

    When collapsed: shows a small "How We Calculate Annual Generation" toggle.
    When expanded:  shows each input value in the formula with its contribution:

        Usable Roof Area (m²)
      × Panel Efficiency (20%)
      × Performance Ratio (75%)
      × Peak Sun Hours per Day (kWh/m²/day)
      × Days per Year (365)
      ─────────────────────────────────────
      = Annual Electricity Generation (kWh)

    This helps users understand where the numbers come from.
  -->
  <div class="formula-card">

    <!--
      Toggle button that expands/collapses the formula rows.
      @click="formulaCardOpen = !formulaCardOpen" flips between true and false.
      :aria-expanded tells screen readers whether the panel is open or closed.
    -->
    <button
      class="formula-card-toggle"
      @click="formulaCardOpen = !formulaCardOpen"
      :aria-expanded="formulaCardOpen"
    >
      <span class="formula-card-title">How We Calculate Annual Generation</span>

      <!--
        Arrow icon that rotates when the panel opens.
        :class="{ 'chevron-up': formulaCardOpen }" adds the 'chevron-up' class
        which applies a 180° CSS rotation (defined in style.css).
      -->
      <svg
        class="chevron-icon"
        :class="{ 'chevron-up': formulaCardOpen }"
        width="13" height="13" viewBox="0 0 14 14" fill="none" aria-hidden="true"
      >
        <path d="M3 5l4 4 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </button>

    <!--
      <Transition> wraps the formula rows with a slide-in animation.
      When formulaCardOpen becomes true  → the rows fade/slide into view.
      When formulaCardOpen becomes false → the rows fade/slide out of view.
      The animation CSS is defined in the <style scoped> section below.
    -->
    <Transition name="formula-collapse">
      <div v-if="formulaCardOpen" class="formula-rows">

        <!-- Row 1: The usable roof area in square metres -->
        <div class="formula-row">
          <span class="formula-row-label">Usable Roof Area</span>
          <span class="formula-row-val">
            <!--
              Show the value from whichever data source is available:
              1. solarApiData?.usableAreaM2 — from the Google Solar API (most accurate)
              2. selectedBuilding?.usable_roof_area — from the GeoJSON building file
              3. 0 — fallback if neither is available
              ?? is the "nullish coalescing" operator: use the right side only if the left is null/undefined.
            -->
            {{ (solarApiData?.usableAreaM2 ?? selectedBuilding?.usable_roof_area ?? 0).toLocaleString(undefined, { maximumFractionDigits: 1 }) }} m²
          </span>
        </div>

        <!-- Row 2: Panel efficiency multiplier (standard commercial solar panels run at ~20%) -->
        <div class="formula-row formula-row-op">
          <span class="formula-row-label">Panel Efficiency</span>
          <span class="formula-row-val">× 20%</span>
        </div>

        <!-- Row 3: Performance ratio accounts for heat loss, wiring, inverter losses, etc. -->
        <div class="formula-row formula-row-op">
          <span class="formula-row-label">Performance Ratio</span>
          <span class="formula-row-val">× 75%</span>
        </div>

        <!-- Row 4: Peak sun hours per day — how much usable sunlight the location gets -->
        <div class="formula-row formula-row-op">
          <span class="formula-row-label">Peak Sun Hours/Day</span>
          <span class="formula-row-val">
            <!--
              If the Google Solar API returned sunshine hours for this building, use
              that (divided by 365 to convert annual → daily, rounded to 1dp).
              Otherwise fall back to Melbourne's BOM-validated average of 4.1 kWh/m²/day.
            -->
            × {{ solarApiData?.sunshineHours != null
                  ? (Math.round(solarApiData.sunshineHours / 365 * 10) / 10).toFixed(1) + ' kWh/m²/day'
                  : '4.1 kWh/m²/day' }}
          </span>
        </div>

        <!-- Row 5: Multiply by 365 to get annual output -->
        <div class="formula-row formula-row-op">
          <span class="formula-row-label">Days per Year</span>
          <span class="formula-row-val">× 365</span>
        </div>

        <!-- Result row: the final calculated annual kWh -->
        <div class="formula-row formula-result">
          <span class="formula-row-label">Annual Electricity Generation</span>
          <span class="formula-row-val">{{ formulaKwhAnnual.toLocaleString() }} kWh</span>
        </div>

      </div>
    </Transition>

  </div>
</template>

<script setup>
// ─────────────────────────────────────────────────────────────────────────────
// FormulaCard.vue — Script section
//
// This is a simple "display only" component. It receives data from its parent
// (ExploreView) and shows it in a formatted breakdown. It manages only one piece
// of local state: whether the card is open or closed.
// ─────────────────────────────────────────────────────────────────────────────

// ref creates a reactive variable.
import { ref } from 'vue'

// ── Props — data passed in from the parent component ─────────────────────────
// Props are read-only inputs. The parent (ExploreView) provides these values.
defineProps({
  // The final calculated annual kWh figure to display in the result row.
  formulaKwhAnnual: { type: Number, required: true },
  // Data from the Google Solar API — may be null if the building has no API record.
  solarApiData:     { type: Object, default: null },
  // The currently selected building's GeoJSON properties (roof area fallback).
  selectedBuilding: { type: Object, default: null },
})

// Whether the formula breakdown is expanded (true) or collapsed (false).
// Starts collapsed so it doesn't take up too much space by default.
const formulaCardOpen = ref(false)
</script>

<style scoped>
/* Container card with a subtle background */
.formula-card {
  margin: 0 0 16px;
  padding: 12px 14px;
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: 8px;
}

/* The clickable header row */
.formula-card-toggle {
  width: 100%; display: flex; align-items: center; justify-content: space-between;
  background: none; border: none; cursor: pointer; padding: 0; gap: 6px;
  font-family: 'DM Sans', sans-serif;
}

.formula-card-toggle .chevron-icon { color: var(--text-muted); }

/* "HOW WE CALCULATE..." label */
.formula-card-title {
  font-size: 12px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.07em; color: var(--text-muted);
}

/* ── Slide/fade animation for the formula rows ────────────────────────────────
   .formula-collapse-enter-active / .formula-collapse-leave-active define the
   transition properties while the element is entering or leaving the DOM.
   -enter-from / -leave-to define the starting/ending state (invisible, collapsed). */
.formula-collapse-enter-active,
.formula-collapse-leave-active {
  transition: opacity 0.2s ease, max-height 0.25s ease;
  overflow: hidden;
  max-height: 400px;  /* large enough to fit all rows when expanded */
}
.formula-collapse-enter-from,
.formula-collapse-leave-to { opacity: 0; max-height: 0; }

/* Vertical list of formula rows */
.formula-rows { display: flex; flex-direction: column; gap: 0; margin-top: 10px; }

/* Each row shows a label on the left and a value on the right */
.formula-row {
  display: flex; justify-content: space-between; align-items: baseline;
  padding: 5px 0; border-bottom: 1px solid var(--border); font-size: 13px;
}
.formula-row:last-child { border-bottom: none; }

.formula-row-label { color: var(--text-secondary); }
.formula-row-val   { font-weight: 600; color: var(--ink); flex-shrink: 0; text-align: right; }

/* Operator rows (× 20%, × 75%, etc.) are slightly indented and muted */
.formula-row-op .formula-row-label { color: var(--text-muted); padding-left: 10px; }
.formula-row-op .formula-row-val   { color: var(--text-secondary); font-weight: 500; }

/* Result row (total kWh) — bold with a thicker top border to look like a sum */
.formula-result {
  margin-top: 2px; padding-top: 8px !important;
  border-top: 1.5px solid var(--ink) !important;
  border-bottom: none !important;
}
.formula-result .formula-row-label { font-weight: 700; color: var(--ink); }
.formula-result .formula-row-val   { font-size: 14px; font-weight: 700; color: var(--ink); }
</style>
