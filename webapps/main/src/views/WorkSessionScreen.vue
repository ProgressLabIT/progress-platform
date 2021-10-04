<template>
  <v-container fluid class="fill py-0">

    <v-card v-if="job_closed">
      <h1 class="text-uppercase">
        {{ $tc('job.alerts.job_closed') }}
      </h1>
      <v-progress-circular indeterminate :color="$theme.blue"></v-progress-circular>
    </v-card>

    <v-row class="fill-height" v-else>

      <!-- ################################ -->
      <!--          JOB DETAILS             -->
      <!-- ################################ -->

      <v-col cols="8" class="fill d-flex flex-column pt-0">
        <v-row class="flex-grow-0 mx-0 pb-3 pt-2">
          <v-tabs
            :color="$theme.text_high"
            background-color="transparent"
            hide-slider>
            <v-tab
              v-for="link in links"
              :key="link.route_name"
              :to="{ name: link.route_name }"
              class="display py-2">
              {{ link.text }}
            </v-tab>
          </v-tabs>
        </v-row>

        <v-card class="fill d-flex flex-column" max-height="100%" >
          <router-view :job="j"></router-view>
        </v-card>

      </v-col>


      <!-- ################################ -->
      <!-- RIGHT COLUMN: JOB DATA & ACTIONS -->
      <!-- ################################ -->

      <v-col cols="4" class="fill-height d-flex flex-column pr-4">

        <!-- PRODUCT CODE & DESCRIPTION -->
        <h2 class="display highlight text-uppercase">{{ j.product_code }}</h2>
        <p class="mt-2 mb-6">{{ j.product_description }}</p>

        <!-- JOB DATA -->
        <template v-for="field in job_info" >
          <v-row
            v-if="j[field.name] != undefined"
            :key="field.name"
            dense
            align="end"
            class="flex-grow-0">
            <v-col cols="4" class="text-uppercase font-weight-medium">
              <h5>{{ field.text }}</h5>
            </v-col>
            <v-col cols="8">
              <span>{{ j[field.name] | capitalize_all }}</span>
            </v-col>
          </v-row>
        </template>

        <!-- JOB PROGRESS / STATUS -->
        <v-progress-linear
          height="8"
          :value="progress_value"
          :color="job_color"
          class="mt-6 mb-1"/>
        <v-row class="ma-0 flex-grow-0" justify="space-between" align="end">
          <h5 class="weight-bold text-uppercase">{{ $tc('progress') }}</h5>
          <span>{{ j.qt_completed }} / {{ j.qt_planned }}</span>
        </v-row>


        <!-- ************************** -->
        <!-- JOB ACTIONS                -->
        <!-- ************************** -->

        <!-- START/PAUSE BUTTOM -->
        <v-row class="mx-0 mt-12">
          <v-btn
            :color="$theme.surface2"
            block tile
            height="auto"
            @click="startPauseResumeJob().action()">
            <v-row class="fill-height mx-0" align="center" justify="center">
              <v-col cols="3" class="text-right">
                <v-icon x-large>
                  {{ j.active ? 'mdi-pause':'mdi-play' }}
                </v-icon>
              </v-col>
              <v-col class="display highlight medium text-left">
                {{ startPauseResumeJob().text }}
              </v-col>
            </v-row>
          </v-btn>
        </v-row>

        <!-- PROGRESS BUTTON -->
        <v-row class="mx-0 mt-2">
          <v-btn
            id="progress_button"
            :color="j.active ? $theme.surface2 : $theme.background"
            block tile
            :disabled="!j.active || current_step_done"
            height="auto"
            :class="{ disabled: !j.active, completed: current_step_done }"
            @click="progress_button.action()">
            <v-row class="fill-height mx-0" align="center" justify="center">
              <v-col cols="3" class="text-right">
                <v-icon x-large>
                  {{ progress_button.icon }}
                </v-icon>
              </v-col>
              <v-col class="display medium text-left" :class="{ highlight: j.active}">
                {{ progress_button.text }}
              </v-col>
            </v-row>
          </v-btn>
        </v-row>

        <!-- PREV/NEXT STEP AND EXIT BUTTONS -->
        <v-row class="mt-2 mx-0" justify="space-between">

          <v-btn
            :color="$theme.surface2"
            tile
            height="auto" width="32%"
            @click="goToPreviousStep"
            class="py-3">
            <v-icon x-large>
              mdi-skip-previous
            </v-icon>
          </v-btn>

          <v-btn
            :color="$theme.surface2"
            tile
            :disabled="!allow_step_forward"
            height="auto" width="32%"
            @click="goToNextStep"
            class="py-3">
            <v-icon x-large>
              mdi-skip-next
            </v-icon>
          </v-btn>

          <v-btn
            :color="$theme.surface2"
            tile
            height="auto" width="32%"
            @click="j.active ? showExitAlert(true) : exitJob()"
            class="py-3">
            <v-icon x-large>
              mdi-keyboard-return
            </v-icon>
          </v-btn>
        </v-row>

      </v-col>

    </v-row>

    <v-dialog v-model="show_exit_alert" max-width="480px">
      <v-card>
        <v-card-title>
          {{ $tc('job.alerts.confirm_exit')}}
        </v-card-title>
        <v-card-actions>
          <v-row class="mx-0" justify="space-between">
            <v-btn text @click="exitJob" :color="$theme.orange">
              {{ $tc('confirm') }}
            </v-btn>
            <v-btn text @click="show_exit_alert=false" :color="$theme.grey">
              {{ $tc('cancel') }}
            </v-btn>
          </v-row>
        </v-card-actions>
      </v-card>
    </v-dialog>

  </v-container>
</template>

<script>
// import { DateTime as DT } from 'luxon'
import { mapState } from 'vuex'

export default {

  name: 'WorkSessionScreen',

  props: {
    // from router
    job_key: String,
  },

  data () {
    return {
      vuex_ready: false,
      job_closed: false,
      show_exit_alert: false
    }
  },

  computed: {

    ...mapState({
      j: state => state.traceability.working_job_data,
      ws_list: state => state.traceability.work_session_list,
      batch_data: state => state.traceability.current_batch_data.step_data,
    }),

    links() {
      return [
          { route_name: 'jobSteps', text: this.$tc('procedure') },
          { route_name: 'jobDocs', text: this.$tc('document.label', 2) },
          { route_name: 'jobBom', text: this.$tc('material', 2) },
      ]
    },

    wo_data() {
      return [
        { name: 'wo_code', text: this.$tc('work_order.wo_code') },
        { name: 'wo_line', text: this.$tc('work_order.wo_line.line_only', 1) },
        { name: 'phase_alias', text: this.$tc('phase.short', 1) },
      ]
    },

    force_order() {
      return this.j.parameters.step_check_force_order
    },

    confirm_batch_done_message() {
      return this.$tc('job.alerts.batch_confirm')
    },

    confirm_job_done_message() {
      return this.$tc('job.alerts.job_complete_confirm')
    },

    job_info() {
      const batch_index = { name: 'batch_index', text: 'iterazione' }
      const step_index = { name: 'step_index', text: 'passo' }

      let result = [...this.wo_data, batch_index]
      const step_check = this.j.parameters ? this.j.parameters.step_check : 'none'
      if (step_check != 'none') result.push(step_index)
      return result
    },

    job_color() {
      if (this.j.critical) return this.$theme.red
      else if (!this.j.on_time) return this.$theme.orange
      else if (this.j.active) return this.$theme.blue
      else return this.$theme.grey
    },

    progress_button() {

      const complete_step = {
        icon: 'mdi-check',
        text: this.$tc('job.complete_step'),
        action: this.completeStep
      }

      const declare_batch = {
        icon: 'mdi-plus',
        text: this.$tc('job.complete_batch'),
        action: this.declareBatch
      }

      if ('parameters' in this.j) {
        return this.j.parameters.step_check != 'none'
        // && !this.current_step_is_last
            ? complete_step
            : declare_batch
      }
      else return declare_batch
    },

    production_batch() {
      let production_batch = 1
      if (this.j.parameters) {
        switch (this.j.parameters.step_check) {
          case 'job':
            production_batch = this.j.qt_planned
            break
          default:
            production_batch = this.j.parameters.production_batch_qt
            break
        }
        // The last batch could include less pieces than the production batch
        const qt_remaining = this.j.qt_planned - this.j.qt_completed
        return Math.min(production_batch, qt_remaining)
      }
      else return production_batch
    },

    current_step_index() {
      const step_index = this.$route.query.step - 1
      return step_index ? step_index : 0
    },

    completed_steps_count() {
      return this.batch_data
        ? this.batch_data.reduce( (total, current) => total + current.done, 0)
        : 0
    },

    current_step_is_last() {
      return this.completed_steps_count === this.j.step_sequence.length -1
    },

    current_batch_is_last() {
      const remaining_qt = this.j.qt_planned - this.j.qt_completed
      return this.production_batch === remaining_qt
    },

    current_step_done() {
      let current_step = this.batch_data ? this.batch_data[this.current_step_index] : null
      return current_step ? current_step.done : null
    },

    progress_value() {
      if ('parameters' in this.j) {
        const completed_batch_progress = this.j.qt_completed / this.j.qt_planned

        if (this.j.parameters.step_check != 'none') {
          const current_batch_total_value = this.production_batch / this.j.qt_planned
          const step_progress_value = current_batch_total_value / this.j.step_sequence.length
          const current_batch_current_value = step_progress_value * this.completed_steps_count
          const total_progress = completed_batch_progress + current_batch_current_value
          return Math.floor( 100 * total_progress )
        }
        else return Math.floor(100 * completed_batch_progress)
      }
      else return 0

    },

    disabled_button_style() {
      if (this.j.active) return ''
      else return {
        backgroundColor: this.$theme.surface1,
        color: this.$theme.text_disabled
      }
    },

    allow_step_forward() {
      let allow = true
      if (this.force_order && !this.current_step_done) {
        allow = false
      }
      return allow
    }
  },

  methods: {

    startPauseResumeJob() {
      const result = {
        text: null,
        action: null
      }

      if (this.j.active) {
        result.text = this.$tc('job.pause').toUpperCase()
        result.action = () => this.$store.dispatch('pauseJob')
        return result
      }

      else {
        // Check if progress has already been made or user has already started
        if (this.j.stage == 'started' ) {
          result.text = this.$tc('job.resume').toUpperCase()
          result.action = () => this.$store.dispatch('resumeJob')
          return result
        }
        else {
          result.text = this.$tc('job.start').toUpperCase()
          result.action = () => this.$store.dispatch('startJob')
          return result
        }
      }
    },

    async completeStep() {
      let can_proceed = true

      // Values will change after committing mutation save to use for navigation later on
      const current_step_was_last = this.current_step_is_last
      const current_batch_was_last = this.current_batch_is_last

      if (this.current_step_is_last) {
        can_proceed = window.confirm(this.confirm_batch_done_message)

        if (can_proceed && this.current_batch_is_last) {
          can_proceed = window.confirm(this.confirm_job_done_message)
        }
      }


      if (can_proceed) {
        await this.$store.dispatch('completeStep', {
          step_index: this.current_step_index,
          last_step: this.current_step_is_last,
          batch_qt: this.production_batch,
          last_batch: this.current_batch_is_last
        })

        if (current_step_was_last && current_batch_was_last) {
          this.$router.push({ name: 'userJobs' })
        }
        else if (current_step_was_last) {
          this.goToStep(0)
        }
        else if (this.j.parameters.step_check != 'none') {
          // Go to first step that is not done.
          // This works with both force_order mode active or not
          this.goToNextUndoneStep()
        }
      }
    },

    async declareBatch() {
      let can_proceed = true

      if (this.current_batch_is_last) {
        can_proceed = window.confirm(this.confirm_job_done_message)
      }

      if (can_proceed) {
        await this.$store.dispatch('declareBatch', {
          batch_qt: this.production_batch,
          last_batch: this.current_batch_is_last
        })
        if (this.j.qt_completed >= this.j.qt_planned) this.exitJob()
        else if (this.j.parameters.step_check != 'none') this.goToStep(0)
      }
    },

    goToStep(step_sequence) {
      this.$router.push({ query: { step: step_sequence + 1 }})
    },

    goToNextUndoneStep() {
      if (this.batch_data) {
        const procedure_length = this.j.step_sequence.length
        for (let i = this.current_step_index; i < procedure_length ; i++) {
          if (!this.batch_data[i].done) {
            this.goToStep(i)
            return
          }
        }
        const next_step_index = this.batch_data.findIndex( step => !step.done )
        this.goToStep(next_step_index)
      }
    },

    goToNextStep() {
      const last_index = this.j.step_sequence.length - 1
      if (this.current_step_index === last_index) this.goToStep(0)
      else this.goToStep(this.current_step_index + 1)
    },

    goToPreviousStep() {
      const last_index = this.j.step_sequence.length - 1
      if (this.current_step_index === 0) this.goToStep(last_index)
      else this.goToStep(this.current_step_index - 1)
    },

    showExitAlert(bool) {
      this.show_exit_alert = bool
    },

    exitJob() {
      if (this.j.active) {
        this.$store.dispatch('pauseJob')
        .then(() => this.$router.push({ name: 'userJobs'}))
      }
      else this.$router.push({ name: 'userJobs'})
    },

    beforeUnloadAlert(event) {
      event.preventDefault()
      event.returnValue = ''
    }
  },

  created() {
    // Load job data
    const job_key = this.job_key
    this.$store.dispatch('loadJobData', job_key)
    .then(() => {
      const data = this.$store.state.traceability
      const job_data = data.working_job_data

      // If job is closed, redirect to
      this.job_closed = job_data.stage == 'closed'

      if (this.job_closed) {
        setTimeout(() => {
          this.$router.push({ name: 'userJobs'})
        }, 6000)
      }
      else {
        this.vuex_ready = true
        if (data.current_batch_data) {
          const next_step_index = this.batch_data.findIndex( step => !step.done )
          this.$router.replace({ query: { step: next_step_index + 1 }})
        }
        // In case the job is already active, e.g. after accidentally closing and reopening the page, restart heartbeat
        if (job_data.active) {
          this.$store.commit('SET_HEARTBEAT', true)
        }
      }
    })
  },

  // Make sure an alert is raised if user tries to close the page
  mounted() {
    window.addEventListener('beforeunload', this.beforeUnloadAlert)
  },

  beforeDestroy() {
    window.removeEventListener('beforeunload', this.beforeUnloadAlert)
  },

  beforeRouteLeave (to, from, next) {
    if (this.j.active) {
      const confirm = window.confirm(this.$tc('job.alerts.confirm_exit'))
      if (confirm) {
        this.$store.dispatch('pauseJob')
        next()
      }
      else {
        next(false)
      }
    }
    else {
      next()
    }
  }
}
</script>

<style lang="css" scoped>
#progress_button.disabled {
  background-color: var(--surface-1) !important;
  color: var(--theme-grey) !important;
}
#progress_button.completed {
  background-color: var(--surface-1) !important;
  color: var(--theme-green) !important;
}
</style>
