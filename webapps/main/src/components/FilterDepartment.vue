<template>
  <v-autocomplete
    autocomplete="off"
    auto-select-first
    clearable
    hide-selected
    hide-details
    @change="$emit('select', $event)"
    :loading="loading"  
    :items="department_list"
    single-line
    item-value="_id">
    <template v-slot:label>
      <span :class="text_classes">Dipartimento</span>
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
      {{ selection.name }}
    </template>
  </v-autocomplete>
</template>

<script>
export default {

  name: 'FilterDepartment',

  props: {
    text_classes: {
      type: String
    }
  },

  data () {
    return {
      loading: true
    }
  },

  computed: {
    department_list() {
      return [ ...this.$store.state.org.departments, { name: 'Non assegnato', _id: 'none', code: '-' }]
    }
  },

  created() {
    this.$store.dispatch('loadDepartments').then(this.loading = false)
  }
}
</script>

<style lang="css" scoped>
</style>