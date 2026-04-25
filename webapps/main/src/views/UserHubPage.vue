<template>
  <q-page-container class="absolute-full">
    <q-page class="row full-height">
      <div class="column col full-height">
        <div class="row col-auto items-center justify-center q-px-md q-py-sm">
          <q-tabs
            v-model="activeTab"
            class="transparent text-low q-mx-auto"
            active-class="text-high weight-bold"
            align="left"
            shrink
            dense
            indicator-color="theme-blue"
          >
            <q-tab
              v-for="[key, { label, count }] in Object.entries(TABS)"
              :key="key"
              :name="key"
              class="display"
            >
              <div class="row items-center no-wrap q-gutter-x-xs">
                <span>{{ label }}</span>
                <q-chip
                  v-if="count"
                  color="theme-blue"
                  text-color="high"
                  size="9px"
                  class="q-ml-sm"
                  rounded
                >
                  {{ count }}
                </q-chip>
              </div>
            </q-tab>
          </q-tabs>

          <div class="absolute-right q-mr-md q-mt-sm">
           <q-btn-toggle
              v-if="activeTab === 'jobs'"
              v-model="layout"
              :options="[
                { value: 'card', icon: 'mdi-view-grid' },
                { value: 'list', icon: 'mdi-view-agenda' },
              ]"
              color="theme-grey"
              toggle-color="text-high"
              flat
              dense
              class="q-mr-sm"
              :aria-label="$t('user_hub.layout_toggle_aria')"
            />
            <q-btn
              flat
              round
              dense
              data-testid="user-hub-refresh"
              icon="mdi-refresh"
              :loading="loading"
              :aria-label="$t('user_hub.refresh_aria')"
              @click="onRefresh"
            />

            <q-btn
              v-if="activeTab === 'jobs' && !show_options"
              class="q-ml-sm"
              size="sm"
              round
              :color="activeFilterCount ? 'theme-blue' : 'theme-grey'"
              icon="mdi-filter"
              @click="show_options = true"
            >
              <q-badge
                v-if="activeFilterCount"
                floating
                rounded
                color="theme-red"
                :label="activeFilterCount"
                size="4px"
                style="font-family: 'Red Hat Text'; font-size: 8px"
              />
            </q-btn>
          </div>
        </div>

        <div class="col relative-position">
          <q-tab-panels
            v-model="activeTab"
            animated
            keep-alive
            class="bg-transparent absolute-full"
          >
            <q-tab-panel name="jobs" class="q-pa-none scroll">
              <UserJobsList :filters="jobFilters" />
            </q-tab-panel>
            <q-tab-panel name="tasks" class="q-pa-none scroll">
              <UserTasksList ref="tasksRef" />
            </q-tab-panel>
          </q-tab-panels>
        </div>
      </div>
    </q-page>

    <FilterDrawer
      v-if="activeTab === 'jobs'"
      v-model="show_options"
      :active-filters="activeFilterCount"
      @reset="resetFilters"
    >
      <div class="column full-height q-col-gutter-md">
        <div class="col-auto">
          <q-select
            :label="$capitalize($t('project'))"
            filled
            use-input
            dense
            clearable
            :options="project_options"
            v-model="project_filter"
            @filter="filterProjects"
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
            v-model="wo_filter"
            @filter="filterWos"
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
            v-model="product_filter"
            @filter="filterProducts"
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
            v-model="phase_filter"
            @filter="filterPhases"
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
      </div>
    </FilterDrawer>
  </q-page-container>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useStore as useVuex } from 'vuex';
import FilterDrawer from '@/components/FilterDrawer.vue';
import UserJobsList from '@/components/user-hub/UserJobsList.vue';
import UserTasksList from '@/components/user-hub/UserTasksList.vue';
import { useUserHubStore } from '@/stores/userHub';
import { capitalize } from '@/boot/filters';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();

const VALID_TABS = ['jobs', 'tasks'];

const route = useRoute();
const router = useRouter();
const vuex = useVuex();
const hub = useUserHubStore();

const activeTab = computed({
  get: () => (VALID_TABS.includes(route.query.tab) ? route.query.tab : 'jobs'),
  set: (tab) => router.replace({ query: { tab } }),
});

const layout = computed({
  get: () => vuex.state.session.user?.preferences?.job_selection_layout || 'card',
  set: (v) => vuex.dispatch('updatePreferences', { job_selection_layout: v }),
});

// ── Filter state ──────────────────────────────────────────────────────────────
const show_options = ref(false);
const project_filter = ref(null);
const wo_filter = ref(null);
const product_filter = ref(null);
const phase_filter = ref(null);
const started_only = ref(false);

const project_options = ref([]);
const wo_options = ref([]);
const product_options = ref([]);
const phase_options = ref([]);

const allJobs = computed(() => [
  ...(hub.jobs.assigned ?? []),
  ...(hub.jobs.unassigned ?? []),
]);

// Filter dropdowns must reflect what the list actually shows. The list hides
// jobs without an actionable batch (`next_batch_available || active_batch_qt`),
// so options derived from the raw list could surface values whose jobs are all
// hidden — picking one would yield zero results. Source options from the
// actionable subset instead.
const actionableJobs = computed(() =>
  allJobs.value.filter((j) => j.next_batch_available || j.active_batch_qt),
);

const activeFilterCount = computed(
  () => [project_filter.value, wo_filter.value, product_filter.value, phase_filter.value, started_only.value].filter(Boolean).length,
);

const jobFilters = computed(() => ({
  project: project_filter.value,
  wo: wo_filter.value,
  product: product_filter.value,
  phase: phase_filter.value,
  startedOnly: started_only.value,
}));

/** Same rules as UserJobsList `match()` (incl. next_batch_available || active_batch_qt). */
function jobVisibleInHubList(j, filters) {
  if (filters.project && j.project_code !== filters.project) return false;
  if (filters.wo && j.wo_code !== filters.wo) return false;
  if (filters.product && j.product_code !== filters.product) return false;
  if (filters.phase && j.phase_alias !== filters.phase) return false;
  if (!(j.next_batch_available || j.active_batch_qt)) return false;
  if (filters.startedOnly && j.stage === 'created') return false;
  return true;
}

const visibleAssignedCount = computed(() =>
  (hub.jobs.assigned ?? []).filter((j) => jobVisibleInHubList(j, jobFilters.value)).length,
);

const TABS = {
  jobs: {
    label: capitalize(t('user_hub.sub_jobs')),
    count: computed(() => visibleAssignedCount.value),
  },
  tasks: {
    label: capitalize(t('user_hub.sub_tasks')),
    count: computed(() => hub.tasks.length),
  },
};

function resetFilters() {
  project_filter.value = null;
  wo_filter.value = null;
  product_filter.value = null;
  phase_filter.value = null;
  started_only.value = false;
}

function filterProjects(value, update) {
  const projects = [...new Set(actionableJobs.value.map((j) => j.project_code).filter(Boolean))];
  update(() => {
    project_options.value = projects.filter((p) => p.toUpperCase().includes(value.toUpperCase()));
  });
}
function filterWos(value, update) {
  const workOrders = [...new Set(actionableJobs.value.map((j) => j.wo_code).filter(Boolean))];
  update(() => {
    wo_options.value = workOrders.filter((w) => w.toUpperCase().includes(value.toUpperCase()));
  });
}
function filterProducts(value, update) {
  const products = [...new Set(actionableJobs.value.map((j) => j.product_code).filter(Boolean))];
  update(() => {
    product_options.value = products.filter((p) => p.toUpperCase().includes(value.toUpperCase()));
  });
}
function filterPhases(value, update) {
  const phases = [...new Set(actionableJobs.value.map((j) => j.phase_alias).filter(Boolean))];
  update(() => {
    phase_options.value = phases.filter((p) => p.toUpperCase().includes(value.toUpperCase()));
  });
}

// ── Refresh / loading ─────────────────────────────────────────────────────────
const tasksRef = ref(null);

const loading = computed(() => {
  if (activeTab.value === 'jobs') return hub.loadingJobs;
  if (activeTab.value === 'tasks') return tasksRef.value?.loading ?? false;
  return false;
});

async function onRefresh() {
  if (activeTab.value === 'jobs') {
    const userKey = vuex.state.session.user?._key;
    if (userKey) await hub.refreshJobs(userKey);
  } else if (activeTab.value === 'tasks') {
    tasksRef.value?.refresh?.();
  }
}

onMounted(() => {
  const userKey = vuex.state.session.user?._key;
  if (userKey) hub.refreshTasks(userKey);
});
</script>
