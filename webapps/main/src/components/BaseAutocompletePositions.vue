<template>
  <q-select
    use-input
    filled
    :label="label"
    :disable="disable"
    :dense="dense"
    :clearable="clearable"
    :options="options"
    option-label="code"
    :model-value="value"
    input-debounce="400"
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
            {{ $capitalize(scope.opt.code) }}
          </q-item-label>
        </q-item-section>
      </q-item>
    </template>
  </q-select>
</template>

<script>
export default {
  name: 'BaseAutocompletePositions',

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

    disable: {
      type: Boolean,
      default: false,
    },
  },

  emits: ['select'],

  data() {
    return {
      loading: false,
      last_research: '',
      options: [],
    };
  },

  computed: {},

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
