<template>
  <v-sheet class="surface-1">
    <v-switch 
      @mouseover="overSwitch = true"
      @mouseleave="overSwitch = false"
      flat dense hide-details
      v-model="product.active"
      :label="switchLabel"
      class="pa-2 ma-0"
      />
  </v-sheet>
</template>

<script>
export default {

  name: 'ProductActions',
  props: ['product'],
  data () {
    return {
      overSwitch: false
    }
  },

  computed: {
    switchLabel() {
      if (this.overSwitch) {
        if (this.product.active) {
          return 'Deactivate'
        }
        else return 'Activate'
      }
      else return ''
    }
  }
}
</script>

<style lang="css" scoped>
</style>