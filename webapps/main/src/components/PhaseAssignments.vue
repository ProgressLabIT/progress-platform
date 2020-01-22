<template>
  <v-container>
    <h3 class="display">assignments</h3>
  </v-container>
</template>

<script>
import { mapState } from 'vuex'

export default {

  name: 'PhaseAssignments',

  props: ['phase'],

  data () {
    return {

    }
  },

  computed: {
    ...mapState({
      current_step: state => state.current_product.current_step
    })
  }
}
</script>

<style lang="css" scoped>
</style>