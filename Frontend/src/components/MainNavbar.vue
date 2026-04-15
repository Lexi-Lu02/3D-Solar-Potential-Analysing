<template>
  <header class="main-nav">
    <div class="main-nav-brand">
      <div class="main-nav-logo"><img :src="logoUrl" alt="SolarMap logo" /></div>
      <div class="main-nav-brand-text">
        <div class="main-nav-title">SolarMap</div>
        <div class="main-nav-subtitle">Melbourne CBD - 3D Solar Platform</div>
      </div>
    </div>

    <nav class="main-nav-links" aria-label="Main navigation">
      <template v-for="item in navItems" :key="item.to">
        <RouterLink
          v-if="!item.disabled"
          :to="item.to"
          class="main-nav-link"
          :class="{ 'is-active': route.path === item.to }"
          :aria-current="route.path === item.to ? 'page' : undefined"
        >
          <img :src="item.icon" :alt="''" class="nav-link-icon" aria-hidden="true" />
          {{ item.label }}
        </RouterLink>
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

    <div class="main-nav-right">
    </div>
  </header>
</template>

<script setup>
import { useRoute } from 'vue-router'
import logoUrl       from '../pictures/Project logo.png'
import iconHome      from '../pictures/home.png'
import iconExplore   from '../pictures/3d explore.png'
import iconPrecincts from '../pictures/precinct.png'
import iconInsights  from '../pictures/ai insights.png'

const route = useRoute()

const navItems = [
  { label: 'Home',        to: '/',          icon: iconHome      },
  { label: '3D Explore',  to: '/explore',   icon: iconExplore   },
  { label: 'Precincts',   to: '/precincts', icon: iconPrecincts, disabled: true },
  { label: 'AI Insights', to: '/insights',  icon: iconInsights,  disabled: true },
]
</script>

<style scoped>
.main-nav {
  background: #3A3A3A;
  border-bottom: 1px solid #555555;
  padding: 10px 20px;
  display: flex;
  align-items: center;
  gap: 18px;
  min-height: 64px;
  flex-shrink: 0;
}

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

.main-nav-title {
  font-family: 'DM Serif Display', serif;
  font-size: 20px;
  line-height: 1;
  color: #FFFFFF;
}

.main-nav-subtitle {
  font-size: 11px;
  color: #A0A0A0;
  margin-top: 2px;
}

.main-nav-links {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: 8px;
}

.main-nav-link {
  text-decoration: none;
  color: #D1D5DB;
  font-size: 13px;
  font-weight: 500;
  padding: 7px 12px;
  border-radius: 9px;
  border: 1px solid transparent;
  transition: background 0.18s ease, color 0.18s ease, border-color 0.18s ease;
  display: flex;
  align-items: center;
  gap: 6px;
}

.nav-link-icon {
  width: 16px;
  height: 16px;
  object-fit: contain;
  flex-shrink: 0;
}

.main-nav-link:hover {
  background: #505050;
  color: #FFFFFF;
}

.main-nav-link:focus-visible {
  outline: 3px solid #FB923C;
  outline-offset: 2px;
  background: #505050;
  color: #FFFFFF;
}

.main-nav-link--disabled {
  opacity: 0.4;
  cursor: not-allowed;
  pointer-events: none;
}

.main-nav-link.is-active {
  background: #4A3728;
  border-color: #C2601A;
  color: #FB923C;
  font-weight: 600;
}

.main-nav-right {
  margin-left: auto;
}

.main-nav-badge {
  background: #4A3728;
  color: #FB923C;
  border: 1px solid #C2601A;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  padding: 6px 12px;
}

@media (max-width: 1100px) {
  .main-nav-subtitle {
    display: none;
  }

  .main-nav-links {
    gap: 4px;
  }

  .main-nav-link {
    font-size: 12px;
    padding: 6px 9px;
  }
}

@media (max-width: 880px) {
  .main-nav {
    flex-wrap: wrap;
    gap: 10px;
    padding-bottom: 12px;
  }

  .main-nav-right {
    margin-left: 0;
  }

  .main-nav-links {
    order: 3;
    width: 100%;
    overflow-x: auto;
    padding-bottom: 2px;
  }
}
</style>
