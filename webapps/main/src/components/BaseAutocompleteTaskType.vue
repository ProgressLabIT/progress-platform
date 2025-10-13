<template>
  <q-select
    use-input
    filled
    :hint="hint"
    :error="error"
    :error-message="errorMessage"
    :hide-bottom-space="!hint && !error"
    label-slot
    :label="$capitalize(t('task_type'))"
    :dense="dense"
    :clearable="clearable"
    :options="options"
    option-label="name"
    :model-value="value"
    input-debounce="100"
    :option-value="keyOnly ? '_key' : null"
    :emit-value="keyOnly"
    :map-options="keyOnly"
    @filter="filter"
    @update:model-value="(selection) => $emit('select', selection)"
  >
    <template #label>
      {{ $capitalize(t('task_type')) }}
      <span v-if="mandatory" class="text-theme-red"> * </span>
    </template>
    <template #option="scope">
      <q-item v-bind="scope.itemProps" class="q-px-lg">
        <q-item-section avatar>
          <q-icon :name="scope.opt.icon || 'mdi-help-circle'" size="lg" />
        </q-item-section>
        <q-item-section>
          <q-item-label class="text-body1 highlight">
            {{ $capitalize(scope.opt.name) }}
          </q-item-label>
          <q-item-label caption>
            {{ scope.opt.description }}
          </q-item-label>
        </q-item-section>
      </q-item>
    </template>
  </q-select>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import multiMatch from '@/lib/MultiFieldSearch.js';
import { useTaskTypeStore } from '@/stores/taskType.js';

const props = defineProps({
  value: {
    type: [String, Object],
    default: null,
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

  mandatory: {
    type: Boolean,
    default: false,
  },

  hint: {
    type: String,
    default: undefined,
  },
  error: {
    type: Boolean,
    default: false,
  },
  errorMessage: {
    type: String,
    default: undefined,
  },
});

defineEmits(['select']);

const { t } = useI18n();
const taskTypeStore = useTaskTypeStore();

const loading = ref(false);
const options = ref([]);
const search_fields = ['name', 'description'];

const origin_list = computed(() => {
  return taskTypeStore.getActiveTaskTypes;
});

function initOptions() {
  options.value = [...origin_list.value];
}

function filter(value, update) {
  if (value === '') {
    update(() => {
      initOptions();
    });
    return;
  }
  update(() => {
    const needle = value.toLowerCase();
    options.value = origin_list.value.filter((option) => {
      return multiMatch(needle, option, search_fields);
    });
  });
}

onMounted(async () => {
  if (props.loadData) {
    loading.value = true;
    await taskTypeStore.fetchTaskTypes(true);
    initOptions();
    loading.value = false;
  }
});
</script>
