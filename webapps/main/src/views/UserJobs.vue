<template>
  <v-container  fluid class="fill scroll">
    
    <transition name="slide-fade" mode="out-in" v-if="vuex_ready">
      <router-view  v-bind="{ first_job, job_list }">
      </router-view>
    </transition>

    <v-row v-else align="center" justify="center">
      <v-col cols="auto" class="d-flex flex-column align-center">
        <p>Recupero dati...</p>
        <v-progress-circular 
          indeterminate 
          size="40" 
          :color="$theme.blue"
          class="mt-6">
        </v-progress-circular>
      </v-col>
    </v-row>

  </v-container>
</template>

<script>
export default {

  name: 'UserJobs',

  data () {
    return {
      vuex_ready: false,
    }
  },

  computed: {

    user_jobs() {
      return this.vuex_ready
        ? this.$store.state.job.assigned_job_list[0].assigned_jobs
        : []
    },

    first_job() {
      return this.$route.query.job === 'first'
    },

    unassigned_jobs() {
      return this.vuex_ready
        ? this.$store.state.job.unassigned_job_list
        : []
    },

    job_list() {
      const assigned_jobs = this.user_jobs.map( j => {
        return {
          assigned: true,
          ...j
        }
      })

      const unassigned_jobs = this.unassigned_jobs.map( j => {
        return {
          assigned: false,
          ...j
        }
      })

      let list = [...assigned_jobs, ...unassigned_jobs]
      return list
    },
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
.slide-fade-enter-active,
.slide-fade-leave-active {
  transition: opacity 0.3s, transform 0.3s;
}

.slide-fade-enter,
.slide-fade-leave-to {
  opacity: 0;
  transform: translateX(-5%);
}


</style>