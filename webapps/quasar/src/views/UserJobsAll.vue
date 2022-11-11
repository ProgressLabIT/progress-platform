<template>
  <!-- Search and options bar -->
  <q-page class="q-pa-lg">

  <div class="row items-center q-gutter-md q-mb-lg">

    <!-- Text field for product filter and search -->
    <div class="column col-12 col-sm-5 col-lg-3">
      <q-input
        clearable
        clear-icon="mdi-close"
        autocomplete="off"
        name="search"
        :label="$capitalize($t('search'))"
        value="search"
        v-model="search_string"
        class="q-ma-none q-pa-none text-uppercase">
        <template v-slot:append>
          <q-icon name="mdi-magnify" />
        </template>
      </q-input>
    </div>

    <!-- View controls -->
    <div class="column col-auto items-center">
      <q-checkbox
        :label="$capitalize($t('job.filters.started_only'))"
        v-model="started_only"
        hide-bottom-space
        no-ripple
        class="q-ma-none q-pa-none nowrap text-low"/>
    </div>
  </div>


  <!-- ASSIGNED JOBS -->
    <div class="row items-center q-mb-md">

      <span class="text-body1">
        {{ $capitalize($t('job.assigned_to_me')) }}
      </span>

      <q-separator class="q-mx-md" style="flex-grow: 1"/>

      <!-- Assigned jobs shown vs total -->
      <q-chip dense color="transparent" class="smaller">
        <i18n-t keypath="job.shown_jobs_message" tag="span">
          <template v-slot:shown>
            <span class="highlight q-mr-xs">
              {{ filtered_assigned_to_user.length }}
            </span>
          </template>
          <template v-slot:total>
            <span class="highlight q-mx-xs">
              {{ assigned_to_user.length }}
            </span>
          </template>
        </i18n-t>
      </q-chip>

    </div>

    <div class="row q-col-gutter-lg">
      <div class="column col-12 col-sm-6 col-md-4 col-lg-3"
        v-for="j in filtered_assigned_to_user"
        :key="j._key"
        @click="goToSelectedJob(j._key)">
        <JobCard
          :job="j"
          class="pointer"
          v-ripple>
        </JobCard>
      </div>
    </div>

    <!-- UNASSIGNED JOBS -->
    <div class="row q-mt-md items-center">

      <div class="text-body1 q-my-md">
        {{ $capitalize($t('unassigned')) }}
      </div>

      <q-separator class="q-mx-md" style="flex-grow: 1;" />

      <!-- Jobs shown vs total -->
      <q-chip small color="transparent" class="smaller">
        <i18n-t keypath="job.shown_jobs_message" tag="span">
          <template v-slot:shown>
            <span class="highlight q-mr-xs">
              {{ filtered_unassigned.length }}
            </span>
          </template>
          <template v-slot:total>
            <span class="highlight q-mx-xs">
              {{ unassigned.length }}
            </span>
          </template>
        </i18n-t>
      </q-chip>

    </div>

    <div class="row q-col-gutter-lg">
      <div class="column col-12 col-sm-6 col-md-4 col-lg-3"
        v-for="j in filtered_unassigned"
        :key="j._key"
        @click="goToSelectedJob(j._key)">
        <JobCard
          :job="j"
          class="pointer"
          v-ripple>
        </JobCard>
      </div>
    </div>
    </q-page>
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
      const fields_to_search = ['wo_code', 'product_code', 'product_description', 'phase_alias']
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
