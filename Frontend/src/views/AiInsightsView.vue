<template>
  <div class="map-page">
    <MainNavbar />

    <main id="main-content" class="main ai-main">
      <aside class="sidebar ai-sidebar" aria-label="AI insight controls">
        <div class="sidebar-body">
          <div class="sidebar-header">
            <div class="sidebar-title-row">
              <div>
                <div class="rankings-label">AI Insights</div>
                <div class="sidebar-title">Generate Insight</div>
              </div>
            </div>
            <p class="sidebar-sub">
              Plain-language solar reports and planning recommendations.
            </p>
          </div>

          <div class="sidebar-content">
            <div class="ai-tabs" role="group" aria-label="Insight type">
              <button
                class="ai-tab"
                :class="{ active: mode === 'building' }"
                type="button"
                @click="mode = 'building'"
              >
                Building
              </button>
              <button
                class="ai-tab"
                :class="{ active: mode === 'precinct' }"
                type="button"
                @click="mode = 'precinct'"
              >
                Precinct
              </button>
            </div>

            <form class="ai-form" @submit.prevent="generateInsight">
              <label class="ai-field">
                <span>{{ mode === 'building' ? 'Building structure ID' : 'Precinct ID or name' }}</span>
                <input
                  v-model.trim="targetId"
                  type="text"
                  :placeholder="mode === 'building' ? 'Example: 105047' : 'Example: Docklands'"
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

              <button class="share-btn ai-generate-btn" type="submit" :disabled="isLoading || !targetId">
                {{ isLoading ? 'Generating...' : primaryButtonLabel }}
              </button>

              <p v-if="errorMessage" class="search-error">{{ errorMessage }}</p>
            </form>

            <div class="section-title">Backend API</div>
            <div class="assumptions">
              <strong>Reserved for integration</strong>
              The page currently uses demo output. When the backend AI endpoint is ready,
              set <code>USE_BACKEND_AI</code> to <code>true</code>.
            </div>
          </div>
        </div>
      </aside>

      <section class="ai-output-area" aria-live="polite">
        <div v-if="isLoading" class="loading">
          <div class="loading-spinner" aria-hidden="true"></div>
          <div class="loading-text">Preparing AI insight from solar data...</div>
        </div>

        <div v-if="!result && !isLoading" class="empty-state ai-empty">
          <div class="empty-icon">AI</div>
          <div class="empty-text">
            Select a building or precinct, then generate an AI-assisted report.
          </div>
        </div>

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
            <p class="score-explanation">
              {{ result.summary }}
            </p>
          </div>

          <div class="section-title">Key Metrics</div>
          <div class="metrics-grid ai-metrics">
            <div v-for="metric in result.metrics" :key="metric.label" class="metric-card">
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
            <div v-for="action in result.actions" :key="action" class="info-row">
              <span class="info-key">Action</span>
              <span class="info-val">{{ action }}</span>
            </div>
          </div>
        </article>
      </section>
    </main>

    <div class="toast" role="status" aria-live="polite" :class="{ show: toastVisible }">
      Copied insight
    </div>
  </div>
</template>

<script>
export default { name: 'AiInsightsView' }
</script>

<script setup>
import { computed, ref } from 'vue'
import MainNavbar from '../components/MainNavbar.vue'

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1'

/*
  Reserved backend switch.

  Keep false until backend AI endpoints exist.
  Change to true when these endpoints are ready:

  POST /api/v1/ai/building-report
  POST /api/v1/ai/precinct-policy
*/
const USE_BACKEND_AI = false

const mode = ref('building')
const targetId = ref('')
const focus = ref('plain')
const audience = ref('owner')
const result = ref(null)
const isLoading = ref(false)
const errorMessage = ref('')
const toastVisible = ref(false)

const primaryButtonLabel = computed(() => {
  return mode.value === 'building' ? 'Generate Report' : 'Generate Recommendation'
})

async function generateInsight() {
  errorMessage.value = ''
  result.value = null
  isLoading.value = true

  const payload = {
    target_id: targetId.value,
    focus: focus.value,
    audience: audience.value,
  }

  try {
    result.value = USE_BACKEND_AI
      ? await callAiInsightApi(mode.value, payload)
      : buildDemoInsight(mode.value, payload)
  } catch (error) {
    errorMessage.value = error.message || 'Unable to generate AI insight.'
  } finally {
    isLoading.value = false
  }
}

/*
  Reserved backend API call.

  Expected response shape:
  {
    type: string,
    title: string,
    priority: string,
    summary: string,
    metrics: [{ label: string, value: string, source: string }],
    recommendation: string,
    reasoning: string,
    actions: string[]
  }
*/
async function callAiInsightApi(selectedMode, payload) {
  const endpoint =
    selectedMode === 'building'
      ? `${API_BASE}/ai/building-report`
      : `${API_BASE}/ai/precinct-policy`

  const response = await fetch(endpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    throw new Error(`AI insight API failed with status ${response.status}`)
  }

  return response.json()
}

function buildDemoInsight(selectedMode, payload) {
  if (selectedMode === 'building') {
    return {
      type: 'Building solar report',
      title: `Building ${payload.target_id}`,
      priority: 'High',
      summary:
        'This building is ready for a solar feasibility review. The final backend report should combine roof suitability, estimated annual generation, financial return, and comparison with nearby buildings.',
      metrics: [
        { label: 'Suitability', value: 'High', source: 'solar_score' },
        { label: 'ROI Outlook', value: 'Medium', source: 'estimated_payback' },
        { label: 'Output Time', value: '< 5 sec', source: 'AI endpoint' },
        { label: 'Audience', value: audienceLabel(payload.audience), source: 'user_input' },
      ],
      recommendation:
        'Prioritise this building for a detailed solar assessment if its annual generation and usable roof area are above the local median.',
      reasoning:
        'The insight should translate technical solar metrics into plain language so a property owner can understand whether the building is suitable and why.',
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
    summary:
      'This precinct should be reviewed for solar adoption gaps, total potential capacity, and buildings with high suitability but low installed capacity.',
    metrics: [
      { label: 'Adoption Gap', value: 'High', source: 'adoption_gap_kw' },
      { label: 'Policy Priority', value: 'Critical', source: 'precinct_rank' },
      { label: 'Output Time', value: '< 5 sec', source: 'AI endpoint' },
      { label: 'Audience', value: audienceLabel(payload.audience), source: 'user_input' },
    ],
    recommendation:
      'Target incentives toward high-potential buildings with low current adoption, then support owners with plain-language return estimates.',
    reasoning:
      'The policy recommendation should reference adoption gap, solar score distribution, installed capacity, and potential capacity across the selected precinct.',
    actions: [
      'Rank buildings by suitability and adoption gap.',
      'Identify incentive candidates in the selected precinct.',
      'Export the recommendation for planning documentation.',
    ],
  }
}

function audienceLabel(value) {
  const labels = {
    owner: 'Owner',
    planner: 'Planner',
    investor: 'Investor',
    community: 'Community',
  }

  return labels[value] || 'User'
}

async function copyInsight() {
  if (!result.value) return

  const text = [
    result.value.title,
    '',
    result.value.summary,
    '',
    result.value.recommendation,
  ].join('\n')

  await navigator.clipboard.writeText(text)

  toastVisible.value = true
  window.setTimeout(() => {
    toastVisible.value = false
  }, 1800)
}
</script>

<style scoped>
.ai-main {
  background: var(--bg);
}

.ai-sidebar {
  width: 430px;
  border-left: 0;
  border-right: 1px solid var(--border);
}

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
}

.ai-tab.active {
  background: var(--ink);
  color: var(--city-light);
}

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

.ai-generate-btn {
  margin-top: 4px;
}

.ai-generate-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.ai-output-area {
  flex: 1;
  position: relative;
  overflow-y: auto;
  padding: 24px;
}

.ai-empty {
  height: 100%;
}

.ai-empty .empty-icon {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: var(--ink);
  color: var(--city-light);
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: 'DM Serif Display', serif;
  opacity: 1;
}

.ai-report {
  max-width: 980px;
  margin: 0 auto;
}

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
  font-size: 34px;
  line-height: 1.15;
  color: var(--text-primary);
}

.ai-summary {
  margin-bottom: 18px;
}

.ai-summary .score-explanation {
  max-height: none;
}

.ai-metrics {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

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

.ai-actions .info-row:first-child {
  padding-top: 0;
}

.ai-actions .info-row:last-child {
  padding-bottom: 0;
}

@media (max-width: 1100px) {
  .ai-sidebar {
    width: 380px;
  }

  .ai-metrics {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 820px) {
  .ai-main {
    flex-direction: column;
    overflow-y: auto;
  }

  .ai-sidebar {
    width: 100%;
    max-height: none;
    border-right: 0;
    border-bottom: 1px solid var(--border);
  }

  .ai-output-area {
    min-height: 520px;
  }

  .ai-report-header {
    flex-direction: column;
  }

  .ai-metrics {
    grid-template-columns: 1fr;
  }
}
</style>