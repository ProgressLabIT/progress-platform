<template>
  <v-text-field
    append-icon="mdi-magnify"
    hide-details
    single-line
    clearable
    autocomplete="off"
    :label="$tc('search') | capitalize"
    v-model="input"
    @input="$emit('update:input', input)">
    <template v-slot:append>
      <span class="material-icons">search</span>
    </template>
  </v-text-field>
</template>

<script>
export default {

  name: 'BaseSearchBox',

  data () {
    return {
      input: null
    }
  }
}
</script>

<style lang="css" scoped>
</style>
