<template>
  <v-card flat outlined width="100%">
    <v-container fluid>
      <!-- TABLE HEADER -->
      <v-row>
        <v-col 
          v-for="col in headers" 
          :key="col.value" 
          :cols="col.cols"
          :offset="col.offset" 
          class="pt-0 text-uppercase">
          <h5>{{ col.text }}</h5>
        </v-col>
      </v-row>

      <v-row dense v-for="(j, index) in temp_jobs" :key="index" align="center">
        <v-col 
          v-for="col in headers" 
          :key="col.value" 
          :cols="col.cols"
          :offset="col.offset" 
          class="body-2">
          <template v-if="col.value === 'key'">
            {{ getKeyFromId(j._id) }}
            <v-chip v-if="j.trash" 
              small label close 
              :color="$theme.orange"
              class="ml-2 solid-white weight-bold"
              @click:close="restoreJob(index)">
              CHIUSO
            </v-chip>
          </template>

          <template v-if="col.value === 'qt_remaining' && !j.trash">
            <v-text-field
              class="ma-0 pa-0"
              :key="index"
              reverse
              single-line
              hide-details
              type="number"
              :value="j.qt_remaining"
              :min="0"
              :max="total_remaining"
              @input="updateRemainingQt(index, $event)">
            </v-text-field>
          </template>

          <template v-if="col.value === 'assigned_to'">
            <!-- Show current operator if present -->
            <template v-if="notReassignable(index)">
              <BaseUserAvatar :user="j.assigned_to" />
            </template>

            <!-- Show operator select if new job -->
            <template v-else>
              <v-autocomplete
                ref="operator_autocomplete"
                autocomplete="off"
                :value="j.assigned_to"
                :items="$store.getters.operator_list()"
                item-value="_id"
                single-line hide-details
                return-object
                :filter="filterOperator"
                label="Assegna a:"

                class="pt-0 flex-grow-0 body-2"
                @focus.native="resetAssignment(index)"
                @change="setAssignment(index, $event)">
                <template v-slot:item="{ item: list_item }">
                  <BaseUserAvatar :user="list_item"/>
                </template>
                <template v-slot:selection="{ item: selection }">
                  <BaseUserAvatar :user="selection"/>
                </template>
              </v-autocomplete>
            </template>
          </template>
        </v-col>

        <v-col 
          cols="auto" 
          v-if="deletable(index) && !j.trash" class="ml-auto pr-8">
          <BaseTooltipIcon
            :color="$theme.red"
            tooltip="Elimina lavoro"
            icon="delete"
            @iconClick="removeJob(index)">
          </BaseTooltipIcon>
        </v-col>
      </v-row>

      <v-row align="center">
        <v-col 
          v-for="col in headers" 
          :key="col.value" 
          :cols="col.cols"
          :offset="col.offset" 
          class="text-uppercase body-2"
          :class="col.value === 'qt_remaining' ? 'text-right' : '' ">
          <template v-if="col.value === 'key'">
            <span class="font-weight-medium">TOTALE INIZIALE/FINALE</span>
          </template>

          <template v-if="col.value === 'qt_remaining'">
            <span class="body-1">{{ total_remaining }} / </span>
            <span class="body-1" :style="remaining_style">{{ new_total }}</span>
            <span class="caption ml-4 mr-n10">({{ remaining_delta }})</span>
          </template>        
        </v-col>
      </v-row>

      <v-row dense class="mt-4">
        <v-col cols="auto">
          <v-btn small
            v-if="job_template.parameters.parallel_job_allowed"
            :color="$theme.blue"
            @click="addJob">
            aggiungi lavoro
          </v-btn>
        </v-col>
        
        <v-col cols="auto">
          <v-btn small
            :color="$theme.blue"
            @click="rebalanceJobs">
            distribuisci qt
          </v-btn>
        </v-col>

        <v-col cols="auto">
          <v-btn small
            :color="$theme.orange"
            @click="resetJobs">
            ripristina qt iniziali
          </v-btn>
        </v-col>
        
        <v-col cols="auto">
          <v-btn small 
            :color="$theme.grey" 
            @click="$emit('changeEditMode','actions')">
            ANNULLA
          </v-btn>
        </v-col>

        <v-col cols="auto" class="ml-auto">
          <v-btn small
            :color="$theme.blue"
            @click="save">
            <span v-if="!saving">SALVA</span>
            <v-progress-circular v-else indeterminate size="26" />
          </v-btn>
        </v-col>
      </v-row>
    </v-container>
  </v-card>
</template>

<script>
import BaseUserAvatar from '@/components/BaseUserAvatar.vue'
import multiMatch from '@/lib/MultiFieldSearch.js'
import BaseTooltipIcon from '@/components/BaseTooltipIcon.vue'

export default {

  name: 'JobRebalanceActionCard',

  components: {
    BaseUserAvatar,
    BaseTooltipIcon
  },

  props: {
    jobs: {
      type: Object,
      required: true,
    }
  },

  data () {
    return {
      headers: [
        { value: 'key', cols: 3, offset: 0, text: 'ID lavoro' },
        { value: 'qt_remaining', cols: 2, offset: 1, text: 'Quantità'},
        { value: 'assigned_to', cols: 3, offset: 1, text: 'Assegnato a'}
      ],
      temp_jobs: [],
      new_total: 0,
      saving: false,

      // Metadata to carry over from existing jobs to new ones
      new_job_keys: [
        'wo_id', 
        'wo_code', 
        'wo_line', 
        'phase_id', 
        'phase_alias',
        'product_id',
        'product_code',
        'product_description',
        'parameters'
      ],
      job_template: {}
    }
  },

  computed: {
    
    wo_key() {
      return this.$route.params.wo_key
    }, 

    total_remaining() {
      return Object.values(this.jobs).reduce( (sum, job) => sum + job.qt_planned - job.qt_completed, 0)
    },

    remaining_match() {
      return this.new_total === this.total_remaining 
    },

    remaining_style() {
      return this.remaining_match
      ? 'color: var(--high-white)'
      : 'color: ' + this.$theme.orange + '; font-weight: bold'
    },

    remaining_delta() {
      const delta = this.new_total - this.total_remaining
      const sign = delta < 0 ? '' : '+'
      return `${sign}${delta}`
    }
  },

  methods: {
    getKeyFromId(id) {
      return id ? id.split('/')[1] : 'NUOVO'
    },

    updateNewTotal() {
      this.new_total = this.temp_jobs
        .filter(j => !j.trash)
        .reduce( (sum, job) => sum + job.qt_remaining, 0)
    },

    notReassignable(index) {
      const j = this.temp_jobs[index]
      const has_assignee = j.assigned_to
      const started = ['started', 'completed'].includes(j.stage)
      const to_be_closed = j.trash
      return (has_assignee && started) || to_be_closed
    },

    deletable(index) {
      // A job can be deleted only if it hasn't been started yet and is not the last one left (there must be at least a job per phase)
      const started = ['started', 'completed'].includes(this.temp_jobs[index].stage)
      const not_last_job = this.temp_jobs.length > 1
      return !started && not_last_job
    },

    removeJob(index) {
      if (this.temp_jobs[index]._id) {
        this.$set(this.temp_jobs[index], 'trash', true)
      }
      else this.temp_jobs.splice(index, 1)
    },

    restoreJob(index) {
      this.$delete(this.temp_jobs[index], 'trash')
    },

    addJob() {
      this.temp_jobs.push({...this.job_template})
    },

    rebalanceJobs() {
      // check if quantity is divisible by the number of jobs considered
      let jobs = this.temp_jobs.filter(j => !j.trash)
      let remainder = this.total_remaining % jobs.length

      // Spread remaining quantity among all jobs, excluding started jobs to be closed
      for (let j of this.temp_jobs) {

        if (!j.trash) j.qt_remaining = Math.floor(this.total_remaining / jobs.length)
      }

      // assign remainder starting from the first job, excluding started jobs to be closed
      if (remainder) {
        for (let i=0; i < remainder; i++) {
          let j = this.temp_jobs[i]
          if (!j.trash) j.qt_remaining ++
        }
      }
    },

    resetJobs() {
      // restore already existing jobs to their original quantity and reset to 0 those that are being created now
      this.temp_jobs.forEach( j => {
        if (!j._id) j.qt_remaining = 0
        else {
          j.trash = false
          const original = this.jobs[j._id]
          j.qt_remaining = original.qt_planned - original.qt_completed
        }
      })
    },
    
    filterOperator(operator, search_text) {
      return multiMatch(search_text, operator, ['name', 'surname'])
    },

    updateRemainingQt(job_index, qt) {
      this.$set(this.temp_jobs[job_index], 'qt_remaining', +qt)
      // this.updateNewTotal()
    },
    
    resetAssignment(job_index) {
      this.$delete(this.temp_jobs[job_index], 'assigned_to')
    },
    
    setAssignment(job_index, operator_id) {
      this.$set(this.temp_jobs[job_index], 'assigned_to', operator_id)
    },

    save() {

      // Check if overall job quantity matches original remaining quantity
      if (!this.remaining_match) window.alert('Le quantità non combaciano')

      else {
        this.saving = true
        const updates = this.temp_jobs.map( j => {
          
          // Delete job
          if (j.trash) {
            return { action: 'delete', data: { _id: j._id } }
          }

          // Update to existing job
          else if (j._id) {
            const new_planned_qt = j.qt_completed + j.qt_remaining
            const assignee = j.assigned_to._id
            return { 
              action: 'update', 
              data: { _id: j._id, qt_planned: new_planned_qt, assigned_to: assignee }
            }
          }

          // New job created
          else return { 
            action: 'insert',
            data: {
              // Use all metadata from template overriding what's necessary
              ...j, 
              qt_planned: j.qt_remaining, 
              assigned_to: j.assigned_to._id 
            }
          }
        })

        this.$store.dispatch('updateJobs', { 
          job_updates: updates, 
          wo_key: this.wo_key 
        })
        .then(() => {
          this.saving = false
          this.$emit('changeEditMode', 'actions')
        })
        .catch( err => {
          window.alert("Couldn't save updates: ", err)
          this.saving = false
        })
      }
    }
  },

  created() {
    this.temp_jobs = Object.values(this.jobs).map(j => {
      return {
        ...j,
        qt_remaining: j.qt_planned - j.qt_completed
      }
    })

    // this.updateNewTotal()

    // Use the first job of the phase to retrieve job metadata for new ones
    this.job_template = Object.fromEntries(
      this.new_job_keys.map( k => {
        return [k, this.temp_jobs[0][k]]
      }, this)
    )
    // This is just temporary data to properly handle presentation to the user. The quantity will eventually be the planned quantity of the new job
    this.job_template.qt_remaining = 0
  },

  watch: {
    temp_jobs: {
      immediate: true,
      deep: true,
      handler: 'updateNewTotal'
    }
  }
}
</script>

<style lang="css" scoped>
</style>