<template>
  <v-container fluid class="pa-0 fill" ref="step_card">

    <v-card class="fill d-flex flex-column" max-height="100%" >
      <v-toolbar dense class="flex-grow-0">
        <v-row align="center" class="fill-height mx-0" ref="stepper">
         
          <template v-for="(step, index) in procedure">
            <v-col 
              cols="auto" 
              class="px-1"
              :key="step._id">
              <v-avatar  
                size="20" 
                :style="stepStyle(index)"
                class="d-flex text-center smaller font-weight-medium"
                @click="stepClick(index)">
                <span :class="current_step_index == index ? 'solid-white weight-bold': ''">
                  {{ index + 1 }}
                </span>
              </v-avatar>
            </v-col>
            <v-divider 
              v-if="index < procedure.length - 1"
              :key="index">
            </v-divider>
          </template>
        </v-row>
      </v-toolbar>
      
      <component 
        :is="step_component" 
        :step="current_step" 
        :height="step_content_height">
      </component>

    </v-card>
  </v-container>
</template>

<script>
import { throttle as _throttle } from 'lodash'

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
    job: {
      type: Object,
      required: true
    },
  },

  data () {
    return {
      stepper_height: 0,
      step_content_height: 0,
    }
  },

  computed: {

    current_step_index: {
      get() {
        const step_index = this.$route.query.step - 1
        return step_index ? step_index : 0
      },
      set(value) {
        if (value != this.current_step_index)
          this.$router.push({ query: { step: value + 1 }})
      }
    },

    procedure() {
      return this.job.step_sequence
    },

    current_step() {
      if (this.procedure) {
        return this.procedure[this.current_step_index]
      }
      else return {}
    },

    step_component() {
      let component = 'JobInstruction'
      if (this.current_step) {
        switch (this.current_step.type) {
          case 'checklist':
            component = 'JobChecklist'
            break
          case 'form':
            component = 'JobForm'
            break
        }
      }
      return component
    },

    batch_data() {
      return this.$store.state.traceability.current_batch_data.step_data
    },

    force_order() {
      return this.job.parameters.step_check_force_order
    }

   
  },

  methods: {
    stepStyle(index) {
      const step_active = this.current_step_index === index
      let step_done = false
      let step_critical = false
      let color = ''
      let cursor = this.allowClick(index) ? 'pointer' : 'not-allowed'
      
      if (this.batch_data) {
        step_done = this.batch_data[index].done
        step_critical = this.batch_data[index].critical
      }

      if (step_critical) {
        color = step_active ? this.$theme.red : this.$theme.red_bg
      }

      else if (step_done) {
        color = step_active ? this.$theme.green : this.$theme.green_bg
      }

      else if (step_active) {
        color = this.job.active ? this.$theme.blue : this.$theme.grey
      }

      else {
        color = 'transparent'
      }

      return {
        backgroundColor: color,
        cursor,
      }
    },

    setContentHeight() {
      const card_height = this.$refs.step_card.clientHeight
      const stepper_height = this.$refs.stepper.clientHeight
      this.step_content_height = card_height - stepper_height
    },

    allowClick(index) {
      let allow = true 
      if (this.force_order) {
        for (let i = 0; i < index; i++) {
          allow *= this.batch_data[i].done
        }
      }

      return allow
    },

    stepClick(index) {
      if (this.allowClick(index)) {
        this.current_step_index = index
      }
    }
  },


  mounted() {
    this.setContentHeight()
    const resizeContent = _throttle(this.setContentHeight, 200)
    window.addEventListener('resize', resizeContent)
  },

  updated() {
    this.setContentHeight()
  },

}
</script>

<style lang="css" scoped>
</style>