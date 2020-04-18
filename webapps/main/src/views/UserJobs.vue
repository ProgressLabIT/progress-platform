<template>
  <v-container fluid class="fill scroll">
    <v-card 
      v-for="j in user_jobs" 
      :key="j._id" 
      class="mt-2" 
      @dblclick="$router.push(routeTo(j._id))">
      <v-container>
        <v-row v-for="e in Object.entries(j)" :key="e[0]" cols="auto">
          <v-col cols="2">{{ e[0] }}</v-col>
          <v-col >{{ e[1] }}</v-col>
        </v-row>
      </v-container>
    </v-card>
  </v-container>
</template>

<script>
export default {

  name: 'UserJobs',

  data () {
    return {
      vuex_ready: false
    }
  },

  computed: {

    user_jobs() {
      return this.vuex_ready
        ? this.$store.state.job.assigned_job_list[0].assigned_jobs
        : []
    },

    unassigned_jobs() {
      return this.vuex_ready
        ? this.$store.state.job.unassigned_job_list
        : []
    }
  },

  methods: {
    routeTo(job_id) {
      return {
        name: 'workSession',
        params: {
          job_key: job_id.split('/')[1]
        }
      }
    }
  },

  created() {
    // this.$store.commit('UPDATE_SCREEN_TITLE', 'SESSIONE DI LAVORO')
    const user_id = this.$store.state.traceability.user._id
    this.$store.dispatch('loadJobAssignments', user_id)
    .then(() => this.vuex_ready = true)
  }
}
</script>

<style lang="css" scoped>
</style>