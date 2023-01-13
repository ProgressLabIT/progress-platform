<template>
  <v-container fluid class="py-0">
   <v-row align="center">

      <!-- Text field for product filter and search -->
      <v-col cols="12" sm="5" lg="3">
        <v-text-field
          hide-details
          single-line
          autocomplete="off"
          name="search"
          :label="$tc('search') | capitalize"
          value="search"
          v-model="search_string"
          class="ma-0 pa-0 text-uppercase">
          <template v-slot:append>
            <span class="material-icons">search</span>
          </template>
        </v-text-field>
      </v-col>

      <!-- View controls -->
      <v-col cols="auto" class="d-flex align-center">
        <v-checkbox
          :ripple="false"
          color="primary" 
          hide-details
          :label="$tc('job.filters.started_only') | capitalize"
          v-model="started_only" 
          class="ma-0 pa-0 nowrap"/>
      </v-col>    
    </v-row> 


    <!-- ASSIGNED JOBS -->
    <v-row class="mx-0 mt-4" align="center">
      
      <span>
        {{ $tc('job.assigned_to_me') | capitalize }}
      </span>

      <v-divider class="mx-3"></v-divider>
      
      <!-- Assigned jobs shown vs total -->
      <v-chip small color="transparent">
        <i18n path="job.shown_jobs_message">
          <template v-slot:shown>
            <span class="highlight mr-1">
              {{ filtered_assigned_to_user.length }}
            </span>
          </template>
          <template v-slot:total>
            <span class="highlight mx-1">
              {{ assigned_to_user.length }}
            </span>
          </template>
        </i18n>
      </v-chip>

    </v-row>

    <v-row >
      <v-col cols="12" sm="6" md="4" lg="3" 
        v-for="j in filtered_assigned_to_user" 
        :key="j._key"
        @click="goToSelectedJob(j._key)">
        <v-hover v-slot:default="{ hover }">
          <JobCard
            :background="hover ? $theme.surface2 : $theme.surface1"
            :job="j"
            class="pointer"
            v-ripple>
          </JobCard>
        </v-hover>
      </v-col>
    </v-row>

    <!-- UNASSIGNED JOBS -->
    <v-row class="mx-0 mt-12" align="center">

      <div>
        {{ $tc('unassigned') | capitalize }}
      </div>
      
      <v-divider class="mx-3"></v-divider>

      <!-- Jobs shown vs total -->
      <v-chip small color="transparent">
        <i18n path="job.shown_jobs_message">
          <template v-slot:shown>
            <span class="highlight mr-1">
              {{ filtered_unassigned.length }}
            </span>
          </template>
          <template v-slot:total>
            <span class="highlight mx-1">
              {{ unassigned.length }}
            </span>
          </template>
        </i18n>
      </v-chip>

    </v-row>

    <v-row >
      <v-col cols="12" sm="6" md="4" lg="3" 
        v-for="j in filtered_unassigned" 
        :key="j._key"
        @click="goToSelectedJob(j._key)">
        <v-hover v-slot:default="{ hover }">
          <JobCard
            :background="hover ? $theme.surface2 : $theme.surface1"
            :job="j"
            class="pointer"
            v-ripple>
          </JobCard>
        </v-hover>
      </v-col>
    </v-row>

  </v-container>
</template>

<script>
import JobCard from '@/components/JobCard.vue'
import multiMatch from '@/lib/MultiFieldSearch.js'


export default {

  name: 'UserJobsAll',

  components: { JobCard },

  props: {
    job_list: {
      type: Array,
      required: true
    }
  },

  data() {
    return {
      search_string: '',
      started_only: false,
    }
  },

  computed: {
    assigned_to_user() {
      return this.job_list.filter( j => j.assigned )
    },

    unassigned() {
      return this.job_list.filter( j => !j.assigned )
    },

    filtered_assigned_to_user() {
      return this.assigned_to_user.filter( j => this.match(j) )
    },

    filtered_unassigned() {
      return this.unassigned.filter( j => this.match(j) )
    }
  },

  methods: {
    match(job) {
      const fields_to_search = ['wo_code', 'product_code', 'product_description', 'phase_alias', 'project_code']
      return (
        multiMatch(this.search_string, job, fields_to_search) 
        && (!this.started_only || job.stage==='started') 
      )
    },

    goToSelectedJob(job_key) {
      const selected_job_route = {
        name: 'userJobsSelected',
        query: { job: job_key }
      }
      this.$router.push(selected_job_route)
    }
  }
}
</script>

<style lang="css" scoped>
</style>
