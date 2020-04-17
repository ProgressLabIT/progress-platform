<template>
  <!-- <v-card class="flex-grow-1 scroll" color="transparent"> -->
    <v-container fluid class="pa-0 fill" ref="step_card">

      <v-card class="fill d-flex flex-column" max-height="100%" >
        <v-toolbar dense class="flex-grow-0">
          <v-row align="center" class="fill-height mx-0" ref="stepper">
            <!-- <v-col cols="auto">
              <h5 class="highlight text-uppercase mr-6">lotto n. {{ 3 }}</h5>
            </v-col> -->
            <template v-for="(step, index) in procedure">
              <v-col 
                cols="auto" 
                class="px-1"
                :key="step._id">
                <v-avatar 
                  :color="current_step_index == index ? $theme.blue : 'transparent'" 
                  size="20" 
                  class="d-flex text-center smaller font-weight-medium pointer"
                  @click="current_step_index = index">
                  <span :class="current_step_index == index ? 'solid-white weight-bold': ''">{{ index + 1 }}</span>
                </v-avatar>
              </v-col>
              <v-divider 
                v-if="index < procedure.length - 1"
                :key="index">
              </v-divider>
            </template>
            <!-- <v-col cols="auto">
              <h5 class="ml-6 highlight text-uppercase">
                passo {{ current_step_index + 1 }} / {{ procedure.length}}
              </h5>
            </v-col> -->
          </v-row>
        </v-toolbar>
        
        <component 
          :is="step_component" 
          :step="current_step" 
          :height="image_height">
        </component>

      </v-card>
    </v-container>
  <!-- </v-card> -->
</template>

<script>
import { cloneDeep as _cloneDeep } from 'lodash'

import JobInstruction from '@/components/JobInstruction.vue'
import JobForm from '@/components/JobForm.vue'
import JobChecklist from '@/components/JobChecklist.vue'

export default {

  name: 'WorkSessionSteps',

  components: {
    JobInstruction,
    JobForm,
    JobChecklist,
  },

  props: {
    parameters: {
      type: Object,
      default: () => {
        return { 
          step_check: 'single',
          step_check_force_order: false,
          release_style: 'job',
          production_batch_qt: 1,        
        }
      }
    },

    procedure: {
      type: Array,
      default: () => []
    },
  },

  data () {
    return {
      current_step_index: 0,
      stepper_height: 0,
      image_height: 0,
    }
  },

  computed: {
    current_step() {
      return this.procedure[this.current_step_index]
    },

    step_component() {
      let component = ''
      switch (this.current_step.type) {
        case 'instruction':
          component = 'JobInstruction'
          break
        case 'checklist':
          component = 'JobChecklist'
          break
        case 'form':
          component = 'JobForm'
          break
      }
      return component
    },
   
  },

  methods: {
    startRun() {
      this.runs.push(_cloneDeep(this.procedure))
    },
  },

  mounted() {
    const stepper_height = this.$refs.stepper.clientHeight
    const card_height = this.$refs.step_card.clientHeight
    this.image_height = card_height - stepper_height
  },

}
</script>

<style lang="css" scoped>
</style>