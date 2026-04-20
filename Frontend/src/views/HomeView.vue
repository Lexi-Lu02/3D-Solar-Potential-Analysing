<template>
  <div class="home-screen">
    <MainNavbar />

    <main id="main-content">

    <!-- Hero -->
    <section class="hero">
      <div class="hero-inner">
        <div class="hero-content hero-content-card">
          <div class="hero-text">
            <div class="hero-eyebrow">Melbourne CBD · 2023 Data</div>
            <h1 class="hero-title">Discover Your Building's<br><span class="hero-accent">Solar Potential</span></h1>
            <p class="hero-desc">
              Explore an interactive 3D model of Melbourne's CBD buildings, each analysed for rooftop solar viability.
              Identify high-yield sites, estimate annual energy generation, and support sustainable urban planning.
            </p>
            <div class="hero-actions">
              <button class="btn-primary" @click="goToExplore" aria-label="Explore the 3D Solar Map">
                Explore the Map →
              </button>
              <a class="btn-ghost" href="#about" aria-label="Learn more about SolarMap features">Learn more</a>
            </div>
          </div>
          <dl class="stat-grid" aria-label="Key statistics">
            <div class="stat-card" v-for="s in stats" :key="s.label">
              <dd class="stat-val">{{ s.value }}</dd>
              <dt class="stat-label">{{ s.label }}</dt>
            </div>
          </dl>
        </div>
      </div>
      <div class="hero-photo-credit">
        Photo by <a href="https://unsplash.com/photos/ZXJKUWUIjSM" target="_blank" rel="noopener" aria-label="Hero photo credit on Unsplash (opens in new tab)">Unsplash</a>
      </div>
    </section>

    <!-- Feature cards -->
    <section class="features" id="about">
      <div class="features-inner">
        <div class="section-eyebrow">What's inside</div>
        <h2 class="section-title">Built for solar decision-making</h2>
        <div class="feature-grid">
          <div class="feature-card" v-for="f in features" :key="f.title">
            <div class="feature-icon"><img :src="f.icon" :alt="f.title" /></div>
            <div class="feature-title">{{ f.title }}</div>
            <div class="feature-desc">{{ f.desc }}</div>
          </div>
        </div>
      </div>
    </section>

    </main>

    <!-- Footer -->
    <footer class="home-footer" aria-label="Site footer">
      <div class="footer-inner">
        <div class="footer-brand">
          <img :src="logoUrl" alt="SolarMap logo" class="footer-logo" />
          <div>
            <div class="footer-brand-name">SolarMap Melbourne</div>
            <div class="footer-brand-sub">3D City Solar Potential Platform</div>
          </div>
        </div>

        <div class="footer-links">
          <div class="footer-col-group">
            <div class="footer-col">
              <div class="footer-col-title">Platform</div>
                <RouterLink class="footer-link footer-link--url" to="/">
                  Home
                </RouterLink>

                <RouterLink class="footer-link footer-link--url" to="/explore">
                  3D Explore
                </RouterLink>

                <RouterLink class="footer-link footer-link--url" to="/precincts">
                  Precincts
                </RouterLink>

                <RouterLink class="footer-link footer-link--url" to="/insights">
                  AI Insights
                </RouterLink>
            </div>
            <div class="footer-col">
              <div class="footer-col-title">Built With</div>
              <span class="footer-link">MapLibre GL JS</span>
              <span class="footer-link">Vue 3 · Vite</span>
              <span class="footer-link">CARTO Basemaps</span>
              <span class="footer-link">OpenStreetMap</span>
            </div>
          </div>
          <div class="footer-col">
            <div class="footer-col-title">Data Sources</div>
            <a class="footer-link footer-link--url" href="https://data.melbourne.vic.gov.au/explore/dataset/2023-building-footprints/" target="_blank" rel="noopener noreferrer">City of Melbourne Building Footprints</a>
            <a class="footer-link footer-link--url" href="https://www.melbourne.vic.gov.au/mapping-our-roofs" target="_blank" rel="noopener noreferrer">City of Melbourne Rooftop Project</a>
            <a class="footer-link footer-link--url" href="http://www.bom.gov.au/climate/austmaps/about-solar-maps.shtml" target="_blank" rel="noopener noreferrer">Bureau of Meteorology (BOM)</a>
            <a class="footer-link footer-link--url" href="https://power.larc.nasa.gov/" target="_blank" rel="noopener noreferrer">NASA POWER Monthly PSH</a>
            <a class="footer-link footer-link--url" href="https://pv-map.apvi.org.au/" target="_blank" rel="noopener noreferrer">APVI Solar Map</a>
            <a class="footer-link footer-link--url" href="https://pv-map.apvi.org.au/sunspot/" target="_blank" rel="noopener noreferrer">SunSPOT (UNSW / APVI)</a>
            <a class="footer-link footer-link--url" href="https://developers.google.com/maps/documentation/solar" target="_blank" rel="noopener noreferrer">Google Solar API</a>
          </div>
          <div class="footer-col">
            <div class="footer-col-title">About Us</div>
            <span class="footer-link">SolarMap is a FIT5120 project built by Team TP06,<br>exploring rooftop solar potential across Melbourne's CBD.</span>
            <a class="footer-link footer-link--url footer-link--eportfolio" href="https://bit.ly/SolarMapTP06" target="_blank" rel="noopener noreferrer">
              View E-Portfolio →
            </a>
          </div>
        </div>

      </div>

    </footer>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import MainNavbar from '../components/MainNavbar.vue'
import logoUrl          from '../pictures/Logo.png'
import icon3DBuilding    from '../pictures/3D Building Extrusion.png'
import iconSolarScore    from '../pictures/Solar Score Ranking.png'
import iconRoofType      from '../pictures/Roof Type Filtering.png'
import iconEnergy        from '../pictures/Energy Estimates.png'
import iconClickInspect  from '../pictures/Click-to-Inspect.png'
import iconComparison    from '../pictures/Comparison View.png'

const router = useRouter()
const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1'

const stats = ref([
  { value: '500+',    label: 'Buildings analysed' },
  { value: '169K m²', label: 'Usable rooftop area' },
  { value: '37.9 GWh', label: 'Est. annual yield' },
  { value: '237',     label: 'High-potential sites' },
])

const features = [
  {
    icon: icon3DBuilding,
    title: '3D Building Extrusion',
    desc: 'Visualise every building in Melbourne CBD as a true-to-scale 3D model, colour-coded by solar score.',
  },
  {
    icon: iconSolarScore,
    title: 'Solar Score Ranking',
    desc: 'Each building receives a solar potential score derived from rooftop area, roof type, and peak sun hours.',
  },
  {
    icon: iconRoofType,
    title: 'Roof Type Filtering',
    desc: 'Filter by Flat, Hip, Gable, Pyramid, or Shed roof types to zero in on suitable installation candidates.',
  },
  {
    icon: iconEnergy,
    title: 'Energy Estimates',
    desc: 'Instant kWh generation estimates using BOM-validated 4.1 peak sun hours/day for Melbourne CBD.',
  },
  {
    icon: iconClickInspect,
    title: 'Click-to-Inspect',
    desc: 'Click any building to open a full analysis panel with area metrics, height, roof type, and energy output.',
  },
  {
    icon: iconComparison,
    title: 'Comparison View',
    desc: 'Select multiple buildings side-by-side to compare solar potential across different city blocks.',
  },
]

function goToExplore() {
  router.push('/explore')
}

onMounted(async () => {
  try {
    const res = await fetch(`${API_BASE}/buildings/stats`)
    if (!res.ok) return
    const d = await res.json()

    const area = d.usable_area_m2
    const areaFmt = Number.isFinite(area)
      ? (area >= 1000 ? `${Math.round(area / 1000)}K m²` : `${Math.round(area).toLocaleString()} m²`)
      : '—'
    const kwh = d.kwh_annual
    const yieldFmt = Number.isFinite(kwh) ? `${(kwh / 1_000_000).toFixed(1)} GWh` : '—'

    stats.value = [
      { value: Number.isFinite(d.total_buildings)      ? d.total_buildings.toLocaleString()      : '—', label: 'Buildings analysed' },
      { value: areaFmt,                                                                                   label: 'Usable rooftop area' },
      { value: yieldFmt,                                                                                  label: 'Est. annual yield' },
      { value: Number.isFinite(d.high_potential_count) ? d.high_potential_count.toLocaleString() : '—', label: 'High-potential sites' },
    ]
  } catch {
    // Keep default fallback values when data cannot be fetched.
  }
})
</script>

<style scoped>
.home-screen {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bg);
  font-family: 'DM Sans', sans-serif;
  color: var(--text-primary);
  overflow-y: auto;
}

/* Hero */
.hero {
  padding: 110px 64px 100px;
  min-height: 72vh;
  width: 100%;
  position: relative;
  display: flex;
  align-items: center;
  background-image:
    linear-gradient(to right, rgba(0,0,0,0.55) 0%, rgba(0,0,0,0.30) 55%, rgba(0,0,0,0.10) 100%),
    url('../pictures/Home Page Background.jpg');
  background-size: cover;
  background-repeat: no-repeat;
  background-position: center center;
}

.hero-inner {
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
  display: flex;
  align-items: center;
}

.hero-content {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 56px;
  width: 100%;
}

.hero-content-card {
  background: transparent;
  border: none;
  border-radius: 0;
  padding: 0;
  backdrop-filter: none;
  -webkit-backdrop-filter: none;
  box-shadow: none;
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  gap: 28px;
  width: 100%;
}

.hero-text {
  flex: 2;
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: rgba(255, 255, 255, 0.10);
  border: 1px solid rgba(255, 255, 255, 0.22);
  border-radius: 16px;
  padding: 36px 40px;
  backdrop-filter: blur(18px) saturate(1.3);
  -webkit-backdrop-filter: blur(18px) saturate(1.3);
  box-shadow: 0 4px 28px rgba(0, 0, 0, 0.18), inset 0 1px 0 rgba(255, 255, 255, 0.18);
}

.hero-photo-credit {
  position: absolute;
  bottom: 6px;
  right: 8px;
  font-size: 10px;
  color: rgba(var(--text-primary-rgb), 0.45);
  background: rgba(var(--bg-rgb), 0.6);
  padding: 2px 6px;
  border-radius: 3px;
}
.hero-photo-credit a {
  color: inherit;
  text-decoration: none;
}
.hero-photo-credit a:hover {
  text-decoration: underline;
}

.hero-eyebrow {
  font-size: 12px; font-weight: 600;
  text-transform: uppercase; letter-spacing: 1px;
  color: var(--city-light); margin-bottom: 14px;
}

.hero-title {
  font-family: 'DM Serif Display', serif;
  font-size: 46px; line-height: 1.15;
  margin-bottom: 18px; color: var(--nav-text);
}

.hero-accent { color: var(--city-light); }

.hero-desc {
  font-size: 15px; line-height: 1.7;
  color: rgba(255, 255, 255, 0.90);
  max-width: 480px;
  margin-bottom: 28px;
  text-shadow: 0 1px 6px rgba(0, 0, 0, 0.45);
}

.hero-actions { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }

.btn-primary {
  padding: 12px 24px;
  background: var(--city-light); color: var(--ink);
  border: none; border-radius: 8px;
  font-family: 'DM Sans', sans-serif; font-size: 14px; font-weight: 600;
  cursor: pointer; transition: background 0.15s;
  text-decoration: none;
}
.btn-primary:hover { background: var(--city-light-dim); color: white; }
.btn-primary:focus-visible {
  outline: 3px solid var(--city-light);
  outline-offset: 3px;
  background: var(--city-light-dim);
  color: white;
}

.btn-ghost {
  padding: 12px 20px;
  color: var(--nav-link); text-decoration: none;
  font-size: 14px; font-weight: 500;
  border: 1px solid rgba(255, 255, 255, 0.25); border-radius: 8px;
  transition: background 0.15s, color 0.15s, border-color 0.15s;
  display: inline-block;
}
.btn-ghost:hover { background: rgba(255,255,255,0.10); color: var(--nav-text); border-color: rgba(255,255,255,0.45); }
.btn-ghost:focus-visible {
  outline: 3px solid var(--city-light);
  outline-offset: 3px;
  background: rgba(255,255,255,0.10);
  color: var(--nav-text);
}

/* Stat grid (inside hero, right side) */
.stat-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
  flex: 2;
  min-width: 0;
}

.stat-card {
  background: rgba(255, 255, 255, 0.13);
  border: 1px solid rgba(255, 255, 255, 0.28);
  border-radius: 14px;
  padding: 20px 22px;
  backdrop-filter: blur(20px) saturate(1.4);
  -webkit-backdrop-filter: blur(20px) saturate(1.4);
  box-shadow:
    0 4px 24px rgba(0, 0, 0, 0.18),
    inset 0 1px 0 rgba(255, 255, 255, 0.20);
  transition: background 0.2s;
}

.stat-card:hover {
  background: rgba(255, 255, 255, 0.19);
}

.stat-val {
  font-family: 'DM Serif Display', serif;
  font-size: 30px; color: #ffffff;
  margin-bottom: 5px;
  text-shadow: 0 1px 8px rgba(0,0,0,0.25);
}

.stat-label {
  font-size: 12px; color: rgba(255,255,255,0.72); line-height: 1.4;
}

/* Features */
.features {
  background: var(--surface);
  border-top: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
  padding: 64px 64px;
}

.features-inner { max-width: 1200px; margin: 0 auto; }

.section-eyebrow {
  font-size: 12px; font-weight: 600;
  text-transform: uppercase; letter-spacing: 1px;
  color: var(--city-light); margin-bottom: 10px;
}

.section-title {
  font-family: 'DM Serif Display', serif;
  font-size: 32px; margin-bottom: 40px; color: var(--text-primary);
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
}

.feature-card {
  background: var(--surface2); border: 1px solid var(--border);
  border-radius: 12px; padding: 22px 20px;
}

.feature-icon { margin-bottom: 10px; }
.feature-icon img { width: 40px; height: 40px; object-fit: contain; }
.feature-title { font-size: 14px; font-weight: 600; margin-bottom: 6px; }
.feature-desc { font-size: 13px; color: var(--text-secondary); line-height: 1.6; }

/* Footer */
.home-footer {
  background: var(--ink);
  color: var(--nav-link);
  font-family: 'DM Sans', sans-serif;
  flex-shrink: 0;
}

.footer-inner {
  display: flex;
  align-items: flex-start;
  gap: 56px;
  max-width: 1200px;
  margin: 0 auto;
  padding: 48px 64px 40px;
  flex-wrap: wrap;
}

.footer-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 0 0 auto;
  min-width: 180px;
}

.footer-logo {
  width: 40px;
  height: 40px;
  object-fit: contain;
  opacity: 0.9;
}

.footer-brand-name {
  font-family: 'DM Serif Display', serif;
  font-size: 16px;
  color: var(--nav-text);
  line-height: 1.2;
}

.footer-brand-sub {
  font-size: 11px;
  color: var(--nav-text-muted);
  margin-top: 2px;
}

.footer-links {
  display: flex;
  gap: 48px;
  flex: 1;
  flex-wrap: wrap;
}

.footer-col-group {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.footer-col {
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-width: 140px;
}

.footer-col-title {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  color: var(--city-light);
  margin-bottom: 2px;
}

.footer-link {
  font-size: 13px;
  color: var(--nav-text-muted);
  line-height: 1.4;
  cursor: default;
  text-decoration: none;
}

.footer-link--url {
  cursor: pointer;
  transition: color 0.15s;
}

.footer-link--url:hover {
  color: var(--accent-warm);
  text-decoration: underline;
}

.footer-link--url:focus-visible {
  outline: 2px solid var(--accent-warm);
  outline-offset: 2px;
  border-radius: 2px;
  color: var(--accent-warm);
}

.footer-link--eportfolio {
  display: inline-block;
  margin-top: 6px;
  color: var(--city-light);
  font-weight: 600;
  font-size: 13px;
}

.footer-link--eportfolio:hover {
  color: var(--city-light-dim);
  text-decoration: underline;
}


/* Responsive */
@media (max-width: 900px) {
  .hero { padding: 64px 24px; min-height: unset; }
  .hero-content-card { flex-direction: column; gap: 36px; }
  .hero-text { max-width: 100%; padding-right: 0; }
  .stat-grid { width: 100%; grid-template-columns: 1fr 1fr; }
  .hero-title { font-size: 34px; }
  .feature-grid { grid-template-columns: 1fr 1fr; }
  .features { padding: 48px 24px; }
  .footer-inner { padding: 40px 24px 32px; gap: 32px; }
  .footer-links { gap: 28px; }
  .footer-bottom { padding: 14px 24px; }
}

@media (max-width: 600px) {
  .feature-grid { grid-template-columns: 1fr; }
  .hero-title { font-size: 28px; }
  .footer-inner { flex-direction: column; gap: 28px; }
  .footer-links { flex-direction: column; gap: 20px; }
  .footer-cta { width: 100%; }
  .footer-cta-btn { width: 100%; }
}
</style>
