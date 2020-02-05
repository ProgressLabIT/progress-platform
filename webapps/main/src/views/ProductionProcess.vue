<template>
  <v-container fluid class="px-0 fill">
    <v-row class="fill mx-0 pl-3">      
      

      <!-- ASIDE - PHASE LIST -->            
      <v-col cols="3" class="d-flex flex-column fill pt-1">

        <h1 class="display highlight mb-2">{{ product_data.code }}</h1>
        <p>{{ product_data.description }}</p>

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
          <draggable 
            v-model="process" 
            @change="updateActivePhaseIndex($event)"
            @start="drag = true" 
            @end="drag = false"
            v-bind="$store.state.drag_options">
            <transition-group type="transition" :name="!drag ? 'flip-list' : null">
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
                @mouseover="over_phase=index"
                @mouseleave="over_phase=null"
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
                
                <v-col cols="1" v-show="over_phase==index" class="mr-2">
                  <TooltipIcon
                    icon="delete"
                    tooltip="Elimina fase"
                    :color="$theme.red"
                    @iconClick="confirming_delete = index"
                  ></TooltipIcon>
                </v-col>  

              </v-row>  

              <!-- CONFIRM DELETE PHASE -->
              <v-row 
                v-if="confirming_delete == index"
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
                        @click.stop="confirming_delete=null">
                        <v-icon small>close</v-icon>
                      </v-btn>
                    </v-col>  

                  </v-row>  
                </v-card>

              </v-row>  

            </v-tab>
          </transition-group>
          </draggable>
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
import draggable from 'vuedraggable'


const views_map = [
        { name: 'procedura', component: 'PhaseSteps' },
        { name: 'parametri', component: 'PhaseParameters' },
        { name:  'assegnazioni', component: 'PhaseAssignments' } 
      ]

export default {


  name: 'ProductionProcess',

  components: {
    PhaseParameters,
    PhaseSteps,
    PhaseAssignments,
    TooltipIcon,
    draggable,
  },

  data() {
    return {
      views: views_map,
      tab:0,
      operations:[],
      new_op: null,
      over_phase: null,
      confirming_delete: null,
      drag: false,
    }
  },

  computed: {
    
    product_key() {
      return this.$route.params.item_key
    }, 

    product_data() {
      return this.$store.getters.productData(this.product_key)
    },

    current_phase: {
      get() {
        return this.product_data.last_phase
      },

      set(value) {
        this.$store.commit(
          'UPDATE_PRODUCT_NAV_STATE', 
          { _key: this.product_key, last_phase: value}
        )
      }
    },

    process: {
      get() {
        return this.$store.state.process.phases
      },

      set(value) {
        this.$store.commit('UPDATE_PROCESS', value)
      }
    },

  },

  methods: {
    ...mapActions(['loadProductDetails']),

    addPhase(new_operation) {
      let new_process = this.process
      new_process.push({ operation: new_operation, steps: []})
      this.$store.commit('UPDATE_PROCESS', new_process)
      this.current_phase = new_process.length - 1

      setTimeout(() => {
        this.new_op = null
        this.$refs.add_phase.blur()
      }, 1)
    },

    deletePhase(phase_index) {
      this.$store.commit('DELETE_PHASE', phase_index)
      this.confirming_delete = null
    },

    updateActivePhaseIndex(event) {
      let moved = event.moved
      if (this.current_phase == moved.oldIndex) {
        this.current_phase = moved.newIndex
      }
      else if ( moved.oldIndex < this.current_phase 
                && moved.newIndex > this.current_phase ) {
        this.current_phase = this.current_phase - 1
      }
      else if ( moved.oldIndex > this.current_phase 
                && moved.newIndex < this.current_phase ) {
        this.current_phase = this.current_phase + 1
      }
      // ADD HERE REORDERING OF last_steps MAP
      let new_steps_map = this.product_data.last_steps
      new_steps_map.splice(moved.oldIndex, 1)
      new_steps_map.splice(moved.newIndex, 0, moved.element)

      this.$store.commit('UPDATE_PRODUCT_NAV_STATE', { last_steps: new_steps_map })
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
