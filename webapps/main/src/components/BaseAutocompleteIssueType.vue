<template>
  <q-select
    use-input
    filled
    :label="$capitalize($t('issue_type'))"
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
        <q-item-section avatar>
          <q-icon :name="scope.opt.icon" size="lg" />
        </q-item-section>
        <q-item-section>
          <q-item-label class="text-body1 highlight">
            {{ $capitalize(scope.opt.name) }}
            <span v-if="scope.opt.code"> ({{ scope.opt.code }}) </span>
          </q-item-label>
          <q-item-label caption>
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
  name: 'BaseAutocompletIssueType',

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
  },

  emits: ['select'],

  data() {
    return {
      loading: false,
      options: [],
      search_fields: ['name', 'code', 'description'],
    };
  },

  computed: {
    origin_list() {
      return this.$store.state.quality.issue_types;
    },
  },

  created() {
    if (this.loadData) {
      this.loading = true;
      this.$store.dispatch('getIssueTypes', true).then(() => {
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
