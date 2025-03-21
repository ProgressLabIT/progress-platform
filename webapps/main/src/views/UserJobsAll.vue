<template>
  <div class="fit">
    <div class="row justify-end q-pr-xl">
      <!-- FILTER BUTTON -->
      <q-btn
        v-if="!show_options"
        class="q-ml-sm"
        size="sm"
        color="theme-blue"
        @click="show_options = true"
      >
        MOSTRA OPZIONI
      </q-btn>
    </div>
    <FilterDrawer
      v-model="show_options"
      :active-filters="filters_active"
      @reset="resetFilters"
    >
      <template #default>
        <div class="column full-height q-col-gutter-md">
          <div class="col-auto">
            <q-select
              :label="$capitalize($t('project'))"
              filled
              use-input
              dense
              clearable
              :options="project_options"
              :model-value="project_filter"
              @filter="filterProjects"
              @update:model-value="(value) => (project_filter = value)"
            />
          </div>
          <div class="col-auto">
            <q-select
              :label="$t('work_order.short').toUpperCase()"
              filled
              use-input
              dense
              clearable
              :options="wo_options"
              :model-value="wo_filter"
              @filter="filterWos"
              @update:model-value="(value) => (wo_filter = value)"
            />
          </div>
          <div class="col-auto">
            <q-select
              :label="$capitalize($t('product.label'))"
              filled
              use-input
              dense
              clearable
              :options="product_options"
              :model-value="product_filter"
              @filter="filterProducts"
              @update:model-value="(value) => (product_filter = value)"
            />
          </div>
          <div class="col-auto">
            <q-select
              :label="$t('phase.short')"
              filled
              use-input
              dense
              clearable
              :options="phase_options"
              :model-value="phase_filter"
              @filter="filterPhases"
              @update:model-value="(value) => (phase_filter = value)"
            />
          </div>

          <div class="col-auto">
            <q-checkbox
              v-model="started_only"
              :label="$capitalize($t('job.filters.started_only'))"
              hide-bottom-space
              no-ripple
              class="q-ma-none q-pa-none nowrap text-low col-auto"
            />
          </div>

          <div class="row justify-between items-center q-pb-md">
            <span class="text-h5 uppercase"> visualizzazione </span>
            <q-btn-toggle
              v-model="layout"
              :options="[
                { value: 'card', icon: 'mdi-view-grid' },
                { value: 'list', icon: 'mdi-view-agenda' },
              ]"
              color="theme-grey"
              toggle-color="text-high"
              flat
              size="md"
              padding="sm sm"
              class="q-ma-none q-pa-none"
            />
          </div>
        </div>
      </template>
    </FilterDrawer>

    <q-page class="q-px-lg fit scroll">
      <div class="row items-center q-col-gutter-md q-mb-lg">
        <!-- Text field for product filter and search -->
        <div class="col-3 col-md-2"></div>
        <div class="col-3 col-md-2"></div>
        <div class="col-3 col-md-2"></div>
        <!-- View controls -->
        <div class="row col items-center justify-between"></div>
      </div>

      <!-- JOBS -->
      <div v-for="(details, type) in jobs_view" :key="type">
        <!-- LIST HEADER -->
        <div class="row items-center q-mb-md q-mt-lg">
          <!-- LIST TITLE -->
          <span class="text-body1">{{ details.label }}</span>

          <q-separator class="q-mx-md" style="flex-grow: 1" />

          <!-- SHOWN VS TOTAL -->
          <q-chip dense color="transparent" class="smaller">
            <i18n-t keypath="job.shown_jobs_message" tag="span">
              <template #shown>
                <span class="highlight q-mr-xs">
                  {{ details.list.length }}
                </span>
              </template>
              <template #total>
                <span class="highlight q-mx-xs">
                  {{ details.total_count }}
                </span>
              </template>
            </i18n-t>
          </q-chip>
        </div>

        <!-- JOB LIST -->
        <div class="row q-col-gutter-lg">
          <!-- CARDS LAYOUT (DEFAULT) -->
          <template v-if="layout !== 'list'">
            <div
              v-for="j in details.list"
              :key="j._key"
              class="column col-12 col-sm-6 col-md-4 col-xl-2"
              @click="goToSelectedJob(j._key)"
            >
              <JobCard :job="j" class="pointer"> </JobCard>
            </div>
          </template>

          <!-- LIST LAYOUT -->
          <template v-if="layout === 'list'">
            <div
              v-for="j in details.list"
              :key="j._key"
              class="col-12 items-center q-my-sm"
            >
              <JobCardSlim :job="j" @click="goToSelectedJob(j._key)" />
            </div>
          </template>
        </div>
      </div>
    </q-page>
  </div>
</template>

<script>
import { storeToRefs } from 'pinia';
import FilterDrawer from '@/components/FilterDrawer.vue';
import JobCard from '@/components/JobCard.vue';
import JobCardSlim from '@/components/JobCardSlim.vue';
import { useConfigStore } from '../stores/config';

export default {
  name: 'UserJobsAll',

  components: { FilterDrawer, JobCard, JobCardSlim },

  props: {
    jobList: {
      type: Array,
      required: true,
    },
  },

  setup() {
    const configStore = useConfigStore();
    const { config } = storeToRefs(configStore);
    return {
      config,
    };
  },

  data() {
    return {
      search_string: '',
      started_only: false,
      product_filter: undefined,
      phase_filter: undefined,
      wo_filter: undefined,
      project_filter: undefined,
      wo_options: [],
      phase_options: [],
      product_options: [],
      project_options: [],
      show_options: false,
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
      return this.jobList.filter((j) => j.assigned);
    },

    unassigned() {
      return this.jobList.filter((j) => !j.assigned);
    },

    filtered_assigned_to_user() {
      return this.assigned_to_user.filter((j) => this.match(j));
    },

    filtered_unassigned() {
      return this.unassigned.filter((j) => this.match(j));
    },

    jobs_view() {
      const assigned = {
        list: this.filtered_assigned_to_user,
        total_count: this.assigned_to_user.length,
        label: this.$capitalize(this.$t('job.assigned_to_me')),
      };

      if (!this.config.allowUnassignedJobs) {
        return { assigned };
      }

      return {
        assigned,
        unassigned: {
          list: this.filtered_unassigned,
          total_count: this.unassigned.length,
          label: this.$capitalize(this.$t('unassigned')),
        },
      };
    },

    projects() {
      return [...new Set(this.jobList.map((j) => j.project_code).filter((p) => !!p))];
    },

    products() {
      return [...new Set(this.jobList.map((j) => j.product_code))];
    },

    phases() {
      return [...new Set(this.jobList.map((j) => j.phase_alias))];
    },

    work_orders() {
      return [...new Set(this.jobList.map((j) => j.wo_code))];
    },

    filters_active() {
      return [
        this.wo_filter,
        this.product_filter,
        this.phase_filter,
        this.started_only,
      ].filter((v) => !!v).length;
    },

    layout: {
      get() {
        const user = this.$store.state.session.user;
        return user.preferences.job_selection_layout || 'card';
      },
      set(layout) {
        this.$store.dispatch('updatePreferences', {
          job_selection_layout: layout,
        });
      },
    },
  },

  created() {
    // Migrate from local storage to DB
    const legacyLayout = localStorage.getItem('LAYOUT');
    if (legacyLayout) {
      this.layout = legacyLayout;
      localStorage.removeItem('LAYOUT');
    }

    // Init filter options
    this.initFilterOptions();
  },

  methods: {
    match(job) {
      return (
        (this.project_filter ? job.project_code === this.project_filter : true) &&
        (this.wo_filter ? job.wo_code === this.wo_filter : true) &&
        (this.phase_filter ? job.phase_alias === this.phase_filter : true) &&
        (this.product_filter
          ? job.product_code === this.product_filter
          : true) &&
        (this.started_only ? job.stage != 'created' : true)
      );
    },

    initFilterOptions() {
      this.wo_options = this.work_orders;
      this.phase_options = this.phases;
      this.product_options = this.products;
      this.project_options = this.projects;
    },

    goToSelectedJob(job_key) {
      const selected_job_route = {
        name: 'userJobsSelected',
        query: { job: job_key },
      };
      this.$router.push(selected_job_route);
    },

    resetFilters() {
      this.wo_filter = undefined;
      this.phase_filter = undefined;
      this.product_filter = undefined;
      this.started_only = false;
    },

    filterProjects(value, update) {
      update(() => {
        this.project_options = this.projects.filter((p) =>
          p.toUpperCase().includes(value.toUpperCase()),
        );
      });
    },

    filterWos(value, update) {
      update(() => {
        this.wo_options = this.work_orders.filter((wo) =>
          wo.toUpperCase().includes(value.toUpperCase()),
        );
      });
    },

    filterProducts(value, update) {
      update(() => {
        this.product_options = this.products.filter((p) =>
          p.toUpperCase().includes(value.toUpperCase()),
        );
      });
    },

    filterPhases(value, update) {
      update(() => {
        this.phase_options = this.phases.filter((phase) =>
          phase.toUpperCase().includes(value.toUpperCase()),
        );
      });
    },
  },
};
</script>
