import { createRouter, createWebHistory } from 'vue-router'
import TonightView from '@/views/TonightView.vue'

export const routes = [
  {
    path: '/',
    name: 'tonight',
    component: TonightView
  },
  {
    path: '/sky',
    name: 'sky',
    component: () => import('@/views/DiscoveryView.vue')
  },
  {
    path: '/plan',
    name: 'plan',
    component: () => import('@/views/PlanningView.vue')
  },
  {
    path: '/observe',
    name: 'observe',
    component: () => import('@/views/ExecutionView.vue')
  },
  {
    path: '/archive',
    name: 'archive',
    component: () => import('@/views/ProcessingView.vue')
  },
  { path: '/execute', redirect: '/observe' },
  { path: '/process', redirect: '/archive' },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

export default router
