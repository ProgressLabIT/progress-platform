<template>
  <q-select
    use-input
    :dense="dense"
    :hint="hint"
    :loading="loading"
    :filled="filled"
    clearable
    :options="options"
    option-label="code"
    :model-value="value"
    :label="label"
    input-debounce="100"
    :option-value="keyOnly ? '_key' : null"
    :emit-value="keyOnly"
    :map-options="keyOnly"
    @filter="filter"
    @update:model-value="(selection) => $emit('select', selection)"
  >
    <template #option="scope">
      <q-item v-bind="scope.itemProps" :id="scope.opt.code">
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

    label: {
      type: String,
      default: undefined,
    },
    hint: {
      type: String,
      default: undefined,
    },
  },

  emits: ['select'],

  data() {
    return {
      loading: false,
      options: [],
      search_fields: ['code', 'description'],
    };
  },

  computed: {
    origin_list() {
      return this.$store.getters.productCatalog(true);
    },
  },

  created() {
    if (this.loadData) {
      this.loading = true;
      this.$store.dispatch('loadProductList').then(() => {
        this.initOptions();
        this.loading = false;
      });
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
        this.loading = true;
        /*const needle = value.toLowerCase();
        this.options = this.origin_list.filter((option) => {
          this.loading = false;
          return multiMatch(needle, option, this.search_fields);
        });*/
        this.$api
          .get('product', {
            params: {
              search: value,
            },
          })
          .then((resp) => {
            this.options = resp.data;
            this.loading = false;
          });
      });
    },
  },
};
</script>
