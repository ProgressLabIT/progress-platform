<template>
  <v-autocomplete
    :outlined="outlined"
    autocomplete="off"
    auto-select-first
    clearable
    hide-selected
    hide-details
    :value="value"
    :return-object="return_object"
    @change="$emit('select', $event)"
    :loading="loading"  
    :items="department_list"
    single-line
    item-value="_id">
    <template v-slot:label>
      <span :class="text_classes">{{ label }}</span>
    </template>
    <template v-slot:item="{ item: list_item }">
      <v-row align="center" justify="space-between" class="mx-0">
        <span :class="text_classes">
          {{ list_item.name }}
        </span>
        <span class="text-right smaller">
          ({{ list_item.code }})
        </span>
      </v-row>
    </template>
    <template v-slot:selection="{ item: selection }">
      <span :class="text_classes">{{ selection.name }}</span>
    </template>
  </v-autocomplete>
</template>

<script>
export default {

  name: 'BaseAutocompleteDepartment',

  props: {
    label: {
      type: String,
      default: 'Seleziona'
    },
    text_classes: {
      type: String
    },
    return_object: {
      type: Boolean,
      default: false
    },
    load_departments: {
      type: Boolean,
      default: true
    },
    value: {
      deafult: null
    },
    outlined: {
      type: Boolean
    }
  },

  data () {
    return {
      loading: false
    }
  },

  computed: {
    department_list() {
      return [ ...this.$store.state.org.departments, { name: 'Non assegnato', _id: 'none', code: '-' }]
    }
  },

  created() {
    if (this.load_departments) {
      this.loading = true
      this.$store.dispatch('loadDepartments').then(this.loading = false)
    }
  }
}
</script>

<style lang="css" scoped>
</style>