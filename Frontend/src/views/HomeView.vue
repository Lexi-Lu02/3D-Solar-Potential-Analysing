<template>
  <div class="home-screen">
    <MainNavbar />

    <main id="main-content">

    <!-- ── Hero ─────────────────────────────────────────────── -->
    <section class="hero">
      <div class="hero-inner">
        <div class="hero-content">
          <div class="hero-text">
            <div class="hero-eyebrow">Melbourne CBD · 2023 Data</div>
            <h1 class="hero-title">
              Discover Your Building's<br>
              <span class="hero-accent">Solar Potential</span>
            </h1>
            <p class="hero-desc">
              Explore an interactive 3D model of Melbourne's CBD buildings, each analysed
              for rooftop solar viability. Identify high-yield sites, estimate annual energy
              generation, and support sustainable urban planning.
            </p>
            <div class="hero-actions">
              <button class="btn-primary" @click="goToExplore" aria-label="Explore the Map">
                Explore the Map →
              </button>
              <a class="btn-ghost" href="#features" aria-label="See platform features">See features</a>
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
    </section>

    <!-- ── 3D Explore ─────────────────────────────────────────── -->
    <section class="seg seg--surface" id="features">
      <div class="seg-inner">
        <span class="deco-num" aria-hidden="true">01</span>

        <div class="split">
          <div class="split-text">
            <p class="eyebrow">3D Explore</p>
            <h2 class="seg-title">Analyse every rooftop in the CBD</h2>
            <p class="seg-desc">
              Fly over Melbourne's CBD in an interactive 3D map. Every building is
              colour-coded by its solar score and a single click opens a complete analysis.
            </p>
            <ul class="bullet-list" aria-label="3D Explore features">
              <li v-for="f in exploreFeatures" :key="f">{{ f }}</li>
            </ul>
            <RouterLink class="text-link" to="/explore" aria-label="Explore the Map">Explore the Map →</RouterLink>
          </div>
          <div class="split-media">
            <img :src="img3dExplore" alt="Screenshot of the 3D solar explore map" class="split-img" />
          </div>
        </div>

        <!-- Three analysis panels woven into this section -->
        <div class="panel-trio">
          <p class="panel-trio-label">Click any building — three analysis panels open instantly</p>
          <div class="panel-row">
            <div class="panel-item" v-for="p in analysisPanels" :key="p.title">
              <img :src="p.icon" :alt="p.title" class="panel-icon" />
              <div class="panel-title">{{ p.title }}</div>
              <div class="panel-desc">{{ p.desc }}</div>
              <ul class="panel-bullets">
                <li v-for="b in p.bullets" :key="b">{{ b }}</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ── Precincts ──────────────────────────────────────────── -->
    <section class="seg seg--bg">
      <div class="seg-inner">
        <span class="deco-num deco-num--right" aria-hidden="true">02</span>

        <div class="split split--rev">
          <div class="split-media">
            <img :src="imgPrecinct" alt="Screenshot of the precinct solar rankings map" class="split-img" />
          </div>
          <div class="split-text">
            <p class="eyebrow">Precincts</p>
            <h2 class="seg-title">Rank neighbourhoods by solar potential</h2>
            <p class="seg-desc">
              Zoom out from individual buildings to compare entire precincts.
              Identify which neighbourhoods have the most untapped solar opportunity.
            </p>
            <ul class="bullet-list" aria-label="Precincts features">
              <li v-for="f in precinctFeatures" :key="f">{{ f }}</li>
            </ul>
            <RouterLink class="text-link" to="/precincts" aria-label="View Precinct">View Precinct →</RouterLink>
          </div>
        </div>
      </div>
    </section>

    <!-- ── How it works ───────────────────────────────────────── -->
    <section class="seg seg--bg" id="how-it-works">
      <div class="seg-inner seg-inner--narrow">
        <p class="eyebrow eyebrow--center">How it works</p>
        <h2 class="seg-title seg-title--center">From map to action in three steps</h2>
        <div class="steps-wrap">
          <div class="steps-line" aria-hidden="true"></div>
          <div class="steps-row">
            <div class="step" v-for="(step, i) in steps" :key="step.title">
              <div class="step-dot" aria-hidden="true"></div>
              <div class="step-num" aria-hidden="true">0{{ i + 1 }}</div>
              <div class="step-title">{{ step.title }}</div>
              <div class="step-desc">{{ step.desc }}</div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ── Feature bento ──────────────────────────────────────── -->
    <section class="seg seg--surface">
      <div class="seg-inner">
        <p class="eyebrow">What's inside</p>
        <h2 class="seg-title">Built for solar decision-making</h2>
        <div class="bento-grid">
          <div
            class="bento-card"
            v-for="f in features"
            :key="f.title"
          >
            <img :src="f.icon" :alt="f.title" class="bento-icon" />
            <div class="bento-title">{{ f.title }}</div>
            <div class="bento-desc">{{ f.desc }}</div>
          </div>
        </div>
      </div>
    </section>

    <!-- ── CTA ────────────────────────────────────────────────── -->
    <section class="seg seg--dark">
      <div class="seg-inner seg-inner--narrow seg-inner--center">
        <p class="eyebrow eyebrow--orange">Get Started — It's Free</p>
        <h2 class="seg-title seg-title--light">
          Your path to smarter<br>solar decisions starts here
        </h2>

        <!-- User journey -->
        <div class="cta-journey" aria-label="User journey steps">
          <div class="cta-journey-step">
            <div class="cta-journey-num" aria-hidden="true">1</div>
            <div class="cta-journey-label">Search</div>
            <div class="cta-journey-desc">Find any Melbourne CBD building by street address or click it on the 3D map</div>
          </div>
          <div class="cta-journey-arrow" aria-hidden="true">→</div>
          <div class="cta-journey-step">
            <div class="cta-journey-num" aria-hidden="true">2</div>
            <div class="cta-journey-label">Analyse</div>
            <div class="cta-journey-desc">Instantly see solar score, annual energy output, financial payback, and CO₂ savings</div>
          </div>
          <div class="cta-journey-arrow" aria-hidden="true">→</div>
          <div class="cta-journey-step">
            <div class="cta-journey-num" aria-hidden="true">3</div>
            <div class="cta-journey-label">Plan</div>
            <div class="cta-journey-desc">Compare buildings side-by-side and export data to support solar investment decisions</div>
          </div>
        </div>

        <!-- Benefits strip -->
        <div class="cta-benefits" role="list" aria-label="Key benefits">
          <div class="cta-benefit" role="listitem">
            <span class="cta-benefit-check" aria-hidden="true">✓</span> Free &amp; open data
          </div>
          <div class="cta-benefit-divider" aria-hidden="true"></div>
          <div class="cta-benefit" role="listitem">
            <span class="cta-benefit-check" aria-hidden="true">✓</span> 19,000+ buildings analysed
          </div>
          <div class="cta-benefit-divider" aria-hidden="true"></div>
          <div class="cta-benefit" role="listitem">
            <span class="cta-benefit-check" aria-hidden="true">✓</span> No sign-up required
          </div>
        </div>

        <!-- Primary CTA -->
        <div class="cta-actions">
          <button class="btn-cta" @click="goToExplore">Explore the Map →</button>
          <RouterLink class="btn-cta-ghost" to="/precincts">View Precinct</RouterLink>
        </div>
      </div>
    </section>

    </main>

    <!-- ── Footer ─────────────────────────────────────────────── -->
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
              <RouterLink class="footer-link footer-link--url" to="/">Home</RouterLink>
              <RouterLink class="footer-link footer-link--url" to="/explore">3D Explore</RouterLink>
              <RouterLink class="footer-link footer-link--url" to="/precincts">Precincts</RouterLink>
              <RouterLink class="footer-link footer-link--url" to="/insights">AI Insights</RouterLink>
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
// ─────────────────────────────────────────────────────────────────────────────
// HomeView.vue — The public landing page / marketing overview.
//
// This page is purely presentational: it has no interactive map and no API data
// beyond the four summary statistics shown in the hero section.
// Its job is to explain what the platform does and guide visitors into the app.
//
// All the content (feature lists, step descriptions, panel definitions) is stored
// as plain JavaScript arrays below. The template renders them using v-for loops
// so adding or reordering items requires changing only the data, not the HTML.
// ─────────────────────────────────────────────────────────────────────────────

import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'   // useRouter lets us navigate programmatically
import MainNavbar from '../components/MainNavbar.vue'

// All images are imported as module URLs. Vite processes these
// during the build, hashes the filenames, and places them in the /assets folder.
// Importing them like this ensures the correct URL is used in both dev and production.
import logoUrl          from '../pictures/Project logo.png'
import icon3DBuilding   from '../pictures/3D Building Extrusion.png'
import iconSolarScore   from '../pictures/Solar Score Ranking.png'
import iconRoofType     from '../pictures/Roof Type Filtering.png'
import iconEnergy       from '../pictures/Energy Estimates.png'
import iconClickInspect from '../pictures/Click-to-Inspect.png'
import iconComparison   from '../pictures/Comparison View.png'
import iconSolarCell    from '../pictures/solar-cell.png'
import iconProfits      from '../pictures/profits.png'
import iconPlanetEarth  from '../pictures/planet-earth.png'
import img3dExplore     from '../pictures/3D Explore map.png'
import imgPrecinct      from '../pictures/Precincts Map.png'

const router = useRouter()

// API_BASE reads the backend URL from the .env file.
// In development it points to localhost; in production it points to the live server.
const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1'

// ── Hero statistics ───────────────────────────────────────────────────────────
// ref() makes this array reactive — when onMounted replaces the values with live data,
// Vue automatically re-renders the stat cards in the hero section.
// These hard-coded numbers are placeholder fallbacks shown while the fetch is in progress
// (or permanently if the API request fails — graceful degradation, no error shown to users).
const stats = ref([
  { value: '500+',     label: 'Buildings analysed' },
  { value: '169K m²',  label: 'Usable rooftop area' },
  { value: '37.9 GWh', label: 'Est. annual yield' },
  { value: '237',      label: 'High-potential sites' },
])

// ── Feature bullet lists ──────────────────────────────────────────────────────
// These plain arrays feed v-for loops in the template.
// Because they never change, they don't need to be ref() — they're static strings.

// Bullet points listed under the "3D Explore" section.
const exploreFeatures = [
  '3D colour-coded map of 40,000+ Melbourne CBD buildings',
  'Search any building instantly by street address',
  'Filter by roof type, solar score, and height',
  'Click any building to open a full three-panel analysis',
  'Compare up to 4 buildings side by side',
  'Sun path & shadow simulation for any date and time',
]

// Defines the three analysis panel cards shown below the Explore section description.
// Each object has: icon (image URL), title, one-line desc, and a bullet array.
const analysisPanels = [
  {
    icon: iconSolarCell,
    title: 'Solar Potential',
    desc: 'Every rooftop rated 0–100 using City of Melbourne survey data.',
    bullets: ['Solar score & dominant rating', 'Usable vs total roof area', 'Annual & monthly electricity generation'],
  },
  {
    icon: iconProfits,
    title: 'Financial Analysis',
    desc: 'Understand the economics of going solar before committing.',
    bullets: ['Estimated installation cost', 'Annual bill savings', 'Payback period in years'],
  },
  {
    icon: iconPlanetEarth,
    title: 'Environmental Impact',
    desc: 'See the real-world climate benefit each system would deliver.',
    bullets: ['Annual CO₂ reduction', 'Equivalent trees planted', 'Cars taken off the road'],
  },
]

// Bullet points for the Precincts feature section.
const precinctFeatures = [
  'Interactive map showing precinct boundaries coloured by solar tier',
  'Ranked list sortable by annual yield, usable area, buildings, or adoption gap',
  'Installed capacity vs potential capacity for each precinct',
  'Detailed stats: kWh/year, usable m², building count',
  'Export full precinct data as CSV for planning teams',
]

// The three steps shown in the "How it works" timeline.
const steps = [
  {
    title: 'Search',
    desc: 'Type any Melbourne CBD address or click a building directly on the 3D map.',
  },
  {
    title: 'Analyse',
    desc: 'Review solar score, estimated system size, indicative cost, and payback/CO₂ outcome, then compare buildings or export a report.',
  },
  {
    title: 'Plan',
    desc: 'Compare buildings and precincts side by side to prioritise the highest-return installations.',
  },
]

// The six "bento" feature cards in the "What's inside" section.
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

// Programmatic navigation to the Explore page.
// router.push() updates the URL without a full page reload (Vue Router's client-side routing).
function goToExplore() {
  router.push('/explore')
}

// onMounted: runs once after the page has been drawn on screen.
// Fetches real aggregate stats from the backend to replace the placeholder numbers.
// If the fetch fails for any reason (network error, 500 error), the catch block silently
// keeps the hard-coded fallback values — the user never sees an error.
onMounted(async () => {
  try {
    const res = await fetch(`${API_BASE}/buildings/stats`)
    if (!res.ok) return  // server returned an error status — keep fallbacks
    const d = await res.json()

    // Format the usable area: express in K m² if it's >= 1000, otherwise plain m²
    const area = d.usable_area_m2
    const areaFmt = Number.isFinite(area)
      ? (area >= 1000 ? `${Math.round(area / 1000)}K m²` : `${Math.round(area).toLocaleString()} m²`)
      : '—'

    // Express annual kWh as GWh (divide by 1,000,000) with one decimal place
    const kwh = d.kwh_annual
    const yieldFmt = Number.isFinite(kwh) ? `${(kwh / 1_000_000).toFixed(1)} GWh` : '—'

    // Replace all four stat cards with live data
    stats.value = [
      { value: Number.isFinite(d.total_buildings)      ? d.total_buildings.toLocaleString()      : '—', label: 'Buildings analysed' },
      { value: areaFmt,                                                                                   label: 'Usable rooftop area' },
      { value: yieldFmt,                                                                                  label: 'Est. annual yield' },
      { value: Number.isFinite(d.high_potential_count) ? d.high_potential_count.toLocaleString() : '—', label: 'High-potential sites' },
    ]
  } catch { /* keep fallback values — no error displayed */ }
})
</script>

<style scoped>
/* ── Base ─────────────────────────────────────────────────── */
.home-screen {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--surface);
  font-family: 'DM Sans', sans-serif;
  color: var(--text-primary);
  overflow-y: auto;
  overflow-x: hidden;
}

/* ── Hero ─────────────────────────────────────────────────── */
.hero {
  position: relative;
  padding: 110px 72px 100px;
  min-height: 76vh;
  display: flex;
  align-items: center;
  background-image:
    linear-gradient(to right, rgba(var(--black-rgb),0.62) 0%, rgba(var(--black-rgb),0.32) 58%, rgba(var(--black-rgb),0.08) 100%),
    url('../pictures/Home Page Background.jpg');
  background-size: cover;
  background-position: center;
  border-bottom: 3px solid var(--city-light);
}

.hero-inner {
  max-width: 1240px;
  margin: 0 auto;
  width: 100%;
  position: relative;
  z-index: 1;
}

.hero-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 40px;
}

.hero-text {
  flex: 2;
  min-width: 0;
  background: rgba(var(--white-rgb),0.07);
  border: 1px solid rgba(var(--white-rgb),0.16);
  border-radius: 18px;
  padding: 40px 46px;
  backdrop-filter: blur(20px) saturate(1.3);
  -webkit-backdrop-filter: blur(20px) saturate(1.3);
  box-shadow: 0 6px 32px rgba(var(--black-rgb),0.22), inset 0 1px 0 rgba(var(--white-rgb),0.14);
}

.hero-eyebrow {
  font-size: 13px; font-weight: 700;
  text-transform: uppercase; letter-spacing: 1.4px;
  color: var(--city-light); margin-bottom: 16px;
}

.hero-title {
  font-family: 'DM Serif Display', serif;
  font-size: 48px; line-height: 1.12;
  color: var(--white); margin-bottom: 18px;
}

.hero-accent { color: var(--city-light); }

.hero-desc {
  font-size: 15px; line-height: 1.78;
  color: rgba(var(--white-rgb),0.84);
  margin-bottom: 32px;
  max-width: 460px;
}

.hero-actions { display: flex; gap: 12px; flex-wrap: wrap; }

.btn-primary {
  padding: 12px 26px;
  background: var(--city-light); color: var(--white);
  border: none; border-radius: 8px;
  font-family: 'DM Sans', sans-serif; font-size: 14px; font-weight: 600;
  cursor: pointer; transition: background 0.15s;
  text-decoration: none; display: inline-block;
}
.btn-primary:hover { background: var(--city-light-dim); }
.btn-primary:focus-visible { outline: 3px solid var(--city-light); outline-offset: 3px; }

.btn-ghost {
  padding: 12px 22px;
  color: rgba(var(--white-rgb),0.82); text-decoration: none;
  font-size: 14px; font-weight: 500;
  border: 1px solid rgba(var(--white-rgb),0.28); border-radius: 8px;
  transition: background 0.15s, color 0.15s;
  display: inline-block;
}
.btn-ghost:hover { background: rgba(var(--white-rgb),0.10); color: var(--white); }
.btn-ghost:focus-visible { outline: 3px solid var(--city-light); outline-offset: 3px; }

/* Stat grid (hero right) */
.stat-grid {
  flex: 1.4; min-width: 0;
  display: grid; grid-template-columns: 1fr 1fr;
  gap: 14px;
}

.stat-card {
  background: rgba(var(--white-rgb),0.12);
  border: 1px solid rgba(var(--white-rgb),0.24);
  border-radius: 14px;
  padding: 24px 22px;
  backdrop-filter: blur(20px) saturate(1.4);
  -webkit-backdrop-filter: blur(20px) saturate(1.4);
  box-shadow: 0 4px 24px rgba(var(--black-rgb),0.16), inset 0 1px 0 rgba(var(--white-rgb),0.18);
  transition: background 0.2s;
}
.stat-card:hover { background: rgba(var(--white-rgb),0.18); }

.stat-val {
  font-family: 'DM Serif Display', serif;
  font-size: 30px; color: var(--white);
  margin-bottom: 6px;
  text-shadow: 0 1px 8px rgba(var(--black-rgb),0.22);
}

.stat-label {
  font-size: 13px; color: rgba(var(--white-rgb),0.68); line-height: 1.4;
}

/* ── Section system ───────────────────────────────────────── */

/* Every content section shares this base — no borders */
.seg {
  position: relative;
  overflow: hidden;
}

.seg--surface { background: var(--surface); }
.seg--bg      { background: var(--bg); }
.seg--dark    { background: var(--ink); }

.seg-inner {
  max-width: 1240px;
  margin: 0 auto;
  padding: 96px 72px;
}

.seg-inner--narrow {
  max-width: 900px;
}

.seg-inner--center {
  text-align: center;
}

/* ── Shared typography ────────────────────────────────────── */
.eyebrow {
  font-size: 13px; font-weight: 700;
  text-transform: uppercase; letter-spacing: 1.4px;
  color: var(--city-light);
  margin-bottom: 12px;
  display: block;
}

.eyebrow--center { text-align: center; }
.eyebrow--orange { color: var(--city-light); }

.seg-title {
  font-family: 'DM Serif Display', serif;
  font-size: 38px; line-height: 1.15;
  color: var(--text-primary);
  margin-bottom: 20px;
}

.seg-title--center { text-align: center; }
.seg-title--light  { color: var(--nav-text); }

.seg-desc {
  font-size: 15px; line-height: 1.78;
  color: var(--text-secondary);
  margin-bottom: 28px;
}

.seg-desc--light { color: var(--nav-link); }

/* ── Decorative section numbers ───────────────────────────── */
.deco-num {
  position: absolute;
  top: 40px; left: 48px;
  font-family: 'DM Serif Display', serif;
  font-size: 220px; line-height: 1;
  color: var(--text-primary);
  opacity: 0.035;
  pointer-events: none; user-select: none;
  z-index: 0;
}

.deco-num--right {
  left: auto; right: 48px;
}

/* ── Two-column split ─────────────────────────────────────── */
.split {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 72px;
  align-items: center;
  position: relative;
  z-index: 1;
}



.split-text {
  display: flex;
  flex-direction: column;
}

.bullet-list {
  list-style: none; margin: 0 0 28px; padding: 0;
  display: flex; flex-direction: column; gap: 10px;
}

.bullet-list li {
  font-size: 14px; color: var(--text-primary); line-height: 1.55;
  padding-left: 18px; position: relative;
}

.bullet-list li::before {
  content: '→';
  position: absolute; left: 0;
  color: var(--city-light); font-size: 13px; font-weight: 700;
  top: 2px;
}

.text-link {
  display: inline-block;
  font-size: 14px; font-weight: 600;
  color: var(--city-light);
  text-decoration: none;
  border-bottom: 1.5px solid transparent;
  transition: border-color 0.15s, color 0.15s;
  padding-bottom: 1px;
}
.text-link:hover { border-color: var(--city-light); }
.text-link:focus-visible { outline: 2px solid var(--city-light); outline-offset: 3px; border-radius: 2px; }

.split-media {
  display: flex; align-items: center; justify-content: center;
}

.split-img {
  width: 100%;
  border-radius: 16px;
  box-shadow: 0 24px 64px rgba(var(--black-rgb),0.14), 0 4px 16px rgba(var(--black-rgb),0.08);
  object-fit: cover;
}

/* ── Analysis panel trio ──────────────────────────────────── */
.panel-trio {
  margin-top: 80px;
  position: relative; z-index: 1;
}

.panel-trio-label {
  font-size: 14px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  color: var(--text-muted);
  margin-bottom: 24px;
  text-align: center;
}

.panel-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.panel-item {
  background: var(--surface2);
  border-radius: 14px;
  padding: 28px 26px;
  transition: box-shadow 0.2s, transform 0.2s;
}

.panel-item:hover {
  box-shadow: 0 8px 32px rgba(var(--black-rgb),0.09);
  transform: translateY(-2px);
}

.panel-icon {
  width: 40px; height: 40px;
  object-fit: contain; opacity: 0.75;
  margin-bottom: 14px;
}

.panel-title {
  font-family: 'DM Serif Display', serif;
  font-size: 18px; color: var(--text-primary);
  margin-bottom: 8px;
}

.panel-desc {
  font-size: 14px; color: var(--text-secondary);
  line-height: 1.6; margin-bottom: 16px;
}

.panel-bullets {
  list-style: none; padding: 0; margin: 0;
  display: flex; flex-direction: column; gap: 7px;
}

.panel-bullets li {
  font-size: 14px; color: var(--text-muted);
  padding-left: 14px; position: relative; line-height: 1.4;
}
.panel-bullets li::before {
  content: '·';
  position: absolute; left: 0;
  color: var(--city-light); font-weight: 700; font-size: 16px;
  line-height: 1.1;
}

/* ── How it works timeline ────────────────────────────────── */
.steps-wrap {
  position: relative;
  margin-top: 56px;
}

.steps-line {
  position: absolute;
  top: 12px;
  left: 12px; right: 12px;
  height: 1px;
  background: var(--border);
}

.steps-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 40px;
  position: relative;
}

.step {
  position: relative;
}

.step-dot {
  width: 10px; height: 10px;
  border-radius: 50%;
  background: var(--city-light);
  margin-bottom: 28px;
  position: relative;
  z-index: 1;
}

.step-num {
  font-family: 'DM Serif Display', serif;
  font-size: 52px; line-height: 1;
  color: var(--city-light);
  opacity: 0.22;
  margin-bottom: 14px;
  user-select: none;
}

.step-title {
  font-family: 'DM Serif Display', serif;
  font-size: 22px; color: var(--text-primary);
  margin-bottom: 10px;
}

.step-desc {
  font-size: 14px; color: var(--text-secondary);
  line-height: 1.72;
}

/* ── Feature bento ────────────────────────────────────────── */
.bento-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-top: 40px;
}

.bento-card {
  background: var(--surface2);
  border-radius: 16px;
  padding: 28px 26px;
  transition: box-shadow 0.2s, transform 0.2s;
}

.bento-card:hover {
  box-shadow: 0 8px 28px rgba(var(--black-rgb),0.09);
  transform: translateY(-2px);
}

.bento-icon {
  width: 38px; height: 38px;
  object-fit: contain; opacity: 0.75;
  margin-bottom: 14px;
}

.bento-title {
  font-size: 15px; font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 7px;
}

.bento-desc {
  font-size: 14px; color: var(--text-secondary);
  line-height: 1.65;
}

/* ── CTA dark section ─────────────────────────────────────── */
.seg--dark .seg-inner {
  padding-top: 100px;
  padding-bottom: 100px;
}

/* User journey */
.cta-journey {
  display: flex;
  align-items: flex-start;
  justify-content: center;
  gap: 0;
  margin: 48px 0 0;
  flex-wrap: wrap;
}

.cta-journey-step {
  flex: 1;
  min-width: 160px;
  max-width: 220px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 0 12px;
}

.cta-journey-num {
  width: 40px; height: 40px;
  border-radius: 50%;
  background: var(--city-light);
  color: #fff;
  font-family: 'DM Serif Display', serif;
  font-size: 18px;
  display: flex; align-items: center; justify-content: center;
  margin-bottom: 14px;
  flex-shrink: 0;
}

.cta-journey-label {
  font-family: 'DM Serif Display', serif;
  font-size: 18px;
  color: var(--nav-text);
  margin-bottom: 8px;
}

.cta-journey-desc {
  font-size: 14px;
  color: var(--nav-text-muted);
  line-height: 1.6;
}

.cta-journey-arrow {
  font-size: 22px;
  color: var(--city-light);
  opacity: 0.5;
  padding: 0 4px;
  margin-top: 10px;
  flex-shrink: 0;
}

/* Benefits strip */
.cta-benefits {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0;
  margin: 36px 0 0;
  flex-wrap: wrap;
}

.cta-benefit {
  font-size: 14px;
  font-weight: 500;
  color: var(--nav-text-muted);
  padding: 0 20px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.cta-benefit-check {
  color: var(--city-light);
  font-weight: 700;
  font-size: 15px;
}

.cta-benefit-divider {
  width: 1px;
  height: 16px;
  background: var(--ink-border);
  flex-shrink: 0;
}

.cta-actions {
  display: flex; gap: 14px; justify-content: center; flex-wrap: wrap;
  margin-top: 36px;
}

.btn-cta {
  padding: 14px 30px;
  background: var(--city-light); color: var(--white);
  border: none; border-radius: 8px;
  font-family: 'DM Sans', sans-serif; font-size: 15px; font-weight: 600;
  cursor: pointer; transition: background 0.15s;
  text-decoration: none; display: inline-block;
}
.btn-cta:hover { background: var(--city-light-dim); }
.btn-cta:focus-visible { outline: 3px solid var(--city-light); outline-offset: 3px; }

.btn-cta-ghost {
  padding: 14px 26px;
  color: var(--nav-link); text-decoration: none;
  font-size: 15px; font-weight: 500;
  border: 1px solid rgba(var(--white-rgb),0.20); border-radius: 8px;
  transition: background 0.15s, color 0.15s;
  display: inline-block;
}
.btn-cta-ghost:hover { background: rgba(var(--white-rgb),0.07); color: var(--nav-text); border-color: rgba(var(--white-rgb),0.38); }
.btn-cta-ghost:focus-visible { outline: 3px solid var(--city-light); outline-offset: 3px; }

/* ── Footer ───────────────────────────────────────────────── */
.home-footer {
  background: var(--ink);
  color: var(--nav-link);
  font-family: 'DM Sans', sans-serif;
  flex-shrink: 0;
}

.footer-inner {
  display: flex; align-items: flex-start; gap: 56px;
  max-width: 1240px; margin: 0 auto;
  padding: 52px 72px 44px; flex-wrap: wrap;
}

.footer-brand { display: flex; align-items: center; gap: 12px; flex: 0 0 auto; min-width: 180px; }
.footer-logo { width: 40px; height: 40px; object-fit: contain; opacity: 0.9; }
.footer-brand-name { font-family: 'DM Serif Display', serif; font-size: 16px; color: var(--nav-text); line-height: 1.2; }
.footer-brand-sub { font-size: 13px; color: var(--nav-text-muted); margin-top: 2px; }

.footer-links { display: flex; gap: 48px; flex: 1; flex-wrap: wrap; }
.footer-col-group { display: flex; flex-direction: column; gap: 32px; }
.footer-col { display: flex; flex-direction: column; gap: 10px; min-width: 140px; }
.footer-col-title {
  font-size: 13px; font-weight: 700;
  text-transform: uppercase; letter-spacing: 0.8px;
  color: var(--city-light); margin-bottom: 2px;
}
.footer-link { font-size: 14px; color: var(--nav-text-muted); line-height: 1.4; cursor: default; text-decoration: none; }
.footer-link--url { cursor: pointer; transition: color 0.15s; }
.footer-link--url:hover { color: var(--accent-warm); text-decoration: underline; }
.footer-link--url:focus-visible { outline: 2px solid var(--accent-warm); outline-offset: 2px; border-radius: 2px; color: var(--accent-warm); }
.footer-link--eportfolio { display: inline-block; margin-top: 6px; color: var(--city-light); font-weight: 600; font-size: 14px; }
.footer-link--eportfolio:hover { color: var(--city-light-dim); text-decoration: underline; }

/* ── Responsive ───────────────────────────────────────────── */
@media (max-width: 1024px) {
  .seg-inner { padding: 72px 48px; }
  .hero { padding: 80px 48px 120px; }
}

@media (max-width: 900px) {
  .hero { padding: 64px 24px 72px; min-height: unset; }
  .hero-content { flex-direction: column; gap: 32px; }
  .hero-text { padding: 30px 28px; }
  .hero-title { font-size: 36px; }
  .stat-grid { width: 100%; grid-template-columns: 1fr 1fr; }

  .seg-inner { padding: 60px 24px; }
  .deco-num { font-size: 140px; }

  .split { grid-template-columns: 1fr; gap: 40px; }
  .split--rev { direction: ltr; }
  .split--rev > * { direction: ltr; }

  .panel-row { grid-template-columns: 1fr; gap: 14px; }

  .steps-line { display: none; }
  .steps-row { grid-template-columns: 1fr; gap: 28px; }

  .bento-grid { grid-template-columns: 1fr 1fr; }

  .seg-title { font-size: 30px; }
  .footer-inner { padding: 40px 24px 32px; gap: 32px; }
  .footer-links { gap: 28px; }
}

@media (max-width: 600px) {
  .hero-title { font-size: 28px; }
  .stat-grid { grid-template-columns: 1fr 1fr; }
  .bento-grid { grid-template-columns: 1fr; }
  .footer-inner { flex-direction: column; gap: 28px; }
  .footer-links { flex-direction: column; gap: 20px; }
}

/* ≤ 480px: 375px phone — tighten spacing and stack any remaining horizontal flows */
@media (max-width: 480px) {
  .hero { padding: 40px 16px 48px; }
  .hero-text { padding: 22px 18px; }
  .hero-title { font-size: 24px; }
  .hero-desc { font-size: 14px; margin-bottom: 24px; }
  .stat-val { font-size: 24px; }
  .seg-inner { padding: 44px 16px; }
  .seg-title { font-size: 26px; }

  /* CTA journey: stack vertically and centre everything horizontally */
  .cta-journey { flex-direction: column; gap: 16px; align-items: center; }
  .cta-journey-step { min-width: unset; width: 100%; max-width: 280px; text-align: center; }
  .cta-journey-arrow { transform: rotate(90deg); align-self: center; }

  /* Benefits strip: stack vertically and hide dividers */
  .cta-benefits { flex-direction: column; gap: 10px; align-items: center; }
  .cta-benefit-divider { display: none; }
}
</style>
