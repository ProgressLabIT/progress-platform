<template>
  <v-sheet class="surface-1">
    <v-row class="pa-0">

      <!-- ACTIVE TOGGLE -->
      <v-col class="py-0">        
        <v-tooltip top 
          color="primary"
          open-delay="300">
          <template v-slot:activator="{on}">
            
            <v-switch 
              flat hide-details
              color="primary"
              :input-value="product.active"
              v-on="on"
              @change="toggleActive(product)"
              class="pa-2 ma-0"/>
          </template>
          <span class="no-transition">
            {{ product.active ? 'Deactivate' : 'Activate' }}
          </span>
        </v-tooltip>
      </v-col>

      <v-spacer></v-spacer>

      <!-- OPTIONS -->
      <v-col class="d-flex py-0 align-center justify-end">
       <!--  <TooltipIcon
          icon="assignment"
          tooltip="documents"
          :color="$theme.green"/>
        <TooltipIcon
          icon="edit"
          tooltip="details"
          :color="$theme.blue"/> -->
        <TooltipIcon
          icon="delete"
          tooltip="delete"
          :color="$theme.red"
          @iconClick="confirmDelete"
          />
      </v-col>
    </v-row>
  </v-sheet>
</template>

<script>
import TooltipIcon from '@/components/TooltipIcon'
import { mapActions } from 'vuex'
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

  methods: {
    ...mapActions(['switchActiveState']),

    toggleActive(product) {
      this.switchActiveState(product)
    },

    confirmDelete() {
      // console.log("TRASH CLICKED!")
      this.$emit('showDelete')
    }
  }
}
</script>

<style lang="css" scoped>
</style>