<template>
  <BaseDialog :show="true" @close.stop="router.back()">
    <q-card class="surface1 column" style="height: 90vh; min-width: 90vw">
      <q-card-section class="row items-center justify-between col-auto q-pb-none">
        <div class="row items-center col">
          <div class="display text-h3 q-mr-md">
            {{ isEditMode ? $t('warehouse.counting.session_edit') : $t('warehouse.counting.session_new') }}
          </div>
          <div class="row items-center q-gutter-x-sm" v-if="sessionStatus">
            <div class="text-caption text-low">
              {{ $t('warehouse.counting.status') }}
            </div>
            <q-chip
              dense
              :color="statusColor"
              text-color="white"
              class="text-caption"
            >
              {{ $t(`warehouse.counting.${sessionStatus}`) }}
            </q-chip>
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

            <!-- Complete Session (started -> completed) -->
            <q-btn
              v-if="sessionStatus === 'started'"
              color="theme-orange"
              :loading="completing"
              size="sm"
              @click="completeSession"
            >
              <q-icon name="mdi-check" class="q-mr-sm"/>
              {{ $t('warehouse.counting.complete_session') }}
            </q-btn>

            <!-- Resume Counting (completed -> started) -->
            <q-btn
              v-if="sessionStatus === 'completed'"
              color="primary"
              :loading="resuming"
              size="sm"
              outline
              @click="resumeSession"
            >
              <q-icon name="mdi-play" class="q-mr-sm"/>
              {{ $t('warehouse.counting.resume_counting') }}
            </q-btn>

            <!-- Apply Adjustments (completed -> applied) -->
            <q-btn
              v-if="sessionStatus === 'completed'"
              color="theme-green"
              :loading="applying"
              size="sm"
              @click="confirmApplyAdjustments"
            >
              <q-icon name="mdi-check-all" class="q-mr-sm"/>
              {{ $t('warehouse.counting.apply_adjustments') }}
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
        >
          <q-tab
            :name="1"
            :label="$t('warehouse.counting.session_data')"
            icon="mdi-information"
          />
          <q-tab
            :name="2"
            :label="$t('warehouse.counting.assignments')"
            icon="mdi-account-multiple"
          />
          <q-tab
            v-if="showRecordsTab"
            :name="3"
            :label="$t('warehouse.counting.records')"
            icon="mdi-clipboard-list"
          />
        </q-tabs>
      </q-card-section>

      <q-separator />

      <q-linear-progress v-if="loading" indeterminate color="primary" />

      <q-tab-panels
        v-model="step"
        class="col surface1"
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

      <q-separator />

      <q-card-section class="col-auto">
        <div class="row items-center q-gutter-x-sm justify-between">
          <div class="col-auto">
            <q-checkbox
              v-if="step === 2"
              v-model="disableAssignedItems"
              :label="$t('warehouse.counting.disable_assigned_items')"
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
              @click="step--"
            />
            <q-btn
              v-if="step < maxStep"
              :label="$t('next')"
              color="primary"
              @click="step++"
            />
            <q-btn
              v-if="step !== 3"
              :label="isEditMode ? $t('save') : $t('create')"
              color="primary"
              :loading="saving"
              @click="saveSession"
            />
          </div>
        </div>
      </q-card-section>
    </q-card>
  </BaseDialog>
</template>

<script setup>
import { ref, watch, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { useStore } from 'vuex';
import { Notify, useQuasar } from 'quasar';
import { useCountSessionStore } from '@/stores/countSession';
import { sendEvent } from '@/composables/event.js';
import BaseDialog from '@/components/BaseDialog.vue';
import CountSessionDataTab from './CountSessionDataTab.vue';
import CountSessionAssignmentsTab from './CountSessionAssignmentsTab.vue';
import CountSessionRecordsTab from './CountSessionRecordsTab.vue';

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
    case 'applied':
      return 'theme-green';
    case 'canceled':
      return 'theme-red';
    default:
      return 'theme-grey';
  }
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
      color: 'theme-green',
    });
  } catch (error) {
    console.error('Error resuming session:', error);
    Notify.create({
      type: 'negative',
      message: error.response?.data?.detail || $t('warehouse.counting.session.resume_error'),
      color: 'theme-red',
      timeout: 0,
      actions: [{ label: 'CLOSE', color: 'white', handler: () => {} }],
    });
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
      event_type: 'COUNT_SESSION_APPLIED',
      event_data: {
        session_key: props.countSessionKey,
      },
    });

    await countSessionStore.loadSessionData(props.countSessionKey);

    const adjustmentsCount = response?.adjustments_count || 0;

    Notify.create({
      message: $t('warehouse.counting.session.applied_successfully', { count: adjustmentsCount }),
      color: 'theme-green',
    });
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
