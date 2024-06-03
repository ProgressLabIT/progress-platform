<template>
  <q-select
    :work_order="work_order"
    :product="product"
    use-input
    filled
    :loading="loading"
    :label-slot="!!label"
    :stack-label="stackLabel"
    :dense="dense"
    :hint="$t('serial_autocomplete_hint')"
    :placeholder="placeholder_computed"
    :clearable="clearable"
    :options="options"
    :display-value="value?.serial"
    :option-value="keyOnly ? '_key' : null"
    :model-value="value"
    input-debounce="500"
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
  name: 'BaseAutocompleteSerial',

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
    };
  },

  computed: {
    placeholder_computed() {
      return this.value ? null : this.placeholder;
    },
  },

  methods: {
    filter(value, update, abort) {
      if (value.length < 3) {
        abort();
        return;
      }
      update(() => {
        this.loading = true;
        // No need of multiFieldSearch here. The api already checks all the necessary fields with a single search term.
        this.$api
          .get('serial-selection', {
            params: {
              search: value,
              wo_key: this.work_order?._key,
              product_key: this.product?._key,
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
