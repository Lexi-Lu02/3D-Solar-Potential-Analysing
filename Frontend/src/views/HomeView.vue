<template>
  <div class="home-screen">
    <MainNavbar />

    <main id="main-content">

    <!-- ── Hero ─────────────────────────────────────────────── -->
    <section class="hero">
      <div class="hero-inner">
        <div class="hero-content">
          <div class="hero-text">
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
              <a class="btn-primary" href="#start-journey" aria-label="Start your personalised journey">
                Start Your Journey →
              </a>
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

    <!-- ── AI-Powered Journey ─────────────────────────────────── -->
    <section class="seg seg--surface" id="start-journey">
      <div class="seg-inner journey-seg">

        <div class="journey-intro">
          <p class="eyebrow eyebrow--center">AI-Powered · Start Here</p>
          <h2 class="seg-title seg-title--center">Find your solar opportunity</h2>
          <p class="journey-sub">Tell us who you are and we'll personalise your experience</p>
        </div>

        <!-- Identity selector -->
        <div class="identity-row" role="group" aria-label="Choose your role">
          <button
            class="identity-card"
            :class="{ 'identity-card--active': identity === 'owner' }"
            @click="selectIdentity('owner')"
            :aria-pressed="identity === 'owner'"
          >
            <div class="identity-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"/>
                <polyline points="9 22 9 12 15 12 15 22"/>
              </svg>
            </div>
            <div class="identity-name">Property Owner</div>
            <div class="identity-desc-text">Analyse your building's solar potential, estimate financial returns, and plan your installation with AI guidance</div>
            <div class="identity-tags">
              <span class="identity-tag">Address Search</span>
              <span class="identity-tag">Solar Score</span>
              <span class="identity-tag">ROI Estimate</span>
            </div>
            <div class="identity-cta">Get Started <span aria-hidden="true">→</span></div>
          </button>

          <button
            class="identity-card"
            :class="{ 'identity-card--active': identity === 'planner' }"
            @click="selectIdentity('planner')"
            :aria-pressed="identity === 'planner'"
          >
            <div class="identity-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="6" width="6" height="15" rx="1"/>
                <rect x="9" y="2" width="6" height="19" rx="1"/>
                <rect x="15" y="9" width="6" height="12" rx="1"/>
              </svg>
            </div>
            <div class="identity-name">City Planner</div>
            <div class="identity-desc-text">Explore precinct-level solar data, compare neighbourhoods, and build the evidence base for urban solar policy</div>
            <div class="identity-tags">
              <span class="identity-tag">Precinct Rankings</span>
              <span class="identity-tag">Adoption Gaps</span>
              <span class="identity-tag">Policy Data</span>
            </div>
            <div class="identity-cta">Get Started <span aria-hidden="true">→</span></div>
          </button>
        </div>

        <!-- ── Property Owner Journey ──────────────────── -->
        <Transition name="fade-slide">
          <div v-if="identity === 'owner'" class="journey-flow" key="owner">

            <!-- Step bar -->
            <div class="step-bar" aria-label="Journey progress">
              <div class="step-bar-item" :class="{ 'step-bar-item--done': !!ownerBuilding, 'step-bar-item--active': !ownerBuilding }">
                <div class="step-bar-dot">{{ ownerBuilding ? '✓' : '1' }}</div>
                <div class="step-bar-label">Search Building</div>
              </div>
              <div class="step-bar-line"></div>
              <div class="step-bar-item" :class="{ 'step-bar-item--done': ownerStep2Done, 'step-bar-item--active': !!ownerBuilding && !ownerStep2Done }">
                <div class="step-bar-dot">{{ ownerStep2Done ? '✓' : '2' }}</div>
                <div class="step-bar-label">Review Insights</div>
              </div>
              <div class="step-bar-line"></div>
              <div class="step-bar-item" :class="{ 'step-bar-item--done': ownerStep3Done, 'step-bar-item--active': ownerStep2Done && !ownerStep3Done }">
                <div class="step-bar-dot">{{ ownerStep3Done ? '✓' : '3' }}</div>
                <div class="step-bar-label">Explore Details</div>
              </div>
            </div>

            <!-- Search field -->
            <div class="search-area">
              <div style="position:relative">
                <div class="search-field-wrap">
                  <svg class="search-field-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
                  </svg>
                  <input
                    v-model="ownerAddressQuery"
                    type="text"
                    class="search-field"
                    placeholder="Start typing a Melbourne CBD address…"
                    @input="onOwnerSearchInput"
                    @blur="ownerDropdownOpen = false"
                    @keydown.escape="ownerDropdownOpen = false"
                    autocomplete="off"
                    aria-label="Building address"
                  />
                  <span v-if="ownerSearchLoading" class="search-spinner" aria-hidden="true"></span>
                </div>
                <div v-if="ownerDropdownOpen && ownerSearchResults.length" class="search-dropdown">
                  <button
                    v-for="r in ownerSearchResults"
                    :key="r.structure_id"
                    class="search-dropdown-item"
                    @mousedown.prevent="selectOwnerResult(r)"
                  >
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px;flex-shrink:0;color:var(--text-muted)">
                      <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
                    </svg>
                    {{ r.address }}
                  </button>
                </div>
              </div>
              <div v-if="ownerSearchError" class="search-not-found">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:15px;height:15px;flex-shrink:0;color:var(--text-muted)">
                  <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
                </svg>
                <span>{{ ownerSearchError }}</span>
              </div>
              <div v-if="!ownerBuilding && !ownerSearchError && !ownerAddressQuery" class="search-hint-row">
                Start typing to search any Melbourne CBD building address
              </div>
            </div>

            <!-- Results: building card + AI chat -->
            <Transition name="fade">
              <div v-if="ownerBuilding" class="results-layout">

                <!-- Building data card -->
                <div class="bdata-card">
                  <div class="bdata-header">
                    <div class="bdata-header-info">
                      <h3 class="bdata-name">{{ ownerBuilding.address }}</h3>
                      <p class="bdata-address">Melbourne CBD</p>
                    </div>
                    <div v-if="ownerBuilding.solarScore !== null" class="solar-score-badge" :class="scoreBadgeClass(ownerBuilding.solarScore)">
                      <div class="solar-score-num">{{ ownerBuilding.solarScore }}</div>
                      <div class="solar-score-denom">/5</div>
                      <div class="solar-score-tier">{{ ownerBuilding.solarTier }}</div>
                    </div>
                    <div v-else class="solar-score-badge solar-score-badge--no-data">
                      <div class="solar-score-num" style="font-size:13px;line-height:1.4">N/A</div>
                      <div class="solar-score-tier">No Rating</div>
                    </div>
                  </div>
                  <div class="bdata-score-bar-track">
                    <div v-if="ownerBuilding.solarScore !== null" class="bdata-score-bar-fill" :class="scoreFillClass(ownerBuilding.solarScore)" :style="{ width: (ownerBuilding.solarScore * 20) + '%' }"></div>
                  </div>
                  <div class="bdata-divider"></div>
                  <div class="bdata-metrics">
                    <div class="bdata-metric" v-for="m in ownerBuildingMetrics" :key="m.label">
                      <div class="bdata-metric-val">{{ m.value }}</div>
                      <div class="bdata-metric-label">{{ m.label }}</div>
                    </div>
                  </div>
                </div>

                <!-- AI Chat -->
                <div class="ai-chat-panel" @mouseenter="ownerStep2Done = true">
                  <div class="ai-chat-head">
                    <span class="ai-spark">✦</span>
                    <div class="ai-chat-head-text">
                      <div class="ai-chat-title">AI Solar Assistant</div>
                      <div class="ai-chat-sub">Ask anything about this building</div>
                    </div>
                    <div class="ai-coming-soon-pill">Demo</div>
                  </div>
                  <div class="ai-chat-body" ref="ownerChatBodyRef">
                    <div
                      v-for="msg in ownerMessages"
                      :key="msg.id"
                      class="ai-msg"
                      :class="msg.role === 'user' ? 'ai-msg--user' : 'ai-msg--ai'"
                    >
                      <div class="ai-msg-bubble">{{ msg.content }}</div>
                    </div>
                    <div v-if="ownerTyping" class="ai-msg ai-msg--ai">
                      <div class="ai-msg-bubble ai-msg-typing">
                        <span></span><span></span><span></span>
                      </div>
                    </div>
                  </div>
                  <div class="ai-suggestions" v-if="ownerMessages.length <= 2">
                    <button
                      v-for="q in ownerSuggestions"
                      :key="q"
                      class="ai-suggest-chip"
                      @click="ownerAsk(q)"
                    >{{ q }}</button>
                  </div>
                  <div class="ai-input-row">
                    <input
                      v-model="ownerChatInput"
                      type="text"
                      class="ai-text-input"
                      placeholder="Ask about savings, installation, or next steps…"
                      @keydown.enter="sendOwnerMessage"
                      :disabled="ownerTyping"
                      aria-label="Chat input"
                    />
                    <button class="ai-send-btn" @click="sendOwnerMessage" :disabled="!ownerChatInput.trim() || ownerTyping">
                      Send
                    </button>
                  </div>
                </div>

              </div>
            </Transition>

            <!-- Deep-dive CTAs: shown once a result is present -->
            <Transition name="fade">
              <div v-if="ownerBuilding" class="explore-jump">
                <p class="explore-jump-label">Want the full picture? Open any panel in 3D Explore</p>
                <div class="explore-jump-row">
                  <button class="explore-jump-card" v-for="p in explorePanels" :key="p.panel" @click="goToExplorePanel(p.panel)">
                    <img :src="p.icon" :alt="p.title" class="explore-jump-icon" />
                    <div class="explore-jump-name">{{ p.title }}</div>
                    <div class="explore-jump-desc">{{ p.desc }}</div>
                    <div class="explore-jump-link">Open in 3D Explore →</div>
                  </button>
                </div>
              </div>
            </Transition>

          </div>
        </Transition>

        <!-- ── City Planner Journey ─────────────────────── -->
        <Transition name="fade-slide">
          <div v-if="identity === 'planner'" class="journey-flow" key="planner">

            <!-- Step bar -->
            <div class="step-bar" aria-label="Journey progress">
              <div class="step-bar-item" :class="{ 'step-bar-item--done': !!plannerResult, 'step-bar-item--active': !plannerResult }">
                <div class="step-bar-dot">{{ plannerResult ? '✓' : '1' }}</div>
                <div class="step-bar-label">Select Precinct</div>
              </div>
              <div class="step-bar-line"></div>
              <div class="step-bar-item" :class="{ 'step-bar-item--active': !!plannerResult }">
                <div class="step-bar-dot">2</div>
                <div class="step-bar-label">Review Data</div>
              </div>
              <div class="step-bar-line"></div>
              <div class="step-bar-item" :class="{ 'step-bar-item--active': !!plannerResult }">
                <div class="step-bar-dot">3</div>
                <div class="step-bar-label">Explore Map</div>
              </div>
            </div>

            <!-- Precinct + building search row -->
            <div class="planner-controls">
              <div class="planner-ctrl-group">
                <label class="planner-ctrl-label" for="precinct-select">Browse by precinct</label>
                <div class="select-wrap">
                  <select id="precinct-select" v-model="selectedPrecinctKey" class="precinct-dropdown" @change="loadPrecinct">
                    <option value="" disabled v-if="precinctListLoading">Loading precincts…</option>
                    <option value="" v-else>Choose a precinct…</option>
                    <option v-for="p in precinctListData" :key="p.precinct_id" :value="p.precinct_id">{{ p.name }}</option>
                  </select>
                  <svg class="select-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="6 9 12 15 18 9"/>
                  </svg>
                </div>
              </div>

              <div class="planner-or-divider">or</div>

              <div class="planner-ctrl-group">
                <label class="planner-ctrl-label">Search a specific building</label>
                <div style="position:relative">
                  <div class="search-field-wrap">
                    <svg class="search-field-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
                    </svg>
                    <input
                      v-model="plannerBuildingQuery"
                      type="text"
                      class="search-field"
                      placeholder="Enter a building address…"
                      @input="onPlannerSearchInput"
                      @blur="plannerBuildingDropdownOpen = false"
                      @keydown.escape="plannerBuildingDropdownOpen = false"
                      autocomplete="off"
                    />
                  </div>
                  <div v-if="plannerBuildingDropdownOpen && plannerBuildingResults.length" class="search-dropdown">
                    <button
                      v-for="r in plannerBuildingResults"
                      :key="r.structure_id"
                      class="search-dropdown-item"
                      @mousedown.prevent="selectPlannerBuildingResult(r)"
                    >
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px;flex-shrink:0;color:var(--text-muted)">
                        <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
                      </svg>
                      {{ r.address }}
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <!-- Results: precinct/building card + AI chat -->
            <Transition name="fade">
              <div v-if="plannerResult" class="results-layout">

                <!-- Data card -->
                <div class="bdata-card">
                  <div class="bdata-header">
                    <div class="bdata-header-info">
                      <h3 class="bdata-name">{{ plannerResult.name }}</h3>
                      <p class="bdata-address">{{ plannerResult.subtitle }}</p>
                    </div>
                    <!-- Rank badge for precincts, score badge for buildings -->
                    <template v-if="plannerResult.type === 'precinct'">
                      <div class="rank-badge">
                        <div class="rank-badge-num">#{{ plannerResult.rank }}</div>
                        <div class="rank-badge-of">of {{ plannerResult.totalPrecincts }}</div>
                        <div class="rank-badge-tier">{{ plannerResult.tierStr }}</div>
                      </div>
                    </template>
                    <template v-else>
                      <div v-if="plannerResult.solarScore !== null" class="solar-score-badge" :class="scoreBadgeClass(plannerResult.solarScore)">
                        <div class="solar-score-num">{{ plannerResult.solarScore }}</div>
                        <div class="solar-score-denom">/5</div>
                        <div class="solar-score-tier">{{ plannerResult.solarTier }}</div>
                      </div>
                      <div v-else class="solar-score-badge solar-score-badge--no-data">
                        <div class="solar-score-num" style="font-size:13px;line-height:1.4">N/A</div>
                        <div class="solar-score-tier">No Rating</div>
                      </div>
                    </template>
                  </div>
                  <div class="bdata-score-bar-track">
                    <div v-if="plannerResult.type !== 'precinct' && plannerResult.solarScore !== null"
                         class="bdata-score-bar-fill" :class="scoreFillClass(plannerResult.solarScore)"
                         :style="{ width: (plannerResult.solarScore * 20) + '%' }">
                    </div>
                  </div>
                  <div class="bdata-divider"></div>
                  <div class="bdata-metrics">
                    <div class="bdata-metric" v-for="m in plannerResultMetrics" :key="m.label">
                      <div class="bdata-metric-val">{{ m.value }}</div>
                      <div class="bdata-metric-label">{{ m.label }}</div>
                    </div>
                  </div>
                  <!-- Adoption gap bar (only for precincts) -->
                  <div v-if="plannerResult.type === 'precinct'" class="adoption-gap">
                    <div class="adoption-gap-header">
                      <span class="adoption-gap-title">Solar Adoption Gap</span>
                      <span class="adoption-gap-pct">{{ plannerResult.adoptionPct }}% installed</span>
                    </div>
                    <div class="adoption-bar-track">
                      <div class="adoption-bar-installed" :style="{ width: plannerResult.adoptionPct + '%' }"></div>
                      <div class="adoption-bar-potential" :style="{ width: Math.max(0, 100 - plannerResult.adoptionPct) + '%', left: plannerResult.adoptionPct + '%' }"></div>
                    </div>
                    <div class="adoption-legend">
                      <span><span class="legend-dot legend-dot--installed"></span>Installed ({{ plannerResult.adoptionPct }}%)</span>
                      <span><span class="legend-dot legend-dot--potential"></span>Untapped potential</span>
                    </div>
                  </div>
                </div>

                <!-- AI Chat -->
                <div class="ai-chat-panel">
                  <div class="ai-chat-head">
                    <span class="ai-spark">✦</span>
                    <div class="ai-chat-head-text">
                      <div class="ai-chat-title">AI Planning Assistant</div>
                      <div class="ai-chat-sub">Ask about this {{ plannerResult.type === 'precinct' ? 'precinct' : 'building' }}'s solar outlook</div>
                    </div>
                    <div class="ai-coming-soon-pill">Demo</div>
                  </div>
                  <div class="ai-chat-body" ref="plannerChatBodyRef">
                    <div
                      v-for="msg in plannerMessages"
                      :key="msg.id"
                      class="ai-msg"
                      :class="msg.role === 'user' ? 'ai-msg--user' : 'ai-msg--ai'"
                    >
                      <div class="ai-msg-bubble">{{ msg.content }}</div>
                    </div>
                    <div v-if="plannerTyping" class="ai-msg ai-msg--ai">
                      <div class="ai-msg-bubble ai-msg-typing">
                        <span></span><span></span><span></span>
                      </div>
                    </div>
                  </div>
                  <div class="ai-suggestions" v-if="plannerMessages.length <= 2">
                    <button
                      v-for="q in plannerSuggestions"
                      :key="q"
                      class="ai-suggest-chip"
                      @click="plannerAsk(q)"
                    >{{ q }}</button>
                  </div>
                  <div class="ai-input-row">
                    <input
                      v-model="plannerChatInput"
                      type="text"
                      class="ai-text-input"
                      placeholder="Ask about adoption gaps, policy implications, or yield…"
                      @keydown.enter="sendPlannerMessage"
                      :disabled="plannerTyping"
                      aria-label="Chat input"
                    />
                    <button class="ai-send-btn" @click="sendPlannerMessage" :disabled="!plannerChatInput.trim() || plannerTyping">
                      Send
                    </button>
                  </div>
                </div>

              </div>
            </Transition>

            <!-- Precincts page CTA -->
            <Transition name="fade">
              <div v-if="plannerResult" class="precinct-explore-cta">
                <p class="explore-jump-label">Ready for the full picture? View all precincts ranked side-by-side</p>
                <div class="precinct-cta-row">
                  <RouterLink to="/precincts" class="btn-primary">View Precincts Map →</RouterLink>
                  <button class="btn-ghost-outline" @click="goToExplore">Explore Individual Buildings</button>
                </div>
              </div>
            </Transition>

          </div>
        </Transition>

      </div>
    </section>

    <!-- ── 3D Explore ─────────────────────────────────────────── -->
    <section class="seg seg--surface" id="features">
      <div class="seg-inner seg-inner--tight-top">
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
          <div class="bento-card" v-for="f in features" :key="f.title">
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
import { onMounted, ref, computed, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import MainNavbar from '../components/MainNavbar.vue'
import {
  identity,
  ownerAddressQuery, ownerSearchLoading, ownerSearchError, ownerBuilding,
  ownerMessages, ownerChatInput, ownerTyping,
  ownerSearchResults, ownerDropdownOpen,
  selectedPrecinctKey, plannerBuildingQuery, plannerResult,
  plannerMessages, plannerChatInput, plannerTyping,
  plannerBuildingResults, plannerBuildingDropdownOpen,
  precinctListData, precinctListLoading,
  ownerStep2Done, ownerStep3Done,
  homeTimers,
} from '../composables/useHomeJourney.js'

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
const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1'

// ── Hero stats ────────────────────────────────────────────────────────────────
const stats = ref([
  { value: '500+',     label: 'Buildings analysed' },
  { value: '169K m²',  label: 'Usable rooftop area' },
  { value: '37.9 GWh', label: 'Est. annual yield' },
  { value: '237',      label: 'High-potential sites' },
])

// ── Existing marketing content ────────────────────────────────────────────────
const exploreFeatures = [
  '3D colour-coded map of 40,000+ Melbourne CBD buildings',
  'Search any building instantly by street address',
  'Filter by roof type, solar score, and height',
  'Click any building to open a full three-panel analysis',
  'Compare up to 4 buildings side by side',
  'Sun path & shadow simulation for any date and time',
]

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

const precinctFeatures = [
  'Interactive map showing precinct boundaries coloured by solar tier',
  'Ranked list sortable by annual yield, usable area, buildings, or adoption gap',
  'Installed capacity vs potential capacity for each precinct',
  'Detailed stats: kWh/year, usable m², building count',
  'Export full precinct data as CSV for planning teams',
]

const steps = [
  { title: 'Search', desc: 'Type any Melbourne CBD address or click a building directly on the 3D map.' },
  { title: 'Analyse', desc: 'Review solar score, estimated system size, indicative cost, and payback/CO₂ outcome, then compare buildings or export a report.' },
  { title: 'Plan', desc: 'Compare buildings and precincts side by side to prioritise the highest-return installations.' },
]

const features = [
  { icon: icon3DBuilding,   title: '3D Building Extrusion', desc: 'Visualise every building in Melbourne CBD as a true-to-scale 3D model, colour-coded by solar score.' },
  { icon: iconSolarScore,   title: 'Solar Score Ranking', desc: 'Each building receives a solar potential score derived from rooftop area, roof type, and peak sun hours.' },
  { icon: iconRoofType,     title: 'Roof Type Filtering', desc: 'Filter by Flat, Hip, Gable, Pyramid, or Shed roof types to zero in on suitable installation candidates.' },
  { icon: iconEnergy,       title: 'Energy Estimates', desc: 'Instant kWh generation estimates using BOM-validated 4.1 peak sun hours/day for Melbourne CBD.' },
  { icon: iconClickInspect, title: 'Click-to-Inspect', desc: 'Click any building to open a full analysis panel with area metrics, height, roof type, and energy output.' },
  { icon: iconComparison,   title: 'Comparison View', desc: 'Select multiple buildings side-by-side to compare solar potential across different city blocks.' },
]

// Explore panel CTAs used in the owner journey
const explorePanels = [
  { panel: 'solar',       icon: iconSolarCell,   title: 'Solar Potential',     desc: 'Score, roof area, monthly generation' },
  { panel: 'financial',   icon: iconProfits,      title: 'Financial Analysis',  desc: 'Install cost, savings, payback period' },
  { panel: 'environment', icon: iconPlanetEarth,  title: 'Environmental Impact', desc: 'CO₂ offset, trees & cars equivalent' },
]

function goToExplore() { router.push('/explore') }
function goToExplorePanel(panel) {
  ownerStep3Done.value = true
  const query = { panel }
  if (ownerBuilding.value?.structureId) query.buildingId = ownerBuilding.value.structureId
  router.push({ path: '/explore', query })
}

// ── AI Journey state ─────────────────────────────────────────────────────────
// All persistent state is imported from useHomeJourney.js (module-level singletons).
// Only DOM template refs are local — they must be re-bound each mount.

const ownerChatBodyRef   = ref(null)
const plannerChatBodyRef = ref(null)

// ── Computed metrics ──────────────────────────────────────────────────────────

const ownerBuildingMetrics = computed(() => {
  const b = ownerBuilding.value
  if (!b) return []
  return [
    { value: b.annualKwh    ? fmtKwh(b.annualKwh)                        : 'N/A', label: 'Annual Generation' },
    { value: b.usableArea   ? `${b.usableArea.toLocaleString()} m²`       : 'N/A', label: 'Usable Roof Area' },
    { value: b.installCost  ? `$${b.installCost.toLocaleString()}`        : 'N/A', label: 'Est. Install Cost' },
    { value: b.annualSavings ? `$${b.annualSavings.toLocaleString()}`     : 'N/A', label: 'Annual Savings' },
    { value: b.paybackYears  ? `${b.paybackYears} yrs`                    : 'N/A', label: 'Payback Period' },
    { value: b.co2Tonnes     ? `${b.co2Tonnes} t`                         : 'N/A', label: 'CO₂ Offset/yr' },
  ]
})

const plannerResultMetrics = computed(() => {
  const p = plannerResult.value
  if (!p) return []
  if (p.type === 'precinct') {
    return [
      { value: p.buildings.toLocaleString(),                                  label: 'Buildings Analysed' },
      { value: fmtKwh(p.annualKwh),                                           label: 'Annual Potential' },
      { value: `${(p.usableArea / 1000).toFixed(0)}K m²`,                    label: 'Usable Roof Area' },
      { value: `${p.adoptionPct}%`,                                            label: 'Solar Adoption' },
      { value: `${(p.installedKw / 1000).toFixed(1)} MW`,                    label: 'Installed Capacity' },
      { value: `${((p.potentialKw - p.installedKw) / 1000).toFixed(1)} MW`, label: 'Untapped Potential' },
    ]
  }
  const b = p
  return [
    { value: b.annualKwh     ? fmtKwh(b.annualKwh)                        : 'N/A', label: 'Annual Generation' },
    { value: b.usableArea    ? `${b.usableArea.toLocaleString()} m²`       : 'N/A', label: 'Usable Roof Area' },
    { value: b.annualSavings ? `$${b.annualSavings.toLocaleString()}`      : 'N/A', label: 'Annual Savings' },
    { value: b.paybackYears  ? `${b.paybackYears} yrs`                     : 'N/A', label: 'Payback Period' },
    { value: b.co2Tonnes     ? `${b.co2Tonnes} t`                          : 'N/A', label: 'CO₂ Offset/yr' },
  ]
})

// ── Suggested questions ───────────────────────────────────────────────────────

const ownerSuggestions = [
  'Is this building suitable for solar?',
  'What financial return can I expect?',
  'How much CO₂ would this offset?',
]

const plannerSuggestions = computed(() => {
  if (!plannerResult.value) return []
  if (plannerResult.value.type === 'precinct') return [
    'What is the total untapped solar capacity?',
    'How does adoption compare to other precincts?',
    'What building types have the most potential?',
  ]
  return [
    'Is this building a good candidate for policy priority?',
    'What financial return can this building expect?',
    'How does this compare to neighbouring buildings?',
  ]
})

// ── Helpers ───────────────────────────────────────────────────────────────────

function fmtKwh(kwh) {
  if (kwh >= 1_000_000) return `${(kwh / 1_000_000).toFixed(1)} GWh`
  if (kwh >= 1000)      return `${(kwh / 1000).toFixed(1)} MWh`
  return `${kwh.toLocaleString()} kWh`
}

function scoreBadgeClass(score) {
  if (score >= 4.5) return 'solar-score-badge--very-high'
  if (score >= 3.5) return 'solar-score-badge--high'
  if (score >= 2.5) return 'solar-score-badge--med'
  if (score >= 1.5) return 'solar-score-badge--low'
  return 'solar-score-badge--very-low'
}

function scoreFillClass(score) {
  if (score >= 4.5) return 'score-fill--very-high'
  if (score >= 3.5) return 'score-fill--high'
  if (score >= 2.5) return 'score-fill--med'
  if (score >= 1.5) return 'score-fill--low'
  return 'score-fill--very-low'
}

let _msgId = 0
function msg(role, content) { return { id: ++_msgId, role, content } }

function scrollChat(refEl) {
  nextTick(() => { if (refEl.value) refEl.value.scrollTop = refEl.value.scrollHeight })
}

// ── Identity selection ────────────────────────────────────────────────────────

function selectIdentity(id) {
  identity.value = id
  ownerBuilding.value = null
  ownerSearchError.value = null
  ownerAddressQuery.value = ''
  ownerSearchResults.value = []
  ownerDropdownOpen.value = false
  ownerMessages.value = []
  ownerStep2Done.value = false
  ownerStep3Done.value = false
  plannerResult.value = null
  selectedPrecinctKey.value = ''
  plannerBuildingQuery.value = ''
  plannerBuildingResults.value = []
  plannerBuildingDropdownOpen.value = false
  plannerMessages.value = []
  if (id === 'planner') loadPrecinctList()
  nextTick(() => {
    document.getElementById('start-journey')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  })
}

// ── Property Owner: debounced search + result selection ──────────────────────

function onOwnerSearchInput() {
  clearTimeout(homeTimers.owner)
  const q = ownerAddressQuery.value.trim()
  if (q.length < 2) {
    ownerSearchResults.value = []
    ownerDropdownOpen.value = false
    ownerSearchLoading.value = false
    return
  }
  ownerSearchLoading.value = true
  homeTimers.owner = setTimeout(async () => {
    try {
      const res = await fetch(`${API_BASE}/buildings/search?q=${encodeURIComponent(q)}`)
      ownerSearchResults.value = res.ok ? await res.json() : []
      ownerDropdownOpen.value = ownerSearchResults.value.length > 0
    } catch { ownerSearchResults.value = [] }
    finally  { ownerSearchLoading.value = false }
  }, 250)
}

async function selectOwnerResult(result) {
  ownerSearchResults.value = []
  ownerDropdownOpen.value = false
  ownerAddressQuery.value = result.address
  ownerMessages.value = []
  ownerBuilding.value = null
  ownerSearchError.value = null
  ownerStep2Done.value = false
  ownerStep3Done.value = false
  ownerSearchLoading.value = true
  try {
    const [yieldData, solarData] = await Promise.all([
      fetch(`${API_BASE}/buildings/structure/${result.structure_id}/yield`).then(r => r.ok ? r.json() : null).catch(() => null),
      fetch(`${API_BASE}/buildings/structure/${result.structure_id}/solar`).then(r => r.ok ? r.json() : null).catch(() => null),
    ])
    const kwhAnnual     = yieldData?.kwh_annual ?? (solarData?.max_panels_kwh_annual ? Math.round(solarData.max_panels_kwh_annual) : null)
    const usableArea    = solarData?.max_array_area_m2 ? Math.round(solarData.max_array_area_m2 * 10) / 10 : null
    const scoreAvg      = yieldData?.solar_score_avg ?? null
    const solarScore    = (scoreAvg !== null && scoreAvg > 0) ? Math.round(scoreAvg * 10) / 10 : null
    const installCost   = usableArea ? Math.round(usableArea * 150) : null
    const annualSavings = kwhAnnual  ? Math.round(kwhAnnual * 0.25) : null
    const paybackYears  = (installCost && annualSavings > 0) ? Math.round(installCost / annualSavings * 10) / 10 : null
    const co2Tonnes     = kwhAnnual  ? Math.round(kwhAnnual * 0.727) / 1000 : null
    ownerBuilding.value = {
      address: result.address,
      structureId: result.structure_id,
      solarScore, solarTier: scoreToTier(scoreAvg),
      annualKwh: kwhAnnual, usableArea, installCost, annualSavings, paybackYears, co2Tonnes,
    }
    await triggerOwnerWelcome()
  } catch { ownerSearchError.value = 'Unable to load data for this building. Please try another.' }
  finally  { ownerSearchLoading.value = false }
}

function scoreToTier(scoreAvg) {
  if (!scoreAvg) return 'No Rating'
  if (scoreAvg >= 4.5) return 'Excellent'
  if (scoreAvg >= 3.5) return 'Good'
  if (scoreAvg >= 2.5) return 'Moderate'
  if (scoreAvg >= 1.5) return 'Poor'
  return 'Very Poor'
}

async function triggerOwnerWelcome() {
  ownerTyping.value = true
  await new Promise(r => setTimeout(r, 1100))
  ownerTyping.value = false
  const b = ownerBuilding.value
  let intro
  if (b.solarScore !== null) {
    const candidacy = b.solarScore >= 3 ? 'a strong candidate for solar' : 'worth evaluating for solar'
    intro = `I've analysed ${b.address}. With a solar score of ${b.solarScore}/5 (${b.solarTier}), this building is ${candidacy}.`
    if (b.usableArea)    intro += ` The ${b.usableArea.toLocaleString()} m² of usable roof`
    if (b.annualKwh)     intro += ` could generate ${fmtKwh(b.annualKwh)} annually`
    if (b.annualSavings) intro += `, saving ~$${b.annualSavings.toLocaleString()}/year`
    intro += '. What would you like to explore?'
  } else {
    intro = `I've found ${b.address}. This building doesn't yet have a full solar rating in our dataset`
    if (b.usableArea) intro += `, but its ${b.usableArea.toLocaleString()} m² of usable rooftop area`
    if (b.annualKwh)  intro += ` suggests an estimated annual yield of ${fmtKwh(b.annualKwh)}`
    intro += '. Use the panels below to explore further details.'
  }
  ownerMessages.value.push(msg('ai', intro))
  scrollChat(ownerChatBodyRef)
}

async function sendOwnerMessage() {
  const q = ownerChatInput.value.trim()
  if (!q || ownerTyping.value) return
  ownerStep2Done.value = true
  ownerChatInput.value = ''
  ownerMessages.value.push(msg('user', q))
  scrollChat(ownerChatBodyRef)
  ownerTyping.value = true
  await new Promise(r => setTimeout(r, 900 + Math.random() * 500))
  ownerTyping.value = false
  ownerMessages.value.push(msg('ai', getOwnerReply(q.toLowerCase(), ownerBuilding.value)))
  scrollChat(ownerChatBodyRef)
}

function ownerAsk(q) { ownerChatInput.value = q; sendOwnerMessage() }

function getOwnerReply(q, b) {
  if (q.includes('suitable') || q.includes('good') || q.includes('score') || q.includes('rating')) {
    if (b.solarScore !== null)
      return `${b.address} scores ${b.solarScore}/5 — rated "${b.solarTier}". This reflects its ${b.usableArea ? b.usableArea.toLocaleString() + ' m²' : 'assessed'} usable roof area and Melbourne's average 4.1 peak sun hours/day.`
    return `${b.address} doesn't yet have a full solar rating in our dataset. ${b.usableArea ? `However, it has ${b.usableArea.toLocaleString()} m² of usable area, which is promising.` : 'Explore the Solar Potential panel below for more detail.'}`
  }
  if (q.includes('financial') || q.includes('return') || q.includes('save') || q.includes('cost') || q.includes('money') || q.includes('investment')) {
    if (b.installCost && b.annualSavings)
      return `The estimated install cost is $${b.installCost.toLocaleString()}, with projected annual savings of $${b.annualSavings.toLocaleString()}. That gives a payback period of about ${b.paybackYears} years — after which you generate essentially free electricity. Open the Financial Analysis panel below for the full breakdown.`
    return `Financial estimates require usable roof area and yield data for this building. Open the Financial Analysis panel below for more detail.`
  }
  if (q.includes('co2') || q.includes('carbon') || q.includes('environment') || q.includes('climate')) {
    if (b.co2Tonnes) {
      const trees = Math.round(b.co2Tonnes * 45)
      const cars  = Math.round(b.co2Tonnes / 4.6)
      return `Installing solar on this building would offset approximately ${b.co2Tonnes} tonnes of CO₂ per year — equivalent to planting ${trees.toLocaleString()} trees or taking ${cars} cars off Melbourne's roads. See the Environmental Impact panel for more detail.`
    }
    return `Environmental impact data requires yield estimates for this building. See the Environmental Impact panel below for more detail.`
  }
  if (q.includes('payback') || q.includes('year') || q.includes('roi')) {
    if (b.paybackYears && b.installCost && b.annualSavings)
      return `The estimated payback period is ${b.paybackYears} years, based on an install cost of $${b.installCost.toLocaleString()} and annual savings of $${b.annualSavings.toLocaleString()} at current Melbourne commercial electricity rates. After payback, the system continues generating returns for 20+ years.`
    return `Payback period data isn't available for this building yet — it requires both rooftop area and yield data. Try the Financial Analysis panel for the most up-to-date calculations.`
  }
  if (q.includes('roof') || q.includes('area') || q.includes('m²') || q.includes('space')) {
    if (b.usableArea) return `This building has ${b.usableArea.toLocaleString()} m² of solar-viable rooftop area. Open the Solar Potential panel for the full rooftop breakdown.`
    return `Detailed roof area data isn't available for this building yet. Open the Solar Potential panel below for more detail.`
  }
  return `For a complete picture of this building's solar potential, explore the three panels below: Solar Potential (scores & generation), Financial Analysis (cost & savings), and Environmental Impact (CO₂ & offsets). Each gives you a deep-dive with supporting data.`
}

// ── City Planner: precinct & building ────────────────────────────────────────

async function loadPrecinctList() {
  if (precinctListData.value.length > 0 || precinctListLoading.value) return
  precinctListLoading.value = true
  try {
    const res = await fetch(`${API_BASE}/precincts`)
    if (!res.ok) return
    const json = await res.json()
    const list = Array.isArray(json) ? json : (json.precincts ?? [])
    precinctListData.value = list
      .filter(p => p.building_count > 0)
      .sort((a, b) => a.name.localeCompare(b.name))
  } catch { /* keep empty */ }
  finally { precinctListLoading.value = false }
}

function precinctRankToTier(rank, total) {
  const pct = rank / total
  if (pct <= 0.25) return 'Top Tier'
  if (pct <= 0.5)  return 'High'
  if (pct <= 0.75) return 'Moderate'
  return 'Lower Tier'
}

async function loadPrecinct() {
  if (!selectedPrecinctKey.value) { plannerResult.value = null; plannerMessages.value = []; return }
  plannerBuildingQuery.value = ''
  plannerMessages.value = []
  const precinct = precinctListData.value.find(p => String(p.precinct_id) === String(selectedPrecinctKey.value))
  if (!precinct) return
  const installedKw = precinct.installed_capacity_kw ?? 0
  const potentialKw = precinct.potential_capacity_kw ?? 0
  const adoptionPct = potentialKw > 0 ? Math.round(installedKw / potentialKw * 1000) / 10 : 0
  const rank = precinct.rank ?? (precinctListData.value.filter(p => (p.total_kwh_annual ?? 0) >= (precinct.total_kwh_annual ?? 0)).length)
  const totalPrecincts = precinctListData.value.length
  plannerResult.value = {
    type: 'precinct',
    name: precinct.name,
    subtitle: [precinct.postcode, 'Melbourne CBD'].filter(Boolean).join(' · '),
    rank, totalPrecincts,
    tierStr: precinctRankToTier(rank, totalPrecincts),
    buildings: precinct.building_count ?? 0,
    annualKwh: precinct.total_kwh_annual ?? 0,
    usableArea: precinct.total_usable_area_m2 ?? 0,
    installedKw, potentialKw, adoptionPct,
    adoptionGapKw: precinct.adoption_gap_kw ?? 0,
  }
  await triggerPlannerWelcome()
}

async function triggerPlannerWelcome() {
  plannerTyping.value = true
  await new Promise(r => setTimeout(r, 1100))
  plannerTyping.value = false
  const p = plannerResult.value
  let intro
  if (p.type === 'precinct') {
    const gapMw = ((p.potentialKw - p.installedKw) / 1000).toFixed(1)
    intro = `I've pulled up the ${p.name} precinct. It has ${p.buildings.toLocaleString()} analysed buildings with an annual generation potential of ${fmtKwh(p.annualKwh)}. Current solar adoption sits at ${p.adoptionPct}% — leaving ${gapMw} MW (${Math.round(100 - p.adoptionPct)}%) of capacity untapped. What would you like to explore?`
  } else {
    const scoreStr = p.solarScore !== null ? ` With a solar score of ${p.solarScore}/5 (${p.solarTier}), this building has notable solar potential.` : ''
    const yieldStr = p.annualKwh ? ` Annual generation estimate: ${fmtKwh(p.annualKwh)}.` : ''
    intro = `I've found ${p.name}.${scoreStr}${yieldStr} What aspects are most relevant to your planning work?`
  }
  plannerMessages.value.push(msg('ai', intro))
  scrollChat(plannerChatBodyRef)
}

function onPlannerSearchInput() {
  clearTimeout(homeTimers.planner)
  const q = plannerBuildingQuery.value.trim()
  if (q.length < 2) {
    plannerBuildingResults.value = []
    plannerBuildingDropdownOpen.value = false
    return
  }
  homeTimers.planner = setTimeout(async () => {
    try {
      const res = await fetch(`${API_BASE}/buildings/search?q=${encodeURIComponent(q)}`)
      plannerBuildingResults.value = res.ok ? await res.json() : []
      plannerBuildingDropdownOpen.value = plannerBuildingResults.value.length > 0
    } catch { plannerBuildingResults.value = [] }
  }, 250)
}

async function selectPlannerBuildingResult(result) {
  plannerBuildingResults.value = []
  plannerBuildingDropdownOpen.value = false
  plannerBuildingQuery.value = result.address
  selectedPrecinctKey.value = ''
  plannerMessages.value = []
  plannerResult.value = null
  try {
    const [yieldData, solarData] = await Promise.all([
      fetch(`${API_BASE}/buildings/structure/${result.structure_id}/yield`).then(r => r.ok ? r.json() : null).catch(() => null),
      fetch(`${API_BASE}/buildings/structure/${result.structure_id}/solar`).then(r => r.ok ? r.json() : null).catch(() => null),
    ])
    const kwhAnnual     = yieldData?.kwh_annual ?? (solarData?.max_panels_kwh_annual ? Math.round(solarData.max_panels_kwh_annual) : null)
    const usableArea    = solarData?.max_array_area_m2 ? Math.round(solarData.max_array_area_m2 * 10) / 10 : null
    const scoreAvg      = yieldData?.solar_score_avg ?? null
    const solarScore    = (scoreAvg !== null && scoreAvg > 0) ? Math.round(scoreAvg * 10) / 10 : null
    const installCost   = usableArea ? Math.round(usableArea * 150) : null
    const annualSavings = kwhAnnual  ? Math.round(kwhAnnual * 0.25) : null
    const paybackYears  = (installCost && annualSavings > 0) ? Math.round(installCost / annualSavings * 10) / 10 : null
    const co2Tonnes     = kwhAnnual  ? Math.round(kwhAnnual * 0.727) / 1000 : null
    plannerResult.value = {
      type: 'building',
      name: result.address,
      subtitle: result.address,
      solarScore, solarTier: scoreToTier(scoreAvg),
      annualKwh: kwhAnnual, usableArea, installCost, annualSavings, paybackYears, co2Tonnes,
    }
    await triggerPlannerWelcome()
  } catch { /* ignore — result card remains null */ }
}

async function sendPlannerMessage() {
  const q = plannerChatInput.value.trim()
  if (!q || plannerTyping.value) return
  plannerChatInput.value = ''
  plannerMessages.value.push(msg('user', q))
  scrollChat(plannerChatBodyRef)
  plannerTyping.value = true
  await new Promise(r => setTimeout(r, 900 + Math.random() * 500))
  plannerTyping.value = false
  plannerMessages.value.push(msg('ai', getPlannerReply(q.toLowerCase(), plannerResult.value)))
  scrollChat(plannerChatBodyRef)
}

function plannerAsk(q) { plannerChatInput.value = q; sendPlannerMessage() }

function getPlannerReply(q, p) {
  if (p.type === 'precinct') {
    if (q.includes('untapped') || q.includes('potential') || q.includes('capacity') || q.includes('total')) {
      const untapped = ((p.potentialKw - p.installedKw) / 1000).toFixed(1)
      const unrealised = fmtKwh(p.annualKwh * (1 - p.adoptionPct / 100))
      return `${p.name} has ${(p.potentialKw / 1000).toFixed(1)} MW of total solar potential, with only ${(p.installedKw / 1000).toFixed(1)} MW currently installed — leaving ${untapped} MW untapped. That represents roughly ${unrealised} of unrealised annual generation, a significant opportunity for targeted policy intervention.`
    }
    if (q.includes('adoption') || q.includes('compare') || q.includes('other')) {
      return `${p.name}'s adoption rate of ${p.adoptionPct}% is ${p.adoptionPct > 8 ? 'above' : 'below'} the Melbourne CBD average of ~8%. View the full Precincts Map for a side-by-side comparison of all 14 precincts — ranked by annual yield, adoption rate, and untapped potential.`
    }
    if (q.includes('building type') || q.includes('roof') || q.includes('flat') || q.includes('commercial')) {
      return `In ${p.name}, commercial buildings with flat roofs represent the highest-value solar targets — they offer the largest usable area with minimal shading risk. The 3D Explore map lets you filter by roof type to identify specific high-priority sites for outreach or subsidy targeting.`
    }
    if (q.includes('economic') || q.includes('financial') || q.includes('investment') || q.includes('cost') || q.includes('roi')) {
      const totalInvest = Math.round(p.usableArea * 150)
      const annualReturn = Math.round(p.annualKwh * 0.2 * (1 - p.adoptionPct / 100))
      return `A full solar rollout across ${p.name}'s untapped rooftop area would require ~$${(totalInvest / 1_000_000).toFixed(0)}M investment (before incentives), with projected returns of $${(annualReturn / 1_000_000).toFixed(1)}M/year in energy savings. Export the full dataset from the Precincts page for use in financial modelling tools.`
    }
    return `For comprehensive planning insights on ${p.name}, the Precincts Map lets you visualise building-level scores, filter by tier and roof type, and export a full CSV dataset — the best starting point for detailed policy and investment analysis.`
  }
  // building in planner context
  if (q.includes('priority') || q.includes('policy') || q.includes('candidate')) {
    const scoreStr = p.solarScore !== null ? `a solar score of ${p.solarScore}/5` : 'unrated solar data'
    const pbStr    = p.paybackYears ? `a ${p.paybackYears}-year payback` : 'unknown payback'
    const strength = p.solarScore && p.solarScore >= 3.5 ? 'a strong' : 'a moderate'
    return `With ${scoreStr} and ${pbStr}, ${p.name} is ${strength} candidate for targeted solar incentive outreach.${p.usableArea ? ` Its ${p.usableArea.toLocaleString()} m² of usable area offers a clear installation path.` : ''}`
  }
  if (q.includes('financial') || q.includes('return') || q.includes('investment')) {
    if (p.installCost && p.annualSavings)
      return `${p.name} has an estimated install cost of $${p.installCost.toLocaleString()} with $${p.annualSavings.toLocaleString()}/year in savings${p.paybackYears ? ` — a ${p.paybackYears}-year payback` : ''}. From a policy perspective, buildings in this range are typically strong candidates for green finance or council solar rebate programs.`
    return `Financial data isn't available for this building yet. Open the Financial Analysis panel in 3D Explore for detailed calculations.`
  }
  const rankDesc = p.solarScore && p.solarScore >= 3.5 ? 'highly' : 'moderately'
  const scoreNote = p.solarScore ? ` (${p.solarScore}/5)` : ''
  return `From a planning perspective, ${p.name} ranks ${rankDesc} in solar viability${scoreNote}. For neighbourhood-level context, select a precinct from the dropdown above, or head to the Precincts Map to see how this area ranks across all Melbourne CBD precincts.`
}

// ── Stats fetch ───────────────────────────────────────────────────────────────

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
  } catch { /* keep fallback */ }
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

.hero-inner { max-width: 1240px; margin: 0 auto; width: 100%; position: relative; z-index: 1; }

.hero-content { display: flex; align-items: center; justify-content: space-between; gap: 40px; }

.hero-text {
  flex: 2; min-width: 0;
  background: rgba(var(--white-rgb),0.07);
  border: 1px solid rgba(var(--white-rgb),0.16);
  border-radius: 18px; padding: 40px 46px;
  backdrop-filter: blur(20px) saturate(1.3);
  -webkit-backdrop-filter: blur(20px) saturate(1.3);
  box-shadow: 0 6px 32px rgba(var(--black-rgb),0.22), inset 0 1px 0 rgba(var(--white-rgb),0.14);
}

.hero-eyebrow { font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: 1.4px; color: var(--city-light); margin-bottom: 16px; }
.hero-title { font-family: 'DM Serif Display', serif; font-size: 48px; line-height: 1.12; color: var(--white); margin-bottom: 18px; }
.hero-accent { color: var(--city-light); }
.hero-desc { font-size: 15px; line-height: 1.78; color: rgba(var(--white-rgb),0.84); margin-bottom: 32px; max-width: 460px; }
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
  transition: background 0.15s, color 0.15s; display: inline-block;
}
.btn-ghost:hover { background: rgba(var(--white-rgb),0.10); color: var(--white); }

.stat-grid { flex: 1.4; min-width: 0; display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.stat-card {
  background: rgba(var(--white-rgb),0.12); border: 1px solid rgba(var(--white-rgb),0.24);
  border-radius: 14px; padding: 24px 22px;
  backdrop-filter: blur(20px) saturate(1.4); -webkit-backdrop-filter: blur(20px) saturate(1.4);
  box-shadow: 0 4px 24px rgba(var(--black-rgb),0.16), inset 0 1px 0 rgba(var(--white-rgb),0.18);
  transition: background 0.2s;
}
.stat-card:hover { background: rgba(var(--white-rgb),0.18); }
.stat-val { font-family: 'DM Serif Display', serif; font-size: 30px; color: var(--white); margin-bottom: 6px; text-shadow: 0 1px 8px rgba(var(--black-rgb),0.22); }
.stat-label { font-size: 13px; color: rgba(var(--white-rgb),0.68); line-height: 1.4; }

/* ── Section system ───────────────────────────────────────── */
.seg { position: relative; overflow: hidden; }
.seg--surface { background: var(--surface); }
.seg--bg      { background: var(--bg); }
.seg--dark    { background: var(--ink); }

.seg-inner { max-width: 1240px; margin: 0 auto; padding: 96px 72px; }
.seg-inner--narrow { max-width: 900px; }
.seg-inner--center { text-align: center; }
.seg-inner--tight-top { padding-top: 32px; }

.eyebrow { font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: 1.4px; color: var(--city-light); margin-bottom: 12px; display: block; }
.eyebrow--center { text-align: center; }
.eyebrow--orange { color: var(--city-light); }

.seg-title { font-family: 'DM Serif Display', serif; font-size: 38px; line-height: 1.15; color: var(--text-primary); margin-bottom: 20px; }
.seg-title--center { text-align: center; }
.seg-title--light  { color: var(--nav-text); }

.seg-desc { font-size: 15px; line-height: 1.78; color: var(--text-secondary); margin-bottom: 28px; }

.deco-num { position: absolute; top: 40px; left: 48px; font-family: 'DM Serif Display', serif; font-size: 220px; line-height: 1; color: var(--text-primary); opacity: 0.035; pointer-events: none; user-select: none; z-index: 0; }
.deco-num--right { left: auto; right: 48px; }

.split { display: grid; grid-template-columns: 1fr 1fr; gap: 72px; align-items: center; position: relative; z-index: 1; }
.split-text { display: flex; flex-direction: column; }

.bullet-list { list-style: none; margin: 0 0 28px; padding: 0; display: flex; flex-direction: column; gap: 10px; }
.bullet-list li { font-size: 14px; color: var(--text-primary); line-height: 1.55; padding-left: 18px; position: relative; }
.bullet-list li::before { content: '→'; position: absolute; left: 0; color: var(--city-light); font-size: 13px; font-weight: 700; top: 2px; }

.text-link { display: inline-block; font-size: 14px; font-weight: 600; color: var(--city-light); text-decoration: none; border-bottom: 1.5px solid transparent; transition: border-color 0.15s; padding-bottom: 1px; }
.text-link:hover { border-color: var(--city-light); }
.text-link:focus-visible { outline: 2px solid var(--city-light); outline-offset: 3px; border-radius: 2px; }

.split-media { display: flex; align-items: center; justify-content: center; }
.split-img { width: 100%; border-radius: 16px; box-shadow: 0 24px 64px rgba(var(--black-rgb),0.14), 0 4px 16px rgba(var(--black-rgb),0.08); object-fit: cover; }

.panel-trio { margin-top: 80px; position: relative; z-index: 1; }
.panel-trio-label { font-size: 14px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.8px; color: var(--text-muted); margin-bottom: 24px; text-align: center; }
.panel-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }
.panel-item { background: var(--surface2); border-radius: 14px; padding: 28px 26px; transition: box-shadow 0.2s, transform 0.2s; }
.panel-item:hover { box-shadow: 0 8px 32px rgba(var(--black-rgb),0.09); transform: translateY(-2px); }
.panel-icon { width: 40px; height: 40px; object-fit: contain; opacity: 0.75; margin-bottom: 14px; }
.panel-title { font-family: 'DM Serif Display', serif; font-size: 18px; color: var(--text-primary); margin-bottom: 8px; }
.panel-desc { font-size: 14px; color: var(--text-secondary); line-height: 1.6; margin-bottom: 16px; }
.panel-bullets { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 7px; }
.panel-bullets li { font-size: 14px; color: var(--text-muted); padding-left: 14px; position: relative; line-height: 1.4; }
.panel-bullets li::before { content: '·'; position: absolute; left: 0; color: var(--city-light); font-weight: 700; font-size: 16px; line-height: 1.1; }

.steps-wrap { position: relative; margin-top: 56px; }
.steps-line { position: absolute; top: 12px; left: 12px; right: 12px; height: 1px; background: var(--border); }
.steps-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 40px; position: relative; }
.step { position: relative; }
.step-dot { width: 10px; height: 10px; border-radius: 50%; background: var(--city-light); margin-bottom: 28px; position: relative; z-index: 1; }
.step-num { font-family: 'DM Serif Display', serif; font-size: 52px; line-height: 1; color: var(--city-light); opacity: 0.22; margin-bottom: 14px; user-select: none; }
.step-title { font-family: 'DM Serif Display', serif; font-size: 22px; color: var(--text-primary); margin-bottom: 10px; }
.step-desc { font-size: 14px; color: var(--text-secondary); line-height: 1.72; }

.bento-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-top: 40px; }
.bento-card { background: var(--surface2); border-radius: 16px; padding: 28px 26px; transition: box-shadow 0.2s, transform 0.2s; }
.bento-card:hover { box-shadow: 0 8px 28px rgba(var(--black-rgb),0.09); transform: translateY(-2px); }
.bento-icon { width: 38px; height: 38px; object-fit: contain; opacity: 0.75; margin-bottom: 14px; }
.bento-title { font-size: 15px; font-weight: 600; color: var(--text-primary); margin-bottom: 7px; }
.bento-desc { font-size: 14px; color: var(--text-secondary); line-height: 1.65; }

.seg--dark .seg-inner { padding-top: 100px; padding-bottom: 100px; }

.cta-journey { display: flex; align-items: flex-start; justify-content: center; gap: 0; margin: 48px 0 0; flex-wrap: wrap; }
.cta-journey-step { flex: 1; min-width: 160px; max-width: 220px; display: flex; flex-direction: column; align-items: center; text-align: center; padding: 0 12px; }
.cta-journey-num { width: 40px; height: 40px; border-radius: 50%; background: var(--city-light); color: #fff; font-family: 'DM Serif Display', serif; font-size: 18px; display: flex; align-items: center; justify-content: center; margin-bottom: 14px; flex-shrink: 0; }
.cta-journey-label { font-family: 'DM Serif Display', serif; font-size: 18px; color: var(--nav-text); margin-bottom: 8px; }
.cta-journey-desc { font-size: 14px; color: var(--nav-text-muted); line-height: 1.6; }
.cta-journey-arrow { font-size: 22px; color: var(--city-light); opacity: 0.5; padding: 0 4px; margin-top: 10px; flex-shrink: 0; }

.cta-benefits { display: flex; align-items: center; justify-content: center; gap: 0; margin: 36px 0 0; flex-wrap: wrap; }
.cta-benefit { font-size: 14px; font-weight: 500; color: var(--nav-text-muted); padding: 0 20px; display: flex; align-items: center; gap: 6px; }
.cta-benefit-check { color: var(--city-light); font-weight: 700; font-size: 15px; }
.cta-benefit-divider { width: 1px; height: 16px; background: var(--ink-border); flex-shrink: 0; }

.cta-actions { display: flex; gap: 14px; justify-content: center; flex-wrap: wrap; margin-top: 36px; }
.btn-cta { padding: 14px 30px; background: var(--city-light); color: var(--white); border: none; border-radius: 8px; font-family: 'DM Sans', sans-serif; font-size: 15px; font-weight: 600; cursor: pointer; transition: background 0.15s; text-decoration: none; display: inline-block; }
.btn-cta:hover { background: var(--city-light-dim); }
.btn-cta-ghost { padding: 14px 26px; color: var(--nav-link); text-decoration: none; font-size: 15px; font-weight: 500; border: 1px solid rgba(var(--white-rgb),0.20); border-radius: 8px; transition: background 0.15s, color 0.15s; display: inline-block; }
.btn-cta-ghost:hover { background: rgba(var(--white-rgb),0.07); color: var(--nav-text); border-color: rgba(var(--white-rgb),0.38); }

/* ── Footer ───────────────────────────────────────────────── */
.home-footer { background: var(--ink); color: var(--nav-link); font-family: 'DM Sans', sans-serif; flex-shrink: 0; }
.footer-inner { display: flex; align-items: flex-start; gap: 56px; max-width: 1240px; margin: 0 auto; padding: 52px 72px 44px; flex-wrap: wrap; }
.footer-brand { display: flex; align-items: center; gap: 12px; flex: 0 0 auto; min-width: 180px; }
.footer-logo { width: 40px; height: 40px; object-fit: contain; opacity: 0.9; }
.footer-brand-name { font-family: 'DM Serif Display', serif; font-size: 16px; color: var(--nav-text); line-height: 1.2; }
.footer-brand-sub { font-size: 13px; color: var(--nav-text-muted); margin-top: 2px; }
.footer-links { display: flex; gap: 48px; flex: 1; flex-wrap: wrap; }
.footer-col-group { display: flex; flex-direction: column; gap: 32px; }
.footer-col { display: flex; flex-direction: column; gap: 10px; min-width: 140px; }
.footer-col-title { font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.8px; color: var(--city-light); margin-bottom: 2px; }
.footer-link { font-size: 14px; color: var(--nav-text-muted); line-height: 1.4; cursor: default; text-decoration: none; }
.footer-link--url { cursor: pointer; transition: color 0.15s; }
.footer-link--url:hover { color: var(--accent-warm); text-decoration: underline; }
.footer-link--eportfolio { display: inline-block; margin-top: 6px; color: var(--city-light); font-weight: 600; font-size: 14px; }
.footer-link--eportfolio:hover { color: var(--city-light-dim); text-decoration: underline; }

/* ════════════════════════════════════════════════════════════
   AI JOURNEY SECTION
   ════════════════════════════════════════════════════════════ */

.journey-seg { padding-top: 80px; padding-bottom: 24px; }

.journey-intro { text-align: center; margin-bottom: 48px; }

.journey-sub {
  font-size: 16px; color: var(--text-secondary); line-height: 1.6;
  max-width: 480px; margin: 0 auto; margin-top: 8px;
}

/* ── Identity cards ───────────────────────────────────────── */
.identity-row {
  display: grid; grid-template-columns: 1fr 1fr;
  gap: 20px; max-width: 740px; margin: 0 auto 48px;
}

.identity-card {
  background: var(--surface-white);
  border: 2px solid var(--border);
  border-radius: 18px;
  padding: 34px 30px;
  cursor: pointer; text-align: left;
  font-family: 'DM Sans', sans-serif;
  transition: border-color 0.2s, box-shadow 0.2s, transform 0.15s;
  display: flex; flex-direction: column; gap: 12px;
}

.identity-card:hover {
  border-color: var(--city-light);
  box-shadow: 0 8px 32px rgba(var(--city-light-rgb), 0.12);
  transform: translateY(-2px);
}

.identity-card--active {
  border-color: var(--city-light);
  background: rgba(var(--city-light-rgb), 0.03);
  box-shadow: 0 0 0 1px var(--city-light), 0 8px 32px rgba(var(--city-light-rgb), 0.12);
}

.identity-icon {
  width: 52px; height: 52px;
  background: rgba(var(--city-light-rgb), 0.1);
  border-radius: 14px;
  display: flex; align-items: center; justify-content: center;
  color: var(--city-light);
}
.identity-icon svg { width: 26px; height: 26px; }

.identity-name { font-family: 'DM Serif Display', serif; font-size: 22px; color: var(--text-primary); }

.identity-desc-text { font-size: 14px; color: var(--text-secondary); line-height: 1.6; }

.identity-tags { display: flex; flex-wrap: wrap; gap: 6px; }

.identity-tag {
  font-size: 11.5px; font-weight: 600;
  color: var(--text-muted);
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: 20px; padding: 3px 10px;
}

.identity-card--active .identity-tag {
  background: rgba(var(--city-light-rgb), 0.08);
  border-color: rgba(var(--city-light-rgb), 0.3);
  color: var(--city-light);
}

.identity-cta { font-size: 14px; font-weight: 600; color: var(--city-light); margin-top: 4px; }

/* ── Journey flow panel ───────────────────────────────────── */
.journey-flow {
  background: var(--surface-white);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 40px 40px 36px;
  box-shadow: var(--shadow-card);
}

/* ── Step bar ─────────────────────────────────────────────── */
.step-bar {
  display: flex; align-items: center;
  margin-bottom: 36px;
}

.step-bar-item {
  display: flex; flex-direction: column; align-items: center; gap: 6px;
  opacity: 0.35; transition: opacity 0.3s;
  min-width: 100px;
}
.step-bar-item--active { opacity: 1; }
.step-bar-item--done   { opacity: 0.9; }

.step-bar-dot {
  width: 32px; height: 32px; border-radius: 50%;
  background: var(--surface2); border: 2px solid var(--border);
  display: flex; align-items: center; justify-content: center;
  font-size: 13px; font-weight: 700; color: var(--text-muted);
  transition: background 0.3s, border-color 0.3s, color 0.3s;
}
.step-bar-item--active .step-bar-dot {
  background: var(--city-light); border-color: var(--city-light); color: white;
}
.step-bar-item--done .step-bar-dot {
  background: #5a9060; border-color: #5a9060; color: white;
}

.step-bar-label {
  font-size: 12px; font-weight: 600; color: var(--text-secondary);
  text-align: center; white-space: nowrap;
}

.step-bar-line {
  flex: 1; height: 2px; background: var(--border); margin-bottom: 22px;
}

/* ── Search area ──────────────────────────────────────────── */
.search-area { margin-bottom: 28px; }

.search-field-wrap {
  display: flex; align-items: center;
  background: var(--input-bg);
  border: 1.5px solid var(--border);
  border-radius: 10px;
  padding: 0 8px 0 14px;
  transition: border-color 0.2s;
  gap: 8px;
}
.search-field-wrap:focus-within {
  border-color: var(--city-light);
  background: var(--surface-white);
}

.search-field-icon { width: 18px; height: 18px; color: var(--text-muted); flex-shrink: 0; }

.search-field {
  flex: 1; border: none; background: transparent;
  font-size: 15px; font-family: 'DM Sans', sans-serif;
  color: var(--text-primary); padding: 13px 0; outline: none;
}
.search-field::placeholder { color: var(--text-muted); }

.search-go-btn {
  padding: 8px 20px;
  background: var(--city-light); color: white;
  border: none; border-radius: 7px;
  font-family: 'DM Sans', sans-serif; font-size: 14px; font-weight: 600;
  cursor: pointer; flex-shrink: 0; transition: background 0.15s;
}
.search-go-btn:hover:not(:disabled) { background: var(--city-light-dim); }
.search-go-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.search-not-found {
  margin-top: 10px; font-size: 13.5px; color: var(--text-secondary);
  display: flex; flex-direction: column; gap: 6px;
}

.search-hint-row {
  margin-top: 8px; font-size: 13px; color: var(--text-muted);
  display: flex; align-items: center; flex-wrap: wrap; gap: 6px;
}

.search-sample-row {
  display: flex; align-items: center; flex-wrap: wrap; gap: 6px;
}

.sample-chip {
  background: var(--surface2); border: 1px solid var(--border);
  border-radius: 6px; padding: 4px 11px;
  font-size: 13px; color: var(--text-primary);
  cursor: pointer; font-family: 'DM Sans', sans-serif;
  transition: background 0.15s, border-color 0.15s, color 0.15s;
}
.sample-chip:hover {
  background: rgba(var(--city-light-rgb), 0.08);
  border-color: var(--city-light); color: var(--city-light);
}

/* ── Autocomplete search dropdown ─────────────────────────── */
.search-dropdown {
  position: absolute; top: calc(100% + 4px); left: 0; right: 0;
  background: var(--surface-white); border: 1.5px solid var(--city-light);
  border-radius: 10px; box-shadow: 0 8px 24px rgba(var(--black-rgb),0.12);
  z-index: 100; overflow: hidden; max-height: 240px; overflow-y: auto;
}

.search-dropdown-item {
  display: flex; align-items: center; gap: 8px;
  width: 100%; padding: 10px 14px;
  font-size: 14px; font-family: 'DM Sans', sans-serif;
  color: var(--text-primary); background: transparent;
  border: none; cursor: pointer; text-align: left;
  transition: background 0.12s;
}
.search-dropdown-item:hover { background: rgba(var(--city-light-rgb), 0.07); }
.search-dropdown-item + .search-dropdown-item { border-top: 1px solid var(--border); }

/* ── Search loading spinner ───────────────────────────────── */
.search-spinner {
  width: 16px; height: 16px; flex-shrink: 0;
  border: 2px solid var(--border);
  border-top-color: var(--city-light);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

/* ── No-data badge ────────────────────────────────────────── */
.solar-score-badge--no-data {
  background: rgba(var(--black-rgb), 0.05);
  color: var(--text-muted);
}

/* ── Precinct rank badge ──────────────────────────────────── */
.rank-badge {
  flex-shrink: 0; border-radius: 10px; padding: 10px 13px;
  text-align: center; min-width: 68px;
  background: rgba(var(--city-light-rgb), 0.10);
  color: var(--city-light);
}
.rank-badge-num  { font-family: 'DM Serif Display', serif; font-size: 22px; line-height: 1; }
.rank-badge-of   { font-size: 11px; opacity: 0.7; }
.rank-badge-tier { font-size: 10.5px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.4px; margin-top: 4px; }

/* ── Results: building card + AI chat ─────────────────────── */
.results-layout {
  display: flex; flex-direction: column;
  gap: 24px; margin-bottom: 28px;
}

/* ── Building / precinct data card ───────────────────────── */
.bdata-card {
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 14px; overflow: hidden;
}

.bdata-header {
  display: flex; justify-content: space-between; align-items: flex-start;
  padding: 22px 22px 16px; gap: 14px;
}

.bdata-header-info { flex: 1; min-width: 0; }

.bdata-name {
  font-family: 'DM Serif Display', serif; font-size: 17px;
  color: var(--text-primary); margin-bottom: 4px; line-height: 1.3;
}

.bdata-address { font-size: 12.5px; color: var(--text-muted); line-height: 1.4; margin-bottom: 8px; }

.bdata-tags { display: flex; flex-wrap: wrap; gap: 5px; }
.bdata-tag { font-size: 11px; font-weight: 600; color: var(--text-muted); background: var(--surface-white); border: 1px solid var(--border); border-radius: 4px; padding: 2px 7px; }

/* Solar score badge */
.solar-score-badge {
  flex-shrink: 0; border-radius: 10px; padding: 10px 13px;
  text-align: center; min-width: 68px;
}
.solar-score-badge--very-high { background: rgba(10,46,31,0.10); color: #0a4a28; }
.solar-score-badge--high      { background: rgba(90,144,96,0.12); color: #3a7a40; }
.solar-score-badge--med       { background: rgba(160,180,80,0.14); color: #6a7e20; }
.solar-score-badge--low       { background: rgba(220,100,80,0.12); color: #b04030; }
.solar-score-badge--very-low  { background: rgba(232,16,64,0.10); color: #c00030; }

.solar-score-num { font-family: 'DM Serif Display', serif; font-size: 26px; line-height: 1; }
.solar-score-denom { font-size: 11px; opacity: 0.6; }
.solar-score-tier { font-size: 10.5px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.4px; margin-top: 4px; }

/* Score bar */
.bdata-score-bar-track {
  margin: 0 22px 0; height: 5px; background: var(--border); border-radius: 3px; overflow: hidden;
}
.bdata-score-bar-fill { height: 100%; border-radius: 3px; transition: width 0.6s ease; }
.score-fill--very-high { background: #2a7a40; }
.score-fill--high      { background: #5a9060; }
.score-fill--med       { background: #a0b040; }
.score-fill--low       { background: #d07050; }
.score-fill--very-low  { background: #e81040; }

.bdata-divider { height: 1px; background: var(--border); margin: 14px 22px 0; }

.bdata-metrics {
  display: grid; grid-template-columns: repeat(4, 1fr);
  padding: 16px 22px 18px; gap: 12px 8px;
}

.bdata-metric-val { font-size: 14px; font-weight: 700; color: var(--text-primary); margin-bottom: 2px; }
.bdata-metric-label { font-size: 11px; color: var(--text-muted); line-height: 1.3; }

.bdata-footer-note {
  display: flex; align-items: flex-start; gap: 6px;
  font-size: 11.5px; color: var(--text-muted);
  padding: 10px 22px 16px; line-height: 1.4;
  border-top: 1px solid var(--border); margin-top: 4px;
}

/* ── Adoption gap bar (city planner) ──────────────────────── */
.adoption-gap { padding: 14px 22px 18px; border-top: 1px solid var(--border); }
.adoption-gap-header { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 8px; }
.adoption-gap-title { font-size: 12px; font-weight: 700; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.6px; }
.adoption-gap-pct { font-size: 12px; color: var(--text-muted); }

.adoption-bar-track { height: 8px; background: var(--border); border-radius: 4px; position: relative; overflow: hidden; }
.adoption-bar-installed { position: absolute; left: 0; top: 0; height: 100%; background: #5a9060; border-radius: 4px 0 0 4px; }
.adoption-bar-potential { position: absolute; top: 0; height: 100%; background: rgba(90, 144, 96, 0.28); }

.adoption-legend { display: flex; gap: 16px; margin-top: 8px; font-size: 11.5px; color: var(--text-muted); flex-wrap: wrap; }
.legend-dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 4px; }
.legend-dot--installed { background: #5a9060; }
.legend-dot--potential { background: rgba(90, 144, 96, 0.5); }

/* ── AI Chat panel ────────────────────────────────────────── */
.ai-chat-panel {
  background: var(--surface-white);
  border: 1px solid var(--border);
  border-radius: 14px;
  display: flex; flex-direction: column;
  overflow: hidden; max-height: 460px;
}

.ai-chat-head {
  display: flex; align-items: center; gap: 10px;
  padding: 14px 18px;
  border-bottom: 1px solid var(--border);
  background: rgba(var(--city-light-rgb), 0.04);
  flex-shrink: 0;
}

.ai-spark { font-size: 20px; color: var(--city-light); flex-shrink: 0; }

.ai-chat-head-text { flex: 1; min-width: 0; }
.ai-chat-title { font-size: 13.5px; font-weight: 700; color: var(--text-primary); }
.ai-chat-sub { font-size: 11.5px; color: var(--text-muted); }

.ai-coming-soon-pill {
  font-size: 10.5px; font-weight: 700;
  background: rgba(var(--city-light-rgb), 0.12);
  color: var(--city-light);
  border-radius: 20px; padding: 3px 9px;
  text-transform: uppercase; letter-spacing: 0.4px;
  flex-shrink: 0;
}

.ai-chat-body {
  flex: 1; overflow-y: auto;
  padding: 14px 16px;
  display: flex; flex-direction: column; gap: 10px;
  min-height: 140px;
}

.ai-msg { display: flex; }
.ai-msg--user { justify-content: flex-end; }
.ai-msg--ai   { justify-content: flex-start; }

.ai-msg-bubble {
  max-width: 88%; font-size: 13.5px; line-height: 1.62;
  padding: 9px 13px; border-radius: 12px;
}
.ai-msg--user .ai-msg-bubble { background: var(--city-light); color: white; border-radius: 12px 12px 2px 12px; }
.ai-msg--ai   .ai-msg-bubble { background: var(--surface2); color: var(--text-primary); border-radius: 12px 12px 12px 2px; }

/* Typing indicator */
.ai-msg-typing { display: flex; align-items: center; gap: 4px; padding: 12px 16px; }
.ai-msg-typing span { width: 7px; height: 7px; background: var(--text-muted); border-radius: 50%; animation: typing-bounce 1.2s infinite ease-in-out; }
.ai-msg-typing span:nth-child(2) { animation-delay: 0.2s; }
.ai-msg-typing span:nth-child(3) { animation-delay: 0.4s; }

@keyframes typing-bounce {
  0%, 60%, 100% { transform: translateY(0); }
  30%            { transform: translateY(-6px); }
}

/* Suggested questions */
.ai-suggestions { padding: 8px 14px 0; display: flex; flex-wrap: wrap; gap: 6px; flex-shrink: 0; }

.ai-suggest-chip {
  background: var(--surface2); border: 1px solid var(--border);
  border-radius: 20px; padding: 5px 11px;
  font-size: 12px; font-family: 'DM Sans', sans-serif;
  color: var(--text-secondary); cursor: pointer;
  transition: background 0.15s, border-color 0.15s, color 0.15s;
}
.ai-suggest-chip:hover {
  background: rgba(var(--city-light-rgb), 0.08);
  border-color: var(--city-light); color: var(--city-light);
}

/* Chat input */
.ai-input-row {
  display: flex; gap: 7px;
  padding: 10px 14px;
  border-top: 1px solid var(--border);
  background: var(--surface-white);
  flex-shrink: 0;
}

.ai-text-input {
  flex: 1; border: 1.5px solid var(--border); border-radius: 8px;
  padding: 8px 13px; font-size: 13.5px;
  font-family: 'DM Sans', sans-serif; color: var(--text-primary);
  background: var(--input-bg); outline: none; transition: border-color 0.2s;
}
.ai-text-input:focus { border-color: var(--city-light); background: var(--surface-white); }
.ai-text-input:disabled { opacity: 0.6; }

.ai-send-btn {
  padding: 8px 16px; background: var(--city-light); color: white;
  border: none; border-radius: 8px;
  font-size: 13px; font-weight: 600; font-family: 'DM Sans', sans-serif;
  cursor: pointer; transition: background 0.15s; flex-shrink: 0;
}
.ai-send-btn:hover:not(:disabled) { background: var(--city-light-dim); }
.ai-send-btn:disabled { opacity: 0.45; cursor: not-allowed; }

/* ── Explore jump CTAs (property owner) ───────────────────── */
.explore-jump { margin-top: 4px; }

.explore-jump-label {
  font-size: 13.5px; color: var(--text-muted);
  text-align: center; margin-bottom: 14px;
}

.explore-jump-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }

.explore-jump-card {
  background: var(--bg); border: 1.5px solid var(--border);
  border-radius: 13px; padding: 18px 16px;
  cursor: pointer; text-align: left; font-family: 'DM Sans', sans-serif;
  transition: border-color 0.2s, box-shadow 0.2s, transform 0.15s;
  display: flex; flex-direction: column; gap: 5px;
}
.explore-jump-card:hover {
  border-color: var(--city-light);
  box-shadow: 0 6px 24px rgba(var(--city-light-rgb), 0.1);
  transform: translateY(-2px);
}

.explore-jump-icon { width: 30px; height: 30px; object-fit: contain; opacity: 0.8; margin-bottom: 4px; }
.explore-jump-name { font-size: 13.5px; font-weight: 700; color: var(--text-primary); }
.explore-jump-desc { font-size: 12px; color: var(--text-muted); line-height: 1.4; }
.explore-jump-link { font-size: 12.5px; font-weight: 600; color: var(--city-light); margin-top: auto; padding-top: 8px; }

/* ── City planner controls ────────────────────────────────── */
.planner-controls {
  display: flex; align-items: flex-end; gap: 18px;
  margin-bottom: 28px; flex-wrap: wrap;
}

.planner-ctrl-group { flex: 1; min-width: 220px; display: flex; flex-direction: column; gap: 7px; }
.planner-ctrl-label { font-size: 12.5px; font-weight: 600; color: var(--text-secondary); }

.select-wrap { position: relative; }

.precinct-dropdown {
  width: 100%; padding: 12px 40px 12px 14px;
  border: 1.5px solid var(--border); border-radius: 10px;
  font-size: 15px; font-family: 'DM Sans', sans-serif;
  color: var(--text-primary); background: var(--input-bg);
  cursor: pointer; outline: none; appearance: none;
  transition: border-color 0.2s;
}
.precinct-dropdown:focus { border-color: var(--city-light); background: var(--surface-white); }

.select-chevron {
  position: absolute; right: 12px; top: 50%; transform: translateY(-50%);
  width: 16px; height: 16px; color: var(--text-muted); pointer-events: none;
}

.planner-or-divider {
  font-size: 13px; color: var(--text-muted); font-weight: 600;
  padding-bottom: 12px; flex-shrink: 0;
}

/* ── Precinct CTA ─────────────────────────────────────────── */
.precinct-explore-cta { margin-top: 8px; text-align: center; }

.precinct-cta-row { display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; margin-top: 14px; }

.btn-ghost-outline {
  padding: 12px 22px; color: var(--text-secondary);
  font-size: 14px; font-weight: 500; font-family: 'DM Sans', sans-serif;
  border: 1.5px solid var(--border); border-radius: 8px;
  background: transparent; cursor: pointer;
  transition: border-color 0.15s, color 0.15s, background 0.15s;
}
.btn-ghost-outline:hover { border-color: var(--city-light); color: var(--city-light); background: rgba(var(--city-light-rgb), 0.04); }

/* ── Transitions ──────────────────────────────────────────── */
.fade-slide-enter-active,
.fade-slide-leave-active { transition: all 0.32s ease; }
.fade-slide-enter-from,
.fade-slide-leave-to { opacity: 0; transform: translateY(14px); }

.fade-enter-active,
.fade-leave-active { transition: opacity 0.28s ease; }
.fade-enter-from,
.fade-leave-to { opacity: 0; }

/* ── Responsive ───────────────────────────────────────────── */
@media (max-width: 1024px) {
  .seg-inner { padding: 72px 48px; }
  .hero { padding: 80px 48px 120px; }
  .bdata-metrics { grid-template-columns: repeat(2, 1fr); }
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

  .identity-row { grid-template-columns: 1fr; max-width: 420px; }
  .results-layout { grid-template-columns: 1fr; }
  .ai-chat-panel { max-height: 360px; }
  .explore-jump-row { grid-template-columns: 1fr 1fr; }
  .planner-controls { flex-direction: column; }
  .planner-or-divider { padding-bottom: 0; text-align: center; }
  .journey-flow { padding: 28px 22px 24px; }
}

@media (max-width: 600px) {
  .hero-title { font-size: 28px; }
  .stat-grid { grid-template-columns: 1fr 1fr; }
  .bento-grid { grid-template-columns: 1fr; }
  .footer-inner { flex-direction: column; gap: 28px; }
  .footer-links { flex-direction: column; gap: 20px; }
  .explore-jump-row { grid-template-columns: 1fr; }
  .bdata-metrics { grid-template-columns: 1fr 1fr; }
  .step-bar-item { min-width: 60px; }
  .step-bar-label { font-size: 11px; }
}

@media (max-width: 480px) {
  .hero { padding: 40px 16px 48px; }
  .hero-text { padding: 22px 18px; }
  .hero-title { font-size: 24px; }
  .hero-desc { font-size: 14px; margin-bottom: 24px; }
  .stat-val { font-size: 24px; }
  .seg-inner { padding: 44px 16px; }
  .seg-title { font-size: 26px; }
  .cta-journey { flex-direction: column; gap: 16px; align-items: center; }
  .cta-journey-step { min-width: unset; width: 100%; max-width: 280px; text-align: center; }
  .cta-journey-arrow { transform: rotate(90deg); align-self: center; }
  .cta-benefits { flex-direction: column; gap: 10px; align-items: center; }
  .cta-benefit-divider { display: none; }
  .journey-flow { padding: 20px 16px 18px; }
  .step-bar { gap: 0; }
}
</style>
