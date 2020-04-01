<template>
  <v-container>
    <v-data-table
      :headers="headers"
      :items="phase_data">
    </v-data-table>
  </v-container>
</template>

<script>
export default {

  name: 'WorkOrderJobs',

  props: {
    wo_data: {
      type: Object,
      required: true,
    }
  },

  data () {
    return {
      headers: [
        { value: 'phase_alias', text: 'FASE'},
        { value: 'progress', text: 'PROGRESSO'},
        { value: 'qt_completed', text: 'QC'},
        { value: 'qt_released', text: 'QR'},
        { value: 'assigned_to', text: 'ASSEGNATO A'},
      ]
    }
  },

  computed: {
    phase_data() {
      return Object.entries(this.wo_data.phase_jobs).map( ([phase_id, phase]) => {
        let jobs = phase.jobs
        const total_completed = jobs.reduce( (sum, job) => sum + job.qt_completed, 0)
        const total_released = jobs.reduce( (sum, job) => sum + job.qt_released, 0 )
        const total_progress = Math.floor(
          jobs.reduce( (sum, job) => sum + job.progress, 0) / jobs.length
        )
        return {
          ...phase,
          phase_id,
          qt_released: total_released,
          qt_completed: total_completed,
          progress: total_progress
        }
      })
    }
  }
}
</script>

<style lang="css" scoped>
</style>