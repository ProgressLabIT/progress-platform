<template>
  <q-page class="row flex-center">
    <div class="column col-12 col-sm-8 col-md-6 col-xl-4 justify-center">
      <div class="text-body1 text-high q-mb-lg text-center">
        {{ $capitalize(greeting) }}. {{ $capitalize(message) }}.
      </div>

      <JobCard v-if="selected_job" :job="selected_job"></JobCard>

      <div class="row q-mt-lg justify-between" v-if="selected_job">
        <q-btn
          size="md"
          color="theme-grey"
          @click="goToJobList">
          {{ $t('show_all') }}
        </q-btn>
        <q-btn
          size="md"
          color="theme-blue"
          @click="goToJob">
          {{ $t('select') }}
        </q-btn>
      </div>
    </div>
  </q-page>
</template>

<script>
import JobCard from '@/components/JobCard.vue'

export default {

  name: 'UserJobsSelected',

  components: { JobCard },

  props: {
    job_list: {
      type: Array,
      required: true
    }
  },

  computed: {
    greeting() {
      const today = new Date()
      const current_hour = today.getHours()

      if (current_hour < 12) {
        return this.$t('greeting.morning')
      }
      else if (current_hour < 18) {
        return this.$t('greeting.afternoon')
      }
      else {
        return this.$t('greeting.evening')
      }
    },

    job_query_param() {
      return this.$route.query.job
    },

    message() {
      if (this.selected_job === null) {
        return this.$t('job.empty_queue')
      }

      else return this.job_query_param == 'first'
        ? this.$t('job.next_job_message')
        : this.$t('job.selected_job_message')
    },

    selected_job() {
      let job = null

      if (this.job_list.length) {
        job = this.job_query_param === 'first'
          ? this.job_list[0]
          : this.job_list.filter(j => j._key === this.job_query_param)[0]
      }

      return job
    }


  },

  methods: {
    goToJob() {
      this.$router.push({
        name: "workSession",
        params: {
          job_key: this.selected_job._key
        }
      })
    },

    goToJobList() {
      this.$router.push({ name: "userJobsAll"})
    }
  },

  created() {
    if (!this.job_query_param) {
      this.$router.replace({ query: 'first' })
    }
  }
 
}
</script>

<style lang="css" scoped>
</style>
