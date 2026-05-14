import { ref, watch } from 'vue'

const CHAT_STORAGE_KEY = 'homeJourney.chatHistory.v1'

// ── Module-level singleton state ─────────────────────────────────────────────
// Defined outside any function so it survives component unmount / navigation.

export const identity             = ref(null)   // 'owner' | 'planner'

// Property owner
export const ownerAddressQuery    = ref('')
export const ownerSearchLoading   = ref(false)
export const ownerSearchError     = ref(null)
export const ownerBuilding        = ref(null)
export const ownerMessages        = ref([])
export const ownerChatInput       = ref('')
export const ownerTyping          = ref(false)
export const ownerSearchResults   = ref([])
export const ownerDropdownOpen    = ref(false)

// City planner
export const selectedPrecinctKey          = ref('')
export const plannerBuildingQuery         = ref('')
export const plannerResult                = ref(null)
export const plannerMessages              = ref([])
export const plannerChatInput             = ref('')
export const plannerTyping                = ref(false)
export const plannerBuildingResults       = ref([])
export const plannerBuildingDropdownOpen  = ref(false)

// Precinct list (shared, loaded once)
export const precinctListData     = ref([])
export const precinctListLoading  = ref(false)

// Step progress for owner journey
export const ownerStep2Done = ref(false)   // true after user engages with AI insights
export const ownerStep3Done = ref(false)   // true after user opens 3D Explore

// Step progress for planner journey
export const plannerStep2Done = ref(false) // true after user engages with AI chat or data
export const plannerStep3Done = ref(false) // true after user navigates to suburb map or explore

// Mutable timer handles — plain object, not reactive
export const homeTimers = { owner: null, planner: null }

function canUseLocalStorage() {
  return typeof window !== 'undefined' && typeof window.localStorage !== 'undefined'
}

export function loadHomeChatHistory() {
  if (!canUseLocalStorage()) return
  try {
    const raw = window.localStorage.getItem(CHAT_STORAGE_KEY)
    if (!raw) return
    const parsed = JSON.parse(raw)
    if (Array.isArray(parsed.ownerMessages)) ownerMessages.value = parsed.ownerMessages
    if (Array.isArray(parsed.plannerMessages)) plannerMessages.value = parsed.plannerMessages
  } catch {
    window.localStorage.removeItem(CHAT_STORAGE_KEY)
  }
}

export function clearHomeChatHistory() {
  ownerMessages.value = []
  ownerChatInput.value = ''
  ownerTyping.value = false
  plannerMessages.value = []
  plannerChatInput.value = ''
  plannerTyping.value = false

  if (canUseLocalStorage()) {
    window.localStorage.removeItem(CHAT_STORAGE_KEY)
  }
}

function persistHomeChatHistory() {
  if (!canUseLocalStorage()) return
  const payload = {
    ownerMessages: ownerMessages.value,
    plannerMessages: plannerMessages.value,
  }
  try {
    window.localStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify(payload))
  } catch {
    // Chat history is a convenience cache only; the app can continue without it.
  }
}

watch([ownerMessages, plannerMessages], persistHomeChatHistory, { deep: true })
