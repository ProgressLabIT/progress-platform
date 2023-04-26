<template>
  <q-page-container>
    <q-page class="q-px-md q-pb-md column">

      <q-circular-progress
        v-if="!vuex_ready"
        indeterminate
        color="theme-blue"
        class="q-mt-lg">
      </q-circular-progress>

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

        <div
          class="column q-px-sm"
          id="job-info-section"
          :class="$route.name === 'jobIssueDetail' ? 'col-12' : 'col-8'">

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

        <div
          id="session-control-section"
          v-if="$route.name != 'jobIssueDetail'"
          class="column col-4 q-px-sm q-pt-md">

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
            <BaseProgressBar
              size="8px"
              :data="j"
              class="q-mt-lg q-mb-xs">
            </BaseProgressBar>

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
              <StartPauseResumeBtn />
            </div>

            <!-- PROGRESS BUTTON -->
            <div class="col-4">
              <ProgressBtn />
            </div>

            <!-- NEW ISSUE AND EXIT BUTTONS -->
            <div class="row col-4 q-col-gutter-x-sm">
              <div class="col">
                <q-btn
                  color="theme-grey"
                  square
                  height="auto"
                  class="fit"
                  @click="show_issue_form = true">
                  <q-icon color="text_high" size="lg" name="mdi-flag" />
                </q-btn>
              </div>

              <div class="col">
                <q-btn
                  color="theme-grey"
                  square
                  height="auto"
                  class="fit"
                  @click="j.active ? showExitAlert(true) : exitJob()">
                  <q-icon color="text-high" size="lg" name="mdi-close" />
                </q-btn>
              </div>
            </div>
          </div>
        </div>

      </div>

      <!-- Consider switching to banner or similar -->
      <q-dialog v-model="show_exit_alert" max-width="480px">
        <q-card class="surface2 q-pa-md">
          <q-card-section class="text-h3">
            {{ $t('job.alerts.confirm_exit')}}
          </q-card-section>
          <q-card-section>
            <div class="row justify-between">
              <q-btn @click="exitJob" color="theme-orange">
                {{ $t('confirm') }}
              </q-btn>
              <q-btn @click="show_exit_alert=false" color="theme-grey">
                {{ $t('cancel') }}
              </q-btn>
            </div>
          </q-card-section>
        </q-card>
      </q-dialog>

      <IssueForm
        :show="show_issue_form"
        mode="new"
        @close="show_issue_form = false">
      </IssueForm>

    </q-page>
  </q-page-container>
</template>

<script>
import { mapState } from 'vuex'

import BaseDialog from '@/components/BaseDialog.vue'
import BaseProgressBar from '@/components/BaseProgressBar.vue'
import IssueForm from '@/components/IssueForm.vue'
import ProgressBtn from '@/components/ProgressBtn.vue'
import StartPauseResumeBtn from '@/components/StartPauseResumeBtn.vue'

export default {

  name: 'WorkSessionScreen',

  components: {
    BaseDialog,
    BaseProgressBar,
    IssueForm,
    ProgressBtn,
    StartPauseResumeBtn
  },

  props: {
    // from router
    job_key: String,
  },

  data () {
    return {
      vuex_ready: false,
      show_exit_alert: false,
      show_issue_form: false,
      alert_timeout: 4000
    }
  },

  computed: {

    ...mapState({
      j: state => state.traceability.working_job_data,
      ws_list: state => state.traceability.work_session_list,
      batch_data: state => state.traceability.current_batch_data.step_data
    }),

    links() {
      return [
          { route_name: 'jobSteps', text: this.$t('procedure') },
          { route_name: 'jobDocs', text: this.$t('document.label', 2) },
          { route_name: 'jobBom', text: this.$t('material', 2) },
          { route_name: 'jobIssues', text: this.$t('issue', 2) },
          { route_name: 'jobNotes', text: this.$t('notes', 2) }
      ]
    },

    job_info() {
      return [
        { name: 'wo_code', text: this.$t('work_order.list_headers.wo_code') },
        { name: 'project_code', text: this.$t('project') },
        { name: 'phase_alias', text: this.$t('phase.short') },
        { name: 'active_batch_qt', text: this.$t('quantity.active.medium') }
      ]
    },

    force_order() {
      return this.j.parameters.step_check_force_order
    },

    job_color() {
      if (this.j.critical) return 'theme-red'
      else if (!this.j.on_time) return 'theme-orange'
      else if (this.j.active) return 'theme-blue'
      else return 'theme-grey'
    },

    current_step_index() {
      const step_index = this.$route.query.step - 1
      return step_index ? step_index : 0
    },

    current_step_done() {
      let current_step = this.batch_data ? this.batch_data[this.current_step_index] : null
      return current_step ? current_step.done : null
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
    loadJob() {
      this.$store.dispatch('loadWorkingJobData', this.job_key)
      .then(() => {
        const data = this.$store.state.traceability
        const job_data = data.working_job_data

        // If job is closed, redirect to
        if (!this.can_work) {
          setTimeout(this.exitJob, this.alert_timeout)
        }

        else {
          this.vuex_ready = true
          if (data.current_batch_data.step_data) {
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

    goToStep(step_sequence) {
      this.$router.push({ query: { step: step_sequence + 1 }})
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
    },

    updateJobData() {
      this.$api.get(`job/${this.job_key}`).then(resp => {
        this.$store.commit('UPDATE_JOB', resp.data.detail)
      })
    }
  },

  created() {
    // Load job data
    this.loadJob()
    this.polling_instance = setInterval(this.updateJobData, 10000)
  },

  // Make sure an alert is raised if user tries to close the page
  mounted() {
    window.addEventListener('beforeunload', this.beforeUnloadAlert)
  },

  beforeUnmount() {
    window.removeEventListener('beforeunload', this.beforeUnloadAlert)
    clearInterval(this.polling_instance)
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
