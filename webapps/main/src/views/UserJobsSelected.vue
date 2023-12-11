<template>
  <q-page class="row flex-center">
    <div
      class="column col-12 col-sm-8 col-md-6 col-xl-4 justify-center q-px-xl"
    >
      <div class="text-body1 text-high q-mb-lg text-center">
        {{ $capitalize(greeting) }}. {{ $capitalize(message) }}.
      </div>

      <JobCard v-if="selected_job" :job="selected_job"></JobCard>

      <div v-if="selected_job" class="row q-mt-lg justify-between">
        <q-btn size="md" color="theme-grey" @click="goToJobList">
          {{ $t('show_all') }}
        </q-btn>
        <q-btn
          size="md"
          :color="selected_job.critical ? 'theme-red' : 'theme-blue'"
          @click="goToJob"
        >
          {{ $t('select') }}
        </q-btn>
      </div>
    </div>
  </q-page>
</template>

<script>
import JobCard from '@/components/JobCard.vue';

export default {
  name: 'UserJobsSelected',

  components: { JobCard },

  props: {
    jobList: {
      type: Array,
      required: true,
    },
  },

  computed: {
    greeting() {
      const today = new Date();
      const current_hour = today.getHours();

      if (current_hour < 12) {
        return this.$t('greeting.morning');
      } else if (current_hour < 18) {
        return this.$t('greeting.afternoon');
      } else {
        return this.$t('greeting.evening');
      }
    },

    job_query_param() {
      return this.$route.query.job;
    },

    message() {
      if (this.selected_job === null) {
        return this.$t('job.empty_queue');
      } else
        return this.job_query_param == 'first'
          ? this.$t('job.next_job_message')
          : this.$t('job.selected_job_message');
    },

    selected_job() {
      let job = null;
      if (this.jobList.length > 0) {
        job =
          this.job_query_param === 'first'
            ? this.jobList[0]
            : this.jobList.find((j) => j._key === this.job_query_param);
      }
      return job;
    },
  },

  created() {
    if (!this.job_query_param) {
      this.$router.replace({ query: 'first' });
    }
  },

  methods: {
    goToJob() {
      this.$router.push({
        name: 'workSession',
        params: {
          jobKey: this.selected_job._key,
        },
      });
    },

    goToJobList() {
      this.$router.push({ name: 'userJobsAll' });
    },
  },
};
</script>

<style lang="css" scoped></style>
