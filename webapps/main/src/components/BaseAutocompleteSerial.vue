<template>
  <q-select
    ref="selectRef"
    :work_order="work_order"
    :product="product"
    :product_key="product_key"
    use-input
    filled
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
          {{ $t('serialInput.noData') }}
        </q-item-section>
      </q-item>
      <q-item v-else clickable @click="createAndAddNewSerial(inputValue)">
        <q-item-section avatar>
          <q-icon name="mdi-plus" />
        </q-item-section>

        <q-item-section>
          <q-item-label>
            {{ $t('serialInput.create.label', { name: inputValue }) }}
          </q-item-label>

          <q-item-label caption>
            <i18n-t keypath="serialInput.create.hint">
              <template #key>
                <kbd>Enter</kbd>
              </template>
            </i18n-t>
          </q-item-label>
        </q-item-section>
      </q-item>
    </template>
  </q-select>
</template>

<script>
import { timestamp } from '@/lib/TimeHandling.js';

export default {
  name: 'BaseAutocompleteSerial',

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
  },

  emits: ['select'],

  data() {
    return {
      loading: false,
      options: [],
      origin_list: [],
      last_research: undefined,
    };
  },

  computed: {
    placeholder_computed() {
      return this.value ? null : this.placeholder;
    },
    session_data() {
      return this.$store.state.session;
    },
  },

  created() {
    if (this.work_order || this.product_key) {
      this.loadSerials();
      this.last_research = '';
    }
  },

  methods: {
    loadSerials(search_value) {
      this.loading = true;
      let params = {
        wo_key: this.work_order?._key || this.work_order_key,
        product_key: this.product?._key || this.product_key,
      };
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
          this.loading = false;
        });
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

    async createAndAddNewSerial(serial_code) {
      await this.createNewSerial(serial_code);
      this.$refs.selectRef.hidePopup();
    },

    async createNewSerial(serial_code) {
      let serial_data = {};

      const user = this.session_data.user._key;

      serial_data.created_by = `User/${user}`; // temporarily hardcoding DB id
      serial_data.product_key = this.product_key;
      serial_data.user_key = this.session_data.user._key;
      serial_data.code = serial_code;
      serial_data.data = [];

      const event = {
        event_type: 'SERIAL_CREATED',
        user_key: user,
        user_session_key: this.session_data.session_key,
        timestamp: timestamp(),
        serial_data,
      };

      await this.$api.post('event', event);
    },
  },
};
</script>
