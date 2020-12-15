<template>
  <v-row class="fill-height" align="center" justify="center">
    <v-col cols="auto" class="d-flex flex-column justify-center align-center">
      <h3 class="display highlight text-uppercase">{{ title }}</h3>
      <v-progress-circular 
        indeterminate 
        size="40" 
        :color="$theme.blue"
        class="mt-6 mx-auto">
      </v-progress-circular>
    </v-col>
  </v-row>
</template>

<script>
export default {

  name: 'LoadingSignal',

  props: {
    title: {
      type: String,
      default: 'caricamento dati'
    },
  }
}
</script>

<style lang="css" scoped>
</style>