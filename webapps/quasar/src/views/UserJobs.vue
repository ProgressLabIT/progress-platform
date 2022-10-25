<template>
  <div class="fill q-pa-md">
    
    <transition name="slide-fade" mode="out-in" v-if="vuex_ready">
      <router-view  v-bind="{ job_list }">
      </router-view>
    </transition>

    <div v-else class="row flex-center">
      <div class="column col-auto items-center">
        <p>{{ $capitalize($t('loading_text')) }}</p>
        <q-circular-progress
          indeterminate 
          size="40px"
          color="theme-blue"
          class="q-mt-md">
        </q-circular-progress>
      </div>
    </div>

  </div>
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

    unassigned_jobs() {
      return this.vuex_ready
        ? this.$store.state.job.unassigned_job_list
        : []
    },

    job_list() {
      const assigned_jobs = this.user_jobs 
        ? this.user_jobs.map( j => {
            return { assigned: true, ...j }
          })
        : []

      const unassigned_jobs = this.unassigned_jobs 
        ? this.unassigned_jobs.map( j => {
            return { assigned: false, ...j }
          })
        : []

      let list = [...assigned_jobs, ...unassigned_jobs]
      return list
    },
  },

  created() {
    const user_key = this.$store.state.session.user._key
    this.$store.dispatch('loadJobAssignments', user_key)
    .then(() => this.vuex_ready = true)
  }
}
</script>

<style lang="css" scoped>
</style>
