<template>
  <v-row 
      class="fill-height" 
      align="center" 
      justify="center">
      <v-col cols="12" sm="8" md="6" xl="4" class="mt-n8">      
        <div class="mb-8 text-center">
          {{ greeting | capitalize }}. {{ message | capitalize }}.
        </div>

        <JobCard v-if="selected_job" :job="selected_job"></JobCard>

        <v-row class="mt-10 mx-0" justify="space-between" v-if="selected_job">
          <v-btn 
            large
            :color="$theme.grey"
            @click="goToJobList">
            {{ $tc('show_all') }}
          </v-btn>
          <v-btn 
            large
            :color="$theme.blue"
            @click="goToJob">
            {{ $tc('select') }}
          </v-btn>
        </v-row>
      </v-col>
    </v-row>
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
        return this.$tc('greeting.morning')
      }
      else if (current_hour < 18) {
        return this.$tc('greeting.afternoon')
      }
      else {
        return this.$tc('greeting.evening')
      }
    },

    job_query_param() {
      return this.$route.query.job
    },

    message() {
      if (this.selected_job === null) {
        return this.$tc('job.empty_queue')
      }

      else return this.job_query_param == 'first'
        ? this.$tc('job.next_job_message')
        : this.$tc('job.selected_job_message')
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
