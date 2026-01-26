<template>
  <BaseDialog :show="true" @close.stop="router.back()">
    <q-card class="surface1 column" style="height: 90vh; min-width: 90vw">
      <q-card-section class="row items-center justify-between col-auto q-pb-none">
        <div class="row items-center col">
          <div class="display text-h3 q-mr-md">
            {{ isEditMode ? $t('warehouse.counting.label') : $t('warehouse.counting.session_new') }}
          </div>
          <div class="row items-center q-gutter-x-sm" v-if="sessionStatus">
            <div class="text-caption text-low">
              {{ $t('warehouse.counting.status') }}
            </div>
            <q-chip
              :color="statusColor"
              size="sm"
              text-color="white"
              class="uppercase highlight"
            >
              {{ statusLabel }}
            </q-chip>

            <!-- Processing - Progress Display (moved to header) -->
            <div
              v-if="sessionStatus === 'processing' &&
                    !errorStates.includes(flowRunStatus)"
              class="row items-center q-gutter-sm"
            >
              <q-spinner-dots color="theme-blue" size="sm" />
              <div class="text-caption">
                {{ $t('warehouse.counting.processing_progress', {
                  processed: processedRecords,
                  total: toBeProcessedRecords
                }) }}
              </div>
            </div>

            <!-- Processing Errors -->
            <template v-if="sessionStatus === 'applied' && processingErrors > 0">
              <q-icon
                color="theme-orange"
                size="xs"
                round
                name="mdi-alert"
              />
              <div class="text-caption highlight">
                {{ $t('warehouse.counting.processing_errors', { count: processingErrors }) }}
              </div>
            </template>


            <!-- Start Session (planned -> started) -->
            <q-btn
              v-if="sessionStatus === 'planned'"
              color="theme-green"
              :loading="starting"
              size="sm"
              @click="startSession"
            >
              <q-icon name="mdi-play" class="q-mr-sm"/>
              {{ $t('warehouse.counting.start_session') }}
            </q-btn>
          </div>
        </div>

        <q-tabs
          v-model="step"
          dense
          active-color="primary"
          indicator-color="primary"
          class="col-auto"
          align="right"
          :disable="isProcessing"
        >
          <q-tab
            :name="1"
            :label="$t('warehouse.counting.session_data')"
            icon="mdi-information"
            :disable="isProcessing"
          />
          <q-tab
            :name="2"
            :label="$t('warehouse.counting.assignments')"
            icon="mdi-account-multiple"
            :disable="isProcessing"
          />
          <q-tab
            v-if="showRecordsTab"
            :name="3"
            :label="$t('warehouse.counting.records')"
            icon="mdi-clipboard-list"
            :disable="isProcessing"
          />
        </q-tabs>
      </q-card-section>

      <q-separator />

      <q-linear-progress v-if="loading || showProcessingOverlay" indeterminate color="primary" />

      <q-card-section class="col column q-pa-none" style="position: relative">
        <q-tab-panels
          v-model="step"
          class="surface1 col"
        >

          <!-- TAB 1: SESSION DATA -->
          <q-tab-panel :name="1" class="q-px-none">
            <CountSessionDataTab
              v-model:session-data="sessionData"
              :session-status="sessionData.status || 'planned'"
            />
          </q-tab-panel>
          <!-- TAB 2: ASSIGNMENTS -->
          <q-tab-panel :name="2" class="q-px-none">
            <CountSessionAssignmentsTab
              v-model:assignments="assignments"
              :session-type="sessionData.type"
              :disable-assigned-items="disableAssignedItems"
            />
          </q-tab-panel>
          <!-- TAB 3: RECORDS -->
          <q-tab-panel v-if="showRecordsTab" :name="3" class="q-pa-none">
            <CountSessionRecordsTab />
          </q-tab-panel>
        </q-tab-panels>

        <q-inner-loading :showing="showProcessingOverlay" />

      </q-card-section>



      <q-separator />

      <!-- SCREEN FOOTER -->
      <q-card-section class="col-auto">
        <div class="row items-center q-gutter-x-sm justify-between">
          <div class="col-auto">
            <q-checkbox
              v-if="step === 2"
              v-model="disableAssignedItems"
              :label="$t('warehouse.counting.disable_assigned_items')"
              :disable="isProcessing"
              dense
            />
          </div>
          <div class="row items-center q-gutter-x-sm">
            <q-btn
              :label="$t('close')"
              color="theme-grey"
              @click="router.back()"
            />
            <q-btn
              v-if="step > 1"
              :label="$t('back')"
              color="theme-grey"
              :disable="isProcessing"
              @click="step--"
            />
            <q-btn
              v-if="step < maxStep"
              :label="$t('next')"
              color="primary"
              :disable="isProcessing"
              @click="step++"
            />
            <q-btn
              v-if="step !== 3 && sessionStatus !== 'applied'"
              :label="isEditMode ? $t('save') : $t('create')"
              color="primary"
              :loading="saving"
              :disable="isProcessing"
              @click="saveSession"
            />

            <!-- Complete Session -->
            <q-btn
              v-if="sessionStatus === 'started'"
              color="theme-orange"
              :loading="completing"
              :disable="isProcessing"
              icon="mdi-check"
              :label="$t('warehouse.counting.complete_session')"
              @click="confirmCompleteSession"
            />

            <!-- Resume Counting -->
            <q-btn
              v-if="sessionStatus === 'completed'"
              color="primary"
              :loading="resuming"
              :disable="isProcessing"
              outline
              icon="mdi-play"
              :label="$t('warehouse.counting.resume_counting')"
              @click="resumeSession"
            />

            <!-- Apply Adjustments -->
            <q-btn
              v-if="sessionStatus === 'completed'"
              color="theme-green"
              :loading="applying"
              :disable="isProcessing"
              icon="mdi-check-all"
              :label="$t('warehouse.counting.apply_adjustments')"
              @click="confirmApplyAdjustments"
            />

            <!-- Processing with Error - Resume Button -->
            <q-btn
              v-if="sessionStatus === 'processing' &&
                    errorStates.includes(flowRunStatus)"
              color="theme-orange"
              :loading="applying"
              icon="mdi-replay"
              :label="$t('warehouse.counting.resume_processing')"
              @click="resumeProcessing"
            />
          </div>
        </div>
      </q-card-section>
    </q-card>
  </BaseDialog>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { useStore } from 'vuex';
import { Notify, useQuasar } from 'quasar';
import { useCountSessionStore } from '@/stores/countSession';
import { usePrefectAPI } from '@/composables/usePrefectAPI';
import { sendEvent } from '@/composables/event.js';
import BaseDialog from '@/components/BaseDialog.vue';
import CountSessionDataTab from './CountSessionDataTab.vue';
import CountSessionAssignmentsTab from './CountSessionAssignmentsTab.vue';
import CountSessionRecordsTab from './CountSessionRecordsTab.vue';
import { api } from 'app/src/boot/axios';

const props = defineProps({
  countSessionKey: {
    type: String,
    default: null,
  },
});

const { t: $t } = useI18n();
const $q = useQuasar();
const store = useStore();
const countSessionStore = useCountSessionStore();
const prefectAPI = usePrefectAPI();
const router = useRouter();
const step = ref(1);
const saving = ref(false);
const starting = ref(false);
const completing = ref(false);
const resuming = ref(false);
const applying = ref(false);
const disableAssignedItems = ref(false);
const isEditMode = computed(() => !!props.countSessionKey);
const originalSessionType = ref(null);
const errorStates = ['FAILED', 'CRASHED', 'NOT_FOUND', 'API_ERROR', 'CANCELLED'];
const processedRecords = ref(0);
const processingErrors = computed(() => {
  return countSessionStore.records.filter(r => r.error_details).length;
});
const toBeProcessedRecords = computed(() => {
  return countSessionStore.records.filter(r => r.status !== 'discarded').length;
});

// Prefect workflow monitoring state
const flowRunStatus = ref(null); // 'RUNNING', 'FAILED', 'CRASHED', 'COMPLETED', 'NOT_FOUND', 'API_ERROR', null

// Computed to check if actively processing (used to disable UI)
const isProcessing = computed(() => {
  return sessionStatus.value === 'processing' &&
         !errorStates.includes(flowRunStatus.value);
});

// Show records tab only when session has been started (not in 'planned' status)
const showRecordsTab = computed(() => {
  return isEditMode.value && sessionData.value.status && sessionData.value.status !== 'planned';
});

// Max step depends on whether records tab is visible
const maxStep = computed(() => showRecordsTab.value ? 3 : 2);

const sessionStatus = computed(() => {
  return sessionData.value.status || 'planned';
});

const statusColor = computed(() => {
  switch (sessionStatus.value) {
    case 'started':
      return 'primary';
    case 'completed':
      return 'theme-orange';
    case 'processing':
      // Check flow run status for error indication
      if (errorStates.includes(flowRunStatus.value)) {
        return 'theme-red';
      }
      return 'theme-blue';
    case 'applied':
      return 'theme-green';
    case 'canceled':
      return 'theme-red';
    default:
      return 'theme-grey';
  }
});


const showProcessingOverlay = computed(() => {
  return sessionStatus.value === 'processing' &&
         !errorStates.includes(flowRunStatus.value);
});

const statusLabel = computed(() => {
  if (sessionStatus.value === 'processing') {
    if (errorStates.includes(flowRunStatus.value)) {
      return $t('error');
    }
  }
  return $t(`warehouse.counting.${sessionStatus.value}`);
});


// Use store state with computed get/set for proper v-model binding
const sessionData = computed({
  get: () => countSessionStore.sessionData,
  set: (value) => { countSessionStore.sessionData = value; }
});
const loading = computed(() => countSessionStore.loading);
const assignments = computed({
  get: () => countSessionStore.assignments,
  set: (value) => { countSessionStore.assignments = value; }
});

// Methods

async function saveSession() {
  if (!sessionData.value.type) {
    Notify.create({
      type: 'negative',
      message: $t('warehouse.counting.type_required'),
      color: 'theme-red',
    });
    return;
  }

  saving.value = true;

  try {
    await countSessionStore.saveSession(props.countSessionKey);

    Notify.create({
      message: isEditMode.value
        ? $t('warehouse.counting.session.updated_successfully')
        : $t('warehouse.counting.session.created_successfully'),
      color: 'theme-green',
    });

    await store.dispatch('getCountSessions');
    router.back();
  } catch (error) {
    console.error('Error saving session:', error);
    Notify.create({
      type: 'negative',
      message: error.response?.data?.detail || (isEditMode.value
        ? $t('warehouse.counting.session.update_error')
        : $t('warehouse.counting.session.creation_error')),
      color: 'theme-red',
      timeout: 0,
      actions: [{ label: 'CLOSE', color: 'white', handler: () => {} }],
    });
  } finally {
    saving.value = false;
  }
}

async function startSession() {
  if (sessionStatus.value !== 'planned' || !props.countSessionKey) {
    return;
  }

  starting.value = true;

  try {
    await sendEvent({
      event_type: 'COUNT_SESSION_STARTED',
      event_data: {
        count_session_key: props.countSessionKey,
      },
    });

    await countSessionStore.loadSessionData(props.countSessionKey);

    Notify.create({
      message: $t('warehouse.counting.session.started_successfully'),
      color: 'theme-green',
    });
  } catch (error) {
    console.error('Error starting session:', error);
    Notify.create({
      type: 'negative',
      message: error.response?.data?.detail || $t('warehouse.counting.session.start_error'),
      color: 'theme-red',
      timeout: 0,
      actions: [{ label: 'CLOSE', color: 'white', handler: () => {} }],
    });
  } finally {
    starting.value = false;
  }
}

function confirmCompleteSession() {
  $q.dialog({
    title: $t('warehouse.counting.complete_session'),
    message: $t('warehouse.counting.complete_confirmation_message'),
    cancel: {
      label: $t('cancel'),
      color: 'theme-grey',
      flat: true,
    },
    ok: {
      label: $t('warehouse.counting.complete_session'),
      color: 'theme-orange',
    },
    persistent: true,
  }).onOk(() => {
    completeSession();
  });
}

async function completeSession() {
  if (sessionStatus.value !== 'started' || !props.countSessionKey) {
    return;
  }

  completing.value = true;

  try {
    await sendEvent({
      event_type: 'COUNT_SESSION_COMPLETED',
      event_data: {
        session_key: props.countSessionKey,
      },
    });

    await countSessionStore.loadSessionData(props.countSessionKey);

    Notify.create({
      message: $t('warehouse.counting.session.completed_successfully'),
      color: 'theme-green',
    });
  } catch (error) {
    console.error('Error completing session:', error);
    Notify.create({
      type: 'negative',
      message: error.response?.data?.detail || $t('warehouse.counting.session.complete_error'),
      color: 'theme-red',
      timeout: 0,
      actions: [{ label: 'CLOSE', color: 'white', handler: () => {} }],
    });
  } finally {
    completing.value = false;
  }
}

async function resumeSession() {
  if (sessionStatus.value !== 'completed' || !props.countSessionKey) {
    return;
  }

  resuming.value = true;

  try {
    await sendEvent({
      event_type: 'COUNT_SESSION_RESUMED',
      event_data: {
        session_key: props.countSessionKey,
      },
    });

    await countSessionStore.loadSessionData(props.countSessionKey);

    Notify.create({
      message: $t('warehouse.counting.session.resumed_successfully'),
      position: 'top',
      timeout: 1500,
      color: 'theme-green',
    });
  } catch (error) {
    console.error('Error resuming session:', error);
  } finally {
    resuming.value = false;
  }
}

function confirmApplyAdjustments() {
  $q.dialog({
    title: $t('warehouse.counting.apply_adjustments'),
    message: $t('warehouse.counting.apply_confirmation_message'),
    cancel: {
      label: $t('cancel'),
      color: 'theme-grey',
      flat: true,
    },
    ok: {
      label: $t('warehouse.counting.apply_adjustments'),
      color: 'theme-green',
    },
    persistent: true,
  }).onOk(() => {
    applyAdjustments();
  });
}

async function applyAdjustments() {
  if (sessionStatus.value !== 'completed' || !props.countSessionKey) {
    return;
  }

  applying.value = true;

  try {
    const response = await sendEvent({
      event_type: 'COUNT_SESSION_CONFIRMED',
      event_data: {
        session_key: props.countSessionKey,
      },
    });

    await countSessionStore.loadSessionData(props.countSessionKey);

    const recordsToProcess = response?.records_to_process || 0;

    // Start polling if status changed to processing
    startProcessingPoll();

  } catch (error) {
    console.error('Error applying adjustments:', error);
    Notify.create({
      type: 'negative',
      message: error.response?.data?.detail || $t('warehouse.counting.session.apply_error'),
      color: 'theme-red',
      timeout: 0,
      actions: [{ label: 'CLOSE', color: 'white', handler: () => {} }],
    });
  } finally {
    applying.value = false;
  }
}

async function resumeProcessing() {
  applying.value = true;

  try {
    // Find deployment and trigger new flow run
    const deployment = await prefectAPI.findDeploymentByName('apply_inventory_counts');
    if (!deployment) {
      throw new Error('Deployment not found');
    }

    await prefectAPI.triggerFlowRun(deployment.id, {
      session_key: props.countSessionKey
    });

    // Restart polling
    flowRunStatus.value = 'RUNNING';
    showProcessingOverlay.value = true;

    startProcessingPoll();

  } catch (error) {
    console.error('Error resuming processing:', error);
    Notify.create({
      type: 'negative',
      message: error.message || $t('warehouse.counting.resume_error'),
      color: 'theme-red',
    });
  } finally {
    applying.value = false;
  }
}

// Enhanced polling for processing status with Prefect flow run monitoring
let processingPollInterval = null;

async function checkProcessingStatus() {
  // Fetch processed records count for progress display
  const response = await api.get(`/inventory/count-session/${props.countSessionKey}/processed-records`);
  processedRecords.value = response.data;

  // If no longer processing, stop polling
  if (sessionData.value.status !== 'processing') {
    clearInterval(processingPollInterval);
    processingPollInterval = null;
    showProcessingOverlay.value = false;
    flowRunStatus.value = null;

    if (sessionData.value.status === 'applied') {
      Notify.create({
        message: $t('warehouse.counting.session.processing_completed'),
        color: 'theme-green',
      });
    }
    return;
  }

  // Check Prefect flow run status
  try {
    const flowRun = await prefectAPI.getFlowRunsForSession(props.countSessionKey);

    if (!flowRun) {
      // No flow run found - workflow failed to start or crashed
      flowRunStatus.value = 'NOT_FOUND';
      showProcessingOverlay.value = false;
      // Stop polling on error
      clearInterval(processingPollInterval);
      processingPollInterval = null;
    } else {
      flowRunStatus.value = flowRun.state_type;

      // Show overlay if workflow is actively running
      if (['SCHEDULED', 'PENDING', 'RUNNING'].includes(flowRun.state_type)) {
        showProcessingOverlay.value = true;
      } else if (flowRun.state_type === 'COMPLETED') {
        // Flow completed - reload session to get updated status
        await countSessionStore.loadSessionData(props.countSessionKey);
        // Status check at the start of next poll iteration will handle cleanup
      } else if (['FAILED', 'CRASHED', 'CANCELLED'].includes(flowRun.state_type)) {
        showProcessingOverlay.value = false;
        // Stop polling on error
        clearInterval(processingPollInterval);
        processingPollInterval = null;
      }
    }
  } catch (error) {
    console.error('Error checking flow run status:', error);
    // If Prefect API is unreachable, assume error state
    flowRunStatus.value = 'API_ERROR';
    showProcessingOverlay.value = false;
    // Stop polling on error
    clearInterval(processingPollInterval);
    processingPollInterval = null;
  }
}

function startProcessingPoll() {
  // Only start if status is processing and polling is not already active
  if (sessionStatus.value === 'processing' && !processingPollInterval) {
    // Start enhanced polling
    processingPollInterval = setInterval(async () => {
      await checkProcessingStatus();
    }, 3000);

    // Check immediately
    checkProcessingStatus();
  }
}

watch(sessionStatus, (newStatus, oldStatus) => {
  if (newStatus === 'processing' && !processingPollInterval) {
    startProcessingPoll();
  }
});

// Load data on mount
onMounted(async () => {
  store.dispatch('loadUsers');
  if (isEditMode.value) {
    // Load session and assignment data
    try {
      const data = await countSessionStore.loadSessionData(props.countSessionKey);
      originalSessionType.value = data.type;
    } catch (error) {
      Notify.create({
        type: 'negative',
        message: $t('warehouse.counting.session.load_error'),
        color: 'theme-red',
      });
    }
  } else {
    // Initialize new session
    countSessionStore.initializeSession();
  }
  await countSessionStore.loadRecords(props.countSessionKey);

  // Start polling if status is already processing on mount
  startProcessingPoll();
});

onBeforeUnmount(() => {
  if (processingPollInterval) {
    clearInterval(processingPollInterval);
  }
});

// Watch session type to reload appropriate data and reset state
watch(
  () => sessionData.value.type,
  async (newType, oldType) => {
    // Only react if type actually changed
    if (newType === oldType) return;

    // In edit mode, warn about type changes
    if (isEditMode.value && originalSessionType.value && newType !== originalSessionType.value) {
      // Show confirmation dialog
      const confirmed = await new Promise((resolve) => {
        Notify.create({
          message: $t('warehouse.counting.type_change_warning'),
          color: 'theme-orange',
          timeout: 0,
          actions: [
            { label: $t('cancel'), color: 'white', handler: () => resolve(false) },
            { label: $t('confirm'), color: 'white', handler: () => resolve(true) },
          ],
        });
      });

      if (!confirmed) {
        // Revert the type change
        countSessionStore.sessionData.type = oldType;
        return;
      }

      // Delete existing assignments
      try {
        await countSessionStore.clearPlannedAssignments();
      } catch (error) {
        console.error('Error deleting assignments:', error);
        Notify.create({
          type: 'negative',
          message: $t('warehouse.counting.session.delete_assignments_error'),
          color: 'theme-red',
          timeout: 0,
        });
        countSessionStore.sessionData.type = oldType;
        return;
      }

      // Clear assignments after confirmation
      countSessionStore.assignments = [];
    } else if (!isEditMode.value) {
      // Only clear assignments when type changes in create mode
      // In edit mode, assignments are cleared above after user confirmation
      countSessionStore.assignments = [];
    }
    // In edit mode during initial load (originalSessionType.value is null),
    // don't clear assignments - they were just loaded from the API
  }
);
</script>
