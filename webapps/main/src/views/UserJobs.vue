<template>
  <q-page-container>
    <template v-if="vuex_ready">
      <router-view :job-list="job_list" />
    </template>

    <div v-else class="row flex-center">
      <div class="column col-auto items-center">
        <p>{{ $capitalize($t('loading_text')) }}</p>
        <q-circular-progress
          indeterminate
          size="40px"
          color="theme-blue"
          class="q-mt-md"
        >
        </q-circular-progress>
      </div>
    </div>
  </q-page-container>
</template>

<script>
export default {
  name: 'UserJobs',

  data() {
    return {
      vuex_ready: false,
    };
  },

  computed: {
    user_jobs() {
      return this.vuex_ready
        ? this.$store.state.job.assigned_job_list[0].assigned_jobs
        : [];
    },

    unassigned_jobs() {
      return this.vuex_ready ? this.$store.state.job.unassigned_job_list : [];
    },

    job_list() {
      const assigned_jobs = this.user_jobs
        ? this.user_jobs.map((j) => {
            return { assigned: true, ...j };
          })
        : [];

      const unassigned_jobs = this.unassigned_jobs
        ? this.unassigned_jobs.map((j) => {
            return { assigned: false, ...j };
          })
        : [];

      let list = [...assigned_jobs, ...unassigned_jobs];
      return list.filter(this.showJob);
    },
  },

  created() {
    const user_key = this.$store.state.session.user._key;
    this.$store
      .dispatch('loadJobAssignments', user_key)
      .then(() => (this.vuex_ready = true));
  },

  methods: {
    showJob(job) {
      const batch_available = job.next_batch_available || job.active_batch_qt;
      const start_from_is_past =
        new Date(job.start_from).getTime() <= new Date().getTime();
      return batch_available && start_from_is_past;
    },
  },
};
</script>
