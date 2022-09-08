<template>
  <v-dialog
    value="true"
    overlay-opacity=".9"
    width="80%"
    persistent no-click-animation>
    <v-row justify="center" class="mx-0 mb-2 highlight display text-uppercase">
      <h4>{{ job_template.phase_alias }}</h4>
    </v-row>
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
              <span class="text-uppercase">
                {{ j._key || $tc('new') }}
              </span>
              <v-chip v-if="j.trash"
                small label close
                :color="$theme.orange"
                class="ml-2 solid-white weight-bold text-uppercase"
                @click:close="reopenJob(index)">
                {{ $tc('closed') }}
              </v-chip>
            </template>

            <template v-if="col.value === 'qt_remaining' && !j.close">
              <v-text-field
                class="ma-0 pa-0"
                :key="index"
                reverse
                single-line
                hide-details
                type="number"
                :value="j.qt_remaining"
                min="0"
                :max="qt_to_allocate"
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
                  item-value="_key"
                  single-line hide-details
                  return-object
                  clearable
                  :filter="filterOperator"
                  :label="$tc('job.assign_to') + ':' | capitalize"

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
              :tooltip="$tc('delete') | capitalize"
              icon="delete"
              @iconClick="closeJob(index)">
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
              <span class="font-weight-medium text-uppercase">
                {{ $tc('start_end_totals') }}
              </span>
            </template>

            <template v-if="col.value === 'qt_remaining'">
              <span class="body-1">{{ qt_to_allocate }} / </span>
              <span class="body-1" :style="remaining_style">{{ working_total_remaining }}</span>
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
              {{ $tc('job.add') }}
            </v-btn>
          </v-col>

          <v-col cols="auto">
            <v-btn small
              :color="$theme.blue"
              @click="rebalanceJobs">
              {{ $tc('job.rebalance.spread') }}
            </v-btn>
          </v-col>

          <v-col cols="auto">
            <v-btn small
              :color="$theme.orange"
              @click="resetJobs">
              {{ $tc('job.rebalance.reset') }}
            </v-btn>
          </v-col>

          <v-col cols="auto">
            <v-btn small
              :color="$theme.grey"
              @click="$emit('changeEditMode','actions')">
              {{ $tc('cancel') }}
            </v-btn>
          </v-col>

          <v-col cols="auto" class="ml-auto">
            <v-btn small
              :color="$theme.blue"
              @click="save">
              <span v-if="!saving">
                {{ $tc('save') }}
              </span>
              <v-progress-circular v-else indeterminate size="26" />
            </v-btn>
          </v-col>
        </v-row>
      </v-container>
    </v-card>
  </v-dialog>
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
      temp_jobs: [],
      working_total_remaining: 0,
      saving: false,

      // Metadata to carry over from existing jobs to new ones
      new_job_keys: [
        'wo_key',
        'wo_code',
        'wo_line',
        'phase_key',
        'phase_alias',
        'product_key',
        'product_code',
        'product_description',
        'parameters',
        'step_sequence'
      ],
      job_template: {}
    }
  },

  computed: {

    headers() {
      return [
        {
          value: 'key',
          text: this.$tc('job.key'),
          cols: 3,
          offset: 0
        },
        {
          value: 'qt_remaining',
          text: this.$tc('quantity.long'),
          cols: 2,
          offset: 1
        },
        {
          value: 'assigned_to',
          text: this.$tc('job.assigned_to'),
          cols: 3,
          offset: 1
        }
      ]
    },

    wo_key() {
      return this.$route.params.wo_key
    },

    qt_to_allocate() {
      return Object.values(this.jobs).reduce( (sum, job) => {
        return sum + job.qt_planned - job.qt_completed - job.active_batch_qt
      }, 0)
    },

    remaining_match() {
      return this.working_total_remaining === this.qt_to_allocate
    },

    remaining_style() {
      return this.remaining_match
      ? 'color: var(--high-white)'
      : 'color: ' + this.$theme.orange + '; font-weight: bold'
    },

    remaining_delta() {
      /*
       * A minus is automatically shown in case of negative numbers.
       * Adds a plus in case of positive ones for better readability
       */
      const delta = this.working_total_remaining - this.qt_to_allocate
      const sign = delta < 0 ? '' : '+'
      return `${sign}${delta}`
    }
  },

  methods: {

    updateNewTotal() {
      this.working_total_remaining = this.temp_jobs
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

    closeJob(index) {
      if (this.temp_jobs[index]._key) {
        this.$set(this.temp_jobs[index], 'close', true)
      }
      else this.temp_jobs.splice(index, 1)
    },

    reopenJob(index) {
      this.$delete(this.temp_jobs[index], 'close')
    },

    addJob() {
      this.temp_jobs.push({...this.job_template})
    },

    rebalanceJobs() {
      // check if quantity is divisible by the number of jobs considered
      let jobs = this.temp_jobs.filter(j => !j.close)
      let remainder = this.qt_to_allocate % jobs.length

      // Spread remaining quantity among all jobs, excluding started jobs to be closed
      for (let j of this.temp_jobs) {

        if (!j.close) j.qt_remaining = Math.floor(this.qt_to_allocate / jobs.length)
      }

      // assign remainder starting from the first job, excluding started jobs to be closed
      if (remainder) {
        for (let i=0; i < remainder; i++) {
          let j = this.temp_jobs[i]
          if (!j.close) j.qt_remaining ++
        }
      }
    },

    resetJobs() {
      // restore already existing jobs to their original quantity and reset to 0 those that are being created now
      this.temp_jobs.forEach( j => {
        if (!j._key) j.qt_remaining = 0
        else {
          j.close = false
          const original = this.jobs[j._key]
          j.qt_remaining = original.qt_planned - original.qt_completed
        }
      })
    },

    filterOperator(operator, search_text) {
      return multiMatch(search_text, operator, ['name', 'surname'])
    },

    updateRemainingQt(job_index, qt) {
      /* If qt is zero and there's no active batch close job
       * otherwise update new quantity
       */
      if (qt === 0 && this.temp_jobs[job_index].active_batch_qt === 0) {
        this.$set(this.temp_jobs[job_index], 'close', true)
      }
      else {
        this.$set(this.temp_jobs[job_index], 'qt_remaining', +qt)
      }
    },

    resetAssignment(job_index) {
      this.$delete(this.temp_jobs[job_index], 'assigned_to')
    },

    setAssignment(job_index, operator) {
      this.$set(this.temp_jobs[job_index], 'assigned_to', operator)
    },

    capitalize(string) {
      return this.$options.filters.capitalize(string)
    },

    save() {
      // Check if overall job quantity matches original remaining quantity
      if (!this.remaining_match) {
        window.alert(
          this.capitalize(this.$tc('job.alerts.rebalance_qt_mismatch'))
        )
      }

      else {
        this.saving = true
        const updates = this.temp_jobs.map( j => {
        const user_full_name = this.$store.getters.userFullName
        const datetime = new Date().toLocaleString()

          // Close job
          if (j.cancel) {
            return {
              action: 'close',
              data: {
                _key: j._key,
                notes: `Job closed by ${user_full_name} on ${datetime}`
              }
            }
          }

          // Update to existing job
          else if (j._key) {
            const new_planned_qt = j.qt_completed + j.qt_remaining + j.active_batch_qt
            const assignee = j.assigned_to ? j.assigned_to._key : null
            return {
              action: 'update',
              data: {
                _key: j._key,
                qt_planned: new_planned_qt,
                assigned_to: assignee,
                notes: `Job last updated by ${user_full_name} on ${datetime}`
              }
            }
          }

          // New job created
          else return {
            action: 'insert',
            data: {
              // Use all metadata from template overriding what's necessary
              ...j,
              qt_planned: j.qt_remaining,
              assigned_to: j.assigned_to ? j.assigned_to._key : null,
              notes: `Job added by ${user_full_name} on ${datetime}`
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
          window.alert(this.$tc("errors.save_err") + ": ", err)
          this.saving = false
        })
      }
    }
  },

  created() {
    this.temp_jobs = Object.values(this.jobs).map(j => {
      return {
        ...j,
        qt_remaining: j.qt_planned - j.qt_completed - j.active_batch_qt
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
