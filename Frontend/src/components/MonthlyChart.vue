<template>
  <!--
    MonthlyChart.vue — A simple bar chart showing estimated solar electricity
    generation for each month of the year (Jan–Dec).

    Each bar's height is proportional to the month's kWh output relative to
    the best month. Hovering (or focusing with keyboard) shows a tooltip with
    the exact kWh value.

    If there's no data for the building, a plain text message is shown instead.
  -->

  <!--
    Case 1: No data available — show a simple "no data" message.
    v-if="monthlyOutput.length === 0" hides the chart when the array is empty.
  -->
  <div
    v-if="monthlyOutput.length === 0"
    class="monthly-no-data"
  >
    No solar data available for this building
  </div>

  <!--
    Case 2: Data is available — show the bar chart.
    v-else means this block only renders when the v-if above is false.
    role="img" + aria-label gives screen readers a text description of the whole chart.
    The aria-label dynamically lists every month and its kWh value.
  -->
  <div
    v-else
    class="monthly-chart"
    role="img"
    :aria-label="`Monthly solar output chart. ${monthlyOutput.map(m => `${m.month}: ${m.kwh.toLocaleString()} kWh`).join(', ')}`"
  >
    <!-- Horizontal row containing all 12 month columns -->
    <div class="monthly-bars" role="list">

      <!--
        v-for loops over the monthlyOutput array, creating one column per month.
        `m` is the current month object  { month: 'Jan', kwh: 1234, pct: 80 }
        `i` is the index (0 for Jan, 11 for Dec)
      -->
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

        <!--
          Tooltip — only shown when this month column is hovered or focused.
          v-if="hoveredMonthIdx === i" renders it only for the currently active column.
          aria-hidden="true" hides it from screen readers (the aria-label above covers it).
        -->
        <div v-if="hoveredMonthIdx === i" class="monthly-tooltip" aria-hidden="true">
          {{ m.kwh.toLocaleString() }} kWh
        </div>

        <!-- Wrapper that aligns the bar to the bottom of the column -->
        <div class="monthly-bar-wrap">
          <!--
            The actual bar — its height is set dynamically via the :style binding.
            m.pct is a 0–100 number where 100 = the best month.
            aria-hidden="true" because the parent element already describes this data.
          -->
          <div class="monthly-bar" :style="{ height: m.pct + '%' }" aria-hidden="true"></div>
        </div>

        <!-- Month abbreviation label below the bar (Jan, Feb, …, Dec) -->
        <div class="monthly-bar-label" aria-hidden="true">{{ m.month }}</div>

      </div>
    </div>
  </div>
</template>

<script setup>
// ─────────────────────────────────────────────────────────────────────────────
// MonthlyChart.vue — Script section
//
// This is a pure display component. It receives the monthly data from its parent
// (ExploreView or ComparisonPanel) and only manages one thing: which month the
// user is currently hovering over.
// ─────────────────────────────────────────────────────────────────────────────

// ref creates a reactive variable.
import { ref } from 'vue'

// ── Props — data passed in from the parent component ─────────────────────────
defineProps({
  // An array of monthly output objects, one per month:
  // [{ month: 'Jan', kwh: 1200, pct: 80 }, { month: 'Feb', ... }, ...]
  // pct is 0–100, where 100 = the month with the highest output.
  // An empty array means no data is available.
  monthlyOutput: {
    type: Array,
    required: true,
  },
})

// ── Local state ───────────────────────────────────────────────────────────────
// Tracks which month column is currently being hovered or focused.
// null  → nothing is hovered
// 0–11  → index of the hovered month (0 = Jan, 11 = Dec)
// When this changes, the corresponding tooltip appears and the bar brightens slightly.
const hoveredMonthIdx = ref(null)
</script>

<style scoped>
/* Bottom margin below the chart */
.monthly-chart { margin-bottom: 6px; }

/* Row of bars — aligned to the bottom so all bars grow upward */
.monthly-bars {
  display: flex; align-items: flex-end; gap: 3px;
  height: 80px;            /* total height of the chart area */
  padding-bottom: 20px;    /* space for the month labels below the bars */
  position: relative;
}

/* Each month column takes equal width */
.monthly-bar-col {
  flex: 1; display: flex; flex-direction: column;
  align-items: center; height: 100%;
  position: relative; cursor: default;
}

/* Slightly brighten the bar when hovered */
.monthly-bar-col--hovered .monthly-bar { filter: brightness(1.15); }

/* Tooltip that floats above the bar on hover */
.monthly-tooltip {
  position: absolute; bottom: calc(100% - 16px);  /* just above the bar top */
  left: 50%; transform: translateX(-50%);          /* centred horizontally */
  background: var(--text-primary); color: #fff;
  font-size: 13px; font-weight: 500;
  padding: 3px 6px; border-radius: 4px;
  white-space: nowrap; z-index: 30;
  pointer-events: none;  /* tooltip doesn't intercept mouse events */
}

/* Small downward-pointing triangle below the tooltip */
.monthly-tooltip::after {
  content: ''; position: absolute; top: 100%; left: 50%;
  transform: translateX(-50%);
  border: 4px solid transparent;
  border-top-color: var(--text-primary);
}

/* First column (Jan): anchor tooltip to left edge so it doesn't clip */
.monthly-bar-col:first-child .monthly-tooltip {
  left: 0; transform: none;
}
.monthly-bar-col:first-child .monthly-tooltip::after {
  left: 8px; transform: none;
}

/* Last column (Dec): anchor tooltip to right edge so it doesn't clip */
.monthly-bar-col:last-child .monthly-tooltip {
  left: auto; right: 0; transform: none;
}
.monthly-bar-col:last-child .monthly-tooltip::after {
  left: auto; right: 8px; transform: none;
}

/* Wrapper that fills remaining height and aligns the bar to the bottom */
.monthly-bar-wrap {
  flex: 1; width: 100%; display: flex; align-items: flex-end;
}

/* The coloured bar — height is set dynamically by the :style binding */
.monthly-bar {
  width: 100%; min-height: 3px;  /* always at least 3px tall so it's visible */
  background: linear-gradient(to top, var(--accent), #DC7249);  /* gold to orange gradient */
  border-radius: 2px 2px 0 0;   /* rounded top corners */
  transition: height 0.4s ease;  /* smooth height changes when data updates */
}

/* Month abbreviation (Jan, Feb…) below each bar */
.monthly-bar-label {
  font-size: 8px; color: var(--text-muted);
  margin-top: 4px; line-height: 1;
}

/* "No data" message shown when monthlyOutput is empty */
.monthly-no-data { font-size: 13px; color: var(--text-muted); padding: 6px 0 12px; }

/* Keyboard focus ring on individual month columns */
.monthly-bar-col:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 1px;
  border-radius: 3px;
}
</style>
