<template>
  <div>
    <h5 class="mb-6 text-uppercase">Lista di controllo</h5>
    <draggable v-model="step_checks"
      handle=".handle"
      :disabled="!edit_mode"
      @start="drag = true" 
      @end="drag = false"
      v-bind="$store.state.drag_options">
      <transition-group type="transition" :name="!drag ? 'flip-list' : null">
      <div v-for="(check, index) in step_checks" 
        :key="index">
        <v-row  
          v-if="confirming_delete != index"
          @mouseover="over_row=index"
          @mouseleave="over_row=null"> 
          <v-col cols="auto" class="pr-0">
            <v-icon v-if="edit_mode" 
              :color="$theme.white_low"
              :style="drag? 'cursor: grabbing' : 'cursor: grab'"
              class="handle">
              drag_handle
            </v-icon>
            
            <v-icon v-else 
              :color="$theme.white_low">
              check_box_outline_blank
            </v-icon>
          </v-col> 
          
          <v-col cols="10" class="py-0">      
            <v-textarea
              v-if="edit_mode" 
              filled single-line dense auto-grow
              rows="1"
              row-height="36px"
              :value="check"
              @change="udpateCheck(index, $event)"
              class="body-2"
              >
            </v-textarea> 
            <p v-else class="pt-3">{{ check }}</p>
          </v-col>  
          
          <!-- DELETE ICON -->
          <v-col cols="1" v-show="over_row==index" v-if="edit_mode && confirming_delete != index">
            <BaseTooltipIcon
              icon="delete"
              tooltip="Rimuovi controllo"
              :color="$theme.red"
              @iconClick="confirming_delete = index"/>
          </v-col> 
        </v-row>

        <!-- DELETE CHECK CONFIRMATION -->
          
        <v-card v-else outlined class="fill mb-6" >
          <v-row justify="end" class="fill"> 

            <v-col cols="auto" class="pl-3">
              <span class="body-2">Confermi?</span>
            </v-col>  
            <v-col cols="auto">
              <v-btn 
                x-small :color="$theme.red" 
                @click.stop="deleteCheck(index)">
                <v-icon small >delete</v-icon>
              </v-btn>
            </v-col>  
                        
            <v-col cols="auto">
              <v-btn 
                x-small :color="$theme.grey"
                @click.stop="confirming_delete=null">
                <v-icon small>close</v-icon>
              </v-btn>
            </v-col>  

          </v-row>  
        </v-card>
      </div>
    </transition-group>
    </draggable>

    <!-- ADD CHECK -->
    <v-hover v-slot:default="{ hover }">    
      <v-btn text small class="ml-n3"
        v-if="edit_mode"
        :color="hover ? $theme.blue : $theme.white_high"
        @click="addCheck">
         + Aggiungi controllo
      </v-btn>
    </v-hover>

  </div>
</template>

<script>
// import {debounce as _debounce} from 'lodash/fp'
import BaseTooltipIcon from '@/components/BaseTooltipIcon'
import draggable from 'vuedraggable'

export default {

  name: 'StepChecklist',

  components: {
    BaseTooltipIcon,
    draggable
  },

  props: ['phase_index', 'step_index', 'edit_mode'],

  data() {
    return {
      over_row: null,
      drag: false,
      confirming_delete: null
    }
  },

  computed: {

    product_key() {
      return this.$route.params.item_key
    },

    current_step() {
      let procedure = this.$store.state.process.temp[this.phase_index].steps
      return procedure[this.step_index]
    },

    step_checks: {
      get() {
        return this.current_step.checks
      },

      set(value) {
        let phase_index = this.phase_index
        let step_index = this.step_index

        this.$store.commit('UPDATE_STEP_DETAILS', { phase_index, step_index, field: 'checks', value })
      }
    }
  },

  methods: {

    addCheck() {
      let phase_index = this.phase_index
      let step_index = this.step_index

      let new_step = this.current_step
      new_step.checks.push('')
      // Handle cases in which step_checks is null

      this.$store.commit('ADD_OR_UPDATE_STEP', { phase_index, step_index, step_data: new_step })
    },

    udpateCheck(index, text) {
        let phase_index = this.phase_index
        let step_index = this.step_index
        let new_checklist = this.step_checks
        new_checklist[index] = text
        this.$store.commit('UPDATE_STEP_DETAILS', { phase_index, step_index, field: 'checks', value: new_checklist })
    },

    deleteCheck(index) {
      let phase_index = this.phase_index
      let step_index = this.step_index
      let new_checklist = this.step_checks
      new_checklist.splice(index, 1)
      this.$store.commit('UPDATE_STEP_DETAILS', { phase_index, step_index, field: 'checks', value: new_checklist }) 
      this.confirming_delete = null
    }
  },
};
</script>

<style lang="css" scoped>
</style>
