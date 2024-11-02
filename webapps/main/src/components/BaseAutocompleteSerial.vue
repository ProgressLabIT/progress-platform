<template>
  <q-select
    ref="selectRef"
    use-input
    filled
    :multiple="multiple"
    :use-chips="multiple"
    :max-values="selection_qt || 1"
    :loading="loading"
    :label-slot="!!label"
    :dense="dense"
    :hint="hint"
    :placeholder="placeholder_computed"
    :clearable="clearable"
    :options="options"
    :display-value="value?.code"
    :option-value="keyOnly ? '_key' : null"
    :model-value="value"
    input-debounce="300"
    input-class="text-uppercase"
    :emit-value="keyOnly"
    :map-options="keyOnly"
    @input-value="makeInputUppercase"
    @filter="filter"
    @update:model-value="
      (selection) => {
        $emit('select', selection);
      }
    "
  >
    <template #option="scope">
      <q-item
        v-bind="scope.itemProps"
        :id="scope.opt.label"
        :disable="filtered_values && filtered_values.includes(scope.opt.label)"
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
      {{ label }}
    </template>

    <template #no-option="{ inputValue }">
      <q-item v-if="!can_create">
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
      code_free: false, // Serial code for product is taken (false) or not (true)
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

  watch: {
    initial_values: {
      handler() {
        this.initialize();
      },
    },
  },

  created() {
    this.initialize();
  },

  beforeUnmount() {
    if (this.events) {
      this.events.close();
    }
  },

  methods: {
    initialize() {
      this.create_serial_form = false;
      if (this.work_order || this.product_key) {
        this.loadSerials();
        this.last_research = '';
      }
    },

    makeInputUppercase(value) {
      this.$refs.selectRef.updateInputValue(value.toUpperCase());
    },

    loadSerials(search_value) {
      this.loading = true;
      this.code_free = false;
      let params = {};
      if (this.work_order_key) {
        params.wo_key = this.work_order_key;
      }

      if (this.product_key) {
        params.product_key = this.product_key;
      }

      if (this.batch_key) {
        params.batch_key = this.batch_key;
      }

      if (this.filter_used) {
        params.filter_used = this.filter_used;
      }

      if (search_value) {
        params.search = search_value;
        this.last_research = search_value;
      }
      params.limit = 100;

      if (search_value) {
        this.$api
          .get('serial-code', {
            params: {
              serial_code: search_value,
              product_key: this.product_key,
            },
          })
          .then((resp) => {
            if (resp.data?.length <= 0) {
              this.code_free = true;
            }
            this.$api.get('serial-selection', { params }).then((resp) => {
              this.options = resp.data;
              this.addInitialValues(search_value);
              this.loading = false;
            });
          });
      } else {
        this.$api.get('serial-selection', { params }).then((resp) => {
          this.options = resp.data;
          this.addInitialValues(search_value);
          this.loading = false;
        });
      }
    },

    closeCreateForm() {
      this.create_serial_form = false;
      this.loadSerials(this.last_research);
    },

    addInitialValues(search_value) {
      if (this.initial_values) {
        if (Array.isArray(this.initial_values)) {
          for (const serial of this.initial_values) {
            this.addValue(search_value, serial);
          }
        } else {
          this.addValue(search_value, this.initial_values);
        }
      }
    },

    addValue(search_value, serial) {
      if (
        (!search_value ||
          search_value === '' ||
          serial.label.includes(search_value)) &&
        this.options.filter((value) => value._key == serial._key).length === 0
      ) {
        this.options.push(serial);
      }
    },

    filter(value, update, abort) {
      if (this.last_research === value) {
        update();
      } else if (!this.can_search && this.initial_values) {
        update(() => {
          this.addInitialValues(value);
        });
      } else if (value.length < this.minChars && !this.product_key) {
        abort();
      } else {
        update(() => {
          this.loadSerials(value);
        });
      }
    },
  },
};
</script>
