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

      <template v-if="procedure.length > 0">
        <JobForm v-if="current_step.type === 'form'" :step="current_step" />
        <JobInstruction v-else :step="current_step" />
      </template>
    </template>
  </div>
</template>

<script>
import JobInstruction from '@/components/JobInstruction.vue'
import JobForm from '@/components/JobForm.vue'
import NoDataAlert from '@/components/NoDataAlert.vue'

export default {
  name: 'WorkSessionSteps',

  components: {
    JobInstruction,
    JobForm,
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
        return this.$store.state.traceability.current_step_index ?? 0
      },
      set(index) {
        this.$store.state.traceability.current_step_index = index
      }
    },

    procedure() {
      return this.job.step_sequence
    },

    current_step() {
      return this.procedure?.[this.current_step_index] ?? {}
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
      const text_color = this.$theme.text_low
      const cursor = this.allowClick(index) ? 'pointer' : 'not-allowed'

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
