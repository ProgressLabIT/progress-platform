<template>
  <q-page-container>
    <q-page class="q-px-md q-pb-md column">

      <q-circular-progress indeterminate color="theme-blue" class="q-mt-lg" v-if="!vuex_ready" />


      <!-- JOB CLOSED NOTIFICATION -->
      <div v-else-if="job_closed || !has_material_to_proceed" class="row flex-center" style="height: 80vh">
        <div class="col-6 text-center">
          <div v-if="job_closed" class="text-h3">
            {{ $t('job.alerts.job_closed') }}
          </div>
          <div v-else-if="!has_material_to_proceed" class="text-h3">
            {{ $t('job.alerts.input_not_available') }}
          </div>
          <q-circular-progress indeterminate color="theme-blue" class="q-mt-lg"/>
        </div>
      </div>

      <div v-else class="row absolute-full q-pb-md q-px-xs" v-if="vuex_ready & !job_closed">

        <!-- ################################ -->
        <!--          JOB DETAILS             -->
        <!-- ################################ -->

        <div class="column col-8 q-px-sm" id="job-info-section">

          <!-- PANEL NAVIGATION -->
          <q-tabs
            class="transparent text-low"
            active-class="text-high weight-bold"
            align="left"
            shrink
            indicator-color="transparent">
            <q-route-tab
              v-for="link in links"
              :key="link.route_name"
              :to="{ name: link.route_name }"
              class="display">
              {{ link.text }}
            </q-route-tab>
          </q-tabs>

          <!-- PANEL CONTENT -->
          <q-card class="surface1 col" square>
            <router-view :job="j" />
          </q-card>

        </div>


        <!-- ################################ -->
        <!-- RIGHT COLUMN: JOB DATA & ACTIONS -->
        <!-- ################################ -->

        <div id="session-control-section" class="column col-4 q-px-sm q-pt-md">

          <!-- JOB DATA -->
          <div id="job-data" class="col-auto">

            <!-- PRODUCT CODE & DESCRIPTION -->
            <div class="text-h2 display highlight text-uppercase">
              {{ j.product_code }}
            </div>
            <p class="q-mt-sm">
              {{ j.product_description }}
            </p>

            <!-- WORK ORDER DATA -->
            <template v-for="field in job_info" >
              <div class="row items-center q-py-xs"
                v-if="j[field.name] != undefined"
                :key="field.name">
                <div class="col-5 text-h5 text-uppercase font-weight-medium">
                  {{ field.text }}
                </div>
                <div class="col-7">
                  <span>{{ $capitalizeAll(j[field.name]) }}</span>
                </div>
              </div>
            </template>

            <!-- JOB PROGRESS / STATUS -->
            <q-linear-progress
              size="8px"
              :value="progress_value / 100"
              :color="job_color"
              :track-color="job_color"
              animation-speed="300"
              class="q-mt-lg q-mb-xs">
            </q-linear-progress>

            <div class="row justify-between items-center q-pt-xs">
              <div class="text-h5 weight-bold text-uppercase">{{ $t('progress') }}</div>
              <div>{{ j.qt_completed }} / {{ j.qt_planned }}</div>
            </div>

          </div>

          <!-- ************************** -->
          <!-- JOB ACTIONS                -->
          <!-- ************************** -->
          <div class="col column q-mt-lg q-col-gutter-y-sm" id="job-actions">

            <!-- START/PAUSE BUTTOM -->
            <div class="col-4">
              <q-btn
                class="fit"
                :style="`background-color: ${j.active ? $theme.grey : $theme.blue + 'aa'}`"
                square
                @click="startPauseResumeJob().action()">
                <div class="row items-center absolute-full">
                  <div class="col-1 offset-2">
                    <q-icon size="lg" :name="j.active ? 'mdi-pause':'mdi-play'" />
                  </div>
                  <div class="display medium offset-1">
                    {{ startPauseResumeJob().text }}
                  </div>
                </div>
              </q-btn>
            </div>

            <!-- PROGRESS BUTTON -->
            <div class="col-4">
              <q-btn
                id="progress_button"
                square
                :style="`background-color: ${progress_button_color}`"
                :disable="!progress_button_active"
                @click="progress_button.action()"
                class="fit">
                <div class="row items-center absolute-full">
                  <div class="col-1 offset-2">
                    <q-icon size="lg" :name="progress_button.icon" />
                  </div>
                  <div class="display medium offset-1">
                    <span>{{ progress_button.text }}</span>
                  </div>
                </div>
              </q-btn>
            </div>

            <!-- PREV/NEXT STEP AND EXIT BUTTONS -->
            <div class="row col-4 q-col-gutter-x-sm">
              <div class="col">
                <q-btn
                  color="theme-grey"
                  square
                  height="auto"
                  class="fit"
                  @click="goToPreviousStep">
                  <q-icon color="text_high" size="lg" name="mdi-skip-previous" />
                </q-btn>
              </div>

              <div class="col">
                <q-btn
                  color="theme-grey"
                  square
                  :disabled="!allow_step_forward"
                  height="auto"
                  class="fit"
                  @click="goToNextStep">
                  <q-icon color="text-high" size="lg" name="mdi-skip-next" />
                </q-btn>
              </div>

              <div class="col">
                <q-btn
                  color="theme-grey"
                  square
                  height="auto"
                  class="fit"
                  @click="j.active ? showExitAlert(true) : exitJob()">
                  <q-icon color="text-high" size="lg" name="mdi-keyboard-return" />
                </q-btn>
              </div>
            </div>
          </div>
        </div>

      </div>

      <!-- Consider switching to banner or similar -->
      <q-dialog v-model="show_exit_alert" max-width="480px">
        <q-card>
          <q-card-section class="text-body1">
            {{ $t('job.alerts.confirm_exit')}}
          </q-card-section>
          <q-card-actions>
            <div class="row justify-between">
              <q-btn flat @click="exitJob" color="theme-orange">
                {{ $t('confirm') }}
              </q-btn>
              <q-btn flat @click="show_exit_alert=false" color="theme-grey">
                {{ $t('cancel') }}
              </q-btn>
            </div>
          </q-card-actions>
        </q-card>
      </q-dialog>

    </q-page>
  </q-page-container>
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
      alert_timeout: 6000
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
          { route_name: 'jobSteps', text: this.$t('procedure') },
          { route_name: 'jobDocs', text: this.$t('document.label', 2) },
          { route_name: 'jobBom', text: this.$t('material', 2) },
      ]
    },

    wo_data() {
      return [
        { name: 'wo_code', text: this.$t('work_order.list_headers.wo_code') },
        { name: 'project_code', text: this.$t('project') },
        { name: 'phase_alias', text: this.$t('phase.short') },
      ]
    },

    force_order() {
      return this.j.parameters.step_check_force_order
    },

    confirm_batch_done_message() {
      return this.$t('job.alerts.batch_confirm')
    },

    confirm_job_done_message() {
      return this.$t('job.alerts.job_complete_confirm')
    },

    job_info() {
      const active_qt = { name: 'active_batch_qt', text: this.$t('quantity.active.medium') }
      return [...this.wo_data, active_qt]
    },

    job_color() {
      if (this.j.critical) return 'theme-red'
      else if (!this.j.on_time) return 'theme-orange'
      else if (this.j.active) return 'theme-blue'
      else return 'theme-grey'
    },

    progress_button() {

      const complete_step = {
        icon: 'mdi-check',
        text: this.$t('job.complete_step'),
        action: this.completeStep,
      }

      const declare_batch = {
        icon: 'mdi-plus',
        text: this.$t('job.complete_batch'),
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

    progress_button_active() {
      return this.j.active && !this.current_step_done
    },

    progress_button_color() {
      return this.progress_button_active
        ? this.$theme.green + 'aa'
        : 'rgba(255,255,255,.13)'
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
        // color: this.$theme.text_disabled
      }
    },

    allow_step_forward() {
      let allow = true
      if (this.force_order && !this.current_step_done) {
        allow = false
      }
      return allow
    },

    has_material_to_proceed() {
      return this.j.next_batch_available || this.j.active_batch_qt
    },

    job_closed() {
      return this.j.stage == 'closed'
    },

    can_work() {
      return this.has_material_to_proceed && !this.job_closed
    }
  },

  methods: {

    startPauseResumeJob() {
      const result = {
        text: null,
        action: null
      }

      if (this.j.active) {
        result.text = this.$t('job.pause').toUpperCase()
        result.action = () => this.$store.dispatch('pauseJob')
        return result
      }

      else {
        // Check if progress has already been made or user has already started
        if (this.j.stage == 'started' ) {
          result.text = this.$t('job.resume').toUpperCase()
          result.action = () => this.$store.dispatch('resumeJob')
          return result
        }
        else {
          result.text = this.$t('job.start').toUpperCase()
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
          batch_qt: this.production_batch,
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
      if (!this.can_work) {
        setTimeout(this.exitJob, this.alert_timeout)
      }

      else {
        this.vuex_ready = true
        if (data.current_batch_data) {
          const next_step_index = this.batch_data.findIndex( step => !step.done ) || 0
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

  beforeUnmount() {
    window.removeEventListener('beforeunload', this.beforeUnloadAlert)
  },

  beforeRouteLeave (to, from, next) {
    if (this.j.active) {
      const confirm = window.confirm(this.$t('job.alerts.confirm_exit'))
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
  },

  watch: {
    can_work(value) {
      if (value == false) {
        setTimeout(this.exitJob, this.alert_timeout)
      }
    }
  }
}
</script>

<style lang="css" scoped>
</style>
