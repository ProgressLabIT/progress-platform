<template>
  <q-popup-proxy fit max-width="450px" :context-menu="contextMenu">
    <q-list :dense="props.showHeaders">

      <!-- HEADER -->

      <!-- WORK ORDER ACTIONS -->
      <template v-if="props.showWorkOrderActions">
        <template v-if="props.showHeaders">
          <q-item>
            <q-item-section side class="text-h5 text-low uppercase">
              {{ $t('work_order.short') }}
            </q-item-section>
            <q-item-section>
              <q-item-label class="highlight">
                {{ woData.wo_code }}
              </q-item-label>
            </q-item-section>
          </q-item>
          <q-separator />
        </template>
        <q-item
          v-for="item in workOrderItems"
          v-show="item.show"
          :key="item.label"
          v-ripple
          v-close-popup
          :disable="item.disable"
          :clickable="!item.disable"
          :class="item.color ? `text-${item.color}` : null"
          @click="item.action()"
        >
          <q-item-section avatar>
            <q-icon :name="item.icon" :size="props.showHeaders ? '18px' : null"/>
          </q-item-section>
          <q-item-section>
            <q-item-label>
              {{ capitalize(t(item.label)) }}
              <q-tooltip
                v-if="item.caption"
                :delay="200"
                style="max-width: 450px;"
                class="smaller"
                anchor="bottom middle"
                self="top middle"
              >
                {{ t(item.caption) }}
              </q-tooltip>
            </q-item-label>
          </q-item-section>
        </q-item>
      </template>


      <!-- JOB ACTIONS -->
      <template v-if="props.showJobActions">
        <q-separator v-if="props.showWorkOrderActions" />
        <template v-if="props.showHeaders">
          <q-item>
            <q-item-section side class="text-h5 text-low uppercase">
              {{ $t('job.label') }}
            </q-item-section>
            <q-item-section class="highlight">
              {{  job.phase_alias }} ({{ job._key }})
            </q-item-section>
          </q-item>
          <q-separator />
        </template>

        <q-item
          v-for="item in jobItems"
          v-show="item.show"
          :key="item.label"
          v-ripple
          v-close-popup
          :disable="item.disable"
          :clickable="!item.disable"
          :class="item.color ? `text-${item.color}` : null"
          @click="item.action()"
        >
          <q-item-section avatar>
            <q-icon :name="item.icon" :size="props.showHeaders ? '18px' : null"/>
          </q-item-section>
          <q-item-section>
            <q-item-label>
              {{ capitalize(t(item.label)) }}
              <q-tooltip
                v-if="item.caption"
                :delay="200"
                anchor="top middle"
                self="bottom middle"
              >
                <div
                  style="max-width: 300px;"
                  class="smaller">
                  {{ t(item.caption) }}
                </div>
              </q-tooltip>
            </q-item-label>
          </q-item-section>
        </q-item>
      </template>
    </q-list>
  </q-popup-proxy>

  <!-- Reusable Basic Confirmation -->
  <BaseConfirmationDialog
    :show="confirmMessage !== undefined"
    :confirm_color="confirmColor"
    @close="resetEditing"
    @confirm="action"
  >
    <div v-if="props.showHeaders" class="text-h5 uppercase highlight q-mb-md">
      <span>
        {{ t('work_order.short') }} {{ woData.wo_code }}
      </span>
      <span v-if="props.showJobActions">
        - {{  job.phase_alias }} -  {{ t('job.label') }} {{ job._key }}
      </span>
    </div>
    <div>
      {{ t(confirmMessage) }}
    </div>
  </BaseConfirmationDialog>


  <!-- ================================================ -->
  <!-- JOB ACTIONS DIALOGS -->
  <!-- ================================================ -->

  <!-- PROCESSING TIME EDIT -->
  <BaseDialog :show="action === forceProcessingTime">
    <q-card square class="surface1 q-pa-md">
      <q-card-section class="text-h3 display highlight">
        {{ $t('update_time') }}
      </q-card-section>
      <q-card-section>
        <div class="row q-col-gutter-md">
          <q-input
            v-model.number="tempData.hours"
            type="number"
            filled
            stack-label
            min="0"
            :label="$t('time.hour', 2)"
            class="col"
            @keyup.enter="forceProcessingTime"
          >
          </q-input>
          <q-input
            v-model.number="tempData.minutes"
            type="number"
            filled
            stack-label
            min="0"
            :label="$t('time.minute', 2)"
            class="col"
            @keyup.enter="forceProcessingTime"
          >
          </q-input>
          <q-input
            v-model.number="tempData.seconds"
            type="number"
            filled
            stack-label
            min="0"
            :label="$t('time.second', 2)"
            class="col"
            @keyup.enter="forceProcessingTime"
          >
          </q-input>
        </div>
      </q-card-section>
      <q-card-section>
        <div class="row justify-between">
          <q-btn
            color="theme-grey"
            :label="$t('cancel')"
            @click="resetEditing"
          >
          </q-btn>
          <q-btn
            color="theme-blue"
            :label="$t('save')"
            @click="forceProcessingTime"
          >
          </q-btn>
        </div>
      </q-card-section>
    </q-card>
  </BaseDialog>

  <!-- PROGRESS EDIT -->
  <BaseDialog :show="action === forceProgress">
    <q-card square class="surface1 q-pa-md">
      <q-card-section class="text-h3 display highlight">
        {{ $t('update_progress') }}
      </q-card-section>

      <q-card-section>
        <q-input
          v-model.number="tempData.newJobQtCompleted"
          type="number"
          filled
          stack-label
          :min="tempData.minProgressQt"
          :max="tempData.maxProgressQt"
          :label="$t('quantity.completed.long')"
          autofocus
          @keyup.enter="forceProgress"
        >
        </q-input>
      </q-card-section>

      <q-card-section>
        <q-checkbox
          v-model="tempData.shouldAdjustDuration"
          :label="$t('quantity.should_adjust_duration')"
        />
      </q-card-section>

      <q-card-section>
        <div class="row justify-between">
          <q-btn
            color="theme-grey"
            :label="$t('cancel')"
            @click="resetEditing"
          >
          </q-btn>
          <q-btn
            v-if="
              tempData.newJobQtCompleted !==
              job.qt_completed
            "
            color="theme-blue"
            :label="$t('save')"
            @click="forceProgress"
          >
          </q-btn>
        </div>
      </q-card-section>
    </q-card>
  </BaseDialog>


  <!-- ================================================ -->
  <!-- WORK ORDER ACTIONS DIALOGS -->
  <!-- ================================================ -->

  <BaseDialog :show="dialog !== undefined" @close="resetEditing">
    <q-card square class="surface1 q-pa-md" style="min-width: 400px;">

      <q-card-section v-if="props.showHeaders" class="text-h5 uppercase highlight q-mb-md">
        <span>
          {{ t('work_order.short') }} {{ woData.wo_code }}
        </span>
        <span v-if="props.showJobActions">
          - {{  job.phase_alias }} -  {{ t('job.label') }} {{ job._key }}
        </span>
      </q-card-section>

      <!-- EDIT PROJECT DIALOG -->
      <template v-if="dialog === 'update_project'">
        <q-card-section>
          <div class="text-h4 display highlight text-uppercase">
            {{ $t('project') }}
          </div>
          <q-input
            v-model="tempData.projectCode"
            autofocus
            class="q-mt-md"
            input-class="text-body1 text-uppercase"
            hide-bottom-space
          >
          </q-input>
        </q-card-section>
        <q-card-actions align="between">
          <q-btn size="12px" flat color="theme-grey" @click="resetEditing">
            {{ $t('cancel') }}
          </q-btn>
          <q-btn
            v-if="tempData.projectCode !== woData.project_code"
            size="12px"
            flat
            color="theme-blue"
            @click="saveWorkOrderUpdate"
          >
            {{ $t('save') }}
          </q-btn>
        </q-card-actions>
      </template>

      <template v-else-if="dialog === 'update_quantity'">
        <q-card-section>
          <div class="text-h4 display highlight text-uppercase">
            {{ $t('work_order.new_quantity') }}
          </div>
          <q-input
            v-model.number="tempData.newQt"
            autofocus
            class="q-mt-md"
            input-class="text-body1"
            hide-bottom-space
            type="number"
            :min="tempData.minAllowableWoQt"
          >
          </q-input>
        </q-card-section>
        <q-card-actions align="between">
          <q-btn size="12px" flat color="theme-grey" @click="resetEditing">
            {{ $t('cancel') }}
          </q-btn>
          <q-btn
            v-if="tempData.newQt !== woData.qt_planned"
            size="12px"
            flat
            color="theme-blue"
            @click="dialog = 'assign_quantity'"
          >
            {{ $t('save') }}
          </q-btn>
        </q-card-actions>
      </template>


      <WorkOrderJobQtRebalance
        v-else-if="dialog === 'assign_quantity'"
        :new_wo_qt="tempData.newQt"
        :phase_data="phaseData"
        :wo_key="woData._key"
        @close="resetEditing"
      />

      <!-- UPDATE DATES DIALOG -->
      <template v-else-if="['update_from_date', 'update_due_date'].includes(dialog)">
        <q-date
          v-model="tempData[dialog === 'update_from_date' ? 'fromDate' : 'dueDate']"
          minimal
          mask="YYYY-MM-DD"
        />
        <div class="row justify-between q-pa-sm">
          <q-btn flat size="12px" color="theme-grey" @click="resetEditing">
            {{ $t('cancel') }}
          </q-btn>
          <q-btn
            flat
            size="12px"
            color="theme-blue"
            @click="saveWorkOrderUpdate"
          >
            {{ $t('save') }}
          </q-btn>
        </div>
      </template>

    </q-card>
  </BaseDialog>

</template>

<script setup>
import { reactive, ref, computed, watch } from 'vue'
import BaseDialog from '@/components/BaseDialog.vue'
import BaseConfirmationDialog from '@/components/BaseConfirmationDialog.vue'
import { sendEvent } from '@/composables/event'
import { useI18n } from 'vue-i18n'
import { Duration } from 'luxon'
import { api } from '@/boot/axios'
import { useStore } from 'vuex'
import { Notify } from 'quasar'
import { useRouter } from 'vue-router'
import { capitalize } from '@/boot/filters'
import WorkOrderJobQtRebalance from '@/components/WorkOrderJobQtRebalance.vue'

const { t } = useI18n()
const store = useStore()
const router = useRouter()

const action = ref(undefined)
const confirmMessage = ref(undefined)
const confirmColor = ref('theme-blue')
const dialog = ref(undefined)

const emit = defineEmits(['ok'])

const props = defineProps({
  job: {
    type: Object,
    default: undefined,
    required: false,
  },
  wo: {
    type: Object,
    default: undefined,
    required: false,
  },
  showJobActions: {
    type: Boolean,
    default: false,
    required: false,
  },
  showWorkOrderActions: {
    type: Boolean,
    default: false,
    required: false,
  },
  contextMenu: {
    type: Boolean,
    default: false,
    required: false,
  },
  showHeaders: {
    type: Boolean,
    default: false,
    required: false,
  },
})

let woData = reactive({})
const tempData = reactive({})


async function getWoData() {
  const wo_key = props.job?.wo_key || props.wo?._key
  const resp = await api.get(`work-order/${wo_key}`)
  Object.assign(woData, resp.data.detail)
}


async function initTempData() {
  await getWoData()

  Object.assign(tempData, {
    hours: 0,
    minutes: 0,
    seconds: 0,
    newJobQtCompleted: 0,
    shouldAdjustDuration: false,
    minProgressQt: null,
    maxProgressQt: null,
    minAllowableWoQt: 1, // Minimum allowed work order quantity
    projectCode: woData.project_code,
    dueDate: woData.due_by,
    fromDate: woData.start_from,
    newQt: woData.qt_planned,
  })
}

// Initialize data on setup
initTempData()

// Watch for changes in props and refresh data
watch(() => props.job, async () => {
  if (props.job) {
    await initTempData()
  }
}, { immediate: false })

watch(() => props.wo, async () => {
  if (props.wo) {
    await initTempData()
  }
}, { immediate: false })

// Figure out if we can force progress. Prevented in case of:
// - Job has mandatory form fields
// - Job has components with traceability
const hasMandatoryFields = ref(false)
const hasComponentsWithTraceability = ref(false)

async function checkMandatoryFields() {
  hasMandatoryFields.value = props.job === undefined
    ? false
    : props.job.step_sequence.some(step => step.form_fields.some(field => field.mandatory))
}

checkMandatoryFields()

async function checkComponentsWithTraceability() {
  hasComponentsWithTraceability.value = woData.wo_bom?.some(component => component.traceability_level && component.phase_key === props.job?.phase_key)
}

checkComponentsWithTraceability()

const canForceProgress = computed(() => !(
  !!props.job?.traceability_level ||
  !!woData.traceability_level ||
  hasMandatoryFields.value ||
  hasComponentsWithTraceability.value
))

// Phase data for job quantity rebalance
const phaseData = computed(() => {
  if (!woData.phase_sequence) {
    return []
  }

  return woData.phase_sequence.map((phase_key) => {
    const jobs = woData.jobs?.filter((j) => j.phase_key === phase_key) || [];
    const params = jobs[0]?.parameters;
    const phase_alias = jobs[0]?.phase_alias;
    const total_completed = jobs.reduce(
      (sum, job) => sum + job.qt_completed,
      0,
    );
    const total_active = jobs.reduce(
      (sum, job) => sum + job.active_batch_qt,
      0,
    );
    // const total_released = jobs.reduce( (sum, job) => sum + job.qt_released, 0 )
    const total_remaining = jobs.reduce((sum, job) => {
      return sum + job.qt_planned - job.qt_completed - job.active_batch_qt;
    }, 0);
    const total_progress = Math.floor(
      jobs.reduce((sum, job) => sum + job.progress * job.qt_planned, 0) /
        woData.qt_planned,
    );
    const active = jobs.reduce((count, job) => count + job.active, 0);

    // const assignments = jobs.map( job => job.assigned_to )
    return {
      jobs,
      phase_key,
      phase_alias,
      active,
      ...params,
      // qt_released: total_released,
      qt_completed: total_completed,
      qt_remaining: total_remaining,
      active_batch_qt: total_active,
      progress: total_progress,
    };
  });
})


/* ===============================
 * JOB ACTIONS
 * =============================== */

async function pauseJob() {
  const resp = await api.get('work-session', {
    params: { job_key: props.job._key },
  });

  let userSessionKey = resp?.data?.detail?.user_session_key;
  if (userSessionKey) {
    api.delete(`/session/${userSessionKey}`, {
      params: { force: true },
    });
  }

  store
    .dispatch('forcePauseJob', { job: props.job })
    .then(async () => {
      await store.dispatch('loadWorkOrderData', woData._key);
      Notify.create({
        message: t('pause_job_success'),
        color: 'theme-green',
        timeout: 1500,
        position: 'top',
      });
    })
    .catch((err) => {
      window.alert(err);
    });
    emit('ok')
}


async function forceProcessingTime() {
  const new_job_duration =
    (tempData.hours * 3600 +
      tempData.minutes * 60 +
      tempData.seconds) *
    1000;

  try {
    await sendEvent({
      event_type: 'TIME_OVERRIDE_REQUESTED',
      event_data: {
        job_key: props.job._key,
        work_order_key: props.job.wo_key,
        phase_key: props.job.phase_key,
        new_job_duration,
      },
    })
    resetEditing();
    await store.dispatch('loadWorkOrderData', props.job.wo_key);
    Notify.create({
      message: t('update_time_success'),
      color: 'theme-green',
      timeout: 1500,
      position: 'top',
    });
    emit('ok')
  } catch (err) {
    window.alert(err);
  }
}

function editJobTime() {
  const duration = Duration.fromMillis(props.job.processing_time)
    .rescale()
    .shiftTo('hours', 'minutes', 'seconds')
    .toObject();
  tempData.hours = duration.hours ?? 0
  tempData.minutes = duration.minutes ?? 0
  tempData.seconds = duration.seconds ?? 0
  action.value = forceProcessingTime
}

async function forceProgress() {
  const newQtWithinBounds =
    tempData.minProgressQt <= tempData.newJobQtCompleted &&
    tempData.newJobQtCompleted <= tempData.maxProgressQt;

  if (!newQtWithinBounds) {
    // TODO: i18n
    window.alert(
      `Quantità deve essere fra ${tempData.minProgressQt} e ${tempData.maxProgressQt}`,
    );
    // Set value to closest limit
    tempData.newJobQtCompleted =
      tempData.newJobQtCompleted < tempData.minProgressQt
        ? tempData.minProgressQt
        : tempData.maxProgressQt;
    return;
  }

  try {
    await sendEvent({
      event_type: 'PROGRESS_OVERRIDE_REQUESTED',
      event_data: {
        job_key: props.job._key,
        new_job_qt_completed: tempData.newJobQtCompleted,
      },
    });
    resetEditing();
    await store.dispatch('loadWorkOrderData', props.job.wo_key);
    Notify.create({
      message: t('update_progress_success'),
      color: 'theme-green',
      timeout: 1500,
      position: 'top',
    });
    emit('ok')
  } catch (error) {
    window.alert(error);
  }
}

async function editJobProgress() {
  console.log('editJobProgress', props.job)
  const resp = await api.get('wip', {
    params: { job_key: props.job._key },
  });
  const minProgressQt = props.job.last_phase
    ? 0
    : Math.max(0, props.job.qt_completed - resp.data.free_wip_qt_downstream);
  const maxProgressQt = props.job.first_phase
    ? props.job.qt_planned
    : Math.min(
        props.job.qt_completed + resp.data.free_wip_qt_upstream,
        props.job.qt_planned,
      );

  tempData.newJobQtCompleted = props.job.qt_completed
  tempData.minProgressQt = minProgressQt
  tempData.maxProgressQt = maxProgressQt
  tempData.shouldAdjustDuration = true
  action.value = forceProgress
}


async function cancelBatch() {
  await sendEvent({
    event_type: 'BATCH_CANCELED',
    event_data: {
      job_key: props.job._key,
    },
  })
  try {
    resetEditing();
    await store.dispatch('loadWorkOrderData', props.job.wo_key);
    Notify.create({
      message: t('cancel_active_batch_success'),
      color: 'theme-green',
        timeout: 1500,
        position: 'top',
    });
    emit('ok')
  } catch (err) {
    window.alert(err);
  }
}

async function resetJob() {
  await sendEvent({
    event_type: 'JOB_RESET',
    event_data: {
      job_key: props.job._key,
    },
  })
  try {
    resetEditing();
    await store.dispatch('loadWorkOrderData', props.job.wo_key);
    Notify.create({
      message: t('reset_job_success'),
      color: 'theme-green',
      timeout: 1500,
      position: 'top',
    });
    emit('ok')
  } catch (err) {
    window.alert(err);
  }
}

async function saveWorkOrderUpdate() {

  const wo_update = {
    wo_key: woData._key,
    new_qt: tempData.newQt,
    new_project_code: tempData.projectCode,
    new_due_date: tempData.dueDate,
    new_from_date: tempData.fromDate,
  };

  await store.dispatch('updateWorkOrder', wo_update);
  await store.dispatch('loadWorkOrderData', wo_update.wo_key);
  resetEditing();
  Notify.create({
    message: t('work_order.update_success'),
    color: 'theme-green',
    timeout: 1500,
    position: 'top',
  });
  emit('ok')
}


async function deleteWorkOrder() {
  await api.delete(`work-order/${woData._key}`)
  await store.dispatch('loadWorkOrders')
  resetEditing()
  Notify.create({
    message: t('work_order.delete_success'),
    color: 'theme-green',
    timeout: 1500,
    position: 'top',
  });
  emit('ok')
  router.back()
}


function resetEditing() {
  confirmMessage.value = undefined
  action.value = undefined
  dialog.value = undefined
}


const jobItems = computed(() => [
  {
    label: 'pause_job',
    caption: 'pause_job_disabled',
    icon: 'mdi-stop-circle-outline',
    show: props.job?.active,
    action: () => {
      confirmMessage.value = 'pause_job_confirmation'
      action.value = pauseJob
    },
  },
  {
    label: 'update_time',
    caption: 'update_time_disabled',
    icon: 'mdi-clock-edit-outline',
    show: !props.job?.active,
    disable: props.job?.stage === 'created',
    action: editJobTime,
  },
  {
    label: 'cancel_active_batch',
    caption: 'cancel_active_batch_disabled',
    icon: 'mdi-cube-off-outline',
    show: !props.job?.active,
    disable: props.job?.active_batch_qt === 0,
    action: () => {
      action.value = cancelBatch
      confirmMessage.value = 'cancel_active_batch_confirm'
    },
  },
  {
    label: 'update_progress',
    caption: 'update_progress_disabled',
    icon: 'mdi-plus-minus-variant',
    show: !props.job?.active,
    disable: props.job?.active_batch_qt > 0 || !canForceProgress.value,
    action: editJobProgress,
  },
  {
    label: 'reset_job',
    caption: 'reset_job_disabled',
    icon: 'mdi-backup-restore',
    show: !props.job?.active,
    disable: props.job?.stage === 'created',
    action: () => {
      action.value = resetJob
      confirmMessage.value = 'reset_job_confirm'
    },
  }
])

const workOrderItems = computed(() => [
  {
    label: 'project_update',
    icon: 'mdi-folder-edit-outline',
    show: !woData.active,
    action: async () => {
      await initTempData();
      action.value = saveWorkOrderUpdate;
      dialog.value = 'update_project'
    },
  },
  {
    label: 'quantity.update',
    icon: 'mdi-plus-minus-variant',
    show: !woData.active,
    action: async () => {
      await initTempData();
      action.value = saveWorkOrderUpdate;
      dialog.value = 'update_quantity'
    },
  },
  {
    label: 'work_order.update_from_date',
    icon: 'mdi-calendar-start',
    show: !woData.active,
    action: async () => {
      await initTempData();
      action.value = saveWorkOrderUpdate;
      dialog.value = 'update_from_date'
    },
  },
  {
    label: 'work_order.update_due_date',
    icon: 'mdi-calendar-end',
    show: !woData.active,
    action: async () => {
      await initTempData();
      action.value = saveWorkOrderUpdate;
      dialog.value = 'update_due_date'
    },
  },
  {
    label: 'work_order.delete_action',
    icon: 'mdi-delete-outline',
    show: !woData.active && woData.status === 'created',
    color: 'theme-red',
    action: () => {
      action.value = deleteWorkOrder
      confirmMessage.value = 'work_order.delete_question'
      confirmColor.value = 'theme-red'
    },
  },
]);
</script>
