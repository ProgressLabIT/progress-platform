<template>
  <v-container class="fill scroll">
    <v-row class="fill-height">

      <!-- LEFT COLUMN -->
      <v-col cols="4" ref="step_list"
        class="d-flex flex-column px-6 fill">
        
        <!-- STEPS LIST -->
        <h5>SEQUENZA PASSI</h5>
        <v-tabs
          v-if="procedure.length"
          vertical dark hide-slider grow
          v-model="current_steps_map[current_phase]"
          :color="$theme.whitehigh"
          background-color="transparent"
          class="mt-8 scroll"
          style="max-width: 100%; max-height: 70%"
          >
          <!--  -->
          <draggable v-model="procedure" @change="updateTabIndex($event)">
            <transition-group >
              <v-tab
                v-for="(step, index) in procedure"
                :key="index"
                class="d-flex justify-start align-center pl-1 pr-0"
                :class="current_step_no == index ? 'weight-bold' : 'font-weight-regular'"
                style="width: 100%; max-height: 40px; text-transform: none !important; letter-spacing: normal"
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
            <p>Comincia ad aggiungere passi</p>
          </div>
        </v-col>  

        <v-spacer></v-spacer>
        
        <!-- ADD STEPS -->
        <div v-for="type in step_types" :key="type" class="d-flex justify-space-between">
          <button
            :color="$theme.whitehigh"
            class="py-1 weight-medium highlight"
            style="font-size: 14px"
            @click="addStep(type)">
            + Add {{ type }}
          </button>
          <v-icon class="ml-6">{{ stepIcon(type) }}</v-icon>
        </div>


      </v-col>  

      <v-divider vertical ></v-divider>
      
      <!-- RIGHT SECTION: STEP DETAILS -->
      <v-col 
        v-if="procedure.length"
        :style="`height: ${detail_box_height}`"
        class="px-6 scroll">

        <h5 class="mb-2">Titolo</h5>
        <v-text-field
          filled dense
          name="step_title"
          label="Titolo"
          single-line
          v-model="step_title"
          class="body-2"
        ></v-text-field>

        <h5 class="mb-2">Descrizione</h5>
        <v-textarea
          filled single-line dense auto-grow
          rows="2"
          row-height="36px"
          name="step_desc"
          label="Descrizione"
          :value="step_desc"
          @change="updateDesc($event)"
          class="body-2"
        ></v-textarea>


        <component 
          :is="step_component()" 
          :phase_no="current_phase" 
          :step_no="current_step_no"
          class="mt-6"
          />


        <!-- DELETE SECTION -->
        <div style="position: absolute; bottom: 16px; right: 16px; height:12vh; width: 40vw">
          <v-container class="fill">
            <v-row class="fill" align="center" justify="end" v-if="confirmingDelete==false">
              <span 
                class="display smaller weight-bold mr-3" 
                v-show="overDelete"
                :style="'color: ' + $theme.red">
                elimina passo    
              </span>
              <v-btn 
                fab :color="overDelete ? $theme.red : $theme.grey"
                @mouseover="overDelete = true"
                @mouseleave="overDelete = false"
                @click="showConfirmDelete">
                <v-icon>delete</v-icon>
              </v-btn>
            </v-row>  


            <!-- STEP DELETE/RESTORE CONFIRMATION -->

            <v-card outlined v-else elevation="4" class="fill">
                <v-row align="center" class="fill px-4" no-gutters>
                  <v-col cols="auto">
                    <span class="display highlight weight-bold">confermi?</span>
                  </v-col>  
                  <v-spacer></v-spacer>
                  <v-col cols="2">
                    <v-btn 
                      class="mx-2" :color="$theme.red" 
                      @click="deleteStep(current_step_no)">
                      <v-icon>delete</v-icon>
                    </v-btn>
                  </v-col> 
                  <v-col cols="auto" class="ml-4">
                    <v-btn :color="$theme.grey" @click="confirmingDelete = false">
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
      overDelete: false,
      confirmingDelete: false,
    };
  },

  computed: {
    product_key() {
      return this.$route.params.item_key
    },

    productData() {
      return this.$store.getters.productData(this.product_key)
    },

    current_phase() {
      return this.productData.last_phase
    },

    current_steps_map: {
      get() {
        return this.productData.last_steps
      },

      set(value) {
        this.$store.commit(
          'UPDATE_PRODUCT', 
          { _key: this.product_key, last_steps: value}
        )
      }
    },

    current_step_no() {
      return this.current_steps_map[this.current_phase]
    },

    procedure: {
      get() {
        return this.$store.state.current_product.process[this.current_phase].steps
      },

      set(value) {
        let phase_no = this.current_phase
        this.$store.commit('UPDATE_PROCEDURE', { phase_no, procedure: value })
      }
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

      let step = this.current_steps_map[this.current_phase] || 0

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
      let step_no = this.procedure.length
      let step_data = {
        type: type,
        title: '',
        description: '', 
        checks: [],
        input_fields: [],
      }
      this.$store.commit('ADD_OR_UPDATE_STEP', { phase_no, step_no, step_data})
    },

    showConfirmDelete() {
      this.confirmingDelete = true
      this.overDelete = false
    },

    deleteStep(step_no) {
      const phase_no = this.current_phase
      this.$store.commit('DELETE_STEP', { phase_no, step_no })
      this.confirmingDelete = false
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
