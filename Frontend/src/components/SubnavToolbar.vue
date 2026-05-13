<template>
  <!--
    SubnavToolbar.vue — The dark secondary toolbar below the main nav bar on the
    Explore page. It contains two groups of controls:

    LEFT GROUP — Panel toggle buttons:
      • Filter         → opens/closes the FilterPanel floating card
      • Comparison     → opens/closes the ComparisonPanel at the bottom
      • Sun Path       → opens/closes the sun path & shadow simulation panel
      • Building Info  → opens/closes the right sidebar with building details

    RIGHT GROUP — Address search:
      A text input that searches buildings by street address.
      As the user types (after 2+ characters), results appear in a dropdown.
      Clicking a result selects that building on the map.
  -->
  <div class="explore-subnav" role="toolbar" aria-label="Explore controls">

    <!-- ── Panel toggle buttons ── -->
    <div class="subnav-actions">

      <!--
        Filter toggle button.
        :class="{ 'subnav-btn--active': filtersOpen }" highlights the button when
        the filter panel is open.
        @click="$emit('toggle-filters')" tells ExploreView to open/close the panel.
        :aria-pressed reports the on/off state to screen readers.
      -->
      <button
        class="subnav-btn"
        :class="{ 'subnav-btn--active': filtersOpen }"
        @click="$emit('toggle-filters')"
        :aria-pressed="filtersOpen"
        aria-label="Toggle map filters"
      >
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
          <path d="M1 3h12M3 7h8M5 11h4" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
        </svg>
        Filter
      </button>

      <!--
        Comparison toggle button.
        A small orange badge shows how many buildings are currently in the comparison list.
        v-if="compareCount > 0" only renders the badge when at least one building is added.
      -->
      <button
        class="subnav-btn"
        :class="{ 'subnav-btn--active': comparePanelOpen }"
        @click="$emit('toggle-compare')"
        :aria-pressed="comparePanelOpen"
        aria-label="Toggle comparison panel"
      >
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
          <rect x="1" y="3" width="5" height="8" rx="1" stroke="currentColor" stroke-width="1.5"/>
          <rect x="8" y="3" width="5" height="8" rx="1" stroke="currentColor" stroke-width="1.5"/>
        </svg>
        Comparison
        <!-- Badge showing "1" or "2" when buildings are in the comparison list -->
        <span v-if="compareCount > 0" class="subnav-badge">{{ compareCount }}</span>
      </button>

      <!-- Sun Path toggle button -->
      <button
        class="subnav-btn"
        :class="{ 'subnav-btn--active': sunPathOpen }"
        @click="$emit('toggle-sun-path')"
        :aria-pressed="sunPathOpen"
        aria-label="Toggle sun path and shadow simulation panel"
      >
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
          <circle cx="7" cy="7" r="2.2" stroke="currentColor" stroke-width="1.4"/>
          <path d="M7 1.2v1.6M7 11.2v1.6M1.2 7h1.6M11.2 7h1.6M2.8 2.8l1.1 1.1M10.1 10.1l1.1 1.1M10.1 3.9l1.1-1.1M2.8 11.2l1.1-1.1" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
        </svg>
        Sun Path
      </button>

      <!-- Building Info sidebar toggle button -->
      <button
        class="subnav-btn"
        :class="{ 'subnav-btn--active': sidebarOpen }"
        @click="$emit('toggle-sidebar')"
        :aria-pressed="sidebarOpen"
        aria-label="Toggle building info panel"
      >
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
          <rect x="1" y="1" width="12" height="12" rx="2" stroke="currentColor" stroke-width="1.5"/>
          <path d="M9 1v12" stroke="currentColor" stroke-width="1.5"/>
        </svg>
        Building Info
      </button>

      <!-- Guide button — reopens the user guide from step 1 -->
      <button
        class="subnav-btn subnav-btn--guide"
        @click="$emit('show-guide')"
        aria-label="Show feature guide"
      >
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
          <circle cx="7" cy="7" r="6" stroke="currentColor" stroke-width="1.5"/>
          <path d="M5.5 5.2a1.5 1.5 0 0 1 2.9.5c0 1-1.4 1.3-1.4 2.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
          <circle cx="7" cy="10.2" r="0.7" fill="currentColor"/>
        </svg>
        Guide
      </button>
    </div>

    <!-- ── Address search ── -->
    <!--
      wrapEl is a template ref — it gives us a reference to this DOM element so
      the "click outside to close dropdown" logic can check if the click was inside.
    -->
    <div class="subnav-search-wrap" ref="wrapEl" role="search">

      <!-- Visually hidden label for screen readers -->
      <label for="search-address" class="visually-hidden">Search buildings by address</label>

      <!-- Search input wrapper (contains the icon, input, and clear button) -->
      <div class="subnav-search-inner">
        <img :src="iconSearch" alt="" aria-hidden="true" class="subnav-search-icon" />

        <!--
          The text input for address search.
          :value="searchQuery" shows the current search text.
          @input="handleInput" runs when the user types — it updates the query
          and tells ExploreView to trigger a search.
          role="combobox" + aria attributes describe the dropdown to screen readers.
          :aria-expanded tells screen readers whether the dropdown is visible.
        -->
        <input
          id="search-address"
          :value="searchQuery"
          type="text"
          class="subnav-search-input"
          placeholder="Search by address…"
          autocomplete="off"
          role="combobox"
          :aria-expanded="searchResults.length > 0 || searchLoading"
          aria-autocomplete="list"
          aria-controls="search-listbox"
          :aria-activedescendant="searchFocusedIdx >= 0 ? `search-option-${searchFocusedIdx}` : undefined"
          @input="handleInput"
          @keydown="$emit('search-keydown', $event)"
        />

        <!--
          "×" clear button — only shown when the search input has text.
          @click emits 'clear-search' so ExploreView can clear the query and close the dropdown.
        -->
        <button
          v-if="searchQuery.length"
          class="subnav-search-clear"
          @click="$emit('clear-search')"
          aria-label="Clear search"
          type="button"
        >
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true">
            <path d="M1 1l10 10M11 1L1 11" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
          </svg>
        </button>
      </div>

      <!-- ── Search dropdown states ── -->

      <!--
        Loading state — shown while waiting for the API to return results.
        Displays three animated dots to indicate activity.
      -->
      <ul v-if="searchLoading" class="search-dropdown subnav-dropdown" role="listbox" id="search-listbox">
        <li class="search-dropdown-loading" aria-live="polite">
          <span class="search-loading-dot"></span>
          <span class="search-loading-dot"></span>
          <span class="search-loading-dot"></span>
        </li>
      </ul>

      <!--
        Results state — shown when the API returned matching addresses.
        Each <li> is one result.
        @mousedown.prevent stops the input from losing focus when clicking a result.
        @mouseover updates the keyboard-focused index for arrow key navigation.
        $emit('select-result', result) tells ExploreView to fly to and select that building.
      -->
      <ul
        v-else-if="searchResults.length"
        class="search-dropdown subnav-dropdown"
        role="listbox"
        id="search-listbox"
        aria-label="Address search results"
      >
        <li
          v-for="(result, i) in searchResults"
          :key="result.structure_id"
          :id="`search-option-${i}`"
          class="search-dropdown-item"
          :class="{ 'search-dropdown-item--focused': searchFocusedIdx === i }"
          role="option"
          :aria-selected="searchFocusedIdx === i"
          @mousedown.prevent="$emit('select-result', result)"
          @mouseover="$emit('update:searchFocusedIdx', i)"
        >
          <!-- Pin icon -->
          <svg class="search-result-pin" width="12" height="14" viewBox="0 0 12 14" fill="none" aria-hidden="true">
            <path d="M6 0C3.24 0 1 2.24 1 5c0 3.75 5 9 5 9s5-5.25 5-9c0-2.76-2.24-5-5-5zm0 6.5A1.5 1.5 0 1 1 6 3.5a1.5 1.5 0 0 1 0 3z" fill="currentColor"/>
          </svg>
          <span class="search-result-address">{{ result.address }}</span>
        </li>
      </ul>

      <!--
        No results state — shown when the user typed 2+ characters and the API
        found no matching buildings.
      -->
      <ul
        v-else-if="searchDropdownOpen && searchQuery.trim().length >= 2 && !searchLoading"
        class="search-dropdown subnav-dropdown"
        role="listbox"
        id="search-listbox"
      >
        <li class="search-dropdown-empty">No matching addresses found</li>
      </ul>

      <!-- Error message (shown if the search API request fails) -->
      <div
        v-if="searchError"
        id="search-error-msg"
        class="search-error subnav-search-error"
        role="alert"
        aria-live="assertive"
      >{{ searchError }}</div>

    </div>
  </div>
</template>

<script setup>
// ─────────────────────────────────────────────────────────────────────────────
// SubnavToolbar.vue — Script section
//
// This component is primarily a "dumb" display component — it receives all its
// data from ExploreView via props and sends actions back via events.
// Its only local logic is:
//   1. Combining the @input handler into a single function (handleInput)
//   2. Detecting when the user clicks outside the search box to close the dropdown
// ─────────────────────────────────────────────────────────────────────────────

// ref        → creates a reactive variable or DOM reference
// onMounted  → runs after the component is added to the page
// onUnmounted → runs before the component is removed from the page
import { ref, onMounted, onUnmounted } from 'vue'

// ── Props — data passed in from ExploreView ────────────────────────────────────
const props = defineProps({
  filtersOpen:        { type: Boolean, required: true },   // is the filter panel open?
  comparePanelOpen:   { type: Boolean, required: true },   // is the comparison panel open?
  sunPathOpen:        { type: Boolean, required: true },   // is the sun path panel open?
  sidebarOpen:        { type: Boolean, required: true },   // is the sidebar open?
  compareCount:       { type: Number,  default: 0 },       // number of buildings in comparison list
  searchQuery:        { type: String,  default: '' },      // current text in the search box
  searchResults:      { type: Array,   default: () => [] },// array of matching address results
  searchLoading:      { type: Boolean, default: false },   // true while waiting for search API
  searchDropdownOpen: { type: Boolean, default: false },   // is the results dropdown visible?
  searchFocusedIdx:   { type: Number,  default: -1 },      // keyboard-focused result index (-1 = none)
  searchError:        { type: String,  default: '' },      // error message from a failed search
  iconSearch:         { type: String,  required: true },   // URL of the search icon image
})

// ── Events this component can send ────────────────────────────────────────────
const emit = defineEmits([
  'toggle-filters',           // open/close the filter panel
  'toggle-compare',           // open/close the comparison panel
  'toggle-sun-path',          // open/close the sun path panel
  'toggle-sidebar',           // open/close the sidebar
  'update:searchQuery',       // two-way binding for the search text
  'search-input',             // user typed something (triggers a debounced API call)
  'search-keydown',           // user pressed a key (for arrow-key navigation in results)
  'select-result',            // user clicked a search result
  'update:searchFocusedIdx',  // update which result is keyboard-highlighted
  'clear-search',             // user clicked the × clear button
  'close-dropdown',           // close the results dropdown
  'show-guide',               // reopen the user guide
])

// wrapEl is a reference to the search wrapper <div>.
// We use it to detect clicks outside the search box.
const wrapEl = ref(null)

// Called whenever the user types in the search input.
// Emits two events: one to update the query text, another to trigger a search.
function handleInput(event) {
  emit('update:searchQuery', event.target.value)
  emit('search-input')
}

// ── Click-outside-to-close logic ──────────────────────────────────────────────
// When the user clicks anywhere outside the search wrapper, the dropdown closes.
// We attach this listener to the whole document and check if the clicked element
// is inside the search wrapper using .contains().
function onClickOutside(e) {
  if (wrapEl.value && !wrapEl.value.contains(e.target)) {
    emit('close-dropdown')
  }
}

// Start listening for outside clicks when this component appears on screen.
onMounted(() => document.addEventListener('mousedown', onClickOutside))

// Stop listening when this component is removed to avoid memory leaks.
onUnmounted(() => document.removeEventListener('mousedown', onClickOutside))
</script>

<style scoped>
/* Dark toolbar bar below the main navbar */
.explore-subnav {
  background: var(--ink2);
  border-bottom: 1px solid var(--ink-border);
  padding: 0 16px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: flex-end;  /* panel buttons on left, search on right */
  gap: 8px;
  flex-shrink: 0;
}

/* Container for the four panel-toggle buttons */
.subnav-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

/* Individual toggle button (Filter, Comparison, Sun Path, Building Info) */
.subnav-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  background: none;
  border: 1px solid transparent;
  border-radius: 7px;
  padding: 5px 11px;
  font-size: 13px;
  font-weight: 500;
  font-family: 'DM Sans', sans-serif;
  color: var(--nav-link);
  cursor: pointer;
  transition: background 0.15s, color 0.15s, border-color 0.15s;
  white-space: nowrap;
  position: relative;
}
.subnav-btn:hover { background: var(--ink); color: var(--nav-text); }

/* Active state (panel is open) — orange border and text */
.subnav-btn--active {
  background: var(--ink-active);
  border-color: var(--ink-active-border);
  color: var(--nav-active-color);
  font-weight: 600;
}
.subnav-btn:focus-visible { outline: 3px solid var(--accent); outline-offset: 2px; }

/* Small orange badge showing how many buildings are in the comparison list */
.subnav-badge {
  background: var(--city-light);
  color: #fff;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 700;
  padding: 1px 5px;
  min-width: 16px;
  text-align: center;
  line-height: 14px;
}

/* Search input wrapper */
.subnav-search-wrap { position: relative; width: 280px; flex-shrink: 0; }

/* Inner row: icon + input + clear button */
.subnav-search-inner {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(255,255,255,0.10);    /* slight white on dark background */
  border: 1px solid rgba(255,255,255,0.20);
  border-radius: 8px;
  padding: 0 12px;
  height: 32px;
  transition: border-color 0.15s, background 0.15s;
}
/* Highlight with orange border when the input is focused */
.subnav-search-inner:focus-within {
  border-color: var(--city-light);
  background: rgba(255,255,255,0.14);
}

.subnav-search-icon { width: 13px; height: 13px; opacity: 0.7; flex-shrink: 0; }

/* The text input itself — transparent background so it blends with the wrapper */
.subnav-search-input {
  flex: 1;
  background: none;
  border: none;
  outline: none;
  font-size: 14px;
  font-family: 'DM Sans', sans-serif;
  color: #F0EFE8;
  min-width: 0;
}
.subnav-search-input::placeholder { color: rgba(240,239,232,0.50); }

/* × clear button */
.subnav-search-clear {
  background: none; border: none; cursor: pointer;
  color: var(--nav-text-muted);
  display: flex; align-items: center;
  padding: 0; flex-shrink: 0;
}
.subnav-search-clear:hover { color: var(--nav-text); }
.subnav-search-clear:focus-visible { outline: 3px solid var(--accent); outline-offset: 2px; border-radius: 3px; }

/* Position the dropdown below the search input */
.subnav-dropdown { position: absolute; top: calc(100% + 6px); left: 0; width: 100%; z-index: 200; }
.subnav-search-error { position: absolute; top: calc(100% + 4px); left: 0; font-size: 13px; }

/* The dropdown list itself */
.search-dropdown {
  position: absolute; top: calc(100% + 4px); left: 0; right: 0;
  background: var(--surface); border: 1px solid var(--border); border-radius: 8px;
  list-style: none; margin: 0; padding: 4px 0; z-index: 200;
  max-height: 220px; overflow-y: auto;
  box-shadow: 0 6px 20px rgba(0,0,0,0.4);
}

/* One address result in the dropdown */
.search-dropdown-item {
  display: flex; align-items: flex-start; gap: 8px;
  padding: 8px 12px; cursor: pointer; transition: background 0.1s;
}
.search-dropdown-item:hover,
.search-dropdown-item--focused { background: var(--surface2); }
.search-result-pin { color: var(--accent); flex-shrink: 0; margin-top: 1px; }
.search-result-address { font-size: 13px; color: var(--text-primary); line-height: 1.4; }

/* Three-dot loading animation */
.search-dropdown-loading {
  display: flex; align-items: center; justify-content: center; gap: 5px; padding: 12px;
}
.search-loading-dot {
  width: 6px; height: 6px; border-radius: 50%; background: var(--accent);
  animation: search-dot-bounce 1s infinite ease-in-out;
}
.search-loading-dot:nth-child(2) { animation-delay: 0.15s; }
.search-loading-dot:nth-child(3) { animation-delay: 0.3s; }
@keyframes search-dot-bounce {
  0%, 80%, 100% { transform: scale(0.7); opacity: 0.5; }
  40% { transform: scale(1); opacity: 1; }
}

/* "No matching addresses found" message */
.search-dropdown-empty {
  padding: 10px 12px; font-size: 13px; color: var(--text-muted); text-align: center;
}

/* Guide button — subtle distinction from the panel toggles */
.subnav-btn--guide {
  border-color: rgba(255,255,255,0.12);
  margin-left: 6px;
}
.subnav-btn--guide:hover { border-color: var(--city-light); color: var(--city-light); }

/* ── Mobile: two-row layout so everything fits in 375px ──────────── */
@media (max-width: 640px) {
  /* Allow the bar to grow taller when content wraps */
  .explore-subnav {
    height: auto;
    flex-wrap: wrap;
    padding: 6px 12px 8px;
    gap: 6px;
    justify-content: flex-end;
  }

  /* Buttons row: stays on first line */
  .subnav-actions { gap: 4px; flex: 0 0 auto; }

  /* Icon-only buttons — font-size: 0 hides text, SVG width/height attrs are unaffected */
  .subnav-btn {
    font-size: 0;
    padding: 9px 10px;
    min-height: 36px;
    min-width: 36px;
    gap: 0;
    justify-content: center;
  }

  /* Restore the badge font size (it inherits font-size: 0 from the button otherwise) */
  .subnav-badge {
    font-size: 10px;
    position: absolute;
    top: 1px;
    right: 2px;
    transform: translate(40%, -40%);
    padding: 1px 4px;
    min-width: 14px;
    line-height: 14px;
  }

  /* Search drops to a full-width second row */
  .subnav-search-wrap {
    order: 2;
    width: 100%;
    flex: 1 1 100%;
  }
}
</style>
