<template>
  TEST
</template>

<script>
import BaseUserAvatar from '@/components/BaseUserAvatar.vue'

export default {

  name: 'WorkOrderJobQtRebalance',

  components: {
    BaseUserAvatar
  },

  props: {
    phase_data: {
      type: Array,
      required: true
    },
    new_wo_qt: {
      type: Number,
      required: true
    },
    wo_key: {
      type: String,
      required: true
    }
  },

  data () {
    return {
      phase_index: 0,
      job_updates: {}, // job_key => qt
      saving: false
    }
  },

  computed: {
    // phases_to_rebalance() {
    //   return this.phase_data.filter( p => p.jobs.length > 1 )
    // },

    phases_delta() {
      if (this.job_updates != {}) {
        const self = this
        const delta_map = this.phase_data.reduce( (obj, phase) => {
          const phase_temp_remaining = phase.jobs.reduce( (sum, job) => sum + self.job_updates[job._key].new_remaining, 0)
          obj[phase.phase_key] = self.new_wo_qt - (phase.qt_completed + phase_temp_remaining)
          return obj
        }, {})
        return delta_map
      }
      else return {}
    },

    can_save() {
      // Check if any delta is not zero
      const any_phase_has_delta = Object.entries(this.phases_delta).some( (phase_entry) => phase_entry.delta )
      return !any_phase_has_delta
    }
  },

  methods: {

    save() {
      if (this.can_save) {
        this.saving = true
        const updates = Object.entries(this.job_updates).map( ([job_key, data]) => {
          const job_update =  {
            action: 'update',
            data: { _key: job_key, qt_planned: data.completed + data.new_remaining }
          }
          return job_update
        })
        // dispatch wo and job updates
        this.$store.dispatch('updateWorkOrder', {
          wo_key: this.wo_key,
          new_qt: this.new_wo_qt,
          job_updates: updates
        })
        .then(() => {
          this.saving = false
          this.$emit('close')
        })
        .catch( err => window.alert(err) )
      }
      else window.alert(this.$tc('work_order.alerts.assign_workload_first'))
    }
  },

  created() {
    this.job_updates = this.phase_data.reduce( (obj, phase) => {
      phase.jobs.forEach( j => {
        obj[j._key] = {
          new_remaining: j.qt_planned - j.qt_completed,
          completed: j.qt_completed
        }
      })
      return obj
    }, {})
  }
}
</script>

<style lang="css" scoped>
</style>
