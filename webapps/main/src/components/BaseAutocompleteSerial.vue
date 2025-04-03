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
    option-value="_key'"
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
        :disable="(usedSerials || []).includes(scope.opt._key)"
      >
        <q-item-section>
          <q-item-label class="highlight">
            {{
              scope.opt.code || '(' + $t('serial_code_to_be_assigned') + ')'
            }}
          </q-item-label>
          <q-item-label caption lines="2">
            {{ 'ID ' + scope.opt._key }}
          </q-item-label>
        </q-item-section>
        <q-item-section side v-if="!props.inventory_only">
          <div class="row items-center q-gutter-x-sm">
            <q-icon v-if="scope.opt.used" size="xs" name="mdi-link-variant" />
            <q-icon v-if="!scope.opt.available" size="xs" name="mdi-package-variant-closed-remove" />
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
import { ref, computed } from 'vue';
import { api } from '@/boot/axios';
import SerialForm from 'app/src/components/traceability/SerialForm.vue';

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

  inventory_only: {
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

  usedSerials: {
    type: Array,
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


console.log(props.value);

const emit = defineEmits(['select', 'remove']);
const selectRef = ref(null);
const loading = ref(false);
const create_serial_form = ref(false);
const options = ref([]);
const code_free = ref(false); // Serial code for product is taken (false) or not (true)

const placeholder_computed = computed(() => {
  return props.value ? null : props.placeholder;
});

const multiple = computed(() => {
  return props.selection_qt != null && props.selection_qt > 1;
});

initialize();

function initialize() {
  create_serial_form.value = false;
  if (props.work_order_key || props.product_key) {
    loadOptions();
    loading.value = false;
  }
};

function loadOptions(search_value) {
  loading.value = true;
  code_free.value = false;
  let params = {
    wo_key: props.work_order_key,
    product_key: props.product_key,
    batch_key: props.batch_key,
    free_only: props.filter_used,
    inventory_only: props.inventory_only,
    inventory_in_position_key: props.inventory_in_position_key,
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
            _key: item._key,
            code: item.serial_code || item.code,
            used: item.used,
            available: item.available,
          }));
          loading.value = false;
        });
      });
  } else {
    api.get('serial-selection', { params }).then((resp) => {
      options.value = resp.data.map((item) => ({
        _key: item._key,
        code: item.serial_code || item.code,
        used: item.used,
        available: item.available,
      }));
      loading.value = false;
    });
  }
};

// function loadInventory(search_value) {
//   api.get('inventory', { params: {
//     product_key: props.product_key,
//     root_position_key: props.inventory_in_position_key,
//     serial_search: search_value,
//     limit: 100,
//   }}).then((resp) => {
//     options.value = resp.data.map((item) => ({
//       _key: item.serial_key,
//       code: item.serial_code || item.code,
//       free: true,
//       available: true,
//     }));
//   });
// }


// function loadOptions(search_value) {
//   if (props.inventory_only !== false) {
//     loadInventory(search_value);
//   } else {
//     loadSerials(search_value);
//   }
// }


function closeCreateForm() {
  create_serial_form.value = false;
  // loadSerials(last_research.value);
};


// function addValue(search_value, serial) {
//   if (
//     (!search_value ||
//       search_value === '' ||
//       serial.label.includes(search_value)) &&
//     options.value.filter((value) => value._key == serial._key).length === 0
//   ) {
//     options.value.push(serial);
//   }
// };

function remove(value) {
  emit('remove', value);
}

function filter(value, update, abort) {
  //   if (last_research.value === value) {
  //   update();
  // } else
  if (!props.can_search && props.initial_values) {
    update(() => {
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
