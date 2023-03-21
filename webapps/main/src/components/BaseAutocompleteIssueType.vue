<template>
  <q-select
    use-input
    :label="$capitalize($t('issue_type'))"
    :dense="dense"
    :clearable="clearable"
    :options="options"
    option-label="name"
    @filter="filter"
    :model-value="value"
    input-debounce="100"
    :option-value="key_only ? '_key' : null"
    :emit-value="key_only"
    :map-options="key_only"
    @update:model-value="(selection) => $emit('select', selection)">
    <template #option="scope">
      <q-item v-bind="scope.itemProps" class="q-px-lg">
        <q-item-section avatar>
          <q-icon :name="scope.opt.icon" size="lg" />
        </q-item-section>
        <q-item-section>
          <q-item-label class="text-body1 highlight">
            {{ $capitalize(scope.opt.name) }}
            <span v-if="scope.opt.code">
              ({{ scope.opt.code }})
            </span>
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
import multiMatch from '@/lib/MultiFieldSearch.js'

export default {

  name: 'BaseAutocompletIssueType',

  props: {
    value: {
      type: Object,
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

    dense: {
      type: Boolean,
      default: false
    },

    clearable: {
      type: Boolean,
      default: true
    }
  },

  data () {
    return {
      loading: false,
      options: [],
      search_fields: ['name', 'code', 'description']
    }
  },

  computed: {
    origin_list() {
      return this.$store.state.issue_types
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
      this.$store.dispatch('getIssueTypes').then(() => {
        this.initOptions()
        this.loading = false
      })
    }
  }
}
</script>

<style lang="css" scoped>
</style>
