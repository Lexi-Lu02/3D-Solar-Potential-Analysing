// ─────────────────────────────────────────────────────────────────────────────
// router/index.js — Controls which page (Vue component) is displayed based on
// the URL in the browser's address bar.
//
// Example: when the user visits  /explore  → show ExploreView.vue
//          when the user visits  /login    → show PasswordView.vue
//
// It also acts as a security gate: protected pages redirect to /login if the
// user hasn't entered the correct password yet.
// ─────────────────────────────────────────────────────────────────────────────

// These two functions come from the vue-router library.
// createRouter   → builds the router object
// createWebHistory → uses clean URLs like /explore instead of /#/explore
import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import PasswordView from '../views/PasswordView.vue'
import ExploreView from '../views/ExploreView.vue'
import PrecinctsView from '../views/PrecinctsView.vue'
import InsightsView from '../views/InsightsView.vue'



// ── Authentication state ──────────────────────────────────────────────────────
//
// sessionStorage is the browser's short-term memory.
// It stores data only for the current browser tab — closing the tab wipes it.
// We use it to remember that the user already entered the correct password.
//
// 'auth' === 'true' means the user is logged in.
let isAuthenticated = sessionStorage.getItem('auth') === 'true'

// ── Route definitions ─────────────────────────────────────────────────────────
//
// Each object in the `routes` array describes one page:
//   path      → the URL (e.g. '/explore')
//   name      → a short nickname used in code (e.g. router.push({ name: 'home' }))
//   component → which Vue file to show
//   meta      → extra information (here: whether the page requires login)
//   props     → static data passed to the component (used by FeaturePlaceholderView)
const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      // Login page — shown to unauthenticated users and anyone who visits /login directly.
      path: '/login',
      name: 'login',
      component: PasswordView,
    },
    {
      // Landing / marketing page shown after login.
      path: '/',
      name: 'home',
      component: HomeView,
      meta: { requiresAuth: true }, // user must be logged in to see this page
    },
    {
      // Interactive 3D building map with solar analysis sidebar.
      path: '/explore',
      name: 'explore',
      component: ExploreView,
      meta: { requiresAuth: true },
    },
    {
      // Precinct-level solar rankings and comparison map.
      path: '/precincts',
      name: 'precincts',
      component: PrecinctsView,
      meta: { requiresAuth: true },
    },
    {
      // AI Insights page — plain-English Q&A interface over solar data.
      path: '/insights',
      name: 'insights',
      component: InsightsView,
      meta: { requiresAuth: true },
    },
    { 
      path: '/:pathMatch(.*)*',
      redirect: '/',
    },
  ],
})

// ── Navigation guard ──────────────────────────────────────────────────────────
//
// `beforeEach` is a function that runs BEFORE every page navigation.
// It acts like a security checkpoint:
//
//   • If the target page needs auth AND the user is NOT logged in
//     → redirect to /login and save the original URL as ?redirect=...
//       so the user lands back on the right page after logging in.
//
//   • If the user is already logged in and tries to visit /login again
//     → skip the login page and go straight home (or their redirect target).
//
//   • Otherwise → allow the navigation to proceed normally.
router.beforeEach((to) => {
  // Check if this page requires login AND the user hasn't logged in yet.
  if (to.meta.requiresAuth && sessionStorage.getItem('auth') !== 'true') {
    return {
      path: '/login',
      query: {
        redirect: to.fullPath, // save where the user was trying to go
      },
    }
  }

  // If the user is already logged in and visits /login, send them home.
  if (to.path === '/login' && isAuthenticated) {
    return to.query.redirect || '/'
  }

  // Allow the navigation.
  return true
})

// ── Called by PasswordView after successful login ─────────────────────────────
//
// This updates both the in-memory flag (for the current session) and
// sessionStorage (so the flag survives a page refresh within the same tab).
function setAuthenticated(value) {
  isAuthenticated = value
  sessionStorage.setItem('auth', value ? 'true' : 'false')
}

// Clears the login state — exported so a future logout button can call it.
function logout() {
  isAuthenticated = false
  sessionStorage.removeItem('auth')
}

// Export setAuthenticated so PasswordView can call it after a correct password.
export { setAuthenticated }

// Export the router so main.js can install it into the Vue app.
export default router
