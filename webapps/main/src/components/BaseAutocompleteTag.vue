<template>
  <q-select
    use-input
    filled
    :label="label"
    :stack-label="stackLabel"
    :dense="dense"
    :placeholder="placeholder_computed"
    :clearable="clearable"
    :options="options"
    option-label="name"
    :option-value="keyOnly ? '_key' : null"
    :model-value="value"
    input-debounce="200"
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
  name: 'BaseAutocompletTag',

  props: {
    value: {
      type: [Object, String],
      default: null,
    },

    loadData: {
      type: Boolean,
      default: true,
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
      default: '',
    },

    stackLabel: {
      type: Boolean,
      default: false,
    },

    showAvatar: {
      type: Boolean,
      default: true,
    },
  },

  emits: ['select'],

  data() {
    return {
      loading: false,
      options: [],
      search_fields: ['name'],
    };
  },

  computed: {
    origin_list() {
      return this.$store.getters.tags();
    },

    placeholder_computed() {
      return this.value ? null : this.placeholder;
    },
  },

  created() {
    if (this.loadData) {
      this.loading = true;
      this.$store.dispatch('loadTags').then(() => {
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
