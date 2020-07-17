<template>
  <v-row 
      class="fill-heigth" 
      align="center" 
      justify="center">
      <v-col cols="12" sm="8" md="6" xl="4">      
        <div class="mt-12 mb-8 text-center">
          {{ greeting }}. {{ message }}.
        </div>

        <JobCard :job="selected_job"></JobCard>

        <v-row class="mt-10 mx-0" justify="space-between">
          <v-btn 
            large
            :color="$theme.grey"
            @click="goToJobList">
            VEDI TUTTI
          </v-btn>
          <v-btn 
            large
            :color="$theme.blue"
            @click="goToJob">
            SELEZIONA
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
        return 'Buongiorno'
      }
      else if (current_hour < 18) {
        return 'Buon pomeriggio'
      }
      else {
        return 'Buonasera'
      }
    },

    job_query_param() {
      return this.$route.query.job
    },

    message() {
      return this.job_query_param == 'first'
        ? "Il prossimo lavoro in coda è il seguente"
        : "Il lavoro selezionato è il seguente"
    },

    selected_job() {
      return this.job_query_param === 'first'
        ? this.job_list[0]
        : this.job_list.filter(j => j._key === this.job_query_param)[0]
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