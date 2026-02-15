<template>
  <div
    class="panel-container"
    :class="layoutClasses"
  >
    <!-- Left Panel -->
    <aside class="left-panel overflow-y-auto border-r border-gray-800 bg-gray-900">
      <div v-if="leftPanelVisible" class="flex flex-col h-full">
        <div class="flex-none flex items-center justify-between p-2 border-b border-gray-800">
          <slot name="left-header" />
          <button
            @click="$emit('update:leftPanelVisible', false)"
            class="p-1 hover:bg-gray-800 rounded transition-colors"
            title="Collapse panel"
          >
            <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
            </svg>
          </button>
        </div>
        <div class="flex-1 overflow-y-auto">
          <slot name="left" />
        </div>
      </div>
    </aside>

    <!-- Left Peek Tab -->
    <button
      v-if="!leftPanelVisible"
      @click="$emit('update:leftPanelVisible', true)"
      class="peek-tab peek-tab-left"
      title="Expand panel"
    >
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
      </svg>
      <span class="peek-label"><slot name="left-label">Panel</slot></span>
    </button>

    <!-- Main Content -->
    <main class="main-content overflow-hidden bg-gray-950">
      <slot name="main" />
    </main>

    <!-- Right Peek Tab -->
    <button
      v-if="!rightPanelVisible"
      @click="$emit('update:rightPanelVisible', true)"
      class="peek-tab peek-tab-right"
      title="Expand panel"
    >
      <span class="peek-label"><slot name="right-label">Panel</slot></span>
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
      </svg>
    </button>

    <!-- Right Panel -->
    <aside class="right-panel overflow-y-auto border-l border-gray-800 bg-gray-900">
      <div v-if="rightPanelVisible" class="flex flex-col h-full">
        <div class="flex-none flex items-center justify-between p-2 border-b border-gray-800">
          <button
            @click="$emit('update:rightPanelVisible', false)"
            class="p-1 hover:bg-gray-800 rounded transition-colors"
            title="Collapse panel"
          >
            <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </button>
          <slot name="right-header" />
        </div>
        <div class="flex-1 overflow-y-auto">
          <slot name="right" />
        </div>
      </div>
    </aside>

    <!-- Console/Logs -->
    <footer class="console border-t border-gray-800 bg-gray-900">
      <slot name="console" />
    </footer>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  leftPanelVisible: {
    type: Boolean,
    default: true
  },
  rightPanelVisible: {
    type: Boolean,
    default: true
  },
  consoleVisible: {
    type: Boolean,
    default: false
  }
})

defineEmits(['update:leftPanelVisible', 'update:rightPanelVisible', 'update:consoleVisible'])

const layoutClasses = computed(() => ({
  'left-collapsed': !props.leftPanelVisible,
  'right-collapsed': !props.rightPanelVisible,
  'console-collapsed': !props.consoleVisible
}))
</script>

<style scoped>
.panel-container {
  display: grid;
  width: 100%;
  height: 100%;
  grid-template-columns: minmax(0, 300px) 1fr minmax(0, 350px);
  grid-template-rows: 1fr 160px;
  grid-template-areas:
    "left main right"
    "console console console";
  transition: grid-template-columns 300ms ease-in-out, grid-template-rows 300ms ease-in-out;
  position: relative;
}

.left-panel {
  grid-area: left;
  min-width: 0;
}

.main-content {
  grid-area: main;
  min-width: 0;
  position: relative;
}

.right-panel {
  grid-area: right;
  min-width: 0;
}

.console {
  grid-area: console;
  min-height: 0;
}

/* Peek tabs */
.peek-tab {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 0.5rem;
  background: linear-gradient(to bottom, rgb(31, 41, 55), rgb(17, 24, 39));
  border: 1px solid rgb(55, 65, 81);
  color: rgb(156, 163, 175);
  cursor: pointer;
  transition: all 200ms ease-in-out;
  z-index: 10;
  writing-mode: vertical-rl;
  text-orientation: mixed;
}

.peek-tab:hover {
  background: linear-gradient(to bottom, rgb(55, 65, 81), rgb(31, 41, 55));
  color: rgb(229, 231, 235);
  border-color: rgb(75, 85, 99);
}

.peek-tab-left {
  left: 0;
  border-radius: 0 0.375rem 0.375rem 0;
  border-left: none;
}

.peek-tab-right {
  right: 0;
  border-radius: 0.375rem 0 0 0.375rem;
  border-right: none;
}

.peek-label {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* Collapsed states */
.panel-container.left-collapsed {
  grid-template-columns: 0 1fr minmax(0, 350px);
}

.panel-container.left-collapsed .left-panel {
  overflow: hidden;
  visibility: hidden;
  border-right: none;
}

.panel-container.right-collapsed {
  grid-template-columns: minmax(0, 300px) 1fr 0;
}

.panel-container.right-collapsed .right-panel {
  overflow: hidden;
  visibility: hidden;
  border-left: none;
}

.panel-container.left-collapsed.right-collapsed {
  grid-template-columns: 0 1fr 0;
}

.panel-container.console-collapsed {
  grid-template-rows: 1fr 0;
}

.panel-container.console-collapsed .console {
  overflow: hidden;
  visibility: hidden;
  border-top: none;
}
</style>
