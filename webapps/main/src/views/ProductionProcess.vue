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
            v-for="(phase, index) in process" 
            :key="index" 
            class="d-flex justify-start pl-1 pr-0"
            style="max-height:40px; width: 100%"
            >
            <v-row 
              align="center" 
              style="width: 100%" 
              no-gutters 
              @mouseover="overPhase=index"
              @mouseleave="overPhase=null"
              class="pr-1">

              <v-col cols="1" class="mr-3">
                <v-avatar size="20"
                  :color="current_phase == index ? $theme.blue : $theme.grey"
                  class="display smaller weight-bold">
                  {{ index + 1 }}
                </v-avatar>
              </v-col>  

              <v-col cols="auto" class="text-left text-truncate">
                <h4 class="display weight-medium" 
                  :class="current_phase == index ? 'highlight weight-bold' : ''">
                  {{ phase.operation.name }}
                </h4>
              </v-col>

              <v-spacer></v-spacer>
              
              <v-col cols="1" v-show="overPhase==index">
                <v-icon>menu</v-icon>  
              </v-col>  
              
              <v-col cols="1">
              </v-col>  
              
              <v-col cols="1" v-show="overPhase==index" class="mr-2">
                <TooltipIcon
                  icon="delete"
                  tooltip="Elimina fase"
                  :color="$theme.red"
                  @iconClick="confirmingDelete = index"
                ></TooltipIcon>
              </v-col>  

            </v-row>  

            <!-- CONFIRM DELETE PHASE -->
            <v-row 
              v-if="confirmingDelete == index"
              style="position:absolute" 
              class="fill mx-n1" >
              
              <v-card outlined elevation="4" class="fill">
                <v-row no-gutters align="center" class="fill">  

                  <v-col cols="auto" class="pl-3">
                    <span class="display highlight weight-bold">Confermi?</span>
                  </v-col>  
                
                  <v-spacer></v-spacer>
                
                  <v-col cols="2">
                    <v-btn 
                      x-small :color="$theme.red" 
                      @click.stop="deletePhase(index)">
                      <v-icon small >delete</v-icon>
                    </v-btn>
                  </v-col>  
                
                  <v-col cols="2">
                    <v-btn 
                      x-small :color="$theme.grey"
                      @click.stop="confirmingDelete=null">
                      <v-icon small>close</v-icon>
                    </v-btn>
                  </v-col>  

                </v-row>  
              </v-card>

            </v-row>  

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
import TooltipIcon from '@/components/TooltipIcon.vue'


export default {


  name: 'ProductionProcess',

  components: {
    PhaseParameters,
    PhaseSteps,
    PhaseAssignments,
    TooltipIcon
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
      new_op: null,
      overPhase: null,
      confirmingDelete: null
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
    },

    deletePhase(phase_index) {
      this.$store.commit('DELETE_PHASE', phase_index)
      this.confirmingDelete = null
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
