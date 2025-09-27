<template>
  <q-select
    ref="selectRef"
    use-input
    filled
    input-class="text-uppercase"
    input-debounce="300"
    :clearable="clearable"
    :dense="dense"
    :hint="hint"
    :label-slot="!!label"
    :loading="loading"
    :map-options="keyOnly"
    :max-values="selection_qt || 1"
    :model-value="value"
    :multiple="multiple"
    :options="options"
    option-value="_key"
    option-label="code"
    :placeholder="placeholder_computed"
    :use-chips="multiple"
    @filter="filter"
    @remove="remove"
    @update:model-value="
      (selection) => {
        emit('select', selection);
      }
    "
  >
    <template #option="scope">
      <q-item
        v-bind="scope.itemProps"
        :id="scope.opt._key"
        :disable="disableKeys.includes(scope.opt._key)"
      >
        <q-item-section side>
          <q-icon :name="scope.opt.icon" size="md" />
        </q-item-section>
        <q-item-section>
          <q-item-label caption>
            <div class="row items-center q-gutter-x-sm">
              <div>
                {{ scope.opt.task_type_name }}
              </div>
              <div>
                {{ scope.opt.code }}
              </div>
            </div>
          </q-item-label>
          <q-item-label class="highlight" lines="2">
            {{
              scope.opt.title || scope.opt.code || '(' + $t('id') + ' ' + scope.opt._key + ')'
            }}
          </q-item-label>
        </q-item-section>
        <q-item-section side top>
          <div class="row items-center q-gutter-x-sm">
            <q-chip
              v-if="scope.opt.status"
              :color="getStatusColor(scope.opt.status)"
              size="sm"
              dense
              class="text-uppercase"
            >
              {{ taskStatusOptions[scope.opt.status]?.label }}
            </q-chip>
          </div>
        </q-item-section>
      </q-item>
    </template>

    <template v-if="!!label" #label>
      <div class="ellipsis">
        {{ label }}
      </div>
    </template>

    <template #no-options>
      <q-item>
        <q-item-section class="text-low">
          {{ $t('task_field.noData') }}
        </q-item-section>
      </q-item>
    </template>

  </q-select>
</template>

<script setup>
import { ref, computed } from 'vue';
import { api } from '@/boot/axios';
import { useTask } from 'src/composables/task';

const props = defineProps({
  value: {
    type: Object,
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

  work_order_key: {
    type: String,
    default: undefined,
  },

  product_key: {
    type: String,
    default: undefined,
  },

  serial_key: {
    type: String,
    default: undefined,
  },

  can_search: {
    type: Boolean,
    default: true,
  },

  selection_qt: {
    type: Number,
    default: 1,
  },

  hint: {
    type: String,
    default: '',
  },

  minChars: {
    type: Number,
    default: 0,
  },

  disableKeys: {
    type: Array,
    default: () => [],
  },
});

const emit = defineEmits(['select', 'remove']);
const selectRef = ref(null);
const loading = ref(false);
const options = ref([]);

const placeholder_computed = computed(() => {
  return props.value ? null : props.placeholder;
});

const multiple = computed(() => {
  return props.selection_qt != null && props.selection_qt > 1;
});

const { taskStatusOptions } = useTask();

initialize();

function initialize() {
  if (props.work_order_key || props.product_key || props.serial_key) {
    loadOptions();
    loading.value = false;
  }
}

function loadOptions(search_value) {
  loading.value = true;
  let params = {
    search: search_value,
    limit: 100,
  };

  api.get('task', { params }).then((resp) => {
    options.value = resp.data.map(({_key, code, title, task_type_name, task_type, status, icon}) => ({
      _key,
      code,
      title,
      task_type_name,
      task_type,
      status,
      icon,
    }));
    loading.value = false;
  }).catch((error) => {
    console.error('Error loading tasks:', error);
    loading.value = false;
  });
}

function getStatusColor(status) {
  const statusOption = taskStatusOptions[status];
  return statusOption?.color || 'theme-grey';
}

function remove(value) {
  emit('remove', value);
}

function filter(value, update, abort) {
  if (!props.can_search) {
    update(() => {
    });
  } else if (value.length < props.minChars) {
    abort();
  } else {
    update(() => {
      loadOptions(value);
    });
  }
}
</script>
