<template>
  <div class="home-screen">
    <MainNavbar />

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
            <button class="btn-primary" @click="goToExplore">
              Explore the Map →
            </button>
            <a class="btn-ghost" href="#about">Learn more</a>
          </div>
        </div>
        <div class="hero-visual">
          <div class="stat-grid">
            <div class="stat-card" v-for="s in stats" :key="s.label">
              <div class="stat-val">{{ s.value }}</div>
              <div class="stat-label">{{ s.label }}</div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Feature cards -->
    <section class="features" id="about">
      <div class="features-inner">
        <div class="section-eyebrow">What's inside</div>
        <h2 class="section-title">Built for solar decision-making</h2>
        <div class="feature-grid">
          <div class="feature-card" v-for="f in features" :key="f.title">
            <div class="feature-icon">{{ f.icon }}</div>
            <div class="feature-title">{{ f.title }}</div>
            <div class="feature-desc">{{ f.desc }}</div>
          </div>
        </div>
      </div>
    </section>

    <!-- CTA -->
    <section class="cta-section">
      <h2 class="cta-title">Ready to explore?</h2>
      <p class="cta-desc">Open the interactive 3D map and click any building to see its solar analysis.</p>
      <button class="btn-primary" @click="goToExplore">Open 3D Solar Map →</button>
    </section>

    <!-- Footer -->
    <footer class="home-footer">
      <span>Data: City of Melbourne Open Data 2023</span>
      <span>·</span>
      <span>Built with MapLibre GL · Vue 3</span>
      <span>·</span>
      <span>FIT5120 Iteration 1</span>
    </footer>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import MainNavbar from '../components/MainNavbar.vue'

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
    icon: '🏙️',
    title: '3D Building Extrusion',
    desc: 'Visualise every building in Melbourne CBD as a true-to-scale 3D model, colour-coded by solar score.',
  },
  {
    icon: '☀️',
    title: 'Solar Score Ranking',
    desc: 'Each building receives a solar potential score derived from rooftop area, roof type, and peak sun hours.',
  },
  {
    icon: '🔍',
    title: 'Roof Type Filtering',
    desc: 'Filter by Flat, Hip, Gable, Pyramid, or Shed roof types to zero in on suitable installation candidates.',
  },
  {
    icon: '⚡',
    title: 'Energy Estimates',
    desc: 'Instant kWh generation estimates using BOM-validated 4.1 peak sun hours/day for Melbourne CBD.',
  },
  {
    icon: '📍',
    title: 'Click-to-Inspect',
    desc: 'Click any building to open a full analysis panel with area metrics, height, roof type, and energy output.',
  },
  {
    icon: '📊',
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

    for (const feature of features) {
      const properties = feature.properties || {}
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
      { value: features.length.toLocaleString(), label: 'Buildings analysed' },
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

.btn-ghost {
  padding: 12px 20px;
  color: #6B6560; text-decoration: none;
  font-size: 14px; font-weight: 500;
  border: 1px solid #E2DDD4; border-radius: 8px;
  transition: background 0.15s, color 0.15s;
  display: inline-block;
}
.btn-ghost:hover { background: #ffffff; color: #1C1917; }

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

.feature-icon { font-size: 24px; margin-bottom: 10px; }
.feature-title { font-size: 14px; font-weight: 600; margin-bottom: 6px; }
.feature-desc { font-size: 13px; color: #6B6560; line-height: 1.6; }

/* CTA */
.cta-section {
  text-align: center;
  padding: 72px 32px;
  max-width: 560px;
  margin: 0 auto;
}

.cta-title {
  font-family: 'DM Serif Display', serif;
  font-size: 30px; margin-bottom: 12px;
}

.cta-desc {
  font-size: 14px; color: #6B6560; line-height: 1.6;
  margin-bottom: 24px;
}

/* Footer */
.home-footer {
  border-top: 1px solid #E2DDD4;
  padding: 16px 32px;
  display: flex; gap: 10px; justify-content: center;
  font-size: 11px; color: #A8A29E; flex-wrap: wrap;
}

/* Responsive */
@media (max-width: 900px) {
  .hero { padding: 48px 24px; }
  .hero-inner { flex-direction: column; gap: 32px; }
  .hero-title { font-size: 34px; }
  .stat-grid { grid-template-columns: 1fr 1fr; }
  .feature-grid { grid-template-columns: 1fr 1fr; }
  .features { padding: 48px 24px; }
}

@media (max-width: 600px) {
  .feature-grid { grid-template-columns: 1fr; }
  .hero-title { font-size: 28px; }
}
</style>
