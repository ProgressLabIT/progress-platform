<template>
  <q-drawer
    v-model="drawerModel"
    side="right"
    bordered
    class="background"
    :width="400"
    show-if-above
    :overlay="$q.screen.lt.lg"
  >
    <div class="column q-px-lg">
      <div class="col-auto row items-center justify-between q-mt-sm q-mb-md">
        <div class="col-auto highlight text-uppercase text-h5">
          {{ $t('filter', 2) }}
        </div>

        <div class="col-auto">
          <q-btn
            v-show="hasActiveFilters"
            color="theme-blue"
            size="sm"
            padding="xs sm"
            @click="emit('reset')"
          >
            <span>
              {{ $t('reset_filters') }}
            </span>
          </q-btn>
        </div>

        <div class="col-auto">
          <q-btn
            color="theme-grey"
            size="sm"
            round
            icon="mdi-minus"
            @click="drawerModel = false"
          />
        </div>
      </div>

      <div class="col scroll q-pb-xl">
        <slot />
      </div>

      <div class="fade-bottom-bg" />
    </div>
  </q-drawer>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  hasActiveFilters: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'reset'])

const drawerModel = computed({
  get: () => props.modelValue,
  set: value => emit('update:modelValue', value)
})
</script>
