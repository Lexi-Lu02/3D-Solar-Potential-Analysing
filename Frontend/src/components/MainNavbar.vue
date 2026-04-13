<template>
  <header class="main-nav">
    <div class="main-nav-brand">
      <div class="main-nav-logo"><img :src="logoUrl" alt="SolarMap logo" /></div>
      <div class="main-nav-brand-text">
        <div class="main-nav-title">SolarMap</div>
        <div class="main-nav-subtitle">Melbourne - 3D Solar Platform</div>
      </div>
    </div>

    <nav class="main-nav-links">
      <RouterLink
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        class="main-nav-link"
        :class="{ 'is-active': route.path === item.to }"
      >
        <img :src="item.icon" :alt="item.label" class="nav-link-icon" />
        {{ item.label }}
      </RouterLink>
    </nav>

    <div class="main-nav-right">
      <span class="main-nav-badge">Iteration 1 · MVP</span>
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
  { label: 'Home',       to: '/',          icon: iconHome      },
  { label: '3D Explore', to: '/explore',   icon: iconExplore   },
  { label: 'Precincts',  to: '/precincts', icon: iconPrecincts },
  { label: 'AI Insights',to: '/insights',  icon: iconInsights  },
]
</script>

<style scoped>
.main-nav {
  background: linear-gradient(135deg, #fff7ed 0%, #f7f5f0 55%, #fef3c7 100%);
  border-bottom: 1px solid #e2ddd4;
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
  color: #1c1917;
}

.main-nav-subtitle {
  font-size: 11px;
  color: #a8a29e;
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
  color: #6b6560;
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
  background: #f0ede6;
  color: #1c1917;
}

.main-nav-link.is-active {
  background: #fff7ed;
  border-color: #fed7aa;
  color: #ea580c;
  font-weight: 600;
}

.main-nav-right {
  margin-left: auto;
}

.main-nav-badge {
  background: #fff7ed;
  color: #ea580c;
  border: 1px solid #fed7aa;
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
