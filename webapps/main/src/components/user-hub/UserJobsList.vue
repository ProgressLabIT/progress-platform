<template>
  <div class="fit column no-wrap q-px-md">
    <LoadingSignal v-if="hub.loadingJobs" />
    <JobsEmpty v-else-if="!hub.loadingJobs && totalJobs === 0 && !hasActiveFilters" />
    <JobsNoMatch v-else-if="!hub.loadingJobs && totalFiltered === 0 && hasActiveFilters" @clear="$emit('reset-filters')" />

    <q-scroll-area v-else class="col">
      <!-- Card layout -->
      <div class="text-low text-uppercase text-h6 q-mt-md q-mb-sm">{{ $capitalize($t('job.assigned_to_me')) }}</div>

      <template v-if="layout !== 'list'">
        <div class="row q-col-gutter-lg">
          <div
            v-for="j in showAssignedSplit ? cappedAssigned : cappedJobs"
            :key="j._key"
            class="column col-12 col-sm-6 col-md-4 col-xl-2"
            @click="goToJob(j._key)"
          >
            <JobCard :job="j" class="pointer" />
          </div>
        </div>
      </template>
      <template v-else>
        <JobCardSlim
          v-for="item in (showAssignedSplit ? cappedAssigned : cappedJobs)"
          :key="item._key"
          :job="item"
          class="q-mb-md"
          @click="goToJob(item._key)"
        />
      </template>

      <template v-if="showUnassigned">
        <div class="text-low text-uppercase text-h6 q-mt-lg q-mb-sm">
          {{ $capitalize($t('unassigned')) }}
        </div>
        <template v-if="layout !== 'list'">
          <div class="row q-col-gutter-lg">
            <div
              v-for="j in cappedUnassigned"
              :key="j._key"
              class="column col-12 col-sm-6 col-md-4 col-xl-2"
              @click="goToJob(j._key)"
            >
              <JobCard :job="j" class="pointer" />
            </div>
          </div>
        </template>
        <template v-else>
          <JobCardSlim
            v-for="item in cappedUnassigned"
            :key="item._key"
            :job="item"
            class="q-mb-md"
            @click="goToJob(item._key)"
          />
        </template>
      </template>

      <div
        v-if="truncated"
        class="text-caption text-low text-center q-my-md"
      >
        {{ $t('user_hub.jobs_truncated_note', { count: MAX_JOBS }) }}
      </div>
    </q-scroll-area>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { storeToRefs } from 'pinia';
import { useStore as useVuex } from 'vuex';
import LoadingSignal from '@/components/LoadingSignal.vue';

import JobCard from '@/components/JobCard.vue';
import JobCardSlim from '@/components/JobCardSlim.vue';
import JobsEmpty from '@/components/user-hub/JobsEmpty.vue';
import JobsNoMatch from '@/components/user-hub/JobsNoMatch.vue';
import { useSSE } from '@/composables/useSSE';
import { useConfigStore } from '@/stores/config';
import { useUserHubStore } from '@/stores/userHub';

const props = defineProps({
  filters: {
    type: Object,
    default: () => ({ project: null, wo: null, product: null, phase: null, startedOnly: false }),
  }
});

defineEmits(['reset-filters']);

const vuex = useVuex();
const hub = useUserHubStore();
const { config } = storeToRefs(useConfigStore());
const router = useRouter();

const layout = computed(() => vuex.state.session.user?.preferences?.job_selection_layout || 'list');
const scopes = computed(() => vuex.state.session.scope?.split(' ') ?? []);
const isOperator = computed(() => scopes.value.includes('operator'));
const showAssignedSplit = computed(() => isOperator.value);
const showUnassigned = computed(() => config.value?.allowUnassignedJobs === true);

const assignedJobs = computed(() => hub.jobs.assigned);
const unassignedJobs = computed(() => hub.jobs.unassigned);
const allJobs = computed(() => [...assignedJobs.value, ...unassignedJobs.value]);
const totalJobs = computed(() => allJobs.value.length);

const hasActiveFilters = computed(
  () => !!(props.filters.project || props.filters.wo || props.filters.product || props.filters.phase || props.filters.startedOnly),
);

function match(j) {
  if (props.filters.project && j.project_code !== props.filters.project) return false;
  if (props.filters.wo && j.wo_code !== props.filters.wo) return false;
  if (props.filters.product && j.product_code !== props.filters.product) return false;
  if (props.filters.phase && j.phase_alias !== props.filters.phase) return false;
  if (!(j.next_batch_available || j.active_batch_qt)) return false;
  if (props.filters.startedOnly && j.stage === 'created') return false;
  return true;
}

const filteredAssigned = computed(() => assignedJobs.value.filter(match));
const filteredUnassigned = computed(() => unassignedJobs.value.filter(match));
const filteredJobs = computed(() => allJobs.value.filter(match));

const MAX_JOBS = 50;

const cappedAssigned = computed(() => filteredAssigned.value.slice(0, MAX_JOBS));
const cappedUnassigned = computed(() => filteredUnassigned.value.slice(0, MAX_JOBS));
const cappedJobs = computed(() => filteredJobs.value.slice(0, MAX_JOBS));

const totalFiltered = computed(() =>
  showAssignedSplit.value
    ? filteredAssigned.value.length + filteredUnassigned.value.length
    : filteredJobs.value.length,
);

const truncated = computed(() => {
  if (showAssignedSplit.value) {
    if (filteredAssigned.value.length > MAX_JOBS) return true;
    if (showUnassigned.value && filteredUnassigned.value.length > MAX_JOBS) return true;
    return false;
  }
  return filteredJobs.value.length > MAX_JOBS;
});

function goToJob(jobKey) {
  router.push({ name: 'workSession', params: { jobKey } });
}

const loading = computed(() => hub.loadingJobs);

async function refresh() {
  const userKey = vuex.state.session.user?._key;
  if (!userKey) return;
  await hub.refreshJobs(userKey);
}

const { subscribe: subscribeSSE } = useSSE('production');

function handleProductionEvent(message) {
  let event;
  try {
    event = JSON.parse(message.data);
  } catch {
    return;
  }
  const type = event.event_type || event.notification;
  const userKey = vuex.state.session.user?._key;
  if (!userKey) return;

  if (type === 'QUEUE_UPDATED') {
    refresh();
    return;
  }
  if (event.job_data) {
    hub.applyJobUpdate(event.job_data, userKey);
  }
}

onMounted(() => {
  const legacyLayout = typeof localStorage !== 'undefined' && localStorage.getItem('LAYOUT');
  if (legacyLayout) {
    layout.value = legacyLayout;
    localStorage.removeItem('LAYOUT');
  }
  refresh();
  subscribeSSE(handleProductionEvent);
});

defineExpose({ loading, refresh });
</script>
