<template>
  <q-select
    :model-value="value"
    :emit-value="keyOnly"
    :map-options="keyOnly"
    :options="
      options.filter(
        (option) => !selected.some(({ _key }) => _key === option._key),
      )
    "
    :option-value="keyOnly ? '_key' : null"
    :option-label="(item) => $capitalize(item.name)"
    use-input
    input-debounce="100"
    :label="label"
    dense
    filled
    @filter="filter"
    @update:model-value="(selection) => $emit('select', selection)"
  >
    <template #option="scope">
      <q-item v-bind="scope.itemProps">
        <q-item-section>
          <q-item-label>
            {{ scope.opt.name }}
          </q-item-label>

          <q-item-label caption :lines="2">
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
  name: 'BaseAutocompleteTemplate',

  props: {
    // TODO: ? selected vs value
    value: {
      type: [Object, String],
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

    label: {
      type: String,
      default: undefined,
    },

    selected: {
      type: Array,
      default: () => [],
    },
  },

  emits: ['select'],

  data() {
    return {
      loading: false,
      templates: [],
      options: [],
    };
  },

  async created() {
    if (!this.loadData) {
      return;
    }

    this.loading = true;
    const { data } = await this.$api.get('print-template');
    this.templates = data;
    this.initOptions();
    this.loading = false;
  },

  methods: {
    initOptions() {
      this.options = [...this.templates];
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
        this.options = this.templates.filter((template) => {
          return multiMatch(needle, template, ['name', 'description']);
        });
      });
    },
  },
};
</script>
