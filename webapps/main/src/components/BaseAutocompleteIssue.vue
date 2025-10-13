<template>
  <q-select
    ref="selectRef"
    use-input
    filled
    input-debounce="300"
    :clearable="clearable"
    :dense="dense"
    :hint="hint"
    :error="error"
    :error-message="errorMessage"
    :hide-bottom-space="!hint && !error"
    :label-slot="!!label"
    :loading="loading"
    :map-options="keyOnly"
    :emit-value="keyOnly"
    :max-values="selection_qt || 1"
    :model-value="value"
    :multiple="multiple"
    :options="options"
    :option-value="keyOnly ? '_key' : null"
    option-label="_key"
    :placeholder="placeholder_computed"
    :use-chips="multiple"
    @filter="filter"
    @remove="remove"
    @update:model-value="(selection) => emit('select', selection)"
  >
    <template #option="scope">
      <q-item
        v-bind="scope.itemProps"
        :id="scope.opt._key"
        :disable="disableKeys.includes(scope.opt._key)"
        :class="scope.opt.open ? 'highlight' : 'text-low'"
      >
        <q-item-section side>
          <q-icon
            :name="scope.opt.icon || 'mdi-alert-circle'"
            :color="scope.opt.open ? 'high' : 'disabled'"
            size="sm"
          />
        </q-item-section>
        <q-item-section side>
          <q-avatar
            size="6px"
            :color="scope.opt.critical && scope.opt.open ? 'theme-red' : 'transparent'"
          />
        </q-item-section>
        <q-item-section>
          <q-item-label lines="1">
            {{ scope.opt.issue_type_name || $t('unknown_type') }}
          </q-item-label>
          <q-item-label caption lines="1">
            {{ 'ID ' + scope.opt._key }}
          </q-item-label>
        </q-item-section>
        <q-item-section side>
          <div class="row items-center q-gutter-x-sm">
            <q-icon
              v-if="scope.opt.priority === 'high'"
              size="xs"
              name="mdi-chevron-triple-up"
              color="red"
            />
            <q-icon
              v-else-if="scope.opt.priority === 'medium'"
              size="xs"
              name="mdi-chevron-double-up"
              color="orange"
            />
          </div>
        </q-item-section>
      </q-item>
    </template>

    <template v-if="!!label" #label>
      <div class="ellipsis">
        {{ label }}
      </div>
    </template>

    <template #no-option="{ inputValue }">
      <q-item v-if="!can_create">
        <q-item-section class="text-low">
          {{ $t('issue_field.noData') }}
        </q-item-section>
      </q-item>
      <q-item v-else-if="inputValue?.length < minChars">
        <q-item-section class="text-low">
          {{ $t('issue_field.noData_min_char', { minChars }) }}
        </q-item-section>
      </q-item>
      <q-item
        v-else
        clickable
        @click="create_issue_form = true"
      >
        <q-item-section avatar>
          <q-icon name="mdi-plus" />
        </q-item-section>

        <q-item-section>
          <q-item-label>
            {{ $t('issue_field.create.label', { title: inputValue }) }}
          </q-item-label>

          <q-item-label caption>
            <i18n-t keypath="issue_field.create.hint">
              <template #key>
                <kbd>Enter</kbd>
              </template>
            </i18n-t>
          </q-item-label>
        </q-item-section>
      </q-item>
      <!-- Issue creation form would go here -->
      <!-- <IssueForm
        :show="create_issue_form"
        mode="new"
        :force_issue_title="inputValue"
        @close="closeCreateForm"
      >
      </IssueForm> -->
    </template>

  </q-select>
</template>

<script setup>
import { ref, computed } from 'vue';
import { api } from '@/boot/axios';
// import IssueForm from 'app/src/components/issues/IssueForm.vue';

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

  equipment_key: {
    type: String,
    default: undefined,
  },

  issue_type_key: {
    type: String,
    default: undefined,
  },

  can_create: {
    type: Boolean,
    default: false,
  },

  can_search: {
    type: Boolean,
    default: true,
  },

  selection_qt: {
    type: Number,
    default: 1,
  },

  filter_status: {
    type: Array,
    default: null,
  },

  filter_priority: {
    type: Array,
    default: null,
  },

  include_closed: {
    type: Boolean,
    default: false,
  },

  initial_values: {
    type: Object,
    default: null,
  },

  disableKeys: {
    type: Array,
    default: () => [],
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

  minChars: {
    type: Number,
    default: 0,
  },
});

const emit = defineEmits(['select', 'remove']);
const selectRef = ref(null);
const loading = ref(false);
const create_issue_form = ref(false);
const options = ref([]);

const placeholder_computed = computed(() => {
  return props.value ? null : props.placeholder;
});

const multiple = computed(() => {
  return props.selection_qt != null && props.selection_qt > 1;
});

initialize();

function initialize() {
  create_issue_form.value = false;
  if (props.work_order_key || props.product_key || props.equipment_key) {
    loadOptions();
    loading.value = false;
  }
}

function loadOptions(search_value) {
  loading.value = true;
  let params = {
    issue_key_search: search_value,
    limit: 100,
  };

  api.get('issue', { params }).then((resp) => {
    options.value = resp.data
    loading.value = false;
  }).catch((error) => {
    console.error('Error loading issues:', error);
    options.value = [];
    loading.value = false;
  });
}

function remove(value) {
  emit('remove', value);
}

function filter(value, update, abort) {
  if (!props.can_search && props.initial_values) {
    update(() => {
    });
  } else if (value.length < props.minChars && !props.work_order_key && !props.product_key && !props.equipment_key) {
    abort();
  } else {
    update(() => {
      loadOptions(value);
    });
  }
}
</script>
