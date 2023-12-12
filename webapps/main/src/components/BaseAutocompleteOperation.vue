<template>
  <q-select
    use-input
    filled
    :label="label"
    :dense="dense"
    :clearable="clearable"
    :options="options"
    option-label="name"
    :model-value="value"
    input-debounce="100"
    :option-value="keyOnly ? '_key' : null"
    :emit-value="keyOnly"
    :map-options="keyOnly"
    @filter="filter"
    @update:model-value="(selection) => $emit('select', selection)"
  >
    <template #option="scope">
      <q-item v-bind="scope.itemProps" class="q-px-lg">
        <q-item-section>
          <q-item-label class="text-body1 highlight">
            {{ $capitalize(scope.opt.name) }}
          </q-item-label>
        </q-item-section>
      </q-item>
    </template>
  </q-select>
</template>

<script>
import multiMatch from '@/lib/MultiFieldSearch.js';

export default {
  name: 'BaseAutocompleteOperation',

  props: {
    value: {
      type: [String, Object],
      default: null,
    },

    loadData: {
      type: Boolean,
      default: true,
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

    label: {
      type: String,
      required: true,
    },
  },

  emits: ['select'],

  data() {
    return {
      loading: false,
      options: [],
      search_fields: ['name', 'code'],
    };
  },

  computed: {
    origin_list() {
      return this.$store.state.process.operations;
    },
  },

  created() {
    if (this.loadData) {
      this.loading = true;
      this.$store.dispatch('getOperations').then(() => {
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
        const needle = value.toLowerCase();
        this.options = this.origin_list.filter((option) => {
          return multiMatch(needle, option, this.search_fields);
        });
      });
    },
  },
};
</script>
