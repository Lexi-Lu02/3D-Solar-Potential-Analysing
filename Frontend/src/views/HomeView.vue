<template>
  <div class="home-screen">
    <MainNavbar />

    <main id="main-content">

    <!-- Hero -->
    <section class="hero">
      <div class="hero-inner">
        <div class="hero-content">
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
        <div class="hero-visual" aria-label="Key statistics">
          <dl class="stat-grid">
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
              <span class="footer-link">Home</span>
              <span class="footer-link">3D Explore</span>
              <span class="footer-link">Precincts</span>
              <span class="footer-link">AI Insights</span>
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
import logoUrl          from '../pictures/Project logo.png'
import icon3DBuilding    from '../pictures/3D Building Extrusion.png'
import iconSolarScore    from '../pictures/Solar Score Ranking.png'
import iconRoofType      from '../pictures/Roof Type Filtering.png'
import iconEnergy        from '../pictures/Energy Estimates.png'
import iconClickInspect  from '../pictures/Click-to-Inspect.png'
import iconComparison    from '../pictures/Comparison View.png'

const router = useRouter()
const GEOJSON_PATH = '/combined-buildings.geojson'

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

function formatAreaM2(value) {
  if (!Number.isFinite(value)) return '—'
  if (value >= 1000) return `${Math.round(value / 1000)}K m²`
  return `${Math.round(value).toLocaleString()} m²`
}

function formatGWhFromKwh(value) {
  if (!Number.isFinite(value)) return '—'
  return `${(value / 1_000_000).toFixed(1)} GWh`
}

onMounted(async () => {
  try {
    const response = await fetch(GEOJSON_PATH)
    if (!response.ok) return
    const data = await response.json()
    const features = data.features || []

    let usableAreaTotal = 0
    let annualKwhTotal = 0
    let highPotentialCount = 0

    const seenIds = new Set()

    for (const feature of features) {
      const properties = feature.properties || {}
      const structureId = properties.structure_id

      // Skip duplicate structure IDs
      if (structureId != null) {
        if (seenIds.has(structureId)) continue
        seenIds.add(structureId)
      }

      const score = Number(properties.solar_score || 0)
      const usableArea = Number(properties.usable_roof_area || 0)
      const annualKwh = Number(properties.kwh_annual || 0)

      if (score >= 60) highPotentialCount += 1
      if (properties.has_solar_data) {
        usableAreaTotal += usableArea
        annualKwhTotal += annualKwh
      }
    }

    stats.value = [
      { value: seenIds.size.toLocaleString(), label: 'Buildings analysed' },
      { value: formatAreaM2(usableAreaTotal), label: 'Usable rooftop area' },
      { value: formatGWhFromKwh(annualKwhTotal), label: 'Est. annual yield' },
      { value: highPotentialCount.toLocaleString(), label: 'High-potential sites' },
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
  background: #F7F5F0;
  font-family: 'DM Sans', sans-serif;
  color: #1C1917;
  overflow-y: auto;
}

/* Hero */
.hero {
  padding: 72px 64px;
  width: 100%;
  position: relative;
  background-image:
    linear-gradient(90deg, rgba(247, 245, 240, 0.88) 0%, rgba(247, 245, 240, 0.72) 45%, rgba(247, 245, 240, 0.52) 100%),
    url('../pictures/Home Pge Background.jpg');
  background-size: cover;
  background-repeat: no-repeat;
  background-position: center 24%;
}

.hero-inner {
  display: flex;
  align-items: center;
  gap: 48px;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}

.hero-content { flex: 1; }

.hero-photo-credit {
  position: absolute;
  bottom: 6px;
  right: 8px;
  font-size: 10px;
  color: rgba(28, 25, 23, 0.45);
  background: rgba(247, 245, 240, 0.6);
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
  color: #EA580C; margin-bottom: 14px;
}

.hero-title {
  font-family: 'DM Serif Display', serif;
  font-size: 46px; line-height: 1.15;
  margin-bottom: 18px; color: #1C1917;
}

.hero-accent { color: #EA580C; }

.hero-desc {
  font-size: 15px; line-height: 1.7;
  color: #6B6560; max-width: 480px;
  margin-bottom: 28px;
}

.hero-actions { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }

.btn-primary {
  padding: 12px 24px;
  background: #EA580C; color: white;
  border: none; border-radius: 8px;
  font-family: 'DM Sans', sans-serif; font-size: 14px; font-weight: 600;
  cursor: pointer; transition: background 0.15s;
  text-decoration: none;
}
.btn-primary:hover { background: #C2410C; }
.btn-primary:focus-visible {
  outline: 3px solid #1C1917;
  outline-offset: 3px;
  background: #C2410C;
}

.btn-ghost {
  padding: 12px 20px;
  color: #6B6560; text-decoration: none;
  font-size: 14px; font-weight: 500;
  border: 1px solid #E2DDD4; border-radius: 8px;
  transition: background 0.15s, color 0.15s;
  display: inline-block;
}
.btn-ghost:hover { background: #ffffff; color: #1C1917; }
.btn-ghost:focus-visible {
  outline: 3px solid #EA580C;
  outline-offset: 3px;
  background: #ffffff;
  color: #1C1917;
}

/* Stat grid (hero right side) */
.hero-visual { flex: 0 0 auto; }
.stat-grid {
  display: grid; grid-template-columns: 1fr 1fr; gap: 16px;
}

.stat-card {
  background: #ffffff; border: 1px solid #E2DDD4;
  border-radius: 12px; padding: 20px 22px;
  min-width: 140px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}

.stat-val {
  font-family: 'DM Serif Display', serif;
  font-size: 28px; color: #1C1917;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 12px; color: #A8A29E; line-height: 1.4;
}

/* Features */
.features {
  background: #ffffff;
  border-top: 1px solid #E2DDD4;
  border-bottom: 1px solid #E2DDD4;
  padding: 64px 64px;
}

.features-inner { max-width: 1200px; margin: 0 auto; }

.section-eyebrow {
  font-size: 12px; font-weight: 600;
  text-transform: uppercase; letter-spacing: 1px;
  color: #EA580C; margin-bottom: 10px;
}

.section-title {
  font-family: 'DM Serif Display', serif;
  font-size: 32px; margin-bottom: 40px; color: #1C1917;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
}

.feature-card {
  background: #F7F5F0; border: 1px solid #E2DDD4;
  border-radius: 12px; padding: 22px 20px;
}

.feature-icon { margin-bottom: 10px; }
.feature-icon img { width: 40px; height: 40px; object-fit: contain; }
.feature-title { font-size: 14px; font-weight: 600; margin-bottom: 6px; }
.feature-desc { font-size: 13px; color: #6B6560; line-height: 1.6; }

/* Footer */
.home-footer {
  background: #2C2C2C;
  color: #D1D5DB;
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
  color: #FFFFFF;
  line-height: 1.2;
}

.footer-brand-sub {
  font-size: 11px;
  color: #9CA3AF;
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
  color: #FB923C;
  margin-bottom: 2px;
}

.footer-link {
  font-size: 13px;
  color: #9CA3AF;
  line-height: 1.4;
  cursor: default;
  text-decoration: none;
}

.footer-link--url {
  cursor: pointer;
  transition: color 0.15s;
}

.footer-link--url:hover {
  color: #FB923C;
  text-decoration: underline;
}

.footer-link--url:focus-visible {
  outline: 2px solid #FB923C;
  outline-offset: 2px;
  border-radius: 2px;
  color: #FB923C;
}

.footer-link--eportfolio {
  display: inline-block;
  margin-top: 6px;
  color: #FB923C;
  font-weight: 600;
  font-size: 13px;
}

.footer-link--eportfolio:hover {
  color: #FDBA74;
  text-decoration: underline;
}


/* Responsive */
@media (max-width: 900px) {
  .hero { padding: 48px 24px; }
  .hero-inner { flex-direction: column; gap: 32px; }
  .hero-title { font-size: 34px; }
  .stat-grid { grid-template-columns: 1fr 1fr; }
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
