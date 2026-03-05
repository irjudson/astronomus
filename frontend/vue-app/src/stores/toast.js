import { defineStore } from 'pinia'

export const useToastStore = defineStore('toast', {
  state: () => ({
    notifications: [],
  }),

  actions: {
    add(message, type = 'info', duration = 3000) {
      const id = Date.now() + Math.random()
      this.notifications.push({ id, type, message })
      if (duration > 0) {
        setTimeout(() => this.dismiss(id), duration)
      }
      return id
    },
    success(message, duration = 3000) {
      return this.add(message, 'success', duration)
    },
    error(message, duration = 5000) {
      return this.add(message, 'error', duration)
    },
    info(message, duration = 3000) {
      return this.add(message, 'info', duration)
    },
    dismiss(id) {
      this.notifications = this.notifications.filter(n => n.id !== id)
    },
  },
})
