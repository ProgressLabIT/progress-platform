<template>
  <v-container class="fill py-0 d-flex flex-column">
    
    <!-- HEADERS -->
    <v-row class="flex-grow-0 mx-0 px-2" align="center">
      <v-col 
        v-for="header in headers" 
        :key="header.value" 
        :cols="header.cols"
        :class="header.value.includes('qt') ? 'text-right' : '' ">
        <h5>{{ header.text}}</h5>
      </v-col>
    </v-row>

    
    <!-- CONTENT -->
    <div class="scroll flex-grow-1">
      <v-expansion-panels flat v-model="expanded_phase">
        <v-expansion-panel 
          v-for="(phase, index) in phase_data" 
          :key="phase.phase_key"
          color="transparent">
          
          <!-- PHASE SUMMARY DATA -->
          <v-expansion-panel-header 
            class="body-2 py-0 px-5"
            :class="expanded_phase === index ? 'border-top highlight font-weight-medium' : '' ">
            <v-row align="center">
              <v-col 
                v-for="header in headers" 
                :key="header.value" 
                :cols="header.cols"
                :class="header.value.includes('qt') || header.value === 'assigned_to' ? 'text-right' : '' ">

                <!-- PHASE PROGRESS -->
                <template v-if="header.value === 'progress'">
                  <v-row no-gutters align="center" >
                    <v-col cols="9">
                      <v-progress-linear 
                        dense 
                        :value="phase.progress"
                        :color="phase.active ? $theme.blue : $theme.grey">
                      </v-progress-linear>
                    </v-col>
                    <v-col class="pl-4 text-right">
                      {{ phase.progress }}%
                    </v-col>
                  </v-row>
                </template>
                <!-- END OF PHASE PROGRESS -->

                <!-- OTHER PHASE DATA -->
                <template v-else-if="header.value != 'assigned_to' ">
                  {{ phase[header.value] | capitalize_all }}
                </template>
              </v-col>
            </v-row>
            <template v-slot:actions>{{''}}</template>
          </v-expansion-panel-header>
          <!-- END OF PHASE SUMMARY DATA -->


          
          <!-- JOB DATA & PHASE/JOB ACTIONS -->
          <v-expansion-panel-content
            :class="expanded_phase === index ? 'border-bottom' : '' ">

            <!-- JOB DATA -->
            <v-row 
              :id="job._key"
              v-for="job in phase.jobs" 
              :key="job._key" 
              align="center">

              <v-col v-for="header in headers" 
                :key="header.value" 
                :cols="header.cols"
                :class="header.value.includes('qt') ? 'text-right' : '' "
                class="py-0">

                <!-- SELECT CHECKBOX -->
                <template v-if="header.value === 'phase_alias'">
                  <v-checkbox 
                    :color="$theme.blue"
                    :disabled="job.active"
                    :value="job_select_model[job._key]"
                    @change="updateSelectedJobData(job, $event)">
                  </v-checkbox>
                </template>

                <!-- JOB PROGRESS BAR -->
                <template v-else-if="header.value === 'progress'">
                  <v-row no-gutters align="center" >
                    <v-col cols="9">
                      <v-progress-linear 
                        dense 
                        :value="job.progress"
                        :color="job.active ? $theme.blue : $theme.grey">
                      </v-progress-linear>
                    </v-col>
                    <v-col class="pl-4 text-right body-2">
                      {{ job.progress }}%
                    </v-col>
                    <!-- <v-col cols="1" class="text-right pl-2">
                      <v-icon small 
                        v-if="item.critical" 
                        :color="$theme.red"
                        @click="$emit('criticalOnly')">
                        mdi-alert-octagon
                      </v-icon>
                      <v-icon small 
                        v-else-if="!item.on_time" 
                        :color="$theme.orange"
                        @click="$emit('lateOnly')">
                        mdi-alert
                      </v-icon>
                    </v-col> -->
                  </v-row>
                </template>
                <!-- END OF JOB PROGRESS BAR -->

                <!-- ASSIGNED OPERATOR -->
                <template v-else-if="header.value === 'assigned_to'">
                  <BaseUserAvatar v-if="job.assigned_to" :user="job.assigned_to" />
                  <v-btn v-else-if="selected_jobs.length === 0" small
                    :color="$theme.blue" 
                    @click="updateSelectedJobData(job, true); edit_mode = 'modify'">
                    ASSEGNA
                  </v-btn>
                </template>


                <template v-else-if="header.value === 'qt_remaining' ">
                  {{ job.qt_planned - job.qt_completed }}
                </template>

                <!-- OTHER FIELDS -->
                <template v-else>
                  <span class="body-2">
                    {{ job[header.value] | capitalize_all }}
                  </span>
                </template>
              </v-col>
            </v-row>    
            <!-- END OF JOB DATA -->
            


            <!-- JOB ACTIONS -->

            <v-row align="center">

              <!-- STARTING ACTION BUTTONS -->
              <template v-if="edit_mode=='actions'">

                <!-- SELECT ALL -->
                <v-btn small 
                  v-if="phase.jobs.length > 1"
                  :color="$theme.grey" 
                  @click="toggleAll(phase)">
                  {{ selected_jobs.length == 0
                    ? 'SELEZIONA TUTTI' 
                    : 'DELESEZIONA TUTTI' }}
                </v-btn>
                
                <!-- EDIT ACTIONS -->
                <template v-if="phase.editing">
                  <v-spacer></v-spacer>
                  <v-btn small 
                    :color="$theme.blue"
                    @click="edit_mode = 'modify'">
                    MODIFICA
                  </v-btn>
                </template>
              </template>
              <!-- END OF STARTING ACTION BUTTONS -->
            
              <!-- REBALANCE ACTION CARD -->
              <template v-if="edit_mode == 'modify' ">
                <JobRebalanceActionCard
                  :jobs="job_select_model"
                  @changeEditMode="edit_mode = $event">
                </JobRebalanceActionCard>
              </template>

            </v-row>
            <!-- END OF JOB ACTIONS -->

          </v-expansion-panel-content>
          <!-- END OF PHASE DETAILS -->

        </v-expansion-panel>
      </v-expansion-panels>
    </div>

    <v-spacer></v-spacer>

    <v-row v-if="!wo_data.active" justify="space-between" class="pb-2 mx-0 flex-grow-0">
      
      <v-btn :color="$theme.blue" @click="edit_qt = true">MODIFICA QUANTITÀ</v-btn>
      <v-btn 
        :color="$theme.blue" 
        :loading="saving"
        @click="edit_due_date = true">
        MODIFICA DATA SCADENZA
      </v-btn>
      <v-btn :color="$theme.red">CHIUDI ORDINE</v-btn>
    </v-row>

    <!-- EDIT DUE DATE -->
    <v-dialog 
      :value="edit_due_date" 
      @click:outside="closeEditDialogs"
      @keydown.esc="closeEditDialogs"
      width="300px">
      <v-date-picker
        :color="$theme.blue"
        show-week no-title
        locale="it-it"
        first-day-of-week="1"
        width="300px"
        :value="wo_data.due_by"
        @change="new_due_date = $event">
        <v-row justify="space-between" class="mx-0">
          <v-btn small text
            :color="$theme.grey" 
            @click="closeEditDialogs">
            ANNULLA
          </v-btn>
          <v-btn small text v-if="new_due_date"
            :color="$theme.blue"
            @click="saveWorkOrderUpdate">
            SALVA
          </v-btn>
        </v-row>
      </v-date-picker>
    </v-dialog>


    <!-- EDIT QT -->
    <v-dialog 
      :value="edit_qt" 
      @click:outside="closeEditDialogs"
      @keydown.esc="closeEditDialogs"
      width="300px">
      <v-card elevation="8">
        <v-container>
          <v-row class="mx-0" align="center">  
            <v-col cols="7">
              <h4 class="display highlight text-uppercase">
                nuova quantità
              </h4>      
            </v-col> 
            <v-col cols="5" class="d-flex align-center">
              <v-text-field
                ref="new_qt" 
                class="pa-0 ma-0" 
                label="Nuova quantità"
                single-line 
                hide-details
                reverse
                type="number"
                :min="min_allowable_wo_qt"
                :value="wo_data.qt_planned"
                @input="new_qt = $event">
              </v-text-field>
            </v-col>       
          </v-row>
          <v-card-actions class="justify-space-between">
            <v-btn small text
              :color="$theme.grey" 
              @click="closeEditDialogs">
              ANNULLA
            </v-btn>
            <v-btn small text v-if="new_qt != wo_data.qt_planned"
              :color="$theme.blue"
              @click="show_job_qt_rebalance = true">
              SALVA
            </v-btn>
          </v-card-actions>    
        </v-container>
      </v-card>
    </v-dialog>
    
      
    <template v-if="show_job_qt_rebalance">
    <WorkOrderJobQtRebalance 
      v-bind="{ new_wo_qt: parseInt(new_qt), phase_data, wo_key: wo_data._key }"
      @close="closeEditDialogs">    
    </WorkOrderJobQtRebalance>
    </template>
  
  </v-container>
</template>

<script>
import BaseUserAvatar from '@/components/BaseUserAvatar.vue'
import JobRebalanceActionCard from '@/components/JobRebalanceActionCard.vue'
import WorkOrderJobQtRebalance from '@/components/WorkOrderJobQtRebalance.vue'

export default {

  name: 'WorkOrderJobs',

  components: {
    BaseUserAvatar,
    JobRebalanceActionCard,
    WorkOrderJobQtRebalance
  },

  props: {
    wo_data: {
      type: Object,
      required: true,
      default: function() {
        return { phase_sequence: [] }
      }
    },
  },

  data () {
    return {
      saving: false,
      headers: [
        { value: 'phase_alias', text: 'FASE', cols: 2, width: '20%'},
        { value: 'progress', text: 'AVANZAMENTO', cols: 4, width: '30%'},
        { value: 'qt_completed', text: 'QComp', align: 'end', cols: false, width: 'auto'},
        // { value: 'qt_released', text: 'QRil', align: 'end', cols: false, width: 'auto'},
        { value: 'qt_remaining', text: 'QRim', align: 'end', cols: false, width: 'auto'},
        { value: 'assigned_to', text: 'ASSEGNATO A', align: 'end', cols: '3', width: '30%'},
      ],
      expanded_phase: null,
      job_select_model: {},
      jobs_temp_data: {},
      edit_mode: 'actions',
      edit_qt: false,
      new_qt: null,
      edit_due_date: false,
      new_due_date: null,
      show_job_qt_rebalance: false
      // selected_jobs: []
    }
  },

  computed: {
    phase_data() {
      return this.wo_data.phase_sequence.map( phase_key => {
        const jobs = this.wo_data.jobs.filter( j => j.phase_key === phase_key )
        const params = jobs[0].parameters
        const phase_alias = jobs[0].phase_alias
        const total_completed = jobs.reduce( (sum, job) => sum + job.qt_completed, 0)
        // const total_released = jobs.reduce( (sum, job) => sum + job.qt_released, 0 )
        const total_remaining = jobs.reduce( (sum, job) => sum + job.qt_planned - job.qt_completed, 0 )
        const total_progress = Math.floor(
          jobs.reduce( (sum, job) => sum + job.progress * job.qt_planned, 0) / this.wo_data.qt_planned
        )
        const active = jobs.reduce( (count, job) => count + job.active, 0)
        const editing = jobs.some( j => this.selected_jobs.includes(j._key) )

        // const assignments = jobs.map( job => job.assigned_to )

        return {
          jobs,
          phase_key,
          phase_alias,
          editing,
          active,
          ...params,
          // qt_released: total_released,
          qt_completed: total_completed,
          qt_remaining: total_remaining,
          progress: total_progress,
        }
      })
    },

    selected_jobs() {
      return Object.entries(this.job_select_model).reduce( 
        ( array, [job,selected] ) => { 
          if (selected) { array.push(job) } 
          return array 
        }, [])
    },

    min_allowable_wo_qt() {
      return Math.max(this.wo_data.jobs.map(j => j.qt_completed))
    }
  },

  methods: {

    toggleAll(phase) {
      if (this.selected_jobs.length) {
        this.job_select_model = {}
      }
      else phase.jobs.forEach( j => {
        this.$set(this.job_select_model, j._key, j)
      })
    },

    updateSelectedJobData(job, selected) {
      if (selected) {
        this.$set(this.job_select_model, job._key, job) 
      }
      else this.$delete(this.job_select_model, job._key)
    },

    closeEditDialogs() {
      this.edit_due_date = false
      this.edit_qt = false
      this.new_due_date = null
      this.new_qt = null
      this.show_job_qt_rebalance = false
      setTimeout(() => {
        this.$refs.new_qt.internalValue = this.wo_data.qt_planned
      }, 500)
    },

    async saveWorkOrderUpdate() {
      this.saving = true

      const wo_update = {
        wo_key: this.wo_data._key,
        new_qt: this.new_qt,
        new_due_date: this.new_due_date
      }
      await this.$store.dispatch('updateWorkOrder', wo_update)
      this.closeEditDialogs()
      setTimeout(() => this.saving = false, 1000)
    }

  },

  watch: {
    expanded_phase() {
      this.job_select_model = {}
    },

    job_select_model() {
      // reset edit_mode after closing/switching phase details
      if (Object.keys(this.job_select_model).length === 0) this.edit_mode = 'actions'
    },
  },
}
</script>

<style lang="css" scoped>
.border-top {
  border-top: thin solid rgba(255,255,255,0.12)
}

.border-bottom {
  border-bottom: thin solid rgba(255,255,255,0.12)
}

.v-expansion-panel {
  background-color: transparent !important
}

.v-expansion-panel-header {
  
}

</style>