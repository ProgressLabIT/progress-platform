<template>
  <q-select
    use-input
    :dense="dense"
    :hint="hint"
    :work_order="work_order"
    :product="product"
    filled
    clearable
    :options="options"
    option-label="label"
    :model-value="value"
    :label="label"
    input-debounce="100"
    :option-value="keyOnly ? 'value' : null"
    :emit-value="keyOnly"
    :map-options="keyOnly"
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
  </q-select>
</template>

<script>
import multiMatch from '@/lib/MultiFieldSearch.js';

export default {
  name: 'BaseAutocompleteSerial',

  props: {
    value: {
      type: [String, Object],
      default: null,
    },

    loadData: {
      type: Boolean,
      default: true,
    },

    dense: {
      type: Boolean,
      default: false,
    },

    keyOnly: {
      type: Boolean,
      default: false,
    },

    label: {
      type: String,
      default: undefined,
    },
    hint: {
      type: String,
      default: undefined,
    },

    work_order: {
      type: Object,
      default: undefined,
    },

    product: {
      type: Object,
      default: undefined,
    },
  },

  emits: ['select'],

  data() {
    return {
      loading: false,
      options: [],
      origin_list: [],
      search_fields: ['label'],
    };
  },

  created() {
    if (this.loadData) {
      this.loading = true;
      /*if (this.props.work_order:false) {
        this.$api
          .get(`serial-work_order/${this.props.work_order._key}`)
          .then(() => {
            this.initOptions();
            this.loading = false;
          });
      } else if (this.props.product) {
        this.$api.get(`serial-product/${this.props.product._key}`).then(() => {
          this.initOptions();
          this.loading = false;
        });
      } else {*/
      this.$api.get(`all-serials`).then((resp) => {
        if (resp.data) {
          this.origin_list = resp.data;
        }
        this.loading = false;
      });
      // }
    }
  },

  methods: {
    initOptions() {
      this.options = [...this.origin_list];
    },

    filter(value, update) {
      if (value === '') {
        update(() => {
          this.initOptions();
        });
        return;
      }
      update(() => {
        const needle = value.toLowerCase();
        this.options = this.origin_list.filter((option) => {
          return multiMatch(needle, option, this.search_fields);
        });
      });
    },
  },
};
</script>
