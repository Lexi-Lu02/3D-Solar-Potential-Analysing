<template>
  <!--
    MainNavbar.vue — The top navigation bar shown on every page after login.

    It contains:
      • The SolarMap logo and subtitle (left side)
      • Navigation links: Home, 3D Explore, Precincts, AI Insights (centre/left)
      • The active link is highlighted with an orange colour and border
      • "AI Insights" is shown as a disabled span (coming soon) instead of a clickable link
  -->
  <header class="main-nav">

    <!-- ── Brand / logo area ── -->
    <div class="main-nav-brand">
      <div class="main-nav-logo">
        <!-- :src binds the image source dynamically from the imported logoUrl variable -->
        <img :src="logoUrl" alt="SolarMap logo" />
      </div>
      <div class="main-nav-brand-text">
        <div class="main-nav-title">SolarMap</div>
        <div class="main-nav-subtitle">Melbourne CBD - 3D Solar Platform</div>
      </div>
    </div>

    <!-- ── Navigation links ── -->
    <!--
      aria-label="Main navigation" helps screen readers identify this as the main nav.
      v-for loops over the navItems array defined in the script section.
    -->
    <nav class="main-nav-links" aria-label="Main navigation">
      <template v-for="item in navItems" :key="item.to">

        <!--
          Active nav links (not disabled):
          RouterLink renders as an <a> tag and navigates to `item.to` when clicked.
          :class="{ 'is-active': route.path === item.to }" adds the active style
          when the current URL matches this link's path.
          :aria-current tells screen readers which page is currently active.
        -->
        <RouterLink
          v-if="!item.disabled"
          :to="item.to"
          class="main-nav-link"
          :class="{ 'is-active': route.path === item.to }"
          :aria-current="route.path === item.to ? 'page' : undefined"
        >
          <!-- Small icon next to the label (aria-hidden hides it from screen readers since the label already describes it) -->
          <img :src="item.icon" :alt="''" class="nav-link-icon" aria-hidden="true" />
          {{ item.label }}
        </RouterLink>

        <!--
          Disabled nav links (e.g. "AI Insights"):
          Rendered as a <span> instead of a link — clicking it does nothing.
          aria-disabled="true" tells screen readers it's not interactive.
          :title shows a "coming soon" tooltip on hover.
        -->
        <span
          v-else
          class="main-nav-link main-nav-link--disabled"
          aria-disabled="true"
          :title="`${item.label} — coming soon`"
        >
          <img :src="item.icon" :alt="''" class="nav-link-icon" aria-hidden="true" />
          {{ item.label }}
        </span>

      </template>
    </nav>

    <!-- Right side reserved for future content (e.g. a logout button) -->
    <div class="main-nav-right">
    </div>
  </header>
</template>

<script setup>
// ─────────────────────────────────────────────────────────────────────────────
// MainNavbar.vue — Script section
//
// This component is "stateless", it doesn't manage any changing data.
// It just reads the current URL route and renders navigation links accordingly.
// ─────────────────────────────────────────────────────────────────────────────

// useRoute gives us the current URL information so we can highlight the active link.
import { useRoute } from 'vue-router'

// Import the logo and icon images for the nav links.
import logoUrl       from '../pictures/Project logo.png'
import iconHome      from '../pictures/home.png'
import iconExplore   from '../pictures/3d explore.png'
import iconPrecincts from '../pictures/precinct.png'
import iconInsights  from '../pictures/ai insights.png'

// `route` is a reactive object representing the current URL.
// We use route.path to check which link is active.
const route = useRoute()

// ── Nav items list ────────────────────────────────────────────────────────────
// Each object in this array becomes one navigation link in the bar.
//   label    → the text shown in the link
//   to       → the URL path to navigate to when clicked
//   icon     → the small icon displayed next to the label
//   disabled → when true, renders a <span> instead of a clickable link
//              (used for features not yet built — they show a "coming soon" tooltip)
const navItems = [
  { label: 'Home',        to: '/',          icon: iconHome      },
  { label: '3D Explore',  to: '/explore',   icon: iconExplore   },
  { label: 'Suburb',      to: '/precincts', icon: iconPrecincts },
  { label: 'AI Insights', to: '/insights',  icon: iconInsights },
]
</script>

<style scoped>
/* Dark navigation bar across the top of every page */
.main-nav {
  background: var(--ink);
  border-bottom: 1px solid var(--ink-border);
  padding: 10px 20px;
  display: flex;
  align-items: center;
  gap: 18px;
  min-height: 64px;
  flex-shrink: 0;  /* prevents the navbar from shrinking when the page content is tall */
}

/* Logo + text side by side */
.main-nav-brand {
  display: flex;
  align-items: center;
  gap: 10px;
}

.main-nav-logo {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.main-nav-logo img {
  width: 36px;
  height: 36px;
  object-fit: contain;
}

/* "SolarMap" heading in the navbar */
.main-nav-title {
  font-family: 'DM Serif Display', serif;
  font-size: 20px;
  line-height: 1;
  color: var(--nav-text);
}

/* Subtitle below the logo text */
.main-nav-subtitle {
  font-size: 13px;
  color: var(--nav-text-muted);
  margin-top: 2px;
}

/* Container for the nav link buttons */
.main-nav-links {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: 8px;
}

/* Individual nav link styling */
.main-nav-link {
  text-decoration: none;
  color: var(--nav-link);
  font-size: 14px;
  font-weight: 500;
  padding: 7px 12px;
  border-radius: 9px;
  border: 1px solid transparent;
  transition: background 0.18s ease, color 0.18s ease, border-color 0.18s ease;
  display: flex;
  align-items: center;
  gap: 6px;
}

/* Small icon inside each link */
.nav-link-icon {
  width: 16px;
  height: 16px;
  object-fit: contain;
  flex-shrink: 0;
}

/* Hover state — slightly lighter background */
.main-nav-link:hover {
  background: var(--ink2);
  color: var(--nav-text);
}

/* Keyboard focus indicator */
.main-nav-link:focus-visible {
  outline: 3px solid var(--accent-warm);
  outline-offset: 2px;
  background: var(--ink2);
  color: var(--nav-text);
}

/* Disabled link (coming soon) — greyed out, cursor shows it's not clickable */
.main-nav-link--disabled {
  opacity: 0.4;
  cursor: not-allowed;
  pointer-events: none;  /* prevents any mouse interaction */
}

/* Active link (current page) — orange text with a border to stand out */
.main-nav-link.is-active {
  background: var(--ink-active);
  border-color: var(--ink-active-border);
  color: var(--nav-active-color);
  font-weight: 600;
}

/* Right side slot (empty, for future use) */
.main-nav-right {
  margin-left: auto;  /* pushes this div to the far right */
}

/* Badge style (currently unused but available for future features like notifications) */
.main-nav-badge {
  background: var(--ink-active);
  color: var(--nav-active-color);
  border: 1px solid var(--ink-active-border);
  border-radius: 999px;
  font-size: 13px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  padding: 6px 12px;
}

/* ── Responsive adjustments ────────────────────────────────────────────────── */

/* On smaller screens, hide the subtitle and tighten the gap between links */
@media (max-width: 1100px) {
  .main-nav-subtitle {
    display: none;
  }

  .main-nav-links {
    gap: 4px;
  }

  .main-nav-link {
    font-size: 13px;
    padding: 6px 9px;
  }
}

/* On very small screens, wrap the navbar to two rows */
@media (max-width: 880px) {
  .main-nav {
    flex-wrap: wrap;
    gap: 10px;
    padding-bottom: 12px;
  }

  .main-nav-right {
    margin-left: 0;
  }

  /* Nav links move to a second row */
  .main-nav-links {
    order: 3;
    width: 100%;
    overflow-x: visible;  /* no horizontal scroll — links will wrap or go icon-only */
    padding-bottom: 2px;
  }
}

/* ≤ 520px: show only icons so all four links fit on one row without overflow */
@media (max-width: 520px) {
  .main-nav { padding: 8px 14px; gap: 8px; }

  .main-nav-links { gap: 4px; flex-wrap: nowrap; }

  /* font-size: 0 hides the text label; the <img> icon is not affected */
  .main-nav-link {
    font-size: 0;
    padding: 10px 12px;
    border-radius: 8px;
    min-width: 44px;
    min-height: 44px;
    justify-content: center;
  }

  .nav-link-icon {
    width: 20px;
    height: 20px;
  }

  .main-nav-title { font-size: 17px; }
}
</style>
