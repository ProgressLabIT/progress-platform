<template>
  <div v-for="n in 100" :key="n">
    THIS IS A TEST
  </div>
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

    headers() {
      return [
        {
          value: 'phase_alias',
          text: this.$tc('phase.short').toUpperCase(),
          cols: 2,
          width: '20%'
        },
        {
          value: 'progress',
          text: this.$tc('progress').toUpperCase(),
          cols: 4,
          width: '30%'
        },
        {
          value: 'qt_completed',
          text: this.$tc('quantity.completed.short').toUpperCase(),
          align: 'end',
          cols: false,
          width: 'auto'
        },
        // { value: 'qt_released', text: 'QRil', align: 'end', cols: false, width: 'auto'},
        {
          value: 'active_batch_qt',
          text: this.$tc('quantity.active.short').toUpperCase(),
          align: 'end',
          cols: false,
          width: 'auto'
        },
        {
          value: 'qt_remaining',
          text: this.$tc('quantity.remaining.short').toUpperCase(),
          align: 'end',
          cols: false,
          width: 'auto'
        },
        {
          value: 'assigned_to',
          text: this.$tc('job.assigned_to').toUpperCase(),
          align: 'end',
          cols: '3',
          width: '30%'
        },
      ]
    },

    phase_data() {
      return this.wo_data.phase_sequence.map( phase_key => {
        const jobs = this.wo_data.jobs.filter( j => j.phase_key === phase_key )
        const params = jobs[0].parameters
        const phase_alias = jobs[0].phase_alias
        const total_completed = jobs.reduce( (sum, job) => sum + job.qt_completed, 0)
        const total_active = jobs.reduce( (sum, job) => sum + job.active_batch_qt, 0)
        // const total_released = jobs.reduce( (sum, job) => sum + job.qt_released, 0 )
        const total_remaining = jobs.reduce( (sum, job) => {
          return sum + job.qt_planned - job.qt_completed - job.active_batch_qt
        }, 0)
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
          active_batch_qt: total_active,
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
      else {
        // Select jobs that are open and NOT active
        phase.jobs.filter(j => {
          const job_is_open = j.stage != 'closed'
          const job_not_active = !j.active
          return job_is_open && job_not_active
        })
        .forEach( j => {
          this.$set(this.job_select_model, j._key, j)
        })
      }
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

    edit_mode() {
      if (this.edit_mode === 'actions') {
        this.job_select_model = {}
      }
    }
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
