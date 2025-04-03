<template>
  <q-select
    use-input
    filled
    :loading="loading"
    :label-slot="!!label"
    :dense="dense"
    :hint="hint"
    :hide-bottom-space="!hint"
    :placeholder="placeholder_computed"
    :clearable="clearable"
    :options="options"
    :display-value="value?.code"
    :option-value="keyOnly ? '_key' : null"
    :model-value="value"
    input-debounce="500"
    :emit-value="keyOnly"
    :map-options="keyOnly"
    @filter="filter"
    @update:model-value="(selection) => emit('select', selection)"
  >
    <template #option="scope">
      <q-item v-bind="scope.itemProps">
        <q-item-section class="text-h4 highlight col-auto q-pr-md">
          {{ scope.opt.code }}
        </q-item-section>
      </q-item>
    </template>

    <template v-if="!!label" #label>
      {{ label }}
    </template>

    <template #no-option>
      <div class="q-pa-md">No results</div>
    </template>
  </q-select>
</template>

<script setup>
import { ref, computed } from 'vue';
import { api } from '@/boot/axios';

const props = defineProps({
  value: {
    type: [Object, String],
    default: null,
  },
  label: {
    type: String,
    default: '',
  },
  keyOnly: {
    type: Boolean,
    default: false,
  },
  dense: {
    type: Boolean,
    default: false,
  },
  clearable: {
    type: Boolean,
    default: true,
  },
  placeholder: {
    type: String,
    default: null,
  },
  hint: {
    type: String,
    default: undefined,
  },
});

const emit = defineEmits(['select']);

const loading = ref(false);
const options = ref([]);
const last_research = ref(undefined);

const placeholder_computed = computed(() => {
  return props.value ? null : props.placeholder;
});

if (props.loadData) {
  loadPositions();
}


const loadPositions = (search_value) => {
  loading.value = true;
  let params = {};

  if (search_value) {
    params.search = search_value;
    last_research.value = search_value;
  }
  params.limit = 100;
  params.open = true;

  api
    .get('position', {
      params,
    })
    .then((resp) => {
      options.value = resp.data;
      loading.value = false;
    });
};

const filter = (value, update) => {
  if (last_research.value === value) {
    update();
  } else {
    update(() => {
      loadPositions(value);
    });
  }
};
</script>
