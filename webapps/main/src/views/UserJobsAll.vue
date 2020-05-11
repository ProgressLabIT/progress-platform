<template>
  <v-container fluid class="py-0">
   <v-row>

      <!-- Text field for product filter and search -->
      <v-col cols="12" sm="5" lg="3">
        <v-text-field
          hide-details
          single-line
          autocomplete="off"
          name="search"
          label="Filtra/Cerca lavori"
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
          label="Solo iniziati" 
          v-model="started_only" 
          class="ma-0 pa-0 nowrap"/>
      </v-col>    
      </v-row> 

    <v-row >
    
    <v-col cols="12" sm="6" md="4" lg="3" 
      v-for="j in job_list" 
      :key="j._id"
      @click="goToSelectedJob(j._key)"
      v-show="(!started_only || j.stage==='started') && match(j)">
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
      started_only: false
    }
  },

  methods: {
    match(job) {
      const fields_to_search = ['wo_code', 'product_code', 'product_description']
      return multiMatch(this.search_string, job, fields_to_search)
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