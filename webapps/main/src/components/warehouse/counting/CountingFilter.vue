<template>
  <FilterDrawer
    v-model="showFilterDrawer"
    :active-filters="filters_active"
    @reset="resetFilters"
  >
    <!-- SEARCH -->
    <q-input
      v-model="search"
      filled
      dense
      clearable
      autocomplete="off"
      name="search"
      debounce="300"
      :label="$capitalize($t('search'))"
      class="q-mb-md"
    >
      <template #append>
        <q-icon name="mdi-magnify" />
      </template>
    </q-input>

    <!-- STATUS -->
    <q-select
      v-model="status"
      :options="statusOptions"
      option-value="value"
      option-label="label"
      emit-value
      map-options
      filled
      dense
      clearable
      :label="$capitalize($t('status'))"
      class="q-mb-md"
    />

    <!-- TYPE -->
    <q-select
      v-model="type"
      :options="typeOptions"
      option-value="value"
      option-label="label"
      emit-value
      map-options
      filled
      dense
      clearable
      :label="$capitalize($t('type'))"
      class="q-mb-md"
    />
  </FilterDrawer>
</template>

<script setup>
import { watch } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import FilterDrawer from '@/components/FilterDrawer.vue';
import { useCountSessionFilters } from 'app/src/composables/warehouse';

const $router = useRouter();
const { t } = useI18n();

const showFilterDrawer = defineModel('showFilterDrawer', {
  type: Boolean,
  required: true,
});

const emit = defineEmits(['filterActiveChange']);

const { filters, search, status, type, filters_active } = useCountSessionFilters();

const statusOptions = [
  { label: t('warehouse.counting.planned'), value: 'planned' },
  { label: t('warehouse.counting.started'), value: 'started' },
  { label: t('warehouse.counting.completed'), value: 'completed' },
  { label: t('warehouse.counting.applied'), value: 'applied' },
  { label: t('warehouse.counting.canceled'), value: 'canceled' },
];

const typeOptions = [
  { label: t('warehouse.counting.by_position'), value: 'position' },
  { label: t('warehouse.counting.by_product'), value: 'product' },
];

function resetFilters() {
  $router.replace({ query: null });
}

watch(filters_active, (newVal) => {
  emit('filterActiveChange', newVal);
});
</script>

