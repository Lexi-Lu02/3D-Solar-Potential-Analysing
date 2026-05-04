<template>
  <div class="explore-subnav" role="toolbar" aria-label="Explore controls">

    <!-- Panel toggles -->
    <div class="subnav-actions">
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
        <span v-if="compareCount > 0" class="subnav-badge">{{ compareCount }}</span>
      </button>

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
    </div>

    <!-- Search by address -->
    <div class="subnav-search-wrap" ref="wrapEl" role="search">
      <label for="search-address" class="visually-hidden">Search buildings by address</label>
      <div class="subnav-search-inner">
        <img :src="iconSearch" alt="" aria-hidden="true" class="subnav-search-icon" />
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

      <!-- Loading -->
      <ul v-if="searchLoading" class="search-dropdown subnav-dropdown" role="listbox" id="search-listbox">
        <li class="search-dropdown-loading" aria-live="polite">
          <span class="search-loading-dot"></span>
          <span class="search-loading-dot"></span>
          <span class="search-loading-dot"></span>
        </li>
      </ul>

      <!-- Results -->
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
          <svg class="search-result-pin" width="12" height="14" viewBox="0 0 12 14" fill="none" aria-hidden="true">
            <path d="M6 0C3.24 0 1 2.24 1 5c0 3.75 5 9 5 9s5-5.25 5-9c0-2.76-2.24-5-5-5zm0 6.5A1.5 1.5 0 1 1 6 3.5a1.5 1.5 0 0 1 0 3z" fill="currentColor"/>
          </svg>
          <span class="search-result-address">{{ result.address }}</span>
        </li>
      </ul>

      <!-- No results -->
      <ul
        v-else-if="searchDropdownOpen && searchQuery.trim().length >= 2 && !searchLoading"
        class="search-dropdown subnav-dropdown"
        role="listbox"
        id="search-listbox"
      >
        <li class="search-dropdown-empty">No matching addresses found</li>
      </ul>

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
import { ref, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  filtersOpen:        { type: Boolean, required: true },
  comparePanelOpen:   { type: Boolean, required: true },
  sunPathOpen:        { type: Boolean, required: true },
  sidebarOpen:        { type: Boolean, required: true },
  compareCount:       { type: Number,  default: 0 },
  searchQuery:        { type: String,  default: '' },
  searchResults:      { type: Array,   default: () => [] },
  searchLoading:      { type: Boolean, default: false },
  searchDropdownOpen: { type: Boolean, default: false },
  searchFocusedIdx:   { type: Number,  default: -1 },
  searchError:        { type: String,  default: '' },
  iconSearch:         { type: String,  required: true },
})

const emit = defineEmits([
  'toggle-filters',
  'toggle-compare',
  'toggle-sun-path',
  'toggle-sidebar',
  'update:searchQuery',
  'search-input',
  'search-keydown',
  'select-result',
  'update:searchFocusedIdx',
  'clear-search',
  'close-dropdown',
])

const wrapEl = ref(null)

function handleInput(event) {
  emit('update:searchQuery', event.target.value)
  emit('search-input')
}

function onClickOutside(e) {
  if (wrapEl.value && !wrapEl.value.contains(e.target)) {
    emit('close-dropdown')
  }
}

onMounted(() => document.addEventListener('mousedown', onClickOutside))
onUnmounted(() => document.removeEventListener('mousedown', onClickOutside))
</script>

<style scoped>
.explore-subnav {
  background: var(--ink2);
  border-bottom: 1px solid var(--ink-border);
  padding: 0 16px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  flex-shrink: 0;
}

.subnav-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

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
.subnav-btn--active {
  background: var(--ink-active);
  border-color: var(--ink-active-border);
  color: var(--nav-active-color);
  font-weight: 600;
}
.subnav-btn:focus-visible { outline: 3px solid var(--accent); outline-offset: 2px; }

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

/* Search */
.subnav-search-wrap { position: relative; width: 280px; flex-shrink: 0; }

.subnav-search-inner {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(255,255,255,0.10);
  border: 1px solid rgba(255,255,255,0.20);
  border-radius: 8px;
  padding: 0 12px;
  height: 32px;
  transition: border-color 0.15s, background 0.15s;
}
.subnav-search-inner:focus-within {
  border-color: var(--city-light);
  background: rgba(255,255,255,0.14);
}

.subnav-search-icon { width: 13px; height: 13px; opacity: 0.7; flex-shrink: 0; }

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

.subnav-search-clear {
  background: none; border: none; cursor: pointer;
  color: var(--nav-text-muted);
  display: flex; align-items: center;
  padding: 0; flex-shrink: 0;
}
.subnav-search-clear:hover { color: var(--nav-text); }
.subnav-search-clear:focus-visible { outline: 3px solid var(--accent); outline-offset: 2px; border-radius: 3px; }

.subnav-dropdown { position: absolute; top: calc(100% + 6px); left: 0; width: 100%; z-index: 200; }

.subnav-search-error { position: absolute; top: calc(100% + 4px); left: 0; font-size: 13px; }

/* Search dropdown — shared classes scoped to this component */
.search-dropdown {
  position: absolute; top: calc(100% + 4px); left: 0; right: 0;
  background: var(--surface); border: 1px solid var(--border); border-radius: 8px;
  list-style: none; margin: 0; padding: 4px 0; z-index: 200;
  max-height: 220px; overflow-y: auto;
  box-shadow: 0 6px 20px rgba(0,0,0,0.4);
}
.search-dropdown-item {
  display: flex; align-items: flex-start; gap: 8px;
  padding: 8px 12px; cursor: pointer; transition: background 0.1s;
}
.search-dropdown-item:hover,
.search-dropdown-item--focused { background: var(--surface2); }
.search-result-pin { color: var(--accent); flex-shrink: 0; margin-top: 1px; }
.search-result-address { font-size: 13px; color: var(--text-primary); line-height: 1.4; }
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
.search-dropdown-empty {
  padding: 10px 12px; font-size: 13px; color: var(--text-muted); text-align: center;
}
</style>
