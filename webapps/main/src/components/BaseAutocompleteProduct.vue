<template>
  <q-select
    use-input
    :dense="dense"
    :hint="hint"
    :error="error"
    :error-message="errorMessage"
    :hide-bottom-space="!hint && !error"
    :loading="loading"
    :filled="filled"
    clearable
    :options="options"
    option-label="code"
    :model-value="value"
    :label="label"
    input-debounce="300"
    :option-value="keyOnly ? '_key' : null"
    :emit-value="keyOnly"
    :map-options="keyOnly"
    @filter="filter"
    @update:model-value="(selection) => $emit('select', selection)"
  >
    <template #option="scope">
      <q-item v-bind="scope.itemProps" :id="scope.opt.code" :disable="disableKeys.includes(scope.opt._key)">
        <q-item-section>
          <q-item-label class="highlight">
            {{ scope.opt.code }}
          </q-item-label>
          <q-item-label caption lines="2">
            {{ scope.opt.description }}
          </q-item-label>
        </q-item-section>
      </q-item>
    </template>
  </q-select>
</template>

<script>
export default {
  name: 'BaseAutocompleteProduct',

  props: {
    value: {
      type: [String, Object],
      default: null,
    },

    loadData: {
      type: Boolean,
      default: true,
    },

    filled: {
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

    disableKeys: {
      type: Array,
      default: () => [],
    },

    filterOrigin: {
      type: Function,
      default: (v) => v,
    },

    traceabilityOnly: {
      type: Boolean,
      default: false
    },

    label: {
      type: String,
      default: undefined,
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
  },

  emits: ['select'],

  data() {
    return {
      loading: false,
      options: [],
      last_research: undefined,
      search_fields: ['code', 'description'],
    };
  },

  created() {
    this.initialize();
  },

  methods: {
    initialize() {
      if (this.loadData) {
        this.loadProducts();
      }
    },

    loadProducts(search_value) {
      this.loading = true;
      let params = {};

      if (this.traceabilityOnly) {
        params.traceability_only = true
      }

      if (search_value) {
        params.search = search_value;
        this.last_research = search_value;
      }
      params.limit = 100;

      this.$api
        .get('product', {
          params,
        })
        .then((resp) => {
          this.options = resp.data.filter(this.filterOrigin);
          this.loading = false;
        });
    },

    filter(value, update) {
      if (value === '') {
        this.loadProducts()
      }
      if (this.last_research === value) {
        update();
      } else {
        update(() => {
          this.loadProducts(value);
        });
      }
    },
  },
};
</script>
