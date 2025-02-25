<template>
  <q-select
    ref="selectRef"
    use-input
    filled
    :multiple="multiple"
    :max-values="selection_qt || 1"
    :loading="loading"
    :label-slot="!!label"
    :dense="dense"
    :hint="hint"
    :use-chips="multiple"
    :placeholder="placeholder_computed"
    :clearable="clearable"
    :options="options"
    :option-value="keyOnly ? '_key' : null"
    :model-value="value"
    input-debounce="300"
    input-class="text-uppercase"
    :emit-value="keyOnly"
    :map-options="keyOnly"
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
        :id="scope.opt.label"
        :disable="filtered_values && filtered_values.includes(scope.opt.code)"
      >
        <q-item-section>
          <q-item-label class="highlight">
            {{
              scope.opt.label || '(' + $t('serial_code_to_be_assigned') + ')'
            }}
          </q-item-label>
          <q-item-label caption lines="2">
            {{ 'ID ' + scope.opt.value }}
          </q-item-label>
        </q-item-section>
      </q-item>
    </template>

    <template v-if="!!label" #label>
      <div class="ellipsis">
        {{ label }}
      </div>
    </template>

    <template #no-option="{ inputValue }">
      <q-item v-if="!can_create || inventory_in_position_key">
        <q-item-section class="text-low">
          {{ $t('serial_field.noData') }}
        </q-item-section>
      </q-item>
      <q-item v-else-if="inputValue?.length < minChars">
        <q-item-section class="text-low">
          {{ $t('serial_field.noData_min_char', { minChars }) }}
        </q-item-section>
      </q-item>
      <q-item
        v-else-if="code_free"
        clickable
        @click="create_serial_form = true"
      >
        <q-item-section avatar>
          <q-icon name="mdi-plus" />
        </q-item-section>

        <q-item-section>
          <q-item-label>
            {{ $t('serial_field.create.label', { name: inputValue }) }}
          </q-item-label>

          <q-item-label caption>
            <i18n-t keypath="serial_field.create.hint">
              <template #key>
                <kbd>Enter</kbd>
              </template>
            </i18n-t>
          </q-item-label>
        </q-item-section>
      </q-item>
      <q-item v-else>
        <q-item-section class="text-low">
          {{
            $t('serial_field.create.code_already_used', { name: inputValue })
          }}
        </q-item-section>
      </q-item>
      <SerialForm
        :show="create_serial_form"
        :auto_link_product="product_key"
        mode="new"
        :force_serial_code="inputValue"
        @close="closeCreateForm"
      >
      </SerialForm>
    </template>

  </q-select>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { api } from '@/boot/axios';
import SerialForm from 'app/src/components/traceability/SerialForm.vue';

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

  work_order_key: {
    type: String,
    default: undefined,
  },

  product_key: {
    type: String,
    default: undefined,
  },

  batch_key: {
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

  filter_used: {
    type: Boolean,
    default: false,
  },

  inventory_in_position_key: {
    type: String,
    default: undefined,
  },

  initial_values: {
    type: Object,
    default: null,
  },

  filtered_values: {
    type: Object,
    default: null,
  },

  hint: {
    type: String,
    default: '',
  },

  minChars: {
    type: Number,
    default: 0,
  },
});

const emit = defineEmits(['select', 'remove']);
const selectRef = ref(null);


const loading = ref(false);
const create_serial_form = ref(false);
const options = ref([]);
// const last_research = ref(undefined);
const code_free = ref(false); // Serial code for product is taken (false) or not (true)

const placeholder_computed = computed(() => {
  return props.value ? null : props.placeholder;
});

const multiple = computed(() => {
  return props.selection_qt != null && props.selection_qt > 1;
});

watch(props.initial_values, () => {
  initialize();
});

initialize();

function initialize() {
  create_serial_form.value = false;
  if (props.work_order_key || props.product_key) {
    loadOptions();
    // last_research.value = '';
  }
};

function loadSerials(search_value) {
  loading.value = true;
  code_free.value = false;
  let params = {
    wo_key: props.work_order_key,
    product_key: props.product_key,
    batch_key: props.batch_key,
    filter_used: props.filter_used,
    search: search_value,
    limit: 100,
  };

  if (search_value) {
    api
      .get('serial-code', {
        params: {
          serial_code: search_value,
          product_key: props.product_key,
        },
      })
      .then((resp) => {
        if (resp.data?.length <= 0) {
          code_free.value = true;
        }
        api.get('serial-selection', { params }).then((resp) => {
          options.value = resp.data.map((item) => ({
            label: item.serial_code,
            value: item._key,
            _key: item._key,
            code: item.code,
          }));
          addInitialValues(search_value);
          loading.value = false;
        });
      });
  } else {
    api.get('serial-selection', { params }).then((resp) => {
      options.value = resp.data.map((item) => ({
        label: item.serial_code,
        value: item._key,
        _key: item._key,
        code: item.code,
      }));
      addInitialValues(search_value);
      loading.value = false;
    });
  }
};

function loadInventory(search_value) {
  api.get('inventory', { params: {
    product_key: props.product_key,
    root_position_key: props.inventory_in_position_key,
    serial_search: search_value,
    limit: 100,
  }}).then((resp) => {
    options.value = resp.data.map((item) => ({
      _key: item.serial_key,
      code: item.serial_code,
      label: item.serial_code,
      value: item._key,
    }));
  });
}


function loadOptions(search_value) {
  if (props.inventory_in_position_key) {
    loadInventory(search_value);
  } else {
    loadSerials(search_value);
  }
}


function closeCreateForm() {
  create_serial_form.value = false;
  // loadSerials(last_research.value);
};

function addInitialValues(search_value) {
  if (props.initial_values) {
    if (Array.isArray(props.initial_values)) {
      for (const serial of props.initial_values) {
        addValue(search_value, serial);
      }
    } else {
      addValue(search_value, props.initial_values);
    }
  }
};

function addValue(search_value, serial) {
  if (
    (!search_value ||
      search_value === '' ||
      serial.label.includes(search_value)) &&
    options.value.filter((value) => value._key == serial._key).length === 0
  ) {
    options.value.push(serial);
  }
};

function remove(value) {
  emit('remove', value);
}

function filter(value, update, abort) {
  //   if (last_research.value === value) {
  //   update();
  // } else
  if (!props.can_search && props.initial_values) {
    update(() => {
      addInitialValues(value);
    });
  } else if (value.length < props.minChars && !props.product_key) {
    abort();
  } else {
    update(() => {
      loadOptions(value);
    });
  }
};
</script>
