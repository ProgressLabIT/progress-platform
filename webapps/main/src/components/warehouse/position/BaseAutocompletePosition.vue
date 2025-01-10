<template>
  <q-select
    use-input
    filled
    :loading="loading"
    :label-slot="!!label"
    :dense="dense"
    :hint="$t('warehouse.position.position_autocomplete_hint')"
    :placeholder="placeholder_computed"
    :clearable="clearable"
    :options="options"
    :display-value="value?.code"
    :option-value="keyOnly ? '_key' : null"
    :model-value="value"
    input-debounce="500"
    :emit-value="keyOnly"
    :map-options="keyOnly"
    @filter="filter"
    @update:model-value="(selection) => $emit('select', selection)"
  >
    <template #option="scope">
      <q-item v-bind="scope.itemProps">
        <q-item-section class="text-h4 highlight col-auto q-pr-md">
          {{ scope.opt.code }}
        </q-item-section>
      </q-item>
    </template>

    <template v-if="!!label" #label>
      {{ label }}
    </template>

    <template #no-option>
      <div class="q-pa-md">No results</div>
    </template>
  </q-select>
</template>

<script>
export default {
  name: 'BaseAutocompletPosition',

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
  },

  emits: ['select'],

  data() {
    return {
      loading: false,
      origin_list: [],
      options: [],
      last_research: undefined,
    };
  },

  computed: {
    placeholder_computed() {
      return this.value ? null : this.placeholder;
    },
  },

  created() {
    this.initialize();
  },

  methods: {
    initialize() {
      if (this.loadData) {
        this.loadPositions();
      }
    },

    loadPositions(search_value) {
      this.loading = true;
      let params = {};

      if (search_value) {
        params.search = search_value;
        this.last_research = search_value;
      }
      params.limit = 100;
      params.open = true;

      this.$api
        .get('position', {
          params,
        })
        .then((resp) => {
          this.options = resp.data;
          this.loading = false;
        });
    },

    filter(value, update) {
      if (this.last_research === value) {
        update();
      } else {
        update(() => {
          this.loadPositions(value);
        });
      }
    },
  },
};
</script>
