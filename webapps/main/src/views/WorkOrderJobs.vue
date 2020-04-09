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
          :key="phase.phase_id"
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
                <!-- END OF PHASE PROGRESS -->

                <!-- OTHER PHASE DATA -->
                <template v-else>
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
              :id="job._id"
              v-for="job in phase.jobs" 
              :key="job._id" 
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
                    :value="job_select_model[job._id]"
                    @change="updateSelectedJobData(job, $event)">
                  </v-checkbox>
                </template>

                <!-- JOB PROGRESS BAR -->
                <template v-else-if="header.value === 'progress'">
                  <v-row no-gutters align="center" >
                    <v-col cols="9">
                      <v-progress-linear 
                        dense 
                        :value="phase.progress"
                        :color="phase.active ? $theme.blue : $theme.grey">
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
                    @click="updateSelectedJobData(job, true); edit_mode = 'assign'">
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
  </v-container>
</template>

<script>
import BaseUserAvatar from '@/components/BaseUserAvatar.vue'
import JobRebalanceActionCard from '@/components/JobRebalanceActionCard.vue'

export default {

  name: 'WorkOrderJobs',

  components: {
    BaseUserAvatar,
    JobRebalanceActionCard
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
      headers: [
        { value: 'phase_alias', text: 'FASE', cols: 2, width: '20%'},
        { value: 'progress', text: 'AVANZAMENTO', cols: 4, width: '30%'},
        { value: 'qt_completed', text: 'QComp', align: 'end', cols: false, width: 'auto'},
        { value: 'qt_released', text: 'QRil', align: 'end', cols: false, width: 'auto'},
        { value: 'qt_remaining', text: 'QRim', align: 'end', cols: false, width: 'auto'},
        { value: 'assigned_to', text: 'ASSEGNATO A', align: 'end', cols: '3', width: '30%'},
      ],
      expanded_phase: null,
      job_select_model: {},
      jobs_temp_data: {},
      edit_mode: 'actions',
      // selected_jobs: []
    }
  },

  computed: {
    phase_data() {
      return this.wo_data.phase_sequence.map( phase_id => {
        const jobs = this.wo_data.jobs.filter( j => j.phase_id === phase_id )
        const params = jobs[0].parameters
        const phase_alias = jobs[0].phase_alias
        const total_completed = jobs.reduce( (sum, job) => sum + job.qt_completed, 0)
        const total_released = jobs.reduce( (sum, job) => sum + job.qt_released, 0 )
        const total_remaining = jobs.reduce( (sum, job) => sum + job.qt_planned - job.qt_completed, 0 )
        const total_progress = Math.floor(
          jobs.reduce( (sum, job) => sum + job.progress, 0) / jobs.length
        )
        const active = jobs.reduce( (count, job) => count + job.active, 0)
        const editing = jobs.some( j => this.selected_jobs.includes(j._id) )

        // const assignments = jobs.map( job => job.assigned_to )

        return {
          jobs,
          phase_id,
          phase_alias,
          editing,
          active,
          ...params,
          qt_released: total_released,
          qt_completed: total_completed,
          qt_remaining: total_remaining,
          progress: total_progress,
          assigned_to: '' //assignments
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
  },

  methods: {

    toggleAll(phase) {
      if (this.selected_jobs.length) {
        this.job_select_model = {}
      }
      else phase.jobs.forEach( j => {
        this.$set(this.job_select_model, j._id, j)
      })
    },

    updateSelectedJobData(job, selected) {
      if (selected) {
        this.$set(this.job_select_model, job._id, job) 
      }
      else this.$delete(this.job_select_model, job._id)
    },

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