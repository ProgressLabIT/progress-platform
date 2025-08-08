<template>
  <q-drawer
    v-model="drawerModel"
    side="right"
    bordered
    :behavior="$q.screen.lt.lg ? 'mobile' : null"
    class="background"
    :width="minWidth"
    show-if-above
    :overlay="$q.screen.lt.lg"
    persistent
  >
    <div class="column full-height q-px-lg">
      <slot name="before-header" />
      <div class="col-auto row items-center q-mt-sm q-mb-md">
        <div class="col-auto highlight text-uppercase text-h5">
          {{ $t('filter', 2) }}
        </div>
        <q-badge
          v-if="activeFilters"
          class="q-ml-md smaller weight-bold"
          rounded
          :label="activeFilters"
          color="theme-grey"
        />
        <div class="col-auto q-ml-md">
          <q-btn
            v-if="hideable"
            size="sm"
            round
            flat
            icon="mdi-eye-off-outline"
            @click="drawerModel = false"
          />
        </div>
        <q-space />
        <div class="col-auto">
          <q-btn
            v-show="!!activeFilters"
            size="sm"
            color="theme-blue"
            :label="$t('filters_reset')"
            @click="emit('reset')"
          >
          </q-btn>
        </div>
      </div>
      <div class="col scroll q-pb-xl">
        <slot />
      </div>
    </div>
  </q-drawer>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  activeFilters: {
    type: Number,
    default: 0,
  },
  hideable: {
    type: Boolean,
    default: true,
  },
  minWidth: {
    type: Number,
    default: 350,
  },
});

const emit = defineEmits(['update:modelValue', 'reset']);

const drawerModel = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
});
</script>

<style lang="scss" scoped>
// When the drawer is in overlay mode, the drawer will be on top everything else with z-index: 9999
// So, we should give it a z-index that is less than $z-menu to allow placing q-selects inside
$z-index: $z-menu - 1;

:deep(.q-drawer--on-top) {
  z-index: $z-index !important;
}

:deep(.q-drawer__backdrop) {
  z-index: $z-index - 1 !important;
}
</style>
