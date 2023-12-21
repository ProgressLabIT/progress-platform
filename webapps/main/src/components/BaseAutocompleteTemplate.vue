<template>
  <q-select
    :model-value="value"
    :emit-value="keyOnly"
    :map-options="keyOnly"
    :options="
      options.filter(
        (option) => !selected.some(({ _key }) => _key === option._key),
      )
    "
    :option-value="keyOnly ? '_key' : null"
    :option-label="(item) => $capitalize(item.name)"
    :loading="isLoading"
    use-input
    input-debounce="100"
    :label="label"
    dense
    filled
    @filter="onFilter"
    @update:model-value="(selection) => emit('select', selection)"
  >
    <template #option="scope">
      <q-item v-bind="scope.itemProps">
        <q-item-section>
          <q-item-label>
            {{ scope.opt.name }}
          </q-item-label>

          <q-item-label caption :lines="2">
            {{ scope.opt.description }}
          </q-item-label>
        </q-item-section>
      </q-item>
    </template>
  </q-select>
</template>

<script setup>
import { ref } from 'vue';
import { usePrintTemplates } from '@/composables/print-template';
import multiMatch from '@/lib/MultiFieldSearch.js';

const props = defineProps({
  // TODO: value vs selected ?
  value: {
    type: [Object, String],
    default: null,
  },

  keyOnly: {
    type: Boolean,
    default: false,
  },

  label: {
    type: String,
    default: undefined,
  },

  selected: {
    type: Array,
    default: () => [],
  },

  context: {
    type: String,
    default: undefined,
    validator: (value) =>
      ['product', 'phase', 'step', 'issue_type'].includes(value),
  },

  contextKey: {
    type: String,
    default: undefined,
  },
});

const emit = defineEmits(['select']);

const { fetchTemplates, templates, isLoading } = usePrintTemplates({
  context: props.context,
  contextKey: props.contextKey,
});

const options = ref([]);
fetchTemplates().then(() => {
  options.value = [...templates.value];
});

function onFilter(value, update) {
  if (value === '') {
    update(() => {
      options.value = [...templates.value];
    });
    return;
  }

  update(() => {
    const needle = value.toLowerCase();
    options.value = templates.value.filter((template) =>
      multiMatch(needle, template, ['name', 'description']),
    );
  });
}
</script>
