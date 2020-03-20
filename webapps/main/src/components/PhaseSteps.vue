<template>
  <v-container class="fill scroll">
    <v-row class="fill-height">

      <!-- LEFT COLUMN -->
      <v-col cols="4" ref="step_list"
        class="d-flex flex-column px-6 fill">
        
        <!-- STEPS LIST -->
        <h5>SEQUENZA PASSI</h5>
        <v-tabs
          v-if="render_steps"
          vertical dark hide-slider grow
          v-model="current_step_no"
          :color="$theme.whitehigh"
          background-color="transparent"
          class="mt-8 scroll px-n4"
          style="max-width: 100%; max-height: 70%"
          >
          <!--  -->
          <draggable 
            v-model="procedure" 
            :disabled="!edit_mode"
            @change="updateTabIndex($event)"
            @start="drag = true" 
            @end="drag = false"
            v-bind="$store.state.drag_options">
            <transition-group type="transition" :name="!drag ? 'flip-list' : null">
              <v-tab
                v-for="(step, index) in procedure"
                :key="index"
                class="d-flex justify-start align-center pl-1 pr-0"
                :class="current_step_no == index ? 'weight-bold' : 'font-weight-regular'"
                style="width: 100%; max-height: 40px; text-transform: none !important; letter-spacing: normal"
                @click="confirming_delete = false"
                >
                <v-row align="center" style="width: 100%" no-gutters class="pr-1">

                  <v-col cols="1" class="mr-3">        
                    <v-avatar
                      size="20"
                      :color="current_step_no == index ? $theme.blue : $theme.grey"
                      class="d-flex text-center smaller weight-bold"
                      >{{ index + 1 }}
                    </v-avatar>
                  </v-col>  

                  <v-col cols="9" class="text-left text-truncate">
                    <span style="max-width: 80%">
                      {{ step.title.length ? step.title : '(nessun titolo)' }}
                    </span>
                  </v-col>

                  <v-spacer></v-spacer>

                  <v-col cols="1">
                    <v-icon 
                      :id="`icon-${index}`"
                      class="ml-auto"
                      :color="current_step_no == index ? $theme.whitehigh : $theme.whitelow">
                      {{ stepIcon(step.type) }}
                    </v-icon>
                  </v-col>    
                </v-row>    
              </v-tab>
            </transition-group>
          </draggable>
        </v-tabs>

        <!-- NO STEPS IN PROCEDURE -->
        <v-col v-else>
          <v-row justify="center" align="end" class="mt-12 pb-6">
            <v-icon 
              x-large 
              :color="$theme.whitelow"
              >
              error_outline
            </v-icon>
          </v-row>
          <div class="text-center">
            <h3>NESSUNA PROCEDURA</h3>
            <p>Comincia ad aggiungere fasi o passi</p>
          </div>
        </v-col>  

        <v-spacer></v-spacer>
        
        <!-- ADD STEPS -->
        <div v-if="edit_mode && typeof phase != 'undefined'">
          <v-hover 
            v-for="type in step_types" 
            :key="type"  
            v-slot:default="{ hover }">    
            <v-btn text small
              class="pr-6 pl-6 ml-n2"
              style="width: 105%"
              :color="hover ? $theme.blue : $theme.whitehigh"
              @click="addStep(type)">
              <v-row justify="space-between" align="center">
                <span>+ Add {{ type }}</span>
                <v-icon>{{ stepIcon(type) }}</v-icon>
              </v-row>
            </v-btn>
          </v-hover>
        </div>


      </v-col>  

      <v-divider vertical ></v-divider>
      
      <!-- RIGHT SECTION: STEP DETAILS -->
      <v-col 
        v-if="render_steps"
        :style="`height: ${detail_box_height}`"
        class="px-6 scroll">

        <h5 class="mb-2">Titolo</h5>
        <v-text-field
          v-if="edit_mode"
          filled dense
          name="step_title"
          label="Titolo"
          single-line
          v-model="step_title"
          class="body-2"
        ></v-text-field>
        <p v-else class="mb-10 mt-4">{{ step_title }}</p>

        <h5 class="mb-2">Descrizione</h5>
        <v-textarea
          v-if="edit_mode"
          filled single-line dense auto-grow
          rows="2"
          row-height="36px"
          name="step_desc"
          label="Descrizione"
          :value="step_desc"
          @change="updateDesc($event)"
          class="body-2"
        ></v-textarea>
        <p v-else class="mb-10 mt-4">{{ step_desc }}</p>



        <component 
          :is="step_component()" 
          :phase_no="current_phase" 
          :step_no="current_step_no"
          :edit_mode="edit_mode"
          class="mt-6"
          />


        <!-- DELETE SECTION -->
        <div v-if="edit_mode" style="position: absolute; bottom: 0px; right: 0px; height:12vh; width: 35%">
          <v-container class="fill">
            <v-row class="fill" align="center" justify="end" v-if="confirming_delete==false">
              <span
                class="display smaller weight-bold mr-3 pa-2" 
                v-show="over_delete"
                :style="'color: white; background-color: ' + $theme.red">
                elimina passo    
              </span>
              <v-btn 
                fab small :color="over_delete ? $theme.red : $theme.grey"
                @mouseover="over_delete = true"
                @mouseleave="over_delete = false"
                @click="showConfirmDelete">
                <v-icon>delete</v-icon>
              </v-btn>
            </v-row>  


            <!-- STEP DELETE/RESTORE CONFIRMATION -->

            <v-card v-else outlined elevation="4">
                <v-row align="center" justify="space-between" class="px-4">
                  <v-col cols="auto">
                    <span class="display medium highlight weight-bold">confermi?</span>
                  </v-col>  
                  <!-- <v-spacer></v-spacer> -->
                  <v-col cols="auto">
                    <v-btn fab small
                      :color="$theme.red" 
                      @click="deleteStep(current_step_no)"
                      class="mr-2">
                      <v-icon>delete</v-icon>
                    </v-btn>
                    <v-btn fab small 
                      :color="$theme.grey" 
                      @click="confirming_delete = false">
                      <v-icon>close</v-icon>
                    </v-btn>
                  </v-col>   
                </v-row>
            </v-card>

          </v-container>
        </div>
        
      </v-col>  
    </v-row>  

  </v-container>
</template>

<script>
import StepInstruction from '@/components/StepInstruction.vue'
import StepChecklist from '@/components/StepChecklist.vue'
import StepForm from '@/components/StepForm.vue'
import draggable from 'vuedraggable'

export default {

  name: 'PhaseSteps',

  props: ['edit_mode', 'phase', 'product_data'],

  components: {
    StepInstruction,
    StepChecklist,
    StepForm,
    draggable
  },

  data() {
    return {
      step_types: ['instruction', 'checklist', 'form'],
      detail_box_height: '79vh',
      over_delete: false,
      confirming_delete: false,
      drag: false,
    };
  },

  computed: {
    product_key() {
      return this.$route.params.product_key
    },

    current_phase() {
      return this.product_data.last_phase
    },

    current_steps_map: {
      get() {
        return this.product_data.last_steps
      },

      set(value) {
        this.$store.commit(
          'UPDATE_PRODUCT_NAV_STATE', 
          { _key: this.product_key, last_steps: value}
        )
      }
    },

    current_step_no: {
      get() {
        return this.current_steps_map[this.current_phase]
      },
      set(value) {
        this.$set(this.current_steps_map, this.current_phase, value)
      }
    },

    procedure: {
      get() {
        return this.phase ? this.phase.steps : null
      },

      set(value) {
        let phase_no = this.current_phase
        this.$store.commit('UPDATE_PROCEDURE', { phase_no, procedure: value })
      }
    },

    render_steps() {
      if (this.procedure != null) {
        if (this.procedure.length) {
          return true
        }
        else return false
      }
      else return false
    },

    current_step() {
      const last_step_viewed = this.procedure[this.current_step_no]
      return typeof last_step_viewed === 'undefined' ? 0 : last_step_viewed
    },

    step_title: {
      get() {
        return this.current_step.title
      },

      set(value) {
        let phase_no = this.current_phase
        let step_no = this.current_steps_map[phase_no]
        this.$store.commit('UPDATE_STEP_DETAILS', { phase_no, step_no, field: 'title', value })
      }
    },

    step_desc() {
        return this.current_step.description
    },
  },

  methods: {
    stepIcon(step_type) {
      switch (step_type) {
        case 'instruction': return 'playlist_add_check';
        case 'checklist': return 'mdi-format-list-checks';
        case 'form': return 'mdi-playlist-edit';
        default: return '';
      }
    },

    step_component() {
      const step_no = this.current_steps_map[this.current_phase]
      const step = typeof step_no == 'undefined' ? 0 : step_no

      switch (this.procedure[step].type) {
        case 'instruction': return 'StepInstruction';
        case 'checklist': return 'StepChecklist';
        case 'form': return 'StepForm';
        default: return '';
      }
    },

    updateDesc(value) {
      let phase_no = this.current_phase
      let step_no = this.current_steps_map[phase_no]
      // console.log(`Committing new description at phase ${phase_no}, step ${step_no}. New value: ${value}`)
      this.$store.commit('UPDATE_STEP_DETAILS', { phase_no, step_no, field: 'description', value })
    },

    addStep(type) {
      let phase_no = this.current_phase
      let step_no = this.procedure ? this.procedure.length : 0
      let step_data = {
        type: type,
        title: '',
        description: '', 
        checks: [],
        input_fields: [],
        media: []
      }
      this.$store.commit('ADD_OR_UPDATE_STEP', { phase_no, step_no, step_data})
      let new_step_index = this.procedure.length - 1
      this.current_step_no = new_step_index
    },

    showConfirmDelete() {
      this.confirming_delete = true
      this.over_delete = false
    },

    deleteStep(step_no) {
      const phase_no = this.current_phase
      const len = this.procedure.length
      // if step to be deleted is last, set next step index to second to last
      if (step_no == len-1) {
        const next_step_no = len > 1 ? len - 2 : 0
        this.$set(this.current_steps_map, this.current_phase, next_step_no)
      }
      this.$store.commit('DELETE_STEP', { phase_no, step_no })
      this.confirming_delete = false

    },

    updateTabIndex(event) {
      let moved = event.moved
      if (this.current_step_no == moved.oldIndex) {
        this.$set(this.current_steps_map, this.current_phase, moved.newIndex)
      }
      else if ( moved.oldIndex < this.current_step_no 
                && moved.newIndex > this.current_step_no ) {
        let new_step_no = this.current_step_no - 1
        this.$set(this.current_steps_map, this.current_phase, new_step_no)
      }
      else if ( moved.oldIndex > this.current_step_no 
                && moved.newIndex < this.current_step_no ) {
        let new_step_no = this.current_step_no + 1
        this.$set(this.current_steps_map, this.current_phase, new_step_no)
      }
    }
  },
};
</script>

<style lang="css" scoped>
</style>
