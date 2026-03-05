import { createRouter, createWebHistory } from 'vue-router'
import DiscoveryView from '@/views/DiscoveryView.vue'

export const routes = [
  {
    path: '/',
    name: 'discovery', // Renamed from 'home' to 'discovery'
    component: DiscoveryView // Use DiscoveryView for the main discovery page
  },
  {
    path: '/plan',
    name: 'plan',
    component: () => import('@/views/PlanningView.vue')
  },
  {
    path: '/execute',
    name: 'execute',
    component: () => import('@/views/ExecutionView.vue')
  },
  {
    path: '/process',
    name: 'process',
    component: () => import('@/views/ProcessingView.vue')
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

export default router
