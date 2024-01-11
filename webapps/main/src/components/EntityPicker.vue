<template>
  <q-card square class="surface1" style="min-width: 400px">
    <q-card-section>
      <q-input
        v-model="searchTerm"
        :label="capitalize($t('search'))"
        icon="mdi-magnify"
        debounce="300"
        dense
        square
        filled
        class="full-width"
      >
        <template #append>
          <q-icon name="mdi-magnify" />
        </template>
      </q-input>
    </q-card-section>

    <q-card-section>
      <div v-if="filteredOptions.length === 0" class="text-center q-mb-sm">
        {{ $t('no_data') }}
      </div>
      <q-virtual-scroll
        v-else
        v-slot="{ item }"
        style="max-height: 200px"
        :items="filteredOptions"
        class="surface2"
      >
        <slot
          name="item"
          :item="item"
          :item-props="{ clickable: true, onClick: () => emit('select', item) }"
        />
      </q-virtual-scroll>
    </q-card-section>

    <q-card-section v-if="$slots.bottom">
      <slot name="bottom" />
    </q-card-section>
  </q-card>
</template>

<script setup>
import { computed, ref } from 'vue';
import { capitalize } from '@/boot/filters';
import multiMatch from '@/lib/MultiFieldSearch.js';

const props = defineProps({
  options: {
    type: Array,
    default: () => [],
  },
  searchableFields: {
    type: Array,
    default: () => [],
  },
});

const emit = defineEmits(['select']);

const searchTerm = ref();

const filteredOptions = computed(() => {
  if (props.searchableFields.length === 0 || !searchTerm.value) {
    return props.options;
  }

  return props.options.filter((option) =>
    multiMatch(searchTerm.value, option, props.searchableFields),
  );
});
</script>
