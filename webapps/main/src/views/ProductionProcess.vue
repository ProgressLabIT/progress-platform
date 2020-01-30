<template>
  <v-container fluid class="px-0 fill">
    <v-row class="fill mx-0 pl-3">      
      

      <!-- ASIDE - PHASE LIST -->            
      <v-col cols="3" class="d-flex flex-column fill">

        <h1 class="display highlight mb-2">{{ productData.code }}</h1>
        <p>{{ productData.description }}</p>

        <h5 class="mt-12 mb-6">FASI PROCESSO</h5>
        <v-tabs
          vertical grow
          v-model="current_phase"
          hide-slider
          :color="$theme.whitehigh"
          background-color="transparent"
          style="max-height: 70%"
          class="scroll"
        >
          <v-tab 
            v-for="(phase, sequence) in process" 
            :key="sequence" 
            class="d-flex justify-start pl-1"
            style="max-height:40px; width: 100%"
            >
            <v-avatar size="20"
              :color="current_phase == sequence ? $theme.blue : $theme.grey"
              class="display smaller weight-bold mr-3">
              {{ sequence + 1 }}
            </v-avatar>
            <h4 class="display weight-medium" 
              :class="current_phase == sequence ? 'highlight weight-bold' : ''">
              {{ phase.operation.name }}
            </h4>
          </v-tab>
        </v-tabs>
        
        <v-spacer></v-spacer>

        <!-- ADD PHASE -->
        <v-select
          id="add_phase"
          ref="add_phase"
          :items="operations"
          :item-text="'description'"
          return-object
          v-model="new_op"
          label="ADD A PHASE"
          hide-details
          single-line
          class="align-end"
          @input="addPhase($event)"
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
            <v-component :is="views[tab].component"></v-component>
          </keep-alive>
        </v-card>
      </v-col>  
      </v-row>
  </v-container>
</template>

<script>
import { mapActions } from 'vuex'
import { api } from '@/lib/apiCall.js'
import PhaseParameters from '@/components/PhaseParameters.vue'
import PhaseSteps from '@/components/PhaseSteps.vue'
import PhaseAssignments from '@/components/PhaseAssignments.vue'


export default {


  name: 'ProductionProcess',

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
      tab:0,
      operations:[],
      new_op: null
    }
  },

  computed: {
    
    product_key() {
      return this.$route.params.item_key
    }, 

    productData() {
      return this.$store.getters.productData(this.product_key)
    },

    current_phase: {
      get() {
        return this.productData.last_phase
      },

      set(value) {
        this.$store.commit(
          'UPDATE_PRODUCT', 
          { _key: this.product_key, last_phase: value}
        )
      }
    },

    process: {
      get() {
        return this.$store.state.current_product.process
      }
    },

  },

  methods: {
    ...mapActions(['loadProductDetails']),

    addPhase(new_operation) {
      let new_process = this.process
      new_process.push({ operation: new_operation, steps: []})
      this.$store.commit('UPDATE_PROCESS', new_process)
      setTimeout(() => {
        this.new_op = null
        this.$refs.add_phase.blur()
      }, 1)
    }
  },


  beforeRouteEnter(to, from, next) {
    // console.log("Before entering route...")
    api.get('operation').then(resp => {
      let op_list = []
      resp.data.forEach(obj => op_list.push(obj))
      next(component => component.operations = op_list)
    })
  },

  created() {
    this.loadProductDetails(this.product_key)
  },

};
</script>

<style lang="css" scoped>
</style>
