import { ref } from 'vue'

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

// Mutable timer handles — plain object, not reactive
export const homeTimers = { owner: null, planner: null }
