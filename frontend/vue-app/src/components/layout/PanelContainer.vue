<template>
  <div
    class="panel-container"
    :class="layoutClasses"
  >
    <!-- Left Panel -->
    <aside class="left-panel overflow-y-auto border-r border-gray-800 bg-gray-900">
      <slot name="left" />
    </aside>

    <!-- Main Content -->
    <main class="main-content overflow-hidden bg-gray-950">
      <slot name="main" />
    </main>

    <!-- Right Panel -->
    <aside class="right-panel overflow-y-auto border-l border-gray-800 bg-gray-900">
      <slot name="right" />
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
}

.left-panel {
  grid-area: left;
  min-width: 0;
}

.main-content {
  grid-area: main;
  min-width: 0;
}

.right-panel {
  grid-area: right;
  min-width: 0;
}

.console {
  grid-area: console;
  min-height: 0;
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
