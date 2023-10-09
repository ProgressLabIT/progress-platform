<template>
  <q-select
    use-input
    dense
    filled
    :label="label"
    :options="options.filter(o => !selected.some(s => s?._key == o._key))"
    :option-label="(item) => $capitalize(item.name)"
    @filter="filter"
    :model-value="value"
    input-debounce="100"
    :option-value="key_only ? '_key' : null"
    :emit-value="key_only"
    :map-options="key_only"
    @update:model-value="(selection) => $emit('select', selection)">
    <template #option="scope">
      <q-item v-bind="scope.itemProps">
        <q-item-section>
          <q-item-label>
            {{ scope.opt.name }}
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
import multiMatch from '@/lib/MultiFieldSearch.js'

export default {

  name: 'BaseAutocompleteTemplate',

  props: {
    value: {
      type: [Object, String],
      deafult: null
    },

    load_data: {
      type: Boolean,
      default: true
    },

    key_only: {
      type: Boolean,
      default: false
    },

    label: {
      type: String,
    },

    selected: {
      type: Array,
      default: []
    }
  },

  data () {
    return {
      loading: false,
      origin_list: [],
      options: []
    }
  },

  methods: {

    initOptions() {
      this.options = [...this.origin_list]
    },

    filter(value, update) {
      if (value === '') {
        update(() => {
          this.initOptions()
        })
        return
      }
      update(() => {
        const needle = value.toLowerCase()
        this.options = this.origin_list.filter(o => {
          return multiMatch(needle, o, ['name', 'description'])
        })
      })
    },
  },

  created() {
    if (this.load_data) {
      this.loading = true
      this.$api.get('print-template').then(resp => {
        this.origin_list = resp.data
        this.initOptions()
        this.loading = false
      })
    }
  }
}
</script>

<style lang="css" scoped>
</style>
