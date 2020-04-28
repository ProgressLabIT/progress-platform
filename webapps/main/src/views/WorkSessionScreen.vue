<template>
  <v-container fluid class="fill py-0">
    <v-row class="fill-height">

      <!-- ################################ -->
      <!--          JOB DETAILS             -->
      <!-- ################################ -->

      <v-col cols="8" class="fill d-flex flex-column pt-0">
        <v-row class="flex-grow-0 mx-0 pb-1">
          <v-tabs 
            :color="$theme.white_high"
            background-color="transparent"
            hide-slider>
            <v-tab 
              v-for="link in links" 
              :key="link.route_name"
              :to="{ name: link.route_name }"
              class="display">
              {{ link.text }}
            </v-tab>
          </v-tabs>
        </v-row>

        <router-view :job="j"></router-view>

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
          <h5 class="weight-bold">PROGRESS</h5>
          <span>{{ j.qt_completed }} / {{ j.qt_planned }}</span>
        </v-row>


        <!-- JOB ACTIONS -->
        <v-row class="mx-0 mt-12">
        
        <v-btn 
          :color="$theme.surface2"
          block tile 
          height="auto"
          @click="startPauseResumeJob.action()">
          <v-row class="fill-height mx-0" align="center" justify="center">
            <v-col cols="3" class="text-right">
              <v-icon x-large>
                {{ j.active ? 'mdi-pause':'mdi-play' }}
              </v-icon>
            </v-col>
            <v-col class="display highlight medium text-left">
              {{ startPauseResumeJob.text }}
            </v-col>
          </v-row>
        </v-btn>
        </v-row>

        <v-row class="mx-0 mt-2">
        
        <v-btn 
          id="progress_button"
          :color="j.active ? $theme.surface2 : $theme.background"
          block tile
          :disabled="!j.active || current_step_status"
          height="auto"
          :class="{ disabled: !j.active, completed: current_step_status }"
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
        
        <v-row class="mt-2 mx-0" justify="space-between">
            <v-btn 
              :color="$theme.surface2"
              tile
              height="auto" width="32%"
              @click="goToPreviousStep"
              class="py-3">
              <!-- <v-row class="fill-height mx-0" align="center" justify="center"> -->
                  <v-icon x-large>
                    mdi-skip-previous
                  </v-icon>
              <!-- </v-row> -->
            </v-btn>  

            <v-btn 
              :color="$theme.surface2"
              tile
              height="auto" width="32%"
              @click="goToNextStep"
              class="py-3">
<!--               <v-row class="fill-height mx-0" align="center" justify="center">
 -->                  <v-icon x-large>
                    mdi-skip-next
                  </v-icon>
              <!-- </v-row> -->
            </v-btn>  

            <v-btn 
              :color="$theme.surface2"
              tile
              height="auto" width="32%"
              @click="exitJob"
              class="py-3">
              <!-- <v-row class="fill-height mx-0" align="center" justify="center"> -->
                  <v-icon x-large>
                    mdi-keyboard-return
                  </v-icon>
              <!-- </v-row> -->
            </v-btn>  
        </v-row>
      </v-col>
    </v-row>
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
      links: [
        // { route_name: 'jobDocs', text: 'DETTAGLI PRODOTTO' },
        // { route_name: 'jobBom', text: 'DISTINTA MATERIALI' },
        { route_name: 'jobSteps', text: 'PROCEDURA' },
      ],

      wo_data: [
        { name: 'wo_code', text: 'codice op' },
        { name: 'wo_line', text: 'riga op' },
        { name: 'phase_alias', text: 'fase' },
      ],

      vuex_ready: false
    }
  },

  computed: {

    ...mapState({
      j: state => state.traceability.working_job_data,
      ws_list: state => state.traceability.work_session_list,
      batch_data: state => state.traceability.current_batch_data.step_data,
    }),

    
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
        text: 'completa passo',
        action: this.completeStep
      }

      const declare_batch = {
        icon: 'mdi-plus',
        text: 'completa lotto',
        action: this.declareBatch
      }
      
      if ('parameters' in this.j) {
        return this.j.parameters.step_check != 'none' && !this.current_step_is_last 
            ? complete_step 
            : declare_batch
      }
      else return declare_batch
    },

    production_batch() {
      let production_batch = 1
      if (this.j.parameters) {
        switch (this.j.parameters.step_check) {
          case 'fixed_batch':
            production_batch = this.j.parameters.production_batch_qt
            break
          case 'job':
            production_batch = this.j.qt_planned
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
      return this.completed_steps_count === this.j.step_sequence.length - 1
    },

    current_batch_is_last() {
      const remaining_qt = this.j.qt_planned - this.j.qt_completed
      return this.production_batch === remaining_qt
    },

    current_step_status() {
      let current_step = this.batch_data ? this.batch_data[this.current_step_index] : null
      return current_step ? current_step.done : null
    },

    progress_value() {
      if ('parameters' in this.j) {
        const completed_batchs_progress = this.j.qt_completed / this.j.qt_planned
        const current_batch_total_value = this.j.qt_planned / this.production_batch
        const step_progress_value = current_batch_total_value / this.j.step_sequence.length
        const current_batch_current_value = step_progress_value * this.completed_steps_count
        const total_progress = completed_batchs_progress + current_batch_current_value

        // console.log({
        //   completed_batchs_progress,
        //   current_batch_total_value,
        //   step_progress_value,
        //   current_batch_current_value,
        //   total_progress
        // })

        return Math.floor( 100 * total_progress )
      }
      else return 0

    },

    disabled_button_style() {
      if (this.j.active) return ''
      else return {
        backgroundColor: this.$theme.surface1,
        color: this.$theme.white_disabled
      }
    },

    startPauseResumeJob() {
      const result = {
        text: null,
        action: null
      }

      if (this.j.active) {
        result.text = 'PAUSA'
        result.action = () => this.$store.dispatch('pauseJob')
        return result
      }

      else {
        // Check if progress has already been made or user has already started
        if (this.j.stage == 'started' ) {
          result.text = 'RIPRENDI'
          result.action = () => this.$store.dispatch('resumeJob')
          return result          
        }
        else {
          result.text = 'INIZIA'
          result.action = () => this.$store.dispatch('startJob')
          return result
        }
      }
    },
  },

  methods: {

    async completeStep() {
      await this.$store.dispatch('completeStep', this.current_step_index)
      // Go to first step that is not done.
      // This works with both force_order mode active or not
      const next_step_index = this.batch_data.findIndex( step => !step.done )
      this.goToStep(next_step_index)
    },

    async declareBatch() {
      await this.$store.dispatch('declareBatch', this.production_batch)
      if (this.current_batch_is_last) this.exitJob()
      else if (this.step_check != 'none') this.goToStep(0)
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

    exitJob() {
      this.$store.dispatch('pauseJob')
      .then(() => this.$router.push({ name: 'userJobs'}))
    }
  },

  beforeMount() {
    const job_key = this.job_key
    this.$store.dispatch('loadJobData', job_key)
    .then(() => this.vuex_ready = true)
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