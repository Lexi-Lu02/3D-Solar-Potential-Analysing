<template>
  <!--
    FilterPanel.vue — A floating control card on the top-left of the map that
    lets users filter which buildings are visible by:
      • Solar Potential tier (Excellent / Good / Moderate / Poor / Very Poor)
      • Roof Type (Flat / Hip / Gable / Pyramid / Shed)

    Each filter section has:
      • An "eye" toggle button to show/hide the map colouring for that filter
      • A collapse/expand button to show/hide the filter buttons
      • Individual filter buttons (one per tier or roof type)

    When a filter is active, a "chip" (small badge) appears at the top of the
    panel showing which filter is applied, with a "×" button to remove it.
  -->
  <div class="map-controls" role="group" aria-label="Map filters">
    <div class="control-card">

      <!-- ── Panel header ── -->
      <div class="filter-panel-header">
        <!-- Filter icon (three horizontal lines) -->
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
          <path d="M1 3h12M3 7h8M5 11h4" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
        </svg>
        <span class="filter-panel-title">Filters</span>
        <!--
          Close button — emits the 'close' event to tell ExploreView to hide this panel.
          $emit('close') sends the event to the parent component.
        -->
        <button class="filter-panel-close" @click="$emit('close')" aria-label="Close filter panel">
          <svg width="13" height="13" viewBox="0 0 14 14" fill="none" aria-hidden="true">
            <path d="M10 4l-4 4 4 4" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
      </div>

      <!-- ── Applied filter chips (shown only when a filter is active) ── -->
      <!--
        v-if="activeFilter !== 'all' || activeSolarFilter !== 'all'" means this
        section only appears when at least one filter is currently selected.
      -->
      <div v-if="activeFilter !== 'all' || activeSolarFilter !== 'all'" class="applied-filters-section">
        <div class="applied-filters-row">
          <span class="applied-filters-label">Applied filters</span>
          <!-- Clear all filters at once -->
          <button class="filter-clear-all" @click="$emit('clear-all')" aria-label="Clear all filters">
            Clear all
            <svg width="10" height="10" viewBox="0 0 10 10" fill="none" aria-hidden="true">
              <path d="M1 1l8 8M9 1L1 9" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            </svg>
          </button>
        </div>
        <!-- List of active filter chips — each can be removed individually -->
        <div class="applied-chips" role="list" aria-label="Active filters">

          <!-- Solar potential chip (shown when a solar tier is selected) -->
          <span v-if="activeSolarFilter !== 'all'" class="filter-chip" role="listitem">
            <!--
              .find() searches the solarTiers array for the object with matching id.
              ?.color uses optional chaining — safe if find() returns undefined.
            -->
            <span class="filter-chip-dot" :style="{ background: solarTiers.find(t => t.id === activeSolarFilter)?.color }"></span>
            {{ solarTiers.find(t => t.id === activeSolarFilter)?.label }}
            <!-- Clicking × emits 'filter-solar' with the current ID, which toggles it off in ExploreView -->
            <button class="filter-chip-remove" @click="$emit('filter-solar', activeSolarFilter)" :aria-label="`Remove ${solarTiers.find(t => t.id === activeSolarFilter)?.label} filter`">×</button>
          </span>

          <!-- Roof type chip (shown when a roof type is selected) -->
          <span v-if="activeFilter !== 'all'" class="filter-chip" role="listitem">
            {{ filters.find(f => f.type === activeFilter)?.label }}
            <button class="filter-chip-remove" @click="$emit('filter-roof', activeFilter)" :aria-label="`Remove ${filters.find(f => f.type === activeFilter)?.label} filter`">×</button>
          </span>

        </div>
      </div>

      <!-- ── Solar Potential section ── -->
      <div class="filter-section-divider" v-if="activeFilter !== 'all' || activeSolarFilter !== 'all'"></div>
      <div class="control-card-toggle-row">

        <!--
          Eye toggle button — turns the solar colour coding on/off without removing the filter.
          :class="{ active: solarPotentialColorOn }" adds the 'active' style when colouring is on.
          Emitting 'toggle-solar-color' tells ExploreView to flip the colouring flag.
        -->
        <button
          class="map-effect-toggle"
          :class="{ active: solarPotentialColorOn }"
          type="button"
          :aria-pressed="solarPotentialColorOn"
          :aria-label="solarPotentialColorOn ? 'Turn off solar potential map colors' : 'Turn on solar potential map colors'"
          :title="solarPotentialColorOn ? 'Hide solar potential colors' : 'Show solar potential colors'"
          @click="$emit('toggle-solar-color')"
        >
          <!-- Open eye icon (when colour is ON) -->
          <svg v-if="solarPotentialColorOn" width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
            <path d="M1.5 7s2-3.5 5.5-3.5S12.5 7 12.5 7s-2 3.5-5.5 3.5S1.5 7 1.5 7Z" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round"/>
            <circle cx="7" cy="7" r="1.7" stroke="currentColor" stroke-width="1.3"/>
          </svg>
          <!-- Crossed-out eye icon (when colour is OFF) -->
          <svg v-else width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
            <path d="M1.5 7s2-3.5 5.5-3.5c1 0 1.9.3 2.6.8M12.5 7s-.7 1.2-1.9 2.1M4.4 9.8c.7.4 1.6.7 2.6.7 3.5 0 5.5-3.5 5.5-3.5M2 2l10 10" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>

        <!--
          Collapse/expand toggle for the solar filter buttons.
          Clicking it flips the `solarFilterOpen` local variable (true/false).
        -->
        <button
          class="control-card-toggle"
          @click="solarFilterOpen = !solarFilterOpen"
          :aria-expanded="solarFilterOpen"
          aria-controls="solar-filter-group"
        >
          <span class="control-title">Solar Potential</span>
          <!-- Mini colour dots showing the full tier spectrum (decorative) -->
          <div class="solar-mini-legend" aria-hidden="true">
            <span
              v-for="t in solarTiers"
              :key="t.id"
              class="solar-mini-pip"
              :style="{ background: t.color }"
              :title="`${t.label} (${t.range})`"
            ></span>
          </div>
          <!-- Arrow icon that rotates when the section expands -->
          <svg class="chevron-icon" :class="{ 'chevron-up': solarFilterOpen }" width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
            <path d="M3 5l4 4 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
      </div>

      <!--
        Solar tier filter buttons — one per tier.
        v-show="solarFilterOpen" hides them (but keeps them in the DOM) when collapsed.
        v-for="t in solarTiers" creates one button per tier object in the array.
      -->
      <div id="solar-filter-group" v-show="solarFilterOpen" class="filter-group" role="group" aria-label="Solar potential filter options">
        <button
          v-for="t in solarTiers"
          :key="t.id"
          class="filter-btn"
          :class="{ active: activeSolarFilter === t.id }"  <!-- highlight when selected -->
          :aria-pressed="activeSolarFilter === t.id"
          :aria-label="`${t.label} solar potential, score range ${t.range} out of 5`"
          @click="$emit('filter-solar', t.id)"  <!-- tell parent which tier was clicked -->
        >
          <!-- Visual: colour dot and bar meter showing tier strength -->
          <div class="tier-visual" aria-hidden="true">
            <div class="legend-dot" :style="{ background: t.color }"></div>
            <div class="tier-bars">
              <!--
                v-for="n in 5" creates 5 bar segments.
                Segments 1..t.bars are filled with the tier colour.
                The remaining segments stay grey (showing the bar is not full).
              -->
              <span
                v-for="n in 5"
                :key="n"
                class="tier-bar-seg"
                :class="{ 'tier-bar-seg--active': n <= t.bars }"
                :style="n <= t.bars ? { background: t.color } : {}"
              ></span>
            </div>
          </div>
          <!-- Text label and score range (e.g. "Good  3.5–4.4 / 5") -->
          <div class="tier-text">
            <span class="tier-name">{{ t.label }}</span>
            <span class="tier-score">{{ t.range }} / 5</span>
          </div>
        </button>
      </div>

      <!-- ── Roof Type section ── (same structure as Solar Potential above) -->
      <div class="filter-section-divider"></div>
      <div class="control-card-toggle-row">

        <!-- Eye toggle for roof type colours -->
        <button
          class="map-effect-toggle"
          :class="{ active: roofTypeEffectOn }"
          type="button"
          :aria-pressed="roofTypeEffectOn"
          :aria-label="roofTypeEffectOn ? 'Turn off roof type map styling' : 'Turn on roof type map styling'"
          :title="roofTypeEffectOn ? 'Hide roof type styling' : 'Show roof type styling'"
          @click="$emit('toggle-roof-type')"
        >
          <svg v-if="roofTypeEffectOn" width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
            <path d="M1.5 7s2-3.5 5.5-3.5S12.5 7 12.5 7s-2 3.5-5.5 3.5S1.5 7 1.5 7Z" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round"/>
            <circle cx="7" cy="7" r="1.7" stroke="currentColor" stroke-width="1.3"/>
          </svg>
          <svg v-else width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
            <path d="M1.5 7s2-3.5 5.5-3.5c1 0 1.9.3 2.6.8M12.5 7s-.7 1.2-1.9 2.1M4.4 9.8c.7.4 1.6.7 2.6.7 3.5 0 5.5-3.5 5.5-3.5M2 2l10 10" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>

        <!-- Collapse/expand toggle for roof type buttons -->
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
      </div>

      <!-- Roof type filter buttons (Flat, Hip, Gable, Pyramid, Shed) -->
      <div id="roof-filter-group" v-show="roofFilterOpen" class="filter-group" role="group" aria-label="Roof type filter options">
        <button
          v-for="f in filters"
          :key="f.type"
          class="filter-btn"
          :class="{ active: activeFilter === f.type }"
          :aria-pressed="activeFilter === f.type"
          :aria-label="`${f.label} filter`"
          @click="$emit('filter-roof', f.type)"
        >
          <!--
            Small texture swatch showing a visual pattern for each roof type.
            The pattern is rendered via CSS (different repeating patterns).
            :class="`roof-pattern-swatch__texture--${f.pattern}`" applies the right pattern class.
          -->
          <span class="roof-pattern-swatch" aria-hidden="true">
            <span class="roof-pattern-swatch__texture" :class="`roof-pattern-swatch__texture--${f.pattern}`"></span>
          </span>
          {{ f.label }}
        </button>
      </div>

    </div>
  </div>
</template>

<script setup>
// ─────────────────────────────────────────────────────────────────────────────
// FilterPanel.vue — Script section
//
// This component is mostly a "display" component — it receives all filter state
// from its parent (ExploreView) via props, and sends filter changes back via events.
// The only local state it manages is whether each filter section is expanded.
// ─────────────────────────────────────────────────────────────────────────────

// ref creates reactive variables.
import { ref } from 'vue'

// ── Props — data passed in from ExploreView ────────────────────────────────────
defineProps({
  // The currently selected solar tier ID (e.g. 'high', 'all' = no filter).
  activeSolarFilter:    { type: String,  required: true },
  // The currently selected roof type (e.g. 'Flat', 'all' = no filter).
  activeFilter:         { type: String,  required: true },
  // Whether the solar potential colour coding on the map is turned on.
  solarPotentialColorOn:{ type: Boolean, required: true },
  // Whether the roof type effect on the map is turned on.
  roofTypeEffectOn:     { type: Boolean, required: true },
  // Array of solar tier objects (from ExploreView) to render the tier buttons.
  solarTiers:           { type: Array,   required: true },
  // Array of roof type filter objects to render the roof buttons.
  filters:              { type: Array,   required: true },
})

// ── Events this component can send to its parent ───────────────────────────────
// defineEmits lists all the event names this component is allowed to emit ($emit).
// 'close'              → user clicked the X button
// 'filter-solar'       → user clicked a solar tier button (value = tier id)
// 'filter-roof'        → user clicked a roof type button (value = roof type string)
// 'clear-all'          → user clicked "Clear all"
// 'toggle-solar-color' → user clicked the solar eye icon
// 'toggle-roof-type'   → user clicked the roof type eye icon
defineEmits(['close', 'filter-solar', 'filter-roof', 'clear-all', 'toggle-solar-color', 'toggle-roof-type'])

// ── Local UI state ────────────────────────────────────────────────────────────
// These control whether each filter section is expanded or collapsed.
// They are LOCAL to this component — ExploreView doesn't need to know about them.
const solarFilterOpen = ref(false)  // false = solar tier buttons are hidden
const roofFilterOpen  = ref(false)  // false = roof type buttons are hidden
</script>

<style scoped>
/* Floating card positioned at the top-left of the map */
.map-controls {
  position: absolute; top: 16px; left: 16px;
  z-index: 10; display: flex; flex-direction: column; gap: 8px;
}

/* Applied filters section — shows which filters are currently on */
.applied-filters-section {
  background: var(--surface2); border-radius: 8px; padding: 8px 10px; margin-bottom: 12px;
}
.applied-filters-row {
  display: flex; align-items: center; justify-content: space-between; margin-bottom: 7px;
}
.applied-filters-label { font-size: 13px; font-weight: 600; color: var(--text-secondary); }
.filter-clear-all {
  display: flex; align-items: center; gap: 4px;
  background: none; border: none; cursor: pointer;
  font-size: 13px; font-weight: 500; color: var(--text-muted);
  font-family: 'DM Sans', sans-serif; transition: color 0.15s;
}
.filter-clear-all:hover { color: var(--error); }
.applied-chips { display: flex; flex-wrap: wrap; gap: 5px; }

/* Individual filter chip badge */
.filter-chip {
  display: inline-flex; align-items: center; gap: 5px;
  background: var(--accent-light); border: 1px solid #F2C0A0;
  color: var(--accent-dark); font-size: 13px; font-weight: 600;
  padding: 3px 7px; border-radius: 20px;
}
.filter-chip-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.filter-chip-remove {
  background: none; border: none; cursor: pointer;
  color: var(--accent-dark); font-size: 14px; line-height: 1;
  padding: 0; display: flex; align-items: center; transition: color 0.15s;
}
.filter-chip-remove:hover { color: var(--error); }

/* Horizontal rule between sections */
.filter-section-divider { height: 1px; background: var(--border); margin: 10px 0; }

/* Row containing the eye toggle + section header */
.control-card-toggle-row { display: flex; align-items: center; gap: 8px; }
.control-card-toggle {
  width: 100%; display: flex; align-items: center; justify-content: space-between;
  background: none; border: none; cursor: pointer; padding: 0; margin-bottom: 0;
  font-family: 'DM Sans', sans-serif; gap: 6px;
}
.control-card-toggle .control-title { margin-bottom: 0; flex: 1; text-align: left; }
.control-card-toggle:focus-visible { outline: 3px solid var(--accent); outline-offset: 2px; border-radius: 4px; }
.control-title {
  font-size: 13px; font-weight: 600; text-transform: uppercase;
  letter-spacing: 0.6px; color: var(--text-muted); margin-bottom: 10px;
}

/* Eye icon button (show/hide map colouring) */
.map-effect-toggle {
  width: 28px; height: 28px; display: inline-flex; align-items: center; justify-content: center;
  background: none; border: 1px solid var(--border);
  border-radius: 6px; color: var(--text-muted); flex-shrink: 0; cursor: pointer;
  transition: all 0.15s ease;
}
.map-effect-toggle:hover { background: var(--surface2); color: var(--text-primary); }
.map-effect-toggle.active { background: var(--accent-light); border-color: #F2C0A0; color: var(--accent); }
.map-effect-toggle:focus-visible { outline: 3px solid var(--accent); outline-offset: 2px; }

/* Container for the list of filter buttons */
.filter-group { display: flex; flex-direction: column; gap: 6px; margin-top: 10px; }

/* Individual filter button */
.filter-btn {
  display: flex; align-items: flex-start; gap: 8px;
  padding: 6px 10px; border-radius: 6px; border: 1px solid var(--border);
  background: transparent; cursor: pointer; font-size: 13px;
  font-family: 'DM Sans', sans-serif; color: var(--text-secondary);
  transition: all 0.15s; text-align: left;
}
/* Active (selected) button — orange tint */
.filter-btn.active { background: var(--accent-light); border-color: #F2C0A0; color: var(--accent); font-weight: 500; }
.filter-btn:hover:not(.active) { background: var(--surface2); }
.filter-btn:focus-visible { outline: 3px solid var(--accent); outline-offset: 2px; }

/* Roof type swatch — small rectangle with a texture pattern */
.roof-pattern-swatch {
  --roof-texture: #4B5563;
  width: 28px; height: 16px; border-radius: 4px;
  border: 1px solid #9CA3AF; background: transparent; overflow: hidden; flex-shrink: 0;
}
.roof-pattern-swatch__texture { display: block; width: 100%; height: 100%; background-color: transparent; }

/* Different SVG/CSS patterns for each roof type */
.roof-pattern-swatch__texture--flat {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 16 16'%3E%3Crect x='3' y='3' width='3' height='3' rx='0.8' fill='%234B5563' fill-opacity='0.85'/%3E%3Crect x='11' y='11' width='3' height='3' rx='0.8' fill='%234B5563' fill-opacity='0.85'/%3E%3C/svg%3E");
  background-size: 16px 16px;
}
.roof-pattern-swatch__texture--diagonal {
  background-image: repeating-linear-gradient(135deg, var(--roof-texture) 0 2px, transparent 2px 8px);
}
.roof-pattern-swatch__texture--cross {
  background-image:
    repeating-linear-gradient(45deg, var(--roof-texture) 0 1.5px, transparent 1.5px 8px),
    repeating-linear-gradient(135deg, var(--roof-texture) 0 1.5px, transparent 1.5px 8px);
}
.roof-pattern-swatch__texture--triangles {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath d='M6 2.2 9.4 8.7H2.6Z' fill='%234B5563' fill-opacity='0.85'/%3E%3C/svg%3E");
  background-size: 12px 12px;
}
.roof-pattern-swatch__texture--horizontal {
  background-image: repeating-linear-gradient(0deg, var(--roof-texture) 0 2px, transparent 2px 7px);
}

/* Row of coloured dots in the Solar Potential header (decorative legend) */
.solar-mini-legend { display: flex; align-items: center; gap: 2px; flex-shrink: 0; }
.solar-mini-pip { display: block; width: 12px; height: 12px; border-radius: 2px; }

/* Bar meter inside each solar tier button */
.legend-dot { width: 12px; height: 12px; border-radius: 3px; flex-shrink: 0; }
.tier-visual { display: flex; flex-direction: column; align-items: center; gap: 4px; flex-shrink: 0; }
.tier-bars { display: flex; align-items: flex-end; gap: 2px; }

/* Five small vertical bars — filled bars represent the tier strength */
.tier-bar-seg { width: 3px; border-radius: 1px 1px 0 0; background: var(--border); }
.tier-bar-seg:nth-child(1) { height: 4px; }
.tier-bar-seg:nth-child(2) { height: 6px; }
.tier-bar-seg:nth-child(3) { height: 9px; }
.tier-bar-seg:nth-child(4) { height: 12px; }
.tier-bar-seg:nth-child(5) { height: 15px; }

.tier-text { display: flex; flex-direction: column; gap: 1px; min-width: 0; }
.tier-name { font-size: 13px; font-weight: 500; line-height: 1.2; }
.tier-score { font-size: 11px; color: var(--text-muted); font-weight: 400; }
</style>
