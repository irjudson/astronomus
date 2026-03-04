<template>
  <div class="p-4 space-y-6">
    <!-- Loading state -->
    <div v-if="loading" class="text-center text-gray-400 py-8">
      Loading solar system data...
    </div>

    <!-- Error state -->
    <div v-else-if="error" class="p-3 bg-red-900/20 border border-red-800 rounded-lg text-red-400 text-sm">
      {{ error }}
    </div>

    <!-- Content -->
    <template v-else>
      <!-- Planets -->
      <section>
        <h3 class="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-3">Planets</h3>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          <SolarSystemCard
            v-for="obj in planets"
            :key="obj.name"
            :object="obj"
            :in-plan="isInPlan(obj.name)"
            :in-wishlist="catalogStore.isInWishlist(obj.name)"
            @add-to-plan="addToPlan(obj)"
            @toggle-wishlist="toggleWishlist(obj)"
          />
        </div>
      </section>

      <!-- Earth's Moon -->
      <section>
        <h3 class="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-3">Earth's Moon</h3>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          <SolarSystemCard
            v-for="obj in earthMoon"
            :key="obj.name"
            :object="obj"
            :in-plan="isInPlan(obj.name)"
            :in-wishlist="catalogStore.isInWishlist(obj.name)"
            @add-to-plan="addToPlan(obj)"
            @toggle-wishlist="toggleWishlist(obj)"
          />
        </div>
      </section>

      <!-- Jupiter's Moons -->
      <section>
        <h3 class="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-3">Jupiter's Moons</h3>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          <SolarSystemCard
            v-for="obj in jupiterMoons"
            :key="obj.name"
            :object="obj"
            :in-plan="isInPlan(obj.name)"
            :in-wishlist="catalogStore.isInWishlist(obj.name)"
            @add-to-plan="addToPlan(obj)"
            @toggle-wishlist="toggleWishlist(obj)"
          />
        </div>
      </section>

      <!-- Saturn's Moons -->
      <section>
        <h3 class="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-3">Saturn's Moons</h3>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          <SolarSystemCard
            v-for="obj in saturnMoons"
            :key="obj.name"
            :object="obj"
            :in-plan="isInPlan(obj.name)"
            :in-wishlist="catalogStore.isInWishlist(obj.name)"
            @add-to-plan="addToPlan(obj)"
            @toggle-wishlist="toggleWishlist(obj)"
          />
        </div>
      </section>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { defineComponent, h } from 'vue'
import axios from 'axios'
import { useCatalogStore } from '@/stores/catalog'
import { useSettingsStore } from '@/stores/settings'

const catalogStore = useCatalogStore()
const settingsStore = useSettingsStore()

const loading = ref(true)
const error = ref(null)
const objects = ref([])

const planets = computed(() =>
  objects.value.filter(o => o.type === 'planet')
)
const earthMoon = computed(() =>
  objects.value.filter(o => o.name === 'Moon')
)
const jupiterMoons = computed(() =>
  objects.value.filter(o => o.type === 'moon' && o.parent === 'Jupiter')
)
const saturnMoons = computed(() =>
  objects.value.filter(o => o.type === 'moon' && o.parent === 'Saturn')
)

function isInPlan(name) {
  return catalogStore.selectedTargets.some(t => t.name === name)
}

function addToPlan(obj) {
  catalogStore.addSelectedTarget({
    name: obj.name,
    type: obj.type,
    object_type: obj.type,
    imaging_mode: 'planet',
  })
}

function toggleWishlist(obj) {
  if (catalogStore.isInWishlist(obj.name)) {
    catalogStore.removeFromWishlist(obj.name)
  } else {
    catalogStore.addToWishlist({ name: obj.name, type: obj.type })
  }
}

onMounted(async () => {
  try {
    const { latitude, longitude } = settingsStore.settings
    const params = {}
    if (latitude != null) params.lat = latitude
    if (longitude != null) params.lon = longitude

    const response = await axios.get('/api/solar-system/objects', { params })
    objects.value = response.data.objects || []
  } catch (err) {
    error.value = 'Failed to load solar system data: ' + (err.response?.data?.detail || err.message)
  } finally {
    loading.value = false
  }
})

// Inline card component
const SolarSystemCard = defineComponent({
  name: 'SolarSystemCard',
  props: {
    object: { type: Object, required: true },
    inPlan: { type: Boolean, default: false },
    inWishlist: { type: Boolean, default: false },
  },
  emits: ['add-to-plan', 'toggle-wishlist'],
  setup(props, { emit }) {
    const typeBadgeClass = computed(() => {
      const map = { planet: 'bg-blue-900/50 text-blue-300', moon: 'bg-purple-900/50 text-purple-300', star: 'bg-yellow-900/50 text-yellow-300' }
      return map[props.object.type] || 'bg-gray-700 text-gray-300'
    })
    const visClass = computed(() =>
      props.object.is_visible ? 'bg-green-500' : 'bg-gray-600'
    )
    const visLabel = computed(() =>
      props.object.is_visible ? 'Visible' : 'Below horizon'
    )
    const visTextClass = computed(() =>
      props.object.is_visible ? 'text-green-400' : 'text-gray-500'
    )

    return () => h('div', { class: 'bg-gray-800 border border-gray-700 rounded-lg p-3 flex flex-col gap-2' }, [
      // Header
      h('div', { class: 'flex items-center justify-between' }, [
        h('div', { class: 'flex items-center gap-2' }, [
          h('h4', { class: 'text-sm font-semibold text-gray-200' }, props.object.name),
          h('span', { class: `text-xs px-1.5 py-0.5 rounded ${typeBadgeClass.value}` }, props.object.type),
        ]),
        h('div', { class: 'flex items-center gap-1' }, [
          h('span', { class: `w-2 h-2 rounded-full ${visClass.value}` }),
          h('span', { class: `text-xs ${visTextClass.value}` }, visLabel.value),
        ]),
      ]),
      // Details
      h('div', { class: 'text-xs text-gray-400 space-y-0.5' }, [
        props.object.magnitude != null
          ? h('div', {}, `Magnitude: ${props.object.magnitude.toFixed(1)}`)
          : null,
        props.object.altitude_deg != null
          ? h('div', {}, `Altitude: ${props.object.altitude_deg.toFixed(1)}°`)
          : null,
        props.object.angular_diameter_arcsec != null
          ? h('div', {}, `Angular size: ${props.object.angular_diameter_arcsec.toFixed(1)}"`)
          : null,
        props.object.constellation
          ? h('div', {}, `Constellation: ${props.object.constellation}`)
          : null,
        props.object.parent
          ? h('div', { class: 'text-gray-500' }, `Moon of ${props.object.parent}`)
          : null,
        props.object.notes
          ? h('div', { class: 'text-gray-500 mt-1 text-xs leading-tight' }, props.object.notes)
          : null,
      ].filter(Boolean)),
      // Action buttons
      h('div', { class: 'flex gap-2' }, [
        // Wishlist star button
        h('button', {
          onClick: () => emit('toggle-wishlist'),
          title: props.inWishlist ? 'Remove from wishlist' : 'Add to wishlist',
          class: props.inWishlist
            ? 'px-3 py-1.5 rounded text-base bg-yellow-600/30 hover:bg-yellow-600/50 text-yellow-400 transition-colors'
            : 'px-3 py-1.5 rounded text-base bg-gray-700 hover:bg-gray-600 text-gray-400 hover:text-yellow-400 transition-colors',
        }, props.inWishlist ? '★' : '☆'),
        // Add to Plan button
        h('button', {
          onClick: () => emit('add-to-plan'),
          disabled: props.inPlan,
          class: props.inPlan
            ? 'flex-1 px-3 py-1.5 rounded text-sm font-medium bg-green-800 text-green-300 cursor-default'
            : 'flex-1 px-3 py-1.5 rounded text-sm font-medium bg-blue-600 hover:bg-blue-700 text-white transition-colors',
        }, props.inPlan ? '✓ In Plan' : 'Add to Plan'),
      ]),
    ])
  },
})
</script>
