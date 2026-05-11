<template>
  <div class="map-page">
    <MainNavbar />

    <main id="main-content" class="main ai-main">

      <!-- ── LEFT SIDEBAR ──────────────────────────────────────────────────── -->
      <aside class="sidebar ai-sidebar" aria-label="AI insight controls">
        <div class="sidebar-body">
          <div class="sidebar-header">
            <div class="sidebar-title-row">
              <img :src="iconInsights" class="ai-sidebar-icon" alt="" aria-hidden="true" />
              <div>
                <div class="rankings-label">AI Insights</div>
                <div class="sidebar-title">Solar Intelligence</div>
              </div>
            </div>
            <p class="sidebar-sub">
              Structured reports and plain-language Q&amp;A for any building or precinct.
            </p>
          </div>

          <div class="sidebar-content">

            <!-- View-mode toggle: Chat vs Report -->
            <div class="ai-mode-toggle" role="group" aria-label="Interaction mode">
              <button
                class="ai-mode-btn"
                :class="{ active: viewMode === 'chat' }"
                type="button"
                @click="viewMode = 'chat'"
              >
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
                  <path d="M2 2h10a1 1 0 0 1 1 1v7a1 1 0 0 1-1 1H5l-3 2V3a1 1 0 0 1 1-1z" stroke="currentColor" stroke-width="1.4"/>
                </svg>
                Ask a Question
              </button>
              <button
                class="ai-mode-btn"
                :class="{ active: viewMode === 'report' }"
                type="button"
                @click="viewMode = 'report'"
              >
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
                  <rect x="1" y="1" width="12" height="12" rx="2" stroke="currentColor" stroke-width="1.4"/>
                  <path d="M3 5h8M3 7.5h5M3 10h7" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
                </svg>
                Generate Report
              </button>
            </div>

            <!-- ── REPORT MODE: form controls ── -->
            <template v-if="viewMode === 'report'">
              <div class="ai-tabs" role="group" aria-label="Insight type">
                <button
                  class="ai-tab"
                  :class="{ active: mode === 'building' }"
                  type="button"
                  @click="mode = 'building'"
                >Building</button>
                <button
                  class="ai-tab"
                  :class="{ active: mode === 'precinct' }"
                  type="button"
                  @click="mode = 'precinct'"
                >Precinct</button>
              </div>

              <form class="ai-form" @submit.prevent="generateInsight">

                <!-- Address search (building mode only) -->
                <div v-if="mode === 'building'" class="ai-field addr-field">
                  <span>Search by address</span>
                  <div class="addr-input-wrap">
                    <input
                      v-model="addrQuery"
                      type="text"
                      class="addr-input"
                      placeholder="e.g. 123 Collins St"
                      autocomplete="off"
                      @input="onAddrInput"
                      @keydown="onAddrKeydown"
                      @blur="closeAddrDropdown"
                      aria-label="Search building by address"
                      aria-autocomplete="list"
                      :aria-expanded="addrDropdownOpen"
                    />
                    <span v-if="addrLoading" class="addr-spinner" aria-hidden="true"></span>
                    <button
                      v-if="addrQuery"
                      type="button"
                      class="addr-clear"
                      @mousedown.prevent="clearAddr"
                      aria-label="Clear address"
                    >×</button>
                  </div>
                  <ul
                    v-if="addrDropdownOpen && addrResults.length"
                    class="addr-dropdown"
                    role="listbox"
                  >
                    <li
                      v-for="(r, i) in addrResults"
                      :key="r.structure_id"
                      class="addr-option"
                      :class="{ 'addr-option--focused': i === addrFocusIdx }"
                      role="option"
                      :aria-selected="i === addrFocusIdx"
                      @mousedown.prevent="selectAddr(r)"
                    >
                      <span class="addr-option-text">{{ r.address }}</span>
                      <span class="addr-option-id">ID {{ r.structure_id }}</span>
                    </li>
                  </ul>
                  <p v-if="addrError" class="search-error">{{ addrError }}</p>
                </div>

                <label class="ai-field">
                  <span>{{ mode === 'building' ? 'Building structure ID' : 'Precinct ID or name' }}</span>
                  <input
                    v-model.trim="targetId"
                    type="text"
                    :placeholder="mode === 'building' ? 'Auto-filled from address, or enter manually' : 'Example: Docklands'"
                  />
                </label>

                <label class="ai-field">
                  <span>Insight focus</span>
                  <select v-model="focus">
                    <option value="plain">Plain-language summary</option>
                    <option value="financial">Financial return</option>
                    <option value="suitability">Solar suitability</option>
                    <option value="policy">Policy action</option>
                  </select>
                </label>

                <label class="ai-field">
                  <span>Audience</span>
                  <select v-model="audience">
                    <option value="owner">Property owner</option>
                    <option value="planner">City planner</option>
                    <option value="investor">Solar investor</option>
                    <option value="community">Community stakeholder</option>
                  </select>
                </label>

                <button
                  class="share-btn ai-generate-btn"
                  type="submit"
                  :disabled="isLoading || !targetId"
                >
                  {{ isLoading ? 'Generating...' : primaryButtonLabel }}
                </button>

                <p v-if="errorMessage" class="search-error">{{ errorMessage }}</p>
              </form>
            </template>

            <!-- ── CHAT MODE: input + suggested question chips ── -->
            <template v-else>
              <!-- Sidebar chat input -->
              <div class="sidebar-chat-input-wrap">
                <textarea
                  v-model="chatQuestion"
                  class="sidebar-chat-input"
                  placeholder="e.g. Which precinct has the highest solar potential?"
                  rows="3"
                  :disabled="chatLoading"
                  @keydown.enter.exact.prevent="submitChat"
                  aria-label="Type your solar question"
                ></textarea>
                <button
                  class="sidebar-chat-submit"
                  @click="submitChat"
                  :disabled="chatLoading || !chatQuestion.trim()"
                  aria-label="Submit question"
                >
                  <span v-if="chatLoading" class="chat-submit-spinner" aria-hidden="true"></span>
                  <span v-else>Ask →</span>
                </button>
                <div class="sidebar-chat-hint">
                  <kbd>Enter</kbd> to submit &nbsp;·&nbsp; <kbd>Shift+Enter</kbd> new line
                </div>
              </div>

              <div class="ai-suggestions-label">Suggested questions</div>
              <div class="ai-suggestions-list">
                <button
                  v-for="s in suggestedQuestions"
                  :key="s.text"
                  class="ai-suggestion-chip"
                  type="button"
                  @click="useSuggestion(s.text)"
                  :aria-label="`Ask: ${s.text}`"
                >
                  <span class="ai-suggestion-emoji" aria-hidden="true">{{ s.emoji }}</span>
                  {{ s.text }}
                </button>
              </div>
            </template>

            <!-- Backend status note -->
            <div class="ai-backend-note">
              <div class="section-title">Status</div>
              <div class="assumptions">
                <strong>Demo mode active</strong>
                Using local sample data. Set <code>USE_BACKEND_AI = true</code> when
                the backend AI endpoints are ready.
              </div>
            </div>

          </div><!-- /.sidebar-content -->
        </div><!-- /.sidebar-body -->
      </aside>

      <!-- ── MAIN OUTPUT AREA ──────────────────────────────────────────────── -->
      <section
        class="ai-output-area"
        :class="{ 'ai-output-area--chat': viewMode === 'chat' }"
        aria-live="polite"
        aria-label="AI output"
      >

        <!-- ── REPORT MODE ── -->
        <template v-if="viewMode === 'report'">

          <!-- Loading -->
          <div v-if="isLoading" class="loading">
            <div class="loading-spinner" aria-hidden="true"></div>
            <div class="loading-text">Preparing AI insight from solar data...</div>
          </div>

          <!-- Empty state -->
          <div v-if="!result && !isLoading" class="empty-state ai-empty">
            <div class="empty-icon">AI</div>
            <div class="empty-text">
              Enter a building ID or precinct name, choose your focus and audience,
              then click Generate.
            </div>
          </div>

          <!-- Structured report -->
          <article v-if="result && !isLoading" class="ai-report">

            <div class="ai-report-header">
              <div>
                <div class="panel-id">{{ result.type }}</div>
                <h1>{{ result.title }}</h1>
              </div>
              <button class="sidebar-export-btn" type="button" @click="copyInsight">
                Copy
              </button>
            </div>

            <div class="score-bar-wrap ai-summary">
              <div class="score-header">
                <span class="score-label">Summary</span>
                <span class="score-value">{{ result.priority }}</span>
              </div>
              <p class="score-explanation">{{ result.summary }}</p>
            </div>

            <div class="section-title">Key Metrics</div>
            <div class="metrics-grid ai-metrics">
              <div
                v-for="metric in result.metrics"
                :key="metric.label"
                class="metric-card"
              >
                <div class="metric-val">{{ metric.value }}</div>
                <div class="metric-label">{{ metric.label }}</div>
                <div class="metric-sub">{{ metric.source }}</div>
              </div>
            </div>

            <div class="section-title">Recommendation</div>
            <div class="ai-text-panel">
              <p>{{ result.recommendation }}</p>
            </div>

            <div class="section-title">Reasoning</div>
            <div class="ai-text-panel">
              <p>{{ result.reasoning }}</p>
            </div>

            <div class="section-title">Suggested Next Actions</div>
            <div class="ai-actions">
              <div
                v-for="action in result.actions"
                :key="action"
                class="info-row"
              >
                <span class="info-key">→</span>
                <span class="info-val">{{ action }}</span>
              </div>
            </div>

          </article>
        </template>

        <!-- ── CHAT MODE ── -->
        <template v-else>

          <!-- Empty / welcome state -->
          <div
            v-if="chatHistory.length === 0 && !chatLoading"
            class="empty-state ai-empty ai-chat-welcome"
          >
            <div class="empty-icon">
              <img :src="iconInsights" alt="" style="width:28px;height:28px;object-fit:contain;filter:brightness(2);opacity:0.7;" />
            </div>
            <div class="empty-text">
              Ask a question about any Melbourne CBD building or precinct in plain English.
            </div>
          </div>

          <!-- Q&A history (scrolls independently) -->
          <div
            v-if="chatHistory.length > 0 || chatLoading"
            class="chat-history"
            ref="historyEl"
            aria-live="polite"
            aria-atomic="false"
          >
            <div
              v-for="(item, idx) in chatHistory"
              :key="idx"
              class="chat-pair"
            >
              <!-- User bubble -->
              <div class="chat-q-row">
                <div class="chat-q-avatar" aria-hidden="true">?</div>
                <div class="chat-q-bubble">{{ item.question }}</div>
              </div>

              <!-- AI answer bubble -->
              <div class="chat-a-row" :class="{ 'chat-a-row--error': item.isError }">
                <div class="chat-a-avatar" aria-hidden="true">
                  <img v-if="!item.isError" :src="iconInsights" alt="" class="chat-a-avatar-img" />
                  <span v-else class="chat-a-avatar-err">!</span>
                </div>
                <div class="chat-a-bubble" :class="{ 'chat-a-bubble--error': item.isError }">
                  <p class="chat-a-text">{{ item.answer }}</p>
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
                  <div v-if="item.source" class="chat-a-source">Source: {{ item.source }}</div>
                </div>
              </div>
            </div>

            <!-- Thinking dots -->
            <div v-if="chatLoading" class="chat-thinking" aria-label="AI is thinking">
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

          <!-- Sticky chat input -->
          <div class="chat-input-area">
            <div class="chat-input-wrap">
              <textarea
                v-model="chatQuestion"
                class="chat-input"
                placeholder="e.g. Which precinct has the highest solar potential?"
                rows="2"
                :disabled="chatLoading"
                @keydown.enter.exact.prevent="submitChat"
                aria-label="Type your solar question"
              ></textarea>
              <button
                class="chat-submit-btn"
                @click="submitChat"
                :disabled="chatLoading || !chatQuestion.trim()"
                aria-label="Submit question"
              >
                <span v-if="chatLoading" class="chat-submit-spinner" aria-hidden="true"></span>
                <span v-else>Ask →</span>
              </button>
            </div>
            <div class="chat-input-hint">
              Press <kbd>Enter</kbd> to submit &nbsp;·&nbsp;
              <kbd>Shift + Enter</kbd> for a new line
              <span v-if="chatHistory.length > 0" class="chat-clear-btn-wrap">
                · <button class="chat-clear-btn" @click="clearChat">Clear history</button>
              </span>
            </div>
          </div>

        </template>
      </section>

      <!-- ── RIGHT INFO PANEL ──────────────────────────────────────────────── -->
      <aside class="ai-info-panel" aria-label="AI Insights information">

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
          <div class="info-card-title">Tips for better answers</div>
          <ul class="tips-list">
            <li v-for="tip in tips" :key="tip">{{ tip }}</li>
          </ul>
        </div>

      </aside>

    </main>

    <!-- Copy toast -->
    <div class="toast" role="status" aria-live="polite" :class="{ show: toastVisible }">
      Copied insight
    </div>
  </div>
</template>

<script setup>
import { computed, ref, nextTick } from 'vue'
import MainNavbar from '../components/MainNavbar.vue'
import iconInsights from '../pictures/ai insights.png'

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1'

// Flip to true when POST /api/v1/ai/building-report and /api/v1/ai/precinct-policy exist
const USE_BACKEND_AI = false

// ── Shared ────────────────────────────────────────────────────────────────────
const viewMode   = ref('report')   // 'report' | 'chat'
const toastVisible = ref(false)

// ── Report mode state ─────────────────────────────────────────────────────────
const mode         = ref('building')
const targetId     = ref('')
const focus        = ref('plain')
const audience     = ref('owner')
const result       = ref(null)
const isLoading    = ref(false)
const errorMessage = ref('')

const primaryButtonLabel = computed(() =>
  mode.value === 'building' ? 'Generate Report' : 'Generate Recommendation'
)

// ── Address search (building mode) ────────────────────────────────────────────
const addrQuery       = ref('')
const addrResults     = ref([])
const addrLoading     = ref(false)
const addrDropdownOpen = ref(false)
const addrFocusIdx    = ref(-1)
const addrError       = ref('')
let addrDebounceTimer = null

function onAddrInput() {
  addrFocusIdx.value = -1
  clearTimeout(addrDebounceTimer)
  const q = addrQuery.value.trim()
  if (q.length < 2) { closeAddrDropdown(); return }
  addrDropdownOpen.value = true
  addrLoading.value = true
  addrError.value = ''
  addrDebounceTimer = setTimeout(async () => {
    try {
      const res = await fetch(`${API_BASE}/buildings/search?q=${encodeURIComponent(q)}`)
      addrResults.value = res.ok ? await res.json() : []
    } catch {
      addrResults.value = []
      addrError.value = 'Address lookup failed.'
    } finally {
      addrLoading.value = false
    }
  }, 250)
}

function onAddrKeydown(e) {
  const len = addrResults.value.length
  if (e.key === 'Escape') { closeAddrDropdown(); return }
  if (e.key === 'ArrowDown') {
    e.preventDefault()
    addrFocusIdx.value = len ? (addrFocusIdx.value + 1) % len : -1
    return
  }
  if (e.key === 'ArrowUp') {
    e.preventDefault()
    addrFocusIdx.value = len ? (addrFocusIdx.value - 1 + len) % len : -1
    return
  }
  if (e.key === 'Enter' && len) {
    e.preventDefault()
    selectAddr(addrResults.value[addrFocusIdx.value >= 0 ? addrFocusIdx.value : 0])
  }
}

function selectAddr(r) {
  addrQuery.value = r.address
  targetId.value  = String(r.structure_id)
  closeAddrDropdown()
}

function clearAddr() {
  addrQuery.value = ''
  targetId.value  = ''
  closeAddrDropdown()
}

function closeAddrDropdown() {
  addrResults.value = []
  addrDropdownOpen.value = false
  addrFocusIdx.value = -1
  addrLoading.value = false
}

async function generateInsight() {
  errorMessage.value = ''
  result.value = null
  isLoading.value = true
  const payload = { target_id: targetId.value, focus: focus.value, audience: audience.value }
  try {
    result.value = USE_BACKEND_AI
      ? await callAiInsightApi(mode.value, payload)
      : buildDemoInsight(mode.value, payload)
  } catch (err) {
    errorMessage.value = err.message || 'Unable to generate AI insight.'
  } finally {
    isLoading.value = false
  }
}

async function callAiInsightApi(selectedMode, payload) {
  const endpoint = selectedMode === 'building'
    ? `${API_BASE}/ai/building-report`
    : `${API_BASE}/ai/precinct-policy`
  const res = await fetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) throw new Error(`AI insight API failed with status ${res.status}`)
  return res.json()
}

function buildDemoInsight(selectedMode, payload) {
  if (selectedMode === 'building') {
    return {
      type: 'Building solar report',
      title: `Building ${payload.target_id}`,
      priority: 'High',
      summary: 'This building is ready for a solar feasibility review. The final backend report will combine roof suitability, estimated annual generation, financial return, and comparison with nearby buildings.',
      metrics: [
        { label: 'Suitability',  value: 'High',                    source: 'solar_score' },
        { label: 'ROI Outlook',  value: 'Medium',                  source: 'estimated_payback' },
        { label: 'Output Time',  value: '< 5 sec',                 source: 'AI endpoint' },
        { label: 'Audience',     value: audienceLabel(payload.audience), source: 'user_input' },
      ],
      recommendation: 'Prioritise this building for a detailed solar assessment if its annual generation and usable roof area are above the local median.',
      reasoning: 'The insight translates technical solar metrics into plain language so a property owner can understand whether the building is suitable and why.',
      actions: [
        'Confirm usable roof area from backend solar data.',
        'Compare annual generation with nearby buildings.',
        'Estimate payback period using current cost assumptions.',
      ],
    }
  }
  return {
    type: 'Precinct policy recommendation',
    title: `${payload.target_id}`,
    priority: 'Critical',
    summary: 'This precinct should be reviewed for solar adoption gaps, total potential capacity, and buildings with high suitability but low installed capacity.',
    metrics: [
      { label: 'Adoption Gap',     value: 'High',                    source: 'adoption_gap_kw' },
      { label: 'Policy Priority',  value: 'Critical',                source: 'precinct_rank' },
      { label: 'Output Time',      value: '< 5 sec',                 source: 'AI endpoint' },
      { label: 'Audience',         value: audienceLabel(payload.audience), source: 'user_input' },
    ],
    recommendation: 'Target incentives toward high-potential buildings with low current adoption, then support owners with plain-language return estimates.',
    reasoning: 'The policy recommendation references adoption gap, solar score distribution, installed capacity, and potential capacity across the selected precinct.',
    actions: [
      'Rank buildings by suitability and adoption gap.',
      'Identify incentive candidates in the selected precinct.',
      'Export the recommendation for planning documentation.',
    ],
  }
}

function audienceLabel(value) {
  return { owner: 'Owner', planner: 'Planner', investor: 'Investor', community: 'Community' }[value] || 'User'
}

async function copyInsight() {
  if (!result.value) return
  await navigator.clipboard.writeText(
    [result.value.title, '', result.value.summary, '', result.value.recommendation].join('\n')
  )
  toastVisible.value = true
  window.setTimeout(() => { toastVisible.value = false }, 1800)
}

// ── Chat mode state ───────────────────────────────────────────────────────────
const chatQuestion = ref('')
const chatLoading  = ref(false)
const chatHistory  = ref([])
const historyEl    = ref(null)

// Keyword-matched mock responses grounded in Melbourne CBD solar data
const MOCK_RESPONSES = [
  {
    keywords: ['highest', 'best', 'top', 'most potential', 'greatest'],
    context:  ['precinct', 'neighbourhood', 'suburb', 'area'],
    answer: 'The Docklands precinct currently ranks highest in solar potential across Melbourne CBD, with an average solar score of 4.2/5. Its mix of large flat commercial rooftops and relatively low surrounding shade gives it an estimated annual yield of 18,400 MWh — enough to power approximately 2,545 Victorian households.',
    dataPoints: [
      { label: 'Precinct',             value: 'Docklands' },
      { label: 'Solar score',          value: '4.2 / 5' },
      { label: 'Est. annual yield',    value: '18,400 MWh' },
      { label: 'Households powered',   value: '~2,545' },
    ],
    source: 'City of Melbourne Rooftop Solar Survey 2023',
  },
  {
    keywords: ['collins', 'collins street'],
    context:  [],
    answer: 'Buildings along Collins Street (CBD precinct) have a median solar score of 3.1/5. The predominantly older high-rise stock limits usable roof area, but the 47 surveyed buildings could collectively generate an estimated 6,200 MWh per year. Top performers on the western end score as high as 4.6/5 due to minimal shade obstruction.',
    dataPoints: [
      { label: 'Street',                value: 'Collins Street' },
      { label: 'Median solar score',    value: '3.1 / 5' },
      { label: 'Surveyed buildings',    value: '47' },
      { label: 'Est. collective yield', value: '6,200 MWh / yr' },
      { label: 'Top score (west end)',  value: '4.6 / 5' },
    ],
    source: 'City of Melbourne Building Footprints + Rooftop Project',
  },
  {
    keywords: ['payback', 'return', 'invest', 'cost', 'financial', 'savings', 'pay back'],
    context:  [],
    answer: 'For a typical commercial building in Docklands with 450 m² of usable roof area, the estimated installation cost is $216,000 AUD. At the Melbourne commercial electricity tariff of $0.28/kWh and an annual output of ~108,000 kWh, annual savings reach approximately $30,240. The simple payback period is 7.1 years.',
    dataPoints: [
      { label: 'Usable area',    value: '450 m²' },
      { label: 'Install cost',   value: '$216,000 AUD' },
      { label: 'Annual output',  value: '108,000 kWh' },
      { label: 'Annual savings', value: '$30,240 AUD' },
      { label: 'Payback period', value: '7.1 years' },
    ],
    source: 'Google Solar API + Melbourne commercial tariff (AER 2023)',
  },
  {
    keywords: ['co2', 'carbon', 'emission', 'environment', 'climate', 'tree', 'green'],
    context:  [],
    answer: 'If all surveyed rooftops in Melbourne CBD were fitted with solar panels, the estimated annual CO₂ reduction would be 79,600 tonnes — equivalent to removing 37,900 cars from the road or planting 3.66 million trees. Over the 25-year lifespan of the systems, that totals approximately 1.99 million tonnes of avoided emissions.',
    dataPoints: [
      { label: 'Annual CO₂ reduction', value: '79,600 t CO₂/yr' },
      { label: 'Cars off road equiv.', value: '~37,900 cars' },
      { label: 'Trees equiv.',         value: '3.66 million / yr' },
      { label: '25-yr lifetime',       value: '~1.99 Mt CO₂' },
    ],
    source: 'Clean Energy Regulator 2022 grid factor (0.79 kg CO₂e/kWh)',
  },
  {
    keywords: ['gap', 'adoption', 'installed', 'untapped', 'uptake'],
    context:  [],
    answer: 'The largest adoption gap is in the Hoddle Grid (CBD core) precinct, where only 8% of the technically viable rooftop area currently has solar installed. With 1,240 surveyed buildings and an estimated potential of 42,000 MWh/year, the untapped capacity is 38,640 MWh/year. Southbank and North Melbourne show similar under-utilisation at 11% and 14% adoption respectively.',
    dataPoints: [
      { label: 'Precinct',                  value: 'Hoddle Grid (CBD)' },
      { label: 'Current adoption',          value: '8%' },
      { label: 'Potential yield',           value: '42,000 MWh / yr' },
      { label: 'Untapped yield',            value: '38,640 MWh / yr' },
      { label: 'Runner-up (Southbank)',     value: '11% adoption' },
    ],
    source: 'City of Melbourne Rooftop Project + installed capacity register',
  },
  {
    keywords: ['top 5', 'top five', 'largest roof', 'biggest roof', 'most panels', 'usable area'],
    context:  [],
    answer: 'The five buildings with the largest usable roof area in Melbourne CBD are: (1) Melbourne Convention & Exhibition Centre — 8,420 m², (2) Southern Cross Station — 7,180 m², (3) Footscray Road warehouse — 6,340 m², (4) Docklands office tower #18342 — 4,910 m², and (5) Spencer Street commercial — 4,670 m².',
    dataPoints: [
      { label: '#1 MCEC',                  value: '8,420 m²' },
      { label: '#2 Southern Cross Stn',    value: '7,180 m²' },
      { label: '#3 Footscray Rd warehouse',value: '6,340 m²' },
      { label: '#4 Docklands tower (18342)',value: '4,910 m²' },
      { label: '#5 Spencer St commercial', value: '4,670 m²' },
    ],
    source: 'Google Solar API + City of Melbourne Building Footprints 2023',
  },
]

const FALLBACK_RESPONSE = {
  answer: 'I couldn\'t find a specific match for your question in the current dataset. For best results, try naming a precinct (e.g. "Docklands", "Southbank", "CBD") or a street, or ask about solar score, annual kWh, payback period, or CO₂ savings.',
  dataPoints: [],
  isError: false,
}

function mockDelay() {
  return new Promise(resolve => setTimeout(resolve, 800 + Math.random() * 1000))
}

function getMockResponse(q) {
  const lower = q.toLowerCase()
  for (const r of MOCK_RESPONSES) {
    if (!r.keywords.some(k => lower.includes(k))) continue
    if (r.context.length === 0 || r.context.some(c => lower.includes(c))) {
      return { answer: r.answer, dataPoints: r.dataPoints, source: r.source, isError: false }
    }
    return { answer: r.answer, dataPoints: r.dataPoints, source: r.source, isError: false }
  }
  return FALLBACK_RESPONSE
}

function useSuggestion(text) {
  chatQuestion.value = text
  viewMode.value = 'chat'
  nextTick(() => {
    const input = document.querySelector('.chat-input')
    if (input) input.focus()
  })
}

function clearChat() {
  chatHistory.value = []
}

async function submitChat() {
  const q = chatQuestion.value.trim()
  if (!q || chatLoading.value) return

  chatLoading.value = true
  chatQuestion.value = ''

  await nextTick()
  scrollToBottom()

  await mockDelay()

  chatHistory.value.push({ question: q, ...getMockResponse(q) })

  chatLoading.value = false
  await nextTick()
  scrollToBottom()
}

function scrollToBottom() {
  if (historyEl.value) historyEl.value.scrollTop = historyEl.value.scrollHeight
}

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
</script>

<style scoped>
/* ── Main layout ──────────────────────────────────────────────────────────── */
.ai-main { background: var(--bg); }

.ai-sidebar {
  width: 380px;
  border-left: 0;
  border-right: 1px solid var(--border);
}

.ai-sidebar .sidebar-title-row {
  justify-content: flex-start;
  gap: 12px;
}

.ai-sidebar-icon {
  width: 36px;
  height: 36px;
  object-fit: contain;
  flex-shrink: 0;
}

/* ── View-mode toggle (Report / Chat) ─────────────────────────────────────── */
.ai-mode-toggle {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 5px;
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 4px;
  margin-bottom: 16px;
}

.ai-mode-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: var(--text-secondary);
  font-family: 'DM Sans', sans-serif;
  font-size: 12px;
  font-weight: 600;
  padding: 8px 6px;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
  white-space: nowrap;
}

.ai-mode-btn.active {
  background: var(--ink);
  color: var(--city-light);
}

.ai-mode-btn:hover:not(.active) {
  background: var(--surface3);
  color: var(--text-primary);
}

/* ── Building / Precinct tabs ─────────────────────────────────────────────── */
.ai-tabs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 5px;
  margin-bottom: 16px;
}

.ai-tab {
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: var(--text-secondary);
  font-family: 'DM Sans', sans-serif;
  font-size: 13px;
  font-weight: 700;
  padding: 9px 8px;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}

.ai-tab.active {
  background: var(--ink);
  color: var(--city-light);
}

/* ── Address search field ─────────────────────────────────────────────────── */
.addr-field { position: relative; }

.addr-input-wrap {
  position: relative;
  display: flex;
  align-items: center;
}

.addr-input {
  width: 100%;
  min-height: 40px;
  border: 1px solid var(--border);
  border-radius: 7px;
  background: var(--input-bg);
  color: var(--text-primary);
  font-family: 'DM Sans', sans-serif;
  font-size: 14px;
  padding: 0 32px 0 10px;
  outline: none;
  transition: border-color 0.15s, background 0.15s;
}

.addr-input:focus {
  border-color: var(--city-light);
  background: var(--surface);
}

.addr-spinner {
  position: absolute;
  right: 10px;
  width: 14px;
  height: 14px;
  border: 2px solid var(--border);
  border-top-color: var(--city-light);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  pointer-events: none;
}

.addr-clear {
  position: absolute;
  right: 8px;
  background: none;
  border: none;
  color: var(--text-muted);
  font-size: 16px;
  line-height: 1;
  cursor: pointer;
  padding: 2px 4px;
}
.addr-clear:hover { color: var(--text-primary); }

.addr-dropdown {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.12);
  list-style: none;
  margin: 0;
  padding: 4px 0;
  z-index: 50;
  max-height: 220px;
  overflow-y: auto;
}

.addr-option {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 8px;
  padding: 9px 12px;
  cursor: pointer;
  transition: background 0.1s;
}

.addr-option:hover,
.addr-option--focused { background: var(--surface2); }

.addr-option-text {
  font-size: 13px;
  color: var(--text-primary);
  line-height: 1.4;
  flex: 1;
  min-width: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.addr-option-id {
  font-size: 11px;
  color: var(--text-muted);
  flex-shrink: 0;
}

/* ── Report form ──────────────────────────────────────────────────────────── */
.ai-form {
  display: flex;
  flex-direction: column;
  gap: 13px;
}

.ai-field {
  display: flex;
  flex-direction: column;
  gap: 7px;
}

.ai-field span {
  font-size: 13px;
  font-weight: 700;
  color: var(--text-secondary);
}

.ai-field input,
.ai-field select {
  width: 100%;
  min-height: 40px;
  border: 1px solid var(--border);
  border-radius: 7px;
  background: var(--input-bg);
  color: var(--text-primary);
  font-family: 'DM Sans', sans-serif;
  font-size: 14px;
  padding: 0 10px;
}

.ai-field input:focus,
.ai-field select:focus {
  outline: 3px solid rgba(var(--city-light-rgb), 0.18);
  border-color: var(--city-light);
  background: var(--surface);
}

.ai-generate-btn { margin-top: 4px; }
.ai-generate-btn:disabled { opacity: 0.55; cursor: not-allowed; }

/* ── Sidebar chat input ───────────────────────────────────────────────────── */
.sidebar-chat-input-wrap {
  display: flex;
  flex-direction: column;
  gap: 0;
  margin-bottom: 20px;
}

.sidebar-chat-input {
  resize: none;
  border: 1px solid var(--border);
  border-bottom: none;
  border-radius: 10px 10px 0 0;
  padding: 10px 14px;
  font-family: 'DM Sans', sans-serif;
  font-size: 14px;
  color: var(--text-primary);
  background: var(--input-bg);
  outline: none;
  line-height: 1.5;
  transition: border-color 0.15s, background 0.15s;
}

.sidebar-chat-input:focus {
  border-color: var(--city-light);
  background: var(--surface);
}

.sidebar-chat-input:disabled { opacity: 0.55; cursor: not-allowed; }
.sidebar-chat-input::placeholder { color: var(--text-muted); }

.sidebar-chat-submit {
  width: 100%;
  padding: 10px;
  background: var(--city-light);
  color: #fff;
  border: none;
  border-radius: 0 0 10px 10px;
  font-family: 'DM Sans', sans-serif;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  transition: background 0.15s;
}

.sidebar-chat-submit:hover:not(:disabled) { background: var(--city-light-dim); }
.sidebar-chat-submit:disabled { opacity: 0.45; cursor: not-allowed; }

.sidebar-chat-hint {
  margin-top: 6px;
  font-size: 11px;
  color: var(--text-muted);
}

.sidebar-chat-hint kbd {
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: 3px;
  padding: 1px 4px;
  font-family: 'DM Sans', sans-serif;
  font-size: 10px;
}

/* ── Chat suggestion chips (in sidebar) ───────────────────────────────────── */
.ai-suggestions-label {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.7px;
  color: var(--text-muted);
  margin-bottom: 10px;
}

.ai-suggestions-list {
  display: flex;
  flex-direction: column;
  gap: 7px;
}

.ai-suggestion-chip {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 9px 12px;
  font-family: 'DM Sans', sans-serif;
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
  cursor: pointer;
  text-align: left;
  line-height: 1.45;
  transition: background 0.15s, border-color 0.15s, color 0.15s;
}

.ai-suggestion-chip:hover {
  background: var(--surface);
  border-color: var(--city-light);
  color: var(--text-primary);
}

.ai-suggestion-chip:focus-visible {
  outline: 3px solid var(--city-light);
  outline-offset: 2px;
}

.ai-suggestion-emoji { font-size: 14px; flex-shrink: 0; margin-top: 1px; }

/* ── Backend note ─────────────────────────────────────────────────────────── */
.ai-backend-note { margin-top: 20px; }

/* ── Output area ──────────────────────────────────────────────────────────── */
.ai-output-area {
  flex: 1;
  position: relative;
  overflow-y: auto;
  padding: 24px;
  background: var(--bg);
}

/* Chat mode: flex column so history scrolls and input stays at bottom */
.ai-output-area--chat {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 0;
}

.ai-empty { height: 100%; }

.ai-chat-welcome { flex: 1; }

.ai-empty .empty-icon {
  width: 56px; height: 56px;
  border-radius: 50%;
  background: var(--ink);
  color: var(--city-light);
  display: flex; align-items: center; justify-content: center;
  font-family: 'DM Serif Display', serif;
  opacity: 1;
}

/* ── Structured report ────────────────────────────────────────────────────── */
.ai-report { max-width: 900px; margin: 0 auto; }

.ai-report-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  padding-bottom: 18px;
  margin-bottom: 18px;
  border-bottom: 1px solid var(--border);
}

.ai-report-header h1 {
  font-family: 'DM Serif Display', serif;
  font-size: 32px;
  line-height: 1.15;
  color: var(--text-primary);
}

.ai-summary { margin-bottom: 18px; }
.ai-summary .score-explanation { max-height: none; }

.ai-metrics { grid-template-columns: repeat(4, minmax(0, 1fr)); }

.ai-text-panel,
.ai-actions {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 14px 16px;
  margin-bottom: 16px;
}

.ai-text-panel p {
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.7;
}

.ai-actions .info-row:first-child { padding-top: 0; }
.ai-actions .info-row:last-child  { padding-bottom: 0; }

/* ── Chat Q&A history ─────────────────────────────────────────────────────── */
.chat-history {
  flex: 1;
  overflow-y: auto;
  padding: 24px 28px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.chat-pair { display: flex; flex-direction: column; gap: 12px; }

.chat-q-row {
  display: flex; align-items: flex-start;
  justify-content: flex-end; gap: 10px;
}

.chat-q-avatar {
  width: 28px; height: 28px; border-radius: 50%;
  background: var(--city-light); color: #fff;
  font-size: 14px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0; order: 2;
}

.chat-q-bubble {
  background: var(--ink2); color: var(--nav-text);
  border-radius: 14px 14px 4px 14px;
  padding: 11px 15px; font-size: 14px; line-height: 1.55;
  max-width: 68%;
}

.chat-a-row { display: flex; align-items: flex-start; gap: 10px; }

.chat-a-avatar {
  width: 28px; height: 28px; border-radius: 50%;
  background: var(--surface2); border: 1px solid var(--border);
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}

.chat-a-row--error .chat-a-avatar { background: var(--error-bg); border-color: var(--error-border); }

.chat-a-avatar-img { width: 16px; height: 16px; object-fit: contain; }
.chat-a-avatar-err { color: var(--error); font-weight: 800; font-size: 14px; }

.chat-a-bubble {
  background: var(--surface2); border: 1px solid var(--border);
  border-radius: 4px 14px 14px 14px; padding: 13px 16px;
  max-width: 80%; display: flex; flex-direction: column; gap: 10px;
}

.chat-a-bubble--error { background: var(--error-bg); border-color: var(--error-border); }

.chat-a-text { font-size: 14px; line-height: 1.65; color: var(--text-primary); }
.chat-a-bubble--error .chat-a-text { color: var(--error); }

.chat-data-strip {
  display: flex; flex-wrap: wrap; gap: 7px;
  padding-top: 4px; border-top: 1px solid var(--border);
}

.chat-data-chip {
  display: flex; align-items: center; gap: 5px;
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 20px; padding: 3px 10px 3px 8px; font-size: 12px;
}

.chat-data-chip-label {
  color: var(--text-muted); font-weight: 500;
  text-transform: uppercase; letter-spacing: 0.4px; font-size: 11px;
}

.chat-data-chip-value { color: var(--city-light); font-weight: 700; font-size: 13px; }
.chat-a-source { font-size: 12px; color: var(--text-muted); font-style: italic; }

/* Animated thinking dots */
.chat-thinking { display: flex; align-items: flex-start; gap: 10px; }

.chat-thinking-avatar {
  width: 28px; height: 28px; border-radius: 50%;
  background: var(--surface2); border: 1px solid var(--border);
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}

.chat-thinking-bubble {
  background: var(--surface2); border: 1px solid var(--border);
  border-radius: 4px 14px 14px 14px; padding: 12px 16px;
  display: flex; align-items: center; gap: 10px;
}

.chat-thinking-label { font-size: 13px; color: var(--text-muted); font-style: italic; }

.chat-dots { display: flex; gap: 4px; align-items: center; }

.chat-dots span {
  width: 6px; height: 6px;
  background: var(--city-light); border-radius: 50%;
  animation: dot-bounce 1.2s infinite ease-in-out;
}

.chat-dots span:nth-child(1) { animation-delay: 0s; }
.chat-dots span:nth-child(2) { animation-delay: 0.2s; }
.chat-dots span:nth-child(3) { animation-delay: 0.4s; }

@keyframes dot-bounce {
  0%, 80%, 100% { transform: scale(0.7); opacity: 0.5; }
  40%           { transform: scale(1.0); opacity: 1.0; }
}

/* ── Chat input bar ───────────────────────────────────────────────────────── */
.chat-input-area {
  flex-shrink: 0;
  padding: 14px 24px 18px;
  border-top: 1px solid var(--border);
  background: var(--surface);
}

.chat-input-wrap { display: flex; gap: 10px; align-items: flex-end; }

.chat-input {
  flex: 1; resize: none;
  border: 1px solid var(--border); border-radius: 10px;
  padding: 10px 14px;
  font-family: 'DM Sans', sans-serif; font-size: 14px;
  color: var(--text-primary); background: var(--surface2);
  outline: none; line-height: 1.5;
  transition: border-color 0.15s, background 0.15s;
}

.chat-input:focus { border-color: var(--city-light); background: var(--surface); }
.chat-input:disabled { opacity: 0.55; cursor: not-allowed; }
.chat-input::placeholder { color: var(--text-muted); }

.chat-submit-btn {
  flex-shrink: 0; height: 42px; padding: 0 20px;
  background: var(--city-light); color: #fff;
  border: none; border-radius: 10px;
  font-family: 'DM Sans', sans-serif; font-size: 14px; font-weight: 600;
  cursor: pointer; display: flex; align-items: center; gap: 6px;
  transition: background 0.15s; white-space: nowrap;
}

.chat-submit-btn:hover:not(:disabled) { background: var(--city-light-dim); }
.chat-submit-btn:disabled { opacity: 0.45; cursor: not-allowed; }
.chat-submit-btn:focus-visible { outline: 3px solid var(--city-light); outline-offset: 3px; }

.chat-submit-spinner {
  width: 14px; height: 14px;
  border: 2px solid rgba(255,255,255,0.4);
  border-top-color: #fff; border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

.chat-input-hint { margin-top: 7px; font-size: 12px; color: var(--text-muted); }

.chat-input-hint kbd {
  background: var(--surface2); border: 1px solid var(--border);
  border-radius: 4px; padding: 1px 5px;
  font-family: 'DM Sans', sans-serif; font-size: 11px;
}

.chat-clear-btn-wrap { margin-left: 4px; }

.chat-clear-btn {
  background: none; border: none; color: var(--error);
  font-family: 'DM Sans', sans-serif; font-size: 12px;
  cursor: pointer; padding: 0; transition: color 0.15s;
}

.chat-clear-btn:hover { color: var(--city-light); }

/* ── Right info panel ─────────────────────────────────────────────────────── */
.ai-info-panel {
  width: 280px;
  flex-shrink: 0;
  background: var(--bg);
  border-left: 1px solid var(--border);
  overflow-y: auto;
  padding: 20px;
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

.info-card--muted { background: var(--surface2); }

.info-card-title {
  font-size: 11px; font-weight: 700;
  text-transform: uppercase; letter-spacing: 0.7px;
  color: var(--city-light); margin-bottom: 12px;
}

.info-cap-list {
  list-style: none; padding: 0; margin: 0;
  display: flex; flex-direction: column; gap: 11px;
}

.info-cap-item { display: flex; align-items: flex-start; gap: 8px; }

.info-cap-arrow {
  color: var(--city-light); font-size: 12px; font-weight: 700;
  flex-shrink: 0; margin-top: 2px;
}

.info-cap-label {
  font-size: 13px; font-weight: 600;
  color: var(--text-primary); line-height: 1.3; margin-bottom: 2px;
}

.info-cap-desc { font-size: 12px; color: var(--text-secondary); line-height: 1.4; }

.info-card-body { font-size: 13px; color: var(--text-secondary); line-height: 1.6; }
.info-card-body strong { color: var(--text-primary); font-weight: 600; }

.tips-list {
  list-style: none; padding: 0; margin: 0;
  display: flex; flex-direction: column; gap: 8px;
}

.tips-list li {
  font-size: 13px; color: var(--text-secondary);
  line-height: 1.5; padding-left: 14px; position: relative;
}

.tips-list li::before {
  content: '·'; position: absolute; left: 0;
  color: var(--city-light); font-size: 16px;
  font-weight: 700; line-height: 1.1;
}

/* ── Responsive ───────────────────────────────────────────────────────────── */
@media (max-width: 1200px) {
  .ai-sidebar { width: 340px; }
  .ai-metrics { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}

@media (max-width: 960px) {
  /* Hide right info panel — move its content to sidebar */
  .ai-info-panel { display: none; }
}

@media (max-width: 820px) {
  .ai-main { flex-direction: column; overflow-y: auto; }

  .ai-sidebar {
    width: 100%;
    border-right: 0;
    border-bottom: 1px solid var(--border);
  }

  .ai-output-area { min-height: 480px; }
  .ai-output-area--chat { min-height: 480px; }

  .ai-report-header { flex-direction: column; }
  .ai-metrics { grid-template-columns: 1fr 1fr; }
}

@media (max-width: 520px) {
  .ai-metrics { grid-template-columns: 1fr; }
  .chat-history,
  .chat-input-area { padding-left: 14px; padding-right: 14px; }
  .chat-input-hint { display: none; }
  .chat-submit-btn { padding: 0 14px; }
}
</style>
