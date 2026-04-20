import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import PasswordView from '../views/PasswordView.vue'
import ExploreView from '../views/ExploreView.vue'
import FeaturePlaceholderView from '../views/FeaturePlaceholderView.vue'

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
      component: FeaturePlaceholderView,
      props: {
        title: 'Precincts',
        description: 'This section will group buildings into analysis precincts for easier planning and reporting.',
      },
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

function setAuthenticated(value) {
  isAuthenticated = value
  sessionStorage.setItem('auth', value ? 'true' : 'false')
}

function logout() {
  isAuthenticated = false
  sessionStorage.removeItem('auth')
}
export { setAuthenticated }
export default router