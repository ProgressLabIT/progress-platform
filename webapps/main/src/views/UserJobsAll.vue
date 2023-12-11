<template>
  <!-- Search and options bar -->
  <q-page class="q-pa-lg">
    <div class="row items-center q-gutter-md q-mb-lg">
      <!-- Text field for product filter and search -->
      <div class="column col-12 col-sm-5 col-lg-3">
        <q-input
          filled
          dense
          clearable
          clear-icon="mdi-close"
          autocomplete="off"
          name="search"
          :label="$capitalize($t('search'))"
          value="search"
          v-model="search_string"
          class="q-ma-none q-pa-none text-uppercase"
        >
          <template v-slot:append>
            <q-icon name="mdi-magnify" />
          </template>
        </q-input>
      </div>

      <!-- View controls -->
      <div class="row col items-center justify-between">
        <q-checkbox
          :label="$capitalize($t('job.filters.started_only'))"
          v-model="started_only"
          hide-bottom-space
          no-ripple
          class="q-ma-none q-pa-none nowrap text-low col-auto"
        />
        <div color="text-low" class="col-auto">
          <q-btn
            flat
            icon="mdi-view-grid"
            :color="layout != 'list' ? 'text-high' : 'theme-grey'"
            @click="setLayout('card')"
            size="md"
            padding="sm sm"
          />
          <q-btn
            flat
            icon="mdi-view-agenda"
            :color="layout == 'list' ? 'text-high' : 'theme-grey'"
            @click="setLayout('list')"
            size="md"
            padding="sm sm"
          />
        </div>
      </div>
    </div>

    <!-- JOBS -->

    <div v-for="[k, v] in Object.entries(jobs_view)">
      <!-- LIST HEADER -->
      <div class="row items-center q-mb-md q-mt-lg">
        <!-- LIST TITLE -->
        <span class="text-body1">{{ v.label }}</span>

        <q-separator class="q-mx-md" style="flex-grow: 1" />

        <!-- SHOWN VS TOTAL -->
        <q-chip dense color="transparent" class="smaller">
          <i18n-t keypath="job.shown_jobs_message" tag="span">
            <template v-slot:shown>
              <span class="highlight q-mr-xs">
                {{ v.list.length }}
              </span>
            </template>
            <template v-slot:total>
              <span class="highlight q-mx-xs">
                {{ v.total_count }}
              </span>
            </template>
          </i18n-t>
        </q-chip>
      </div>

      <!-- JOB LIST -->
      <div class="row q-col-gutter-lg">
        <!-- CARDS LAYOUT (DEFAULT) -->
        <template v-if="layout != 'list'">
          <div
            class="column col-12 col-sm-6 col-md-4 col-lg-3"
            v-for="j in v.list"
            :key="j._key"
            @click="goToSelectedJob(j._key)"
          >
            <JobCard :job="j" class="pointer"> </JobCard>
          </div>
        </template>

        <!-- LIST LAYOUT -->
        <template v-if="layout === 'list'">
          <div
            class="col-12 items-center q-my-sm"
            v-for="j in v.list"
            :key="j._key"
          >
            <JobCardSlim :job="j" @click="goToSelectedJob(j._key)" />
          </div>
        </template>
      </div>
    </div>
  </q-page>
</template>

<script>
import JobCard from '@/components/JobCard.vue';
import JobCardSlim from '@/components/JobCardSlim.vue';
import multiMatch from '@/lib/MultiFieldSearch.js';

export default {
  name: 'UserJobsAll',

  components: { JobCard, JobCardSlim },

  props: {
    job_list: {
      type: Array,
      required: true,
    },
  },

  data() {
    return {
      search_string: '',
      started_only: false,
      layout: 'card',
    };
  },

  computed: {
    layout_options() {
      return [
        { value: 'card', slot: 'card' },
        { value: 'row', slot: 'row' },
      ];
    },

    assigned_to_user() {
      return this.job_list.filter((j) => j.assigned);
    },

    unassigned() {
      return this.job_list.filter((j) => !j.assigned);
    },

    filtered_assigned_to_user() {
      return this.assigned_to_user.filter((j) => this.match(j));
    },

    filtered_unassigned() {
      return this.unassigned.filter((j) => this.match(j));
    },

    jobs_view() {
      return {
        assigned: {
          list: this.filtered_assigned_to_user,
          total_count: this.assigned_to_user.length,
          label: this.$capitalize(this.$t('job.assigned_to_me')),
        },
        unassigned: {
          list: this.filtered_unassigned,
          total_count: this.unassigned.length,
          label: this.$capitalize(this.$t('unassigned')),
        },
      };
    },
  },

  methods: {
    setLayout(layout) {
      this.layout = layout;
      localStorage.setItem('LAYOUT', layout);
    },

    match(job) {
      const fields_to_search = [
        'wo_code',
        'product_code',
        'product_description',
        'project_code',
        'phase_alias',
      ];
      return (
        multiMatch(this.search_string, job, fields_to_search) &&
        (!this.started_only || job.stage === 'started')
      );
    },

    goToSelectedJob(job_key) {
      const selected_job_route = {
        name: 'userJobsSelected',
        query: { job: job_key },
      };
      this.$router.push(selected_job_route);
    },
  },

  created() {
    this.layout = localStorage.getItem('LAYOUT');
  },
};
</script>

<style lang="css" scoped></style>
