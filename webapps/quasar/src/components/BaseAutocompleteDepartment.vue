<template>
  <q-select
    use-input
    :options="options"
    :option-label="(item) => $capitalize(item.name)"
    @filter="filterDepartments"
    :model-value="value"
    @update:model-value="(selection) => $emit('select', selection)">
  </q-select>
</template>

<script>
export default {

  name: 'BaseAutocompleteDepartment',

  props: {
    value: {
      type: Object,
      deafult: null
    },

    load_departments: {
      type: Boolean,
      default: true
    }
  },

  data () {
    return {
      loading: false,
      options: []
    }
  },

  computed: {
    department_list() {
      return [ ...this.$store.state.org.departments , {
        name: this.$t("unassigned", 1),
        _key: 'none', 
        code: '-' 
      }]
    }
  },

  methods: {

    initOptions() {
      this.options = [...this.department_list]
    },

    filterDepartments(value, update) {
      if (value === '') {
        update(() => {
          this.initOptions()
        })
        return
      }
      update(() => {
        const needle = value.toLowerCase()
        this.options = this.department_list.filter(d => {
          const include = d.name.toLowerCase().includes(needle)
          return include
        })
      })
    },
  },

  created() {
    if (this.load_departments) {
      this.loading = true
      this.$store.dispatch('loadDepartments').then(() => {
        this.initOptions()
        this.loading = false
      })
    }
  }
}
</script>

<style lang="css" scoped>
</style>
