<template>
  <q-select
    use-input
    :dense="dense"
    :hint="hint"
    filled
    clearable
    :options="options"
    option-label="code"
    @filter="filter"
    :model-value="value"
    :label="label"
    input-debounce="100"
    :option-value="keyOnly ? '_key' : null"
    :emit-value="keyOnly"
    :map-options="keyOnly"
    popup-content-style="width: 0px"
    @update:model-value="(selection) => $emit('select', selection)"
  >
    <template #option="scope">
      <q-item v-bind="scope.itemProps">
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
import multiMatch from '@/lib/MultiFieldSearch.js';

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

  created() {
    if (this.loadData) {
      this.loading = true;
      this.$store.dispatch('loadProductList').then(() => {
        this.initOptions();
        this.loading = false;
      });
    }
  },
};
</script>

<style lang="css" scoped></style>
