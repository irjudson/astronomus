import { createRouter, createWebHistory } from 'vue-router'

export const routes = [
  {
    path: '/',
    name: 'home',
    component: () => import('@/views/HomeView.vue')
  },
  {
    path: '/catalog',
    name: 'catalog',
    component: () => import('@/views/CatalogView.vue')
  },
  {
    path: '/plan',
    name: 'plan',
    component: () => import('@/views/PlanView.vue')
  },
  {
    path: '/execute',
    name: 'execute',
    component: () => import('@/views/ExecuteView.vue')
  },
  {
    path: '/process',
    name: 'process',
    component: () => import('@/views/ProcessView.vue')
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

export default router
