<template>
  <v-sheet class="surface-1">
    <v-row class="pa-0">
      <v-col class="py-0">
        <v-tooltip top 
          color="primary"
          open-delay="300">
          <template v-slot:activator="{on}">
            
            <v-switch 
              flat dense hide-details
              v-model="product.active"
              v-on="on"
              class="pa-2 ma-0"/>
          </template>
          <span class="no-transition">
            {{ product.active ? 'Deactivate' : 'Activate' }}
          </span>
        </v-tooltip>
      </v-col>
      <v-spacer></v-spacer>
      <v-col class="d-flex py-0 align-center justify-end">
        <TooltipIcon
          icon="assignment"
          tooltip="Documents"
          :color="$vuetify.theme.themes.dark.colors.green"/>
        <TooltipIcon
          icon="edit"
          tooltip="Details"
          :color="$vuetify.theme.themes.dark.colors.blue"/>
        <TooltipIcon
          icon="delete"
          tooltip="Delete"
          :color="$vuetify.theme.themes.dark.colors.red"/>
      </v-col>
    </v-row>
  </v-sheet>
</template>

<script>
import TooltipIcon from '@/components/TooltipIcon'

export default {

  name: 'ProductActions',
  components: {
    TooltipIcon
  },

  props: ['product'],
  data () {
    return {
      // overSwitch: false
    }
  },

  computed: {
    // switchLabel() {
    //   if (this.overSwitch) {
    //     if (this.product.active) {
    //       return 'Deactivate'
    //     }
    //     else return 'Activate'
    //   }
    //   else return ''
    // }
  }
}
</script>

<style lang="css" scoped>
</style>