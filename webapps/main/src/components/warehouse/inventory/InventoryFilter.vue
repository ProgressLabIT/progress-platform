<template>
  <FilterDrawer
    v-model="showFilterDrawer"
    :active-filters="filters_active"
    @reset="resetFilters"
  >
    <!-- PRODUCT CODE -->
    <div class="column q-col-gutter-xs">

    <!-- ROOT POSITION -->
      <BaseAutocompletePosition
        dense
        filled
        class="q-mb-md col"
        behavior="menu"
        popup-content-class="z-max"
        key-only
        :load-data="false"
        label="Posizione di partenza"
        :value="rootPositionKey"
        @select="(selection) => (rootPositionKey = selection)"
      />

      <!-- PRODUCT SEARCH -->
      <q-input
        v-model="productSearch"
        filled
        dense
        clearable
        autocomplete="off"
        name="search"
        debounce="300"
        label="Filtro prodotto"
        class="q-mb-md col"
      />

      <!-- SERIAL SEARCH -->
      <q-input
        v-model="serialSearch"
        filled
        dense
        clearable
        autocomplete="off"
        name="search"
        debounce="300"
        label="Filtro seriale"
        class="q-mb-md col"
      />

      <!-- POSITION SEARCH -->
      <q-input
        v-model="positionSearch"
        filled
        dense
        clearable
        autocomplete="off"
        name="search"
        debounce="300"
        label="Filtro posizione"
        class="q-mb-md col"
      />
    </div>
  </FilterDrawer>
</template>

<script setup>
import { watch } from 'vue';
import { useRouter } from 'vue-router';
import BaseAutocompletePosition from '@/components/BaseAutocompletePosition.vue';
import FilterDrawer from '@/components/FilterDrawer.vue';
import { useInventoryFilters } from 'app/src/composables/warehouse';
const $router = useRouter();

const showFilterDrawer = defineModel('showFilterDrawer', {
  type: Boolean,
  required: true,
});

const emit = defineEmits(['filterActiveChange']);

const { productSearch, positionSearch, serialSearch, rootPositionKey, filters_active } = useInventoryFilters();


function resetFilters() {
  $router.replace({ query: null });
}

watch(filters_active, (newVal) => {
  emit('filterActiveChange', newVal);
});

</script>
