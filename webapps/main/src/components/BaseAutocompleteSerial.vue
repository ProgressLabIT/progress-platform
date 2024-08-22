<template>
  <q-select
    ref="selectRef"
    :work_order="work_order"
    :product="product"
    :product_key="product_key"
    use-input
    filled
    :multiple="multiple"
    :use-chips="multiple"
    :max-values="selection_qt || 1"
    :loading="loading"
    :label-slot="!!label"
    :dense="dense"
    :hint="$t('serial_autocomplete_hint')"
    :placeholder="placeholder_computed"
    :clearable="clearable"
    :options="options"
    :display-value="value?.code"
    :option-value="keyOnly ? '_key' : null"
    :model-value="value"
    input-debounce="500"
    :emit-value="keyOnly"
    :map-options="keyOnly"
    :work_order_key="work_order_key"
    @filter="filter"
    @update:model-value="(selection) => $emit('select', selection)"
  >
    <template #option="scope">
      <q-item v-bind="scope.itemProps" :id="scope.opt.label">
        <q-item-section>
          <q-item-label class="highlight">
            {{ scope.opt.label }}
          </q-item-label>
          <q-item-label caption lines="2">
            {{ scope.opt.value }}
          </q-item-label>
        </q-item-section>
      </q-item>
    </template>

    <template v-if="!!label" #label>
      {{ label }}
    </template>

    <template #no-option="{ inputValue }">
      <q-item v-if="!can_create">
        <q-item-section class="text-low">
          {{ $t('serial_field.noData') }}
        </q-item-section>
      </q-item>
      <q-item v-else-if="inputValue.length < 3">
        <q-item-section class="text-low">
          {{ $t('serial_field.noData_min_char', { minChars: 3 }) }}
        </q-item-section>
      </q-item>
      <q-item v-else clickable @click="create_serial_form = true">
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

<script>
import SerialForm from 'app/src/components/traceability/SerialForm.vue';

export default {
  name: 'BaseAutocompleteSerial',

  components: {
    SerialForm,
  },

  props: {
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

    work_order: {
      type: Object,
      default: undefined,
    },

    work_order_key: {
      type: String,
      default: undefined,
    },

    product: {
      type: Object,
      default: undefined,
    },

    product_key: {
      type: String,
      default: undefined,
    },

    can_create: {
      type: Boolean,
      default: false,
    },

    selection_qt: {
      type: Number,
      default: 1,
    },
    filter_used: {
      type: Boolean,
      default: false,
    },
    initial_values: {
      type: Object,
      default: null,
    },
  },

  emits: ['select'],

  data() {
    return {
      loading: false,
      create_serial_form: false,
      options: [],
      origin_list: [],
      last_research: undefined,
      events: NaN,
    };
  },

  computed: {
    placeholder_computed() {
      return this.value ? null : this.placeholder;
    },
    session_data() {
      return this.$store.state.session;
    },
    multiple() {
      return this.selection_qt != null && this.selection_qt > 1;
    },
  },

  created() {
    this.create_serial_form = false;
    if (this.work_order || this.product_key) {
      this.loadSerials();
      this.last_research = '';
    }
  },

  beforeUnmount() {
    if (this.events) {
      this.events.close();
    }
  },

  methods: {
    loadSerials(search_value) {
      this.loading = true;
      let params = {};
      if (this.work_order?._key || this.work_order_key) {
        params = {
          ...params,
          wo_key: this.work_order?._key || this.work_order_key,
        };
      }
      if (this.product?._key || this.product_key) {
        params = {
          ...params,
          product_key: this.product?._key || this.product_key,
        };
      }
      if (this.filter_used) {
        params = {
          ...params,
          filter_used: this.filter_used,
        };
      }
      if (search_value) {
        params = {
          ...params,
          search: search_value,
          limit: 50,
        };
        this.last_research = search_value;
      }
      this.$api
        .get('serial-selection', {
          params: params,
        })
        .then((resp) => {
          this.options = resp.data;
          this.addInitialValues(search_value);
          this.loading = false;
        });
    },

    closeCreateForm() {
      this.create_serial_form = false;
      this.loadSerials(this.last_research);
    },

    addInitialValues(search_value) {
      if (this.initial_values) {
        for (const serial of this.initial_values) {
          if (
            (!search_value ||
              search_value === '' ||
              serial.label.includes(search_value)) &&
            this.options.filter((value) => value._key == serial._key).length ===
              0
          ) {
            this.options.push(serial);
          }
        }
      }
    },

    filter(value, update, abort) {
      if (this.last_research === value) {
        update();
      } else if (value.length < 3 && !this.product_key) {
        abort();
      } else {
        update(() => {
          this.loadSerials(value);
          // No need of multiFieldSearch here. The api already checks all the necessary fields with a single search term.
        });
      }
    },
  },
};
</script>
