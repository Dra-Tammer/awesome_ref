import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('../components/LoginPage.vue'),
    meta: { requiresGuest: true },
  },
  {
    path: '/',
    component: () => import('../layouts/AppLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        redirect: '/references',
      },
      {
        path: 'references',
        name: 'references',
        component: () => import('../layouts/ReferencesLayout.vue'),
      },
      {
        path: 'notes',
        name: 'notes',
        component: () => import('../layouts/NotesLayout.vue'),
      },
      {
        path: 'daily-tasks',
        name: 'daily-tasks',
        component: () => import('../components/DailyTasksPage.vue'),
      },
      {
        path: 'profile',
        name: 'profile',
        component: () => import('../components/ProfilePage.vue'),
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  // Only guard logged-in users from visiting login page
  // Auth check for protected routes is handled in App.vue after session restoration
  if (to.meta.requiresGuest && auth.logged) {
    return { name: 'references' }
  }
})

export default router
