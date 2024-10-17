<template>
  <div class="fit">
    <FilterDrawer
      v-model="show_filters"
      :active-filters="filters_active"
      :hideable="false"
      @reset="resetFilters"
    >
      <div class="column full-height q-col-gutter-md">
        <div class="col-auto">
          <q-select
            v-model="wo_filter"
            :label="$t('work_order.short').toUpperCase()"
            filled
            use-input
            dense
            clearable
            :options="work_orders"
          />
        </div>
        <div class="col-auto">
          <q-select
            v-model="product_filter"
            :label="$capitalize($t('product.label'))"
            filled
            use-input
            dense
            clearable
            :options="products"
          />
        </div>
        <div class="col-auto">
          <q-select
            v-model="phase_filter"
            :label="$t('phase.short')"
            filled
            use-input
            dense
            clearable
            :options="phases"
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
        <div
          color="text-low"
          class="row justify-between items-center col-auto absolute-bottom q-pb-md q-px-lg"
        >
          <span class="text-h5 text-low uppercase"> visualizzazione </span>
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
      wo_filter: undefined,
      product_filter: undefined,
      phase_filter: undefined,
      show_filters: false,
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
      return (
        this.wo_filter ||
        this.product_filter ||
        this.phase_filter ||
        this.started_only
      );
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
  },

  methods: {
    match(job) {
      return (
        (this.wo_filter ? job.wo_code === this.wo_filter : true) &&
        (this.phase_filter ? job.phase_alias === this.phase_filter : true) &&
        (this.product_filter
          ? job.product_code === this.product_filter
          : true) &&
        (this.started_only ? job.stage != 'created' : true)
      );
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
  },
};
</script>
