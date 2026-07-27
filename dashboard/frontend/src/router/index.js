/**
 * Vue Router Configuration
 */

import { createRouter, createWebHistory } from 'vue-router'
import { useRoleStore, useNavStore } from '../stores/index.js'

const REVIEWER_ALLOWED_ROUTES = new Set(['today', 'inbox', 'insight'])
const PUBLIC_ROUTES = new Set(['ask', 'today'])

function getStore(storeFn) {
  try {
    return storeFn()
  } catch {
    return null
  }
}

const routes = [
  {
    path: '/',
    redirect: '/today',
  },
  {
    path: '/today',
    name: 'today',
    component: () => import('../pages/TodayPage.vue'),
  },
  {
    path: '/ask',
    name: 'ask',
    component: () => import('../pages/AskPage.vue'),
  },
  {
    path: '/write',
    redirect: '/creator',
  },
  {
    path: '/creator',
    name: 'creator',
    component: () => import('../pages/CreatorPage.vue'),
  },
  {
    path: '/library',
    name: 'library',
    component: () => import('../pages/LibraryPage.vue'),
  },
  {
    path: '/more',
    name: 'more',
    component: () => import('../pages/MorePage.vue'),
  },
  {
    path: '/produce',
    name: 'produce',
    component: () => import('../pages/ProducePage.vue'),
  },
  {
    path: '/inbox',
    name: 'inbox',
    component: () => import('../pages/InboxPage.vue'),
  },
  {
    path: '/insight',
    name: 'insight',
    component: () => import('../pages/InsightPage.vue'),
  },
  {
    path: '/cascade-runs',
    name: 'cascade-runs',
    component: () => import('../pages/CascadeRunsPage.vue'),
  },
  {
    path: '/settings',
    name: 'settings',
    component: () => import('../pages/SettingsPage.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const roleStore = getStore(useRoleStore)
  const navStore = getStore(useNavStore)

  if (roleStore) {
    roleStore.checkUrlRole()
  }

  if (roleStore?.isReviewer) {
    if (REVIEWER_ALLOWED_ROUTES.has(to.name)) {
      next()
    } else {
      next({ name: 'inbox' })
    }
    return
  }

  if (navStore) {
    navStore.navigateTo(to.name || 'ask')
  }

  next()
})

router.afterEach((to) => {
  const navStore = getStore(useNavStore)
  if (navStore && typeof window !== 'undefined' && typeof navStore.syncNavUrl === 'function') {
    navStore.syncNavUrl()
  }
})

export default router