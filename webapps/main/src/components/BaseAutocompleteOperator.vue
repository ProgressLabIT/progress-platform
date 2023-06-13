<template>
  <q-select
    use-input
    filled
    :label-slot="!!label"
    :stack-label="stackLabel"
    :dense="dense"
    :placeholder="placeholder_computed"
    :clearable="clearable"
    :options="options"
    :option-label="(operator) => operator.name + ' ' + operator.surname"
    :option-value="key_only ? '_key' : null"
    @filter="filter"
    @clear="$emit('selection', null)"
    :model-value="value"
    input-debounce="200"
    :emit-value="key_only"
    :map-options="key_only"
    @update:model-value="(selection) => $emit('select', selection)">
    <template #option="scope">
      <q-item v-bind="scope.itemProps">
        <BaseUserAvatar :user="scope.opt"/>
      </q-item>
    </template>

    <template #label v-if="!!label">
      {{ label }}
    </template>

    <template #selected-item="scope">
      <BaseUserAvatar :user="scope.opt" :show_avatar="show_avatar" :dense="dense" reverse/>
    </template>
  </q-select>
</template>

<script>
import multiMatch from '@/lib/MultiFieldSearch.js'
import BaseUserAvatar from '@/components/BaseUserAvatar.vue'
export default {

  name: 'BaseAutocompletOperator',

  components: {
    BaseUserAvatar
  },

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
      default: false
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
      options: [],
      search_fields: ['name', 'surname']
    }
  },

  computed: {
    origin_list() {
      return this.$store.getters.operator_list()
    },

    placeholder_computed() {
      return this.value ? null : this.placeholder
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
      this.$store.dispatch('loadUsers').then(() => {
        this.initOptions()
        this.loading = false
      })
    }
  }
}
</script>

<style lang="css" scoped>
</style>
