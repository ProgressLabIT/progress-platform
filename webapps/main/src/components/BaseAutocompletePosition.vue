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
    option-label="code"
    :option-value="keyOnly ? '_key' : null"
    :model-value="selectModelValue"
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
import { ref, computed, onMounted, watch } from 'vue';
import { useStore } from 'vuex';

const props = defineProps({
  value: {
    type: [Object, String],
    default: null,
  },
  label: {
    type: String,
    default: '',
  },
  loadData: {
    type: Boolean,
    default: true,
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
const store = useStore();

const loading = ref(false);
const options = ref([]);
const last_research = ref(undefined);

const placeholder_computed = computed(() => {
  return props.value ? null : props.placeholder;
});

// When using key-only mode, avoid showing the raw key before we have
// loaded the corresponding option. Until then, keep the model null so
// the field is blank/placeholder, then switch to the key once the
// option exists and the label can be resolved.
const selectModelValue = computed(() => {
  if (!props.keyOnly) {
    return props.value;
  }

  if (!props.value || typeof props.value !== 'string') {
    return props.value;
  }

  const hasOption = options.value.some((opt) => opt._key === props.value);
  return hasOption ? props.value : null;
});

onMounted(() => {
  if (props.loadData) {
    loadPositions();
  }
});

const loadPositions = (search_value) => {
  loading.value = true;
  let params = {};

  if (search_value) {
    params.search = search_value;
    last_research.value = search_value;
  }
  params.limit = 100;
  params.open = true;

  store
    .dispatch('getPositions', params)
    .then((data) => {
      
      let newOptions = data;
      if (props.keyOnly && props.value && typeof props.value === 'string') {
        const found = newOptions.some((opt) => opt._key === props.value);
        if (!found) {
          const preserved = options.value.find((opt) => opt._key === props.value);
          if (preserved) {
            newOptions = [preserved, ...data];
          }
        }
      }
      options.value = newOptions;
    })
    .finally(() => {
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

// Ensure that when using key-only mode with an initial key value,
// we load and cache the corresponding position so the select
// can display the proper `code` label instead of the raw key.
const ensureOptionForKey = async (key) => {
  if (!key || typeof key !== 'string') return;
  if (options.value.some((opt) => opt._key === key)) return;

  loading.value = true;
  try {
    const code = await store.dispatch('resolvePositionCode', key);
    if (code) {
      if (!options.value.some((opt) => opt._key === key)) {
        options.value = [...options.value, { _key: key, code }];
      }
    }
  } finally {
    loading.value = false;
  }
};

watch(
  () => props.value,
  (newVal) => {
    if (props.keyOnly) {
      ensureOptionForKey(newVal);
    }
  },
  { immediate: true },
);
</script>
