<template>
  <v-container fluid class="fill py-0">
    <v-row class="fill-height">

      <!-- ################################ -->
      <!--          JOB DETAILS             -->
      <!-- ################################ -->

      <v-col cols="8" class="fill d-flex flex-column pt-0">
        <v-row class="flex-grow-0 mx-0 pb-1">
          <v-tabs 
            :color="$theme.whitehigh"
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

        <router-view 
          :procedure="j.step_sequence"
          :parameters="j.parameters">
        </router-view>

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
          :value="j.progress" 
          :color="job_color" 
          class="mt-6 mb-1"/>
        <v-row class="ma-0 flex-grow-0" justify="space-between" align="end">
          <h5 class="weight-bold">PROGRESS</h5>
          <span>{{ j.qt_completed }} / {{ j.qt_planned }}</span>
        </v-row>


        <!-- JOB ACTIONS -->
        <v-btn 
          :color="$theme.surface1"
          block tile 
          height="auto"
          class="flex-shrink-0 flex-grow-1 mt-12"
          @click="startWorkSession">
          <v-row class="fill-height mx-0" align="center" justify="center">
            <v-col cols="3" class="text-right">
              <v-icon x-large>
                {{ j.active ? 'mdi-pause':'mdi-play' }}
              </v-icon>
            </v-col>
            <v-col class="display highlight medium text-left">
              {{ j.active ? 'PAUSA':'INIZIA' }}
            </v-col>
          </v-row>
        </v-btn>

        <v-btn 
          :color="$theme.surface1"
          block tile
          height="auto"
          class="mt-2 flex-shrink-0 flex-grow-1"
          @click="progress_button.action">
          <v-row class="fill-height mx-0" align="center" justify="center">
            <v-col cols="3" class="text-right">
              <v-icon x-large>
                {{ progress_button.icon }}
              </v-icon>
            </v-col>
            <v-col class="display highlight medium text-left">
              {{ progress_button.text }}
            </v-col>
          </v-row>
        </v-btn>

        <v-btn 
          :color="$theme.surface1"
          block tile
          height="auto"
          class="mt-2 flex-shrink-0 flex-grow-1"
          @click="startWorkSession">
          <v-row class="fill-height mx-0" align="center" justify="center">
            <v-col cols="3" class="text-right">
              <v-icon x-large>
                mdi-keyboard-return
              </v-icon>
            </v-col>
            <v-col class="display highlight medium text-left">
              ELENCO LAVORI
            </v-col>
          </v-row>
        </v-btn>  
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import { DateTime as DT } from 'luxon'

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
    }
  },

  computed: {
    // job_data
    j() {
      return this.$store.state.worksession.session_job_data
    },

    job_info() {
      const iteration_index = { name: 'iteration_index', text: 'iterazione' }
      const step_index = { name: 'step_index', text: 'passo' }

      let result = [...this.wo_data, iteration_index]
      if (this.j.parameters.step_check) result.push(step_index)
      return result
    },

    job_color() {
      return this.$theme.blue
    },

    progress_button() {
      const step_check = {
        icon: 'mdi-check',
        text: 'passo completato',
        action: this.markStepComplete
      }

      const piece_add = {
        icon: 'mdi-plus',
        text: 'pezzo completato',
        action: this.declarePieceCompleted
      }

      return this.j.parameters.step_check != 'none'
      ? step_check
      : piece_add
    }
  },

  methods: {
    startWorkSession() {
      let now = DT.utc()
      console.log(`Started! ${now.toLocal().toLocaleString(DT.DATETIME_FULL)}`)
    },

    markStepComplete() {
      console.log("step complete!")
    },

    declarePieceCompleted() {
      console.log("piece completed!")
    }
  },

  beforeMount() {
    const job_key = this.job_key
    this.$store.dispatch('loadJobData', {job_key})
  }
}
</script>

<style lang="css" scoped>
</style>