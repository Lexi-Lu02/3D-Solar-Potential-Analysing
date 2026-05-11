<template>
  <div class="insights-page">
    <MainNavbar />

    <main class="insights-shell" id="main-content">

      <!-- ── Page header ── -->
      <div class="insights-hero">
        <div class="insights-hero-inner">
          <div class="insights-hero-icon" aria-hidden="true">
            <img :src="iconInsights" alt="" />
          </div>
          <div class="insights-hero-text">
            <h1 class="insights-hero-title">AI Solar Insights</h1>
            <p class="insights-hero-sub">
              Ask any question about Melbourne CBD buildings or precincts in plain English —
              answers are grounded in live solar, financial, and environmental data.
            </p>
          </div>
        </div>
      </div>

      <!-- ── Two-column body ── -->
      <div class="insights-body">

        <!-- LEFT: chat panel -->
        <section class="insights-chat" aria-label="AI question and answer">

          <!-- Welcome / suggested questions (shown until the first question is asked) -->
          <div v-if="history.length === 0 && !loading" class="suggestions-wrap">
            <div class="suggestions-heading">Suggested questions</div>
            <div class="suggestions-grid">
              <button
                v-for="s in suggestedQuestions"
                :key="s.text"
                class="suggestion-chip"
                @click="useSuggestion(s.text)"
                :aria-label="`Ask: ${s.text}`"
              >
                <span class="suggestion-emoji" aria-hidden="true">{{ s.emoji }}</span>
                {{ s.text }}
              </button>
            </div>
          </div>

          <!-- Q&A history -->
          <div
            v-if="history.length > 0 || loading"
            class="chat-history"
            ref="historyEl"
            aria-live="polite"
            aria-atomic="false"
          >
            <div
              v-for="(item, idx) in history"
              :key="idx"
              class="chat-pair"
            >
              <!-- User question bubble -->
              <div class="chat-q-row">
                <div class="chat-q-avatar" aria-hidden="true">?</div>
                <div class="chat-q-bubble">{{ item.question }}</div>
              </div>

              <!-- AI answer bubble -->
              <div
                class="chat-a-row"
                :class="{ 'chat-a-row--error': item.isError }"
              >
                <div class="chat-a-avatar" aria-hidden="true">
                  <img v-if="!item.isError" :src="iconInsights" alt="" class="chat-a-avatar-img" />
                  <span v-else class="chat-a-avatar-err">!</span>
                </div>
                <div class="chat-a-bubble" :class="{ 'chat-a-bubble--error': item.isError }">
                  <!-- Plain-language answer text -->
                  <p class="chat-a-text">{{ item.answer }}</p>

                  <!-- Highlighted data points (solar score, kWh, adoption gap, etc.) -->
                  <div v-if="item.dataPoints && item.dataPoints.length" class="chat-data-strip">
                    <div
                      v-for="dp in item.dataPoints"
                      :key="dp.label"
                      class="chat-data-chip"
                    >
                      <span class="chat-data-chip-label">{{ dp.label }}</span>
                      <span class="chat-data-chip-value">{{ dp.value }}</span>
                    </div>
                  </div>

                  <!-- Source citation (optional) -->
                  <div v-if="item.source" class="chat-a-source">
                    Source: {{ item.source }}
                  </div>
                </div>
              </div>
            </div>

            <!-- Animated loading indicator while waiting for the API -->
            <div v-if="loading" class="chat-thinking" aria-label="AI is thinking">
              <div class="chat-thinking-avatar" aria-hidden="true">
                <img :src="iconInsights" alt="" class="chat-a-avatar-img" />
              </div>
              <div class="chat-thinking-bubble">
                <span class="chat-thinking-label">Analysing solar data</span>
                <span class="chat-dots" aria-hidden="true">
                  <span></span><span></span><span></span>
                </span>
              </div>
            </div>
          </div>

          <!-- ── Input area (always visible at the bottom) ── -->
          <div class="chat-input-area">
            <div class="chat-input-wrap">
              <textarea
                v-model="question"
                class="chat-input"
                placeholder="e.g. Which precinct has the highest solar potential?"
                rows="2"
                :disabled="loading"
                @keydown.enter.exact.prevent="submitQuestion"
                aria-label="Type your solar question"
                aria-describedby="input-hint"
              ></textarea>

              <button
                class="chat-submit-btn"
                @click="submitQuestion"
                :disabled="loading || !question.trim()"
                aria-label="Submit question"
              >
                <span v-if="loading" class="chat-submit-spinner" aria-hidden="true"></span>
                <span v-else>Ask →</span>
              </button>
            </div>
            <div class="chat-input-hint" id="input-hint">
              Press <kbd>Enter</kbd> to submit &nbsp;·&nbsp; <kbd>Shift + Enter</kbd> for a new line
              <span v-if="history.length > 0" class="chat-clear-btn-wrap">
                · <button class="chat-clear-btn" @click="clearHistory">Clear history</button>
              </span>
            </div>
          </div>

        </section>

        <!-- RIGHT: info sidebar -->
        <aside class="insights-sidebar" aria-label="AI Insights information">

          <div class="info-card">
            <div class="info-card-title">What can I ask?</div>
            <ul class="info-cap-list">
              <li v-for="cap in capabilities" :key="cap.label" class="info-cap-item">
                <span class="info-cap-arrow" aria-hidden="true">→</span>
                <div>
                  <div class="info-cap-label">{{ cap.label }}</div>
                  <div class="info-cap-desc">{{ cap.desc }}</div>
                </div>
              </li>
            </ul>
          </div>

          <div class="info-card info-card--muted">
            <div class="info-card-title">Data coverage</div>
            <p class="info-card-body">
              Answers draw on <strong>40,000+ Melbourne CBD buildings</strong>, City of
              Melbourne rooftop solar survey data, Google Solar API metrics, and
              NASA POWER irradiance values.
            </p>
          </div>

          <div class="info-card info-card--muted">
            <div class="info-card-title">Tips for better answers</div>
            <ul class="tips-list">
              <li v-for="tip in tips" :key="tip">{{ tip }}</li>
            </ul>
          </div>

        </aside>
      </div>

    </main>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import MainNavbar from '../components/MainNavbar.vue'
import iconInsights from '../pictures/ai insights.png'

// API_BASE is kept for when the backend is ready — currently using mock responses.
const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1'

// ── Mock response engine ──────────────────────────────────────────────────────
// Simulates AI answers grounded in plausible Melbourne CBD solar data.
// Swap this out for a real fetch() when the /insights/ask endpoint is available.

const MOCK_RESPONSES = [
  {
    keywords: ['highest', 'best', 'top', 'most potential', 'greatest'],
    context: ['precinct', 'neighbourhood', 'suburb', 'area'],
    answer: 'The Docklands precinct currently ranks highest in solar potential across Melbourne CBD, with an average solar score of 4.2/5. Its mix of large flat commercial rooftops and relatively low surrounding shade gives it an estimated annual yield of 18,400 MWh — enough to power approximately 2,545 Victorian households.',
    dataPoints: [
      { label: 'Precinct', value: 'Docklands' },
      { label: 'Solar score', value: '4.2 / 5' },
      { label: 'Est. annual yield', value: '18,400 MWh' },
      { label: 'Households powered', value: '~2,545' },
    ],
    source: 'City of Melbourne Rooftop Solar Survey 2023',
  },
  {
    keywords: ['collins', 'collins street'],
    context: [],
    answer: 'Buildings along Collins Street (CBD precinct) have a median solar score of 3.1/5. The predominantly older high-rise stock limits usable roof area, but the 47 surveyed buildings could collectively generate an estimated 6,200 MWh per year. Top performers on the western end score as high as 4.6/5 due to minimal shade obstruction.',
    dataPoints: [
      { label: 'Street', value: 'Collins Street' },
      { label: 'Median solar score', value: '3.1 / 5' },
      { label: 'Surveyed buildings', value: '47' },
      { label: 'Est. collective yield', value: '6,200 MWh / yr' },
      { label: 'Top score (west end)', value: '4.6 / 5' },
    ],
    source: 'City of Melbourne Building Footprints + Rooftop Project',
  },
  {
    keywords: ['payback', 'return', 'invest', 'cost', 'financial', 'savings', 'pay back'],
    context: ['docklands', 'cbd', 'melbourne'],
    answer: 'For a typical commercial building in Docklands with 450 m² of usable roof area, the estimated installation cost is $216,000 AUD (based on $1.20/W × 400W panels). At the Melbourne commercial electricity tariff of $0.28/kWh and an annual output of ~108,000 kWh, annual savings reach approximately $30,240. The simple payback period is 7.1 years.',
    dataPoints: [
      { label: 'Usable area', value: '450 m²' },
      { label: 'Install cost', value: '$216,000 AUD' },
      { label: 'Annual output', value: '108,000 kWh' },
      { label: 'Annual savings', value: '$30,240 AUD' },
      { label: 'Payback period', value: '7.1 years' },
    ],
    source: 'Google Solar API + Melbourne commercial tariff (AER 2023)',
  },
  {
    keywords: ['co2', 'carbon', 'emission', 'environment', 'climate', 'tree', 'green'],
    context: [],
    answer: 'If all surveyed rooftops in Melbourne CBD were fitted with solar panels, the estimated annual CO₂ reduction would be 79,600 tonnes — equivalent to removing 37,900 cars from the road or planting 3.66 million trees. Over the 25-year lifespan of the systems, that totals approximately 1.99 million tonnes of avoided emissions.',
    dataPoints: [
      { label: 'Annual CO₂ reduction', value: '79,600 t CO₂/yr' },
      { label: 'Cars off road equiv.', value: '~37,900 cars' },
      { label: 'Trees equiv.', value: '3.66 million / yr' },
      { label: '25-yr lifetime savings', value: '~1.99 Mt CO₂' },
    ],
    source: 'Clean Energy Regulator 2022 grid factor (0.79 kg CO₂e/kWh)',
  },
  {
    keywords: ['gap', 'adoption', 'installed', 'potential', 'uptake', 'untapped'],
    context: ['precinct'],
    answer: 'The largest adoption gap is in the Hoddle Grid (CBD core) precinct, where only 8% of the technically viable rooftop area currently has solar installed. With 1,240 surveyed buildings and an estimated potential of 42,000 MWh/year, the untapped capacity is 38,640 MWh/year. Southbank and North Melbourne precincts show similar under-utilisation at 11% and 14% adoption respectively.',
    dataPoints: [
      { label: 'Precinct', value: 'Hoddle Grid (CBD)' },
      { label: 'Current adoption', value: '8%' },
      { label: 'Potential yield', value: '42,000 MWh / yr' },
      { label: 'Untapped yield', value: '38,640 MWh / yr' },
      { label: 'Runner-up (Southbank)', value: '11% adoption' },
    ],
    source: 'City of Melbourne Rooftop Project + installed capacity register',
  },
  {
    keywords: ['top 5', 'top five', 'largest roof', 'biggest roof', 'most panels', 'usable area'],
    context: [],
    answer: 'The five buildings with the largest usable roof area for solar installation in Melbourne CBD are: (1) Melbourne Convention & Exhibition Centre — 8,420 m², (2) Southern Cross Station — 7,180 m², (3) a warehouse complex on Footscray Road — 6,340 m², (4) a Docklands office tower (structure ID 18342) — 4,910 m², and (5) a Spencer Street commercial building — 4,670 m².',
    dataPoints: [
      { label: '#1 MCEC', value: '8,420 m²' },
      { label: '#2 Southern Cross Stn', value: '7,180 m²' },
      { label: '#3 Footscray Rd warehouse', value: '6,340 m²' },
      { label: '#4 Docklands tower (18342)', value: '4,910 m²' },
      { label: '#5 Spencer St commercial', value: '4,670 m²' },
    ],
    source: 'Google Solar API + City of Melbourne Building Footprints 2023',
  },
]

const FALLBACK_RESPONSE = {
  answer: 'I couldn\'t find a specific match for your question in the current dataset. For best results, try naming a precinct (e.g. "Docklands", "Southbank", "CBD") or a street, or ask about a specific metric like solar score, annual kWh, payback period, or CO₂ savings.',
  dataPoints: [],
  isError: false,
}

// Simulates a network round-trip delay (800 ms – 1.8 s) so the loading state is visible
function mockDelay() {
  return new Promise(resolve => setTimeout(resolve, 800 + Math.random() * 1000))
}

// Finds the best matching mock response for a given question string
function getMockResponse(q) {
  const lower = q.toLowerCase()
  for (const r of MOCK_RESPONSES) {
    const keywordHit = r.keywords.some(k => lower.includes(k))
    if (!keywordHit) continue
    // If the response has context constraints, at least one must also match
    if (r.context.length === 0 || r.context.some(c => lower.includes(c))) {
      return { answer: r.answer, dataPoints: r.dataPoints, source: r.source, isError: false }
    }
    // Keyword hit but no context match — still use it (context is optional guidance)
    return { answer: r.answer, dataPoints: r.dataPoints, source: r.source, isError: false }
  }
  return FALLBACK_RESPONSE
}

// ── Reactive state ────────────────────────────────────────────────────────────

// The text currently typed in the input box
const question = ref('')

// true while waiting for the API response (disables input, shows spinner)
const loading = ref(false)

// Array of { question, answer, dataPoints, source, isError } objects
const history = ref([])

// Template ref to the scrollable Q&A history div (used to scroll to bottom after each answer)
const historyEl = ref(null)

// ── Static content ────────────────────────────────────────────────────────────

const suggestedQuestions = [
  { emoji: '🏆', text: 'Which precinct has the highest solar potential in Melbourne CBD?' },
  { emoji: '⚡', text: 'How much energy could buildings on Collins Street generate annually?' },
  { emoji: '💰', text: 'What is the estimated payback period for solar in Docklands?' },
  { emoji: '🌿', text: 'How much CO₂ could the CBD avoid if all rooftops had solar?' },
  { emoji: '📊', text: 'Which precincts have the biggest gap between installed and potential solar?' },
  { emoji: '🔍', text: 'What are the top 5 buildings by usable roof area for solar installation?' },
]

const capabilities = [
  { label: 'Precinct comparisons', desc: 'Solar potential, kWh output, adoption gap across all CBD precincts' },
  { label: 'Building analysis',    desc: 'Solar score, usable roof area, financial payback for any address' },
  { label: 'Energy estimates',     desc: 'Annual generation, peak sun hours, panel capacity calculations' },
  { label: 'Environmental impact', desc: 'CO₂ savings, equivalent trees, homes powered' },
  { label: 'Financial metrics',    desc: 'Installation cost, annual savings, payback period' },
]

const tips = [
  'Name a specific precinct or street for grounded answers',
  'Ask about a single metric at a time for clearer responses',
  'Include "compare" when you want side-by-side analysis',
  'Use "top" or "highest" to get ranked results',
]

// ── Actions ───────────────────────────────────────────────────────────────────

// Pre-fills the input with a suggested question and focuses the textarea
function useSuggestion(text) {
  question.value = text
  // Focus the input so the user can immediately edit or submit
  nextTick(() => {
    const input = document.querySelector('.chat-input')
    if (input) input.focus()
  })
}

// Clears all Q&A history (resets to the welcome / suggestions state)
function clearHistory() {
  history.value = []
}

// Submits the current question and resolves it through the mock response engine.
// When the backend is ready, replace mockDelay() + getMockResponse() with a real fetch().
async function submitQuestion() {
  const q = question.value.trim()
  if (!q || loading.value) return

  loading.value = true
  question.value = ''

  // Scroll to show the loading indicator as soon as it appears
  await nextTick()
  scrollToBottom()

  // Simulate network round-trip so the loading state is visible
  await mockDelay()

  const result = getMockResponse(q)
  history.value.push({ question: q, ...result })

  loading.value = false
  await nextTick()
  scrollToBottom()
}

// Scrolls the Q&A history container to the bottom so the latest answer is visible
function scrollToBottom() {
  if (historyEl.value) {
    historyEl.value.scrollTop = historyEl.value.scrollHeight
  }
}
</script>

<style scoped>
/* ── Page shell ───────────────────────────────────────────────────────────── */
.insights-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: var(--bg);
  font-family: 'DM Sans', sans-serif;
  color: var(--text-primary);
  overflow: hidden;
}

.insights-shell {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* ── Hero header ──────────────────────────────────────────────────────────── */
.insights-hero {
  background: var(--ink);
  border-bottom: 2px solid var(--city-light);
  padding: 18px 32px;
  flex-shrink: 0;
}

.insights-hero-inner {
  max-width: 1280px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  gap: 16px;
}

.insights-hero-icon img {
  width: 36px;
  height: 36px;
  object-fit: contain;
  filter: brightness(1.4);
  opacity: 0.9;
}

.insights-hero-title {
  font-family: 'DM Serif Display', serif;
  font-size: 22px;
  color: var(--nav-text);
  line-height: 1.2;
  margin-bottom: 3px;
}

.insights-hero-sub {
  font-size: 13px;
  color: var(--nav-text-muted);
  line-height: 1.5;
  max-width: 620px;
}

/* ── Two-column body ──────────────────────────────────────────────────────── */
.insights-body {
  flex: 1;
  display: flex;
  overflow: hidden;
  max-width: 1280px;
  width: 100%;
  margin: 0 auto;
  padding: 0;
  /* Allow full-width up to 1280px */
  align-self: stretch;
}

/* ── Chat panel (left) ────────────────────────────────────────────────────── */
.insights-chat {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border-right: 1px solid var(--border);
  background: var(--surface);
}

/* ── Suggestions ─────────────────────────────────────────────────────────── */
.suggestions-wrap {
  padding: 28px 28px 0;
}

.suggestions-heading {
  font-size: 13px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.7px;
  color: var(--text-muted);
  margin-bottom: 14px;
}

.suggestions-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.suggestion-chip {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 12px 14px;
  font-family: 'DM Sans', sans-serif;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  cursor: pointer;
  text-align: left;
  line-height: 1.45;
  transition: background 0.15s, border-color 0.15s, color 0.15s;
}

.suggestion-chip:hover {
  background: var(--surface);
  border-color: var(--city-light);
  color: var(--text-primary);
}

.suggestion-chip:focus-visible {
  outline: 3px solid var(--city-light);
  outline-offset: 2px;
}

.suggestion-emoji {
  font-size: 16px;
  flex-shrink: 0;
  margin-top: 1px;
}

/* ── Q&A history (scrollable) ─────────────────────────────────────────────── */
.chat-history {
  flex: 1;
  overflow-y: auto;
  padding: 24px 28px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.chat-pair {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* User question row */
.chat-q-row {
  display: flex;
  align-items: flex-start;
  justify-content: flex-end;
  gap: 10px;
}

.chat-q-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--city-light);
  color: #fff;
  font-size: 14px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  order: 2;
}

.chat-q-bubble {
  background: var(--ink2);
  color: var(--nav-text);
  border-radius: 14px 14px 4px 14px;
  padding: 11px 15px;
  font-size: 14px;
  line-height: 1.55;
  max-width: 68%;
}

/* AI answer row */
.chat-a-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.chat-a-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--surface2);
  border: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.chat-a-row--error .chat-a-avatar {
  background: var(--error-bg);
  border-color: var(--error-border);
}

.chat-a-avatar-img {
  width: 16px;
  height: 16px;
  object-fit: contain;
}

.chat-a-avatar-err {
  color: var(--error);
  font-weight: 800;
  font-size: 14px;
}

.chat-a-bubble {
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: 4px 14px 14px 14px;
  padding: 13px 16px;
  max-width: 80%;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.chat-a-bubble--error {
  background: var(--error-bg);
  border-color: var(--error-border);
}

.chat-a-text {
  font-size: 14px;
  line-height: 1.65;
  color: var(--text-primary);
}

.chat-a-bubble--error .chat-a-text {
  color: var(--error);
}

/* Highlighted data value chips inside answers */
.chat-data-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
  padding-top: 4px;
  border-top: 1px solid var(--border);
}

.chat-data-chip {
  display: flex;
  align-items: center;
  gap: 5px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 3px 10px 3px 8px;
  font-size: 12px;
}

.chat-data-chip-label {
  color: var(--text-muted);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.4px;
  font-size: 11px;
}

.chat-data-chip-value {
  color: var(--city-light);
  font-weight: 700;
  font-size: 13px;
}

.chat-a-source {
  font-size: 12px;
  color: var(--text-muted);
  font-style: italic;
}

/* ── Thinking / loading bubble ────────────────────────────────────────────── */
.chat-thinking {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.chat-thinking-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--surface2);
  border: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.chat-thinking-bubble {
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: 4px 14px 14px 14px;
  padding: 12px 16px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.chat-thinking-label {
  font-size: 13px;
  color: var(--text-muted);
  font-style: italic;
}

/* Three animated dots */
.chat-dots {
  display: flex;
  gap: 4px;
  align-items: center;
}

.chat-dots span {
  width: 6px;
  height: 6px;
  background: var(--city-light);
  border-radius: 50%;
  animation: dot-bounce 1.2s infinite ease-in-out;
}

.chat-dots span:nth-child(1) { animation-delay: 0s; }
.chat-dots span:nth-child(2) { animation-delay: 0.2s; }
.chat-dots span:nth-child(3) { animation-delay: 0.4s; }

@keyframes dot-bounce {
  0%, 80%, 100% { transform: scale(0.7); opacity: 0.5; }
  40%           { transform: scale(1.0); opacity: 1.0; }
}

/* ── Input area ───────────────────────────────────────────────────────────── */
.chat-input-area {
  flex-shrink: 0;
  padding: 16px 28px 20px;
  border-top: 1px solid var(--border);
  background: var(--surface);
}

.chat-input-wrap {
  display: flex;
  gap: 10px;
  align-items: flex-end;
}

.chat-input {
  flex: 1;
  resize: none;
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 10px 14px;
  font-family: 'DM Sans', sans-serif;
  font-size: 14px;
  color: var(--text-primary);
  background: var(--surface2);
  outline: none;
  line-height: 1.5;
  transition: border-color 0.15s, background 0.15s;
}

.chat-input:focus {
  border-color: var(--city-light);
  background: var(--surface);
}

.chat-input:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.chat-input::placeholder {
  color: var(--text-muted);
}

.chat-submit-btn {
  flex-shrink: 0;
  height: 42px;
  padding: 0 20px;
  background: var(--city-light);
  color: #fff;
  border: none;
  border-radius: 10px;
  font-family: 'DM Sans', sans-serif;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: background 0.15s;
  white-space: nowrap;
}

.chat-submit-btn:hover:not(:disabled) {
  background: var(--city-light-dim);
}

.chat-submit-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.chat-submit-btn:focus-visible {
  outline: 3px solid var(--city-light);
  outline-offset: 3px;
}

/* Spinner inside the button while loading */
.chat-submit-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255,255,255,0.4);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

.chat-input-hint {
  margin-top: 7px;
  font-size: 12px;
  color: var(--text-muted);
}

.chat-input-hint kbd {
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 1px 5px;
  font-family: 'DM Sans', sans-serif;
  font-size: 11px;
}

.chat-clear-btn-wrap { margin-left: 4px; }

.chat-clear-btn {
  background: none;
  border: none;
  color: var(--error);
  font-family: 'DM Sans', sans-serif;
  font-size: 12px;
  cursor: pointer;
  padding: 0;
  transition: color 0.15s;
}

.chat-clear-btn:hover { color: var(--city-light); }

/* ── Right sidebar ────────────────────────────────────────────────────────── */
.insights-sidebar {
  width: 300px;
  flex-shrink: 0;
  background: var(--bg);
  overflow-y: auto;
  padding: 20px 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.info-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 16px 18px;
}

.info-card--muted {
  background: var(--surface2);
}

.info-card-title {
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.7px;
  color: var(--city-light);
  margin-bottom: 12px;
}

.info-cap-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 11px;
}

.info-cap-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.info-cap-arrow {
  color: var(--city-light);
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;
  margin-top: 2px;
}

.info-cap-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.3;
  margin-bottom: 2px;
}

.info-cap-desc {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.4;
}

.info-card-body {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
}

.info-card-body strong {
  color: var(--text-primary);
  font-weight: 600;
}

.tips-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.tips-list li {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.5;
  padding-left: 14px;
  position: relative;
}

.tips-list li::before {
  content: '·';
  position: absolute;
  left: 0;
  color: var(--city-light);
  font-size: 16px;
  font-weight: 700;
  line-height: 1.1;
}

/* ── Responsive ───────────────────────────────────────────────────────────── */
@media (max-width: 960px) {
  .insights-sidebar {
    display: none;
  }

  .insights-chat {
    border-right: none;
  }

  .suggestions-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 600px) {
  .insights-hero { padding: 14px 16px; }
  .suggestions-wrap,
  .chat-history,
  .chat-input-area { padding-left: 16px; padding-right: 16px; }
  .chat-q-bubble { max-width: 85%; }
  .chat-a-bubble { max-width: 92%; }
}

/* ≤ 480px: 375px phone — tighten further, ensure input row fits */
@media (max-width: 480px) {
  .suggestions-wrap,
  .chat-history,
  .chat-input-area { padding-left: 12px; padding-right: 12px; }

  /* Compress the input area so it doesn't crowd the chat history */
  .chat-input-area { padding-top: 12px; padding-bottom: 14px; }

  /* Hide the keyboard shortcut hint — not relevant on touchscreens */
  .chat-input-hint { display: none; }

  /* Submit button: shrink label text to save horizontal space */
  .chat-submit-btn { padding: 0 14px; font-size: 13px; }

  /* Hero: smaller title on very narrow screens */
  .insights-hero-title { font-size: 20px; }
  .insights-hero-sub { font-size: 13px; }
}
</style>
