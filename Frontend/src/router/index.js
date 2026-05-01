// Router — maps URL paths to page components and enforces the password gate.
import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import PasswordView from '../views/PasswordView.vue'
import ExploreView from '../views/ExploreView.vue'
import PrecinctsView from '../views/PrecinctsView.vue'
import FeaturePlaceholderView from '../views/FeaturePlaceholderView.vue'

// sessionStorage persists auth for the current browser tab only — closing the tab logs you out.
let isAuthenticated = sessionStorage.getItem('auth') === 'true'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: PasswordView,
    },
    {
      path: '/',
      name: 'home',
      component: HomeView,
      meta: { requiresAuth: true },
    },
    {
      path: '/explore',
      name: 'explore',
      component: ExploreView,
      meta: { requiresAuth: true },
    },
    {
      path: '/precincts',
      name: 'precincts',
      component: PrecinctsView,
      meta: { requiresAuth: true },
    },
    {
      path: '/insights',
      name: 'insights',
      component: FeaturePlaceholderView,
      props: {
        title: 'AI Insights',
        description: 'This section will surface explainable AI recommendations from building-level and precinct-level data.',
      },
      meta: { requiresAuth: true },
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/',
    },
  ],
})

// Auth guard — runs before every navigation.
// Unauthenticated users trying to reach a protected page are redirected to /login.
// The original URL is saved in ?redirect so they land back there after logging in.
// Already-logged-in users hitting /login are bounced straight to home (or their redirect target).
router.beforeEach((to) => {
  if (to.meta.requiresAuth && sessionStorage.getItem('auth') !== 'true') {
    return {
      path: '/login',
      query: {
        redirect: to.fullPath,
      },
    }
  }

  if (to.path === '/login' && isAuthenticated) {
    return to.query.redirect || '/'
  }

  return true
})

// Called by PasswordView after a successful login — sets the in-memory flag and writes to sessionStorage.
function setAuthenticated(value) {
  isAuthenticated = value
  sessionStorage.setItem('auth', value ? 'true' : 'false')
}

// logout is exported so it can be wired to a logout button if one is added later.
function logout() {
  isAuthenticated = false
  sessionStorage.removeItem('auth')
}
export { setAuthenticated }
export default router