<template>
  <div ref="step_card" class="full-height column">

      <!-- NO PROCEDURE -->
      <NoDataAlert v-if="!procedure.length">
        {{ $t('phase.no_procedure') }}
      </NoDataAlert>

      <template v-else>
        <q-toolbar dense class="col-1 q-pa-md shadow-4 surface2">
          <div class="row full-width justify-between items-center q-col-gutter-xs" ref="stepper">

            <template v-for="(step, index) in procedure" :key="step._key">
              <div class="col-auto q-px-xs">
                <q-avatar
                  size="20px"
                  :style="stepStyle(index)"
                  class="row flex-center items-stretch text-center smaller text-weight-medium"
                  @click="stepClick(index)">
                  <span :class="current_step_index == index ? 'solid-white weight-bold': ''" class="smaller">
                    {{ index + 1 }}
                  </span>
                </q-avatar>
              </div>
              <hr
                v-if="index < procedure.length - 1"
                :key="index"
                class="step-divider">
            </template>

          </div>
        </q-toolbar>

        <component
          v-if="procedure.length"
          :is="step_component"
          :step="current_step">
        </component>
      </template>
  </div>
</template>

<script>
import { throttle as _throttle } from 'lodash'

import JobInstruction from '@/components/JobInstruction.vue'
import JobForm from '@/components/JobForm.vue'
import JobChecklist from '@/components/JobChecklist.vue'
import NoDataAlert from '@/components/NoDataAlert.vue'

export default {

  name: 'WorkSessionSteps',

  components: {
    JobInstruction,
    JobForm,
    JobChecklist,
    NoDataAlert
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
      let bg_color = ''
      let text_color = this.$theme.text_low
      let cursor = this.allowClick(index) ? 'pointer' : 'not-allowed'
      
      if (this.batch_data) {
        step_done = this.batch_data[index].done
        step_critical = this.batch_data[index].critical
      }

      if (step_critical) {
        bg_color = step_active ? this.$theme.red : this.$theme.red_bg
      }

      else if (step_done) {
        bg_color = step_active ? this.$theme.green : this.$theme.green_bg
      }

      else if (step_active) {
        bg_color = this.job.active ? this.$theme.blue : this.$theme.grey
      }

      else {
        bg_color = 'transparent'
      }

      return {
        backgroundColor: bg_color,
        color: text_color,
        cursor,
      }
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
  }
}
</script>

<style lang="css" scoped>
</style>
