<template>
  <q-select
    use-input
    dense
    clearable
    :options="options"
    option-label="code"
    @filter="filter"
    :model-value="value"
    :label="label ?? $capitalize($t('product.label'))"
    input-debounce="100"
    :option-value="key_only ? '_key' : null"
    :emit-value="key_only"
    :map-options="key_only"
    @update:model-value="(selection) => $emit('select', selection)">
    <template #option="scope">
      <q-item v-bind="scope.itemProps" style="max-width: 300px;">
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
import multiMatch from '@/lib/MultiFieldSearch.js'

export default {

  name: 'BaseAutocompleteProduct',

  props: {
    value: {
      type: [String, Object],
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

    label: String
  },

  data () {
    return {
      loading: false,
      options: [],
      search_fields: ['code', 'description']
    }
  },

  computed: {
    origin_list() {
      return this.$store.getters.productCatalog(true)
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
        this.options = this.origin_list.filter(option => {
          return multiMatch(needle, option, this.search_fields)
        })
      })
    },
  },

  created() {
    if (this.load_data) {
      this.loading = true
      this.$store.dispatch('loadProductList').then(() => {
        this.initOptions()
        this.loading = false
      })
    }
  }
}
</script>

<style lang="css" scoped>
</style>
