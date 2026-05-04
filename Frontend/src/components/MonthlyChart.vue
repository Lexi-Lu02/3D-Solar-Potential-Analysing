<template>
  <div
    v-if="monthlyOutput.length === 0"
    class="monthly-no-data"
  >
    No solar data available for this building
  </div>
  <div
    v-else
    class="monthly-chart"
    role="img"
    :aria-label="`Monthly solar output chart. ${monthlyOutput.map(m => `${m.month}: ${m.kwh.toLocaleString()} kWh`).join(', ')}`"
  >
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
        <div v-if="hoveredMonthIdx === i" class="monthly-tooltip" aria-hidden="true">
          {{ m.kwh.toLocaleString() }} kWh
        </div>
        <div class="monthly-bar-wrap">
          <div class="monthly-bar" :style="{ height: m.pct + '%' }" aria-hidden="true"></div>
        </div>
        <div class="monthly-bar-label" aria-hidden="true">{{ m.month }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  monthlyOutput: {
    type: Array,
    required: true,
  },
})

const hoveredMonthIdx = ref(null)
</script>

<style scoped>
.monthly-chart { margin-bottom: 6px; }

.monthly-bars {
  display: flex; align-items: flex-end; gap: 3px;
  height: 80px; padding-bottom: 20px; position: relative;
}

.monthly-bar-col {
  flex: 1; display: flex; flex-direction: column;
  align-items: center; height: 100%;
  position: relative; cursor: default;
}

.monthly-bar-col--hovered .monthly-bar { filter: brightness(1.15); }

.monthly-tooltip {
  position: absolute; bottom: calc(100% - 16px);
  left: 50%; transform: translateX(-50%);
  background: var(--text-primary); color: #fff;
  font-size: 13px; font-weight: 500;
  padding: 3px 6px; border-radius: 4px;
  white-space: nowrap; z-index: 30;
  pointer-events: none;
}

.monthly-tooltip::after {
  content: ''; position: absolute; top: 100%; left: 50%;
  transform: translateX(-50%);
  border: 4px solid transparent;
  border-top-color: var(--text-primary);
}

.monthly-bar-wrap {
  flex: 1; width: 100%; display: flex; align-items: flex-end;
}

.monthly-bar {
  width: 100%; min-height: 3px;
  background: linear-gradient(to top, var(--accent), #DC7249);
  border-radius: 2px 2px 0 0;
  transition: height 0.4s ease;
}

.monthly-bar-label {
  font-size: 8px; color: var(--text-muted);
  margin-top: 4px; line-height: 1;
}

.monthly-no-data { font-size: 13px; color: var(--text-muted); padding: 6px 0 12px; }

.monthly-bar-col:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 1px;
  border-radius: 3px;
}
</style>
