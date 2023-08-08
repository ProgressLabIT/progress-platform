<template>
  <q-select
    use-input
    filled
    :loading="loading"
    :label-slot="!!label"
    :stack-label="stackLabel"
    :dense="dense"
    :hint="$t('work_order_autocomplete_hint')"
    :placeholder="placeholder_computed"
    :clearable="clearable"
    :options="options"
    :display-value="value?.wo_code"
    :option-value="key_only ? '_key' : null"
    @filter="filter"
    @clear="$emit('selection', null)"
    :model-value="value"
    input-debounce="500"
    :emit-value="key_only"
    :map-options="key_only"
    @update:model-value="(selection) => $emit('select', selection)"
    popup-content-class="full-width">
    <template #option="scope">
      <q-item v-bind="scope.itemProps">
        <q-item-section class="text-h4 highlight">
          {{ scope.opt.wo_code }}
        </q-item-section>
        <q-item-section>
          <q-item-label>
            {{ scope.opt.product_code }}
          </q-item-label>
          <q-item-label caption class="smaller text-uppercase">
            {{ scope.opt.product_description }}
          </q-item-label>
        </q-item-section>
        <q-item-section>
          x{{ scope.opt.qt_planned }}
        </q-item-section>
        <q-item-section class="ellipsis">
          {{ scope.opt.project_code }}
        </q-item-section>
      </q-item>
    </template>

    <template #label v-if="!!label">
      {{ label }}
    </template>

    <template #no-option>
      <div class="q-pa-md">
        No results
      </div>
    </template>
  </q-select>
</template>

<script>
export default {

  name: 'BaseAutocompletWorkOrder',

  props: {
    value: {
      type: [Object, String],
      deafult: null
    },

    load_data: {
      type: Boolean,
      default: true
    },

    label: {
      type: String,
      default: ''
    },

    key_only: {
      type: Boolean,
      default: false
    },

    operator_only: {
      type: Boolean,
      default: true
    },

    dense: {
      type: Boolean,
      default: false
    },

    clearable: {
      type: Boolean,
      default: true
    },

    placeholder: {
      type: String,
      default: null
    },

    stackLabel: {
      type: Boolean,
      default: false
    },

    show_avatar: {
      type: Boolean,
      default: true
    }
  },

  data () {
    return {
      loading: false,
      origin_list: [],
      options: []
    }
  },

  computed: {
    placeholder_computed() {
      return this.value ? null : this.placeholder
    }
  },

  methods: {
    filter(value, update, abort) {
      if (value.length < 3) {
        abort()
        return
      }
      update(() => {
        this.loading = true
        const needle = value.toLowerCase()
        // No need of multiFieldSearch here. The api already checks all the necessary fields with a single search term.
        this.$api
          .get('work-order-archive', { params: { search: value, open: true }})
          .then((resp) => {
            this.options = resp.data
            this.loading = false
          })
      })
    },
  }
}
</script>

<style lang="css" scoped>
</style>
