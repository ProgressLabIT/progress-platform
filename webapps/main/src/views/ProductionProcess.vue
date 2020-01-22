<template>
  <v-container fluid fill-height class="px-0">
    <v-row class="fill mx-0 pl-3">      
      

      <!-- ASIDE - PHASE LIST -->            
      <v-col cols="3" class="d-flex flex-column">

        <h1 class="display highlight mb-2">{{ product.code }}</h1>
        <p>{{ product.description }}</p>

        <h5 class="mt-12 mb-6">FASI PROCESSO</h5>
        <v-tabs
          vertical 
          v-model="current_phase"
          hide-slider
          :color="$theme.whitehigh"
          background-color="transparent"
        >
          <v-tab 
            v-for="(phase, sequence) in process_data" 
            :key="sequence" 
            class="d-flex justify-start pl-1"
            style="height:38px; width: 100%"
            >
            <v-avatar size="20"
              :color="current_phase == sequence ? $theme.blue : $theme.grey"
              class="display smaller weight-bold mr-3">
              {{ sequence + 1 }}
            </v-avatar>
            <h4 class="display weight-medium" 
              :class="current_phase == sequence ? 'highlight weight-bold' : ''">
              {{ phase.operation }}
            </h4>
          </v-tab>
        </v-tabs>
        
        <v-spacer></v-spacer>

        <v-select
          id="operations"
          :items="operations"
          label="ADD A PHASE"
          hide-details
          single-line
          class="align-end"
          ></v-select>

      <!-- PHASE DETAILS -->
      </v-col>  
      <v-col cols="9" class="fill d-flex flex-column pl-6 py-0">
        <v-row dense class="flex-grow-0">
          <v-tabs
            v-model="tab"
            background-color="transparent"
            :color="$theme.whitehigh"
            hide-slider right
            class="flex-shrink-1 flex-grow-0"
          >
        <v-tab 
          v-for="(view, idx) in views" 
          :key="idx"
          class="display"
          >
          {{ view.name }}
        </v-tab>
        </v-tabs>
      </v-row>  
        <v-card elevation="0" class="scroll flex-grow-1">
          <keep-alive>
            <v-component 
              :is="views[tab].component" 
              :product_key="item_key"
              :current_phase="current_phase"
              >
            </v-component>
          </keep-alive>
        </v-card>
      </v-col>  
      </v-row>
  </v-container>
</template>

<script>
import { mapState, mapActions } from 'vuex'
import { api } from '@/lib/apiCall.js'
import PhaseParameters from '@/components/PhaseParameters.vue'
import PhaseSteps from '@/components/PhaseSteps.vue'
import PhaseAssignments from '@/components/PhaseAssignments.vue'


export default {


  name: 'ProductionProcess',

  props: ['item_key'],

  components: {
    PhaseParameters,
    PhaseSteps,
    PhaseAssignments
  },

  data() {
    return {
      views: [
        {
          name: 'procedura',
          component: 'PhaseSteps',
        },
        {
          name: 'parametri',
          component: 'PhaseParameters',
        },
        {
          name:  'assegnazioni',
          component: 'PhaseAssignments'
        } 
      ],
      tab:0
    }
  },

  computed: {
    ...mapState({
      product: state => state.current_product.metadata, 
      process_data: state => state.current_product.process_data
    }),

    current_phase: {
      get() {
        return this.$store.state.products.find(p => p._key == this.product._key).last_phase
      },

      set(value) {
        this.$store.commit(
          'UPDATE_PRODUCT', 
          { _key: this.product._key, last_phase: value}
        )
      }
    },

    // tab: {
    //   get() {
    //     return this.$store.state.products.find(p => p._key == this.product._key).last_process_tab
    //   },

    //   set(value) {
    //     this.$store.commit(
    //       'UPDATE_PRODUCT',
    //       { _key: this.product._key, last_process_tab: value }
    //     )
    //   }
    // }

  },

  methods: {
    ...mapActions(['loadProductDetails'])
  },

  created() {
    this.loadProductDetails(this.item_key)
  },

  beforeRouteEnter(to, from, next) {
    api.get('operation').then(resp => {
      let op_list = []
      resp.data.forEach(obj => op_list.push(obj.description))
      next(component => component.operations = op_list)
    })
  }

};
</script>

<style lang="css" scoped>
</style>
