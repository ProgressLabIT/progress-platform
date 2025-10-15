import { Duration } from 'luxon'
import { Notify } from 'quasar'
import { computed, ref, reactive } from 'vue'
import { useI18n } from 'vue-i18n'
import { useStore } from 'vuex'
import { api } from '@/boot/axios'
import { sendEvent } from '@/composables/event'
import store from '@/store'

/* ================================================
 * UTILITY FUNCTIONS
 * ================================================ */

/**
 * Compute phase data from a full work order object with jobs
 * @param {Object} wo - Work order object with jobs array and phase_sequence
 * @returns {Array} Array of phase objects with aggregated job data
 */
export function computePhaseData(wo) {
  if (!wo.phase_sequence) {
    return []
  }

  return wo.phase_sequence.map((phase_key) => {
    const jobs = (wo.jobs || []).filter((j) => j.phase_key === phase_key)
    const params = jobs[0]?.parameters
    const phase_alias = jobs[0]?.phase_alias

    const total_completed = jobs.reduce(
      (sum, job) => sum + job.qt_completed,
      0,
    )
    const total_active = jobs.reduce(
      (sum, job) => sum + job.active_batch_qt,
      0,
    )
    const total_remaining = jobs.reduce((sum, job) => {
      return sum + job.qt_planned - job.qt_completed - job.active_batch_qt
    }, 0)
    const total_progress = Math.floor(
      jobs.reduce((sum, job) => sum + job.progress * job.qt_planned, 0) /
        Math.max(wo.qt_planned, 1),
    )
    const active = jobs.reduce((count, job) => count + (job.active ? 1 : 0), 0)

    return {
      jobs,
      phase_key,
      phase_alias,
      active,
      ...params,
      qt_completed: total_completed,
      qt_remaining: total_remaining,
      active_batch_qt: total_active,
      progress: total_progress,
    }
  })
}

/* ================================================
 * JOB ACTIONS
 * ================================================ */
export function useJobActions() {
  const { t } = useI18n()

  // Modal state management
  const modals = reactive({
    editTime: {
      show: false,
      data: {
        hours: 0,
        minutes: 0,
        seconds: 0,
        _key: null,
        phase_key: null,
        work_order_key: null
      }
    },
    editProgress: {
      show: false,
      data: {
        new_job_qt_completed: 0,
        min_progress_qt: 0,
        max_progress_qt: 100,
        should_adjust_duration: true,
        job_key: null,
        phase_key: null,
        work_order_key: null
      },
      originalCompleted: 0
    },
    cancelBatch: {
      show: false,
      jobKey: null,
      workOrderKey: null
    },
    resetJob: {
      show: false,
      jobKey: null,
      workOrderKey: null
    }
  })

  // Legacy state for backward compatibility (will be removed)
  const editJobTime = ref(null)
  const editJobProgress = ref(null)
  const confirmCancelBatch = ref(null)
  const confirmResetJob = ref(null)
  const jobsTempData = ref({})

  // Job action implementations
  const pauseJob = async (job_data) => {
    try {
      const resp = await api.get('work-session', {
        params: { job_key: job_data._key },
      })

      let userSessionKey = resp?.data?.detail?.user_session_key
      if (userSessionKey) {
        await api.delete(`/session/${userSessionKey}`, {
          params: { force: true },
        })
      }

      await store.dispatch('forcePauseJob', { job: job_data })
      await store.dispatch('loadWorkOrderData', job_data.wo_key)

      Notify.create({
        message: t('pause_job_success'),
        color: 'theme-green',
        timeout: 1500,
        position: 'top',
      })
    } catch (err) {
      window.alert(err)
    }
  }

    const editJobTimeAction = (job_data) => {
    const duration = Duration.fromMillis(job_data.processing_time)
      .rescale()
      .shiftTo('hours', 'minutes', 'seconds')
      .toObject()

    // Update modal state
    modals.editTime.data = {
      _key: job_data._key,
      phase_key: job_data.phase_key,
      work_order_key: job_data.wo_key,
      hours: duration.hours ?? 0,
      minutes: duration.minutes ?? 0,
      seconds: duration.seconds ?? 0,
    }
    modals.editTime.show = true

    // Legacy compatibility
    jobsTempData.value = modals.editTime.data
    editJobTime.value = job_data._key
  }

    const editJobProgressAction = async (job_data) => {
    try {
      const resp = await api.get('wip', {
        params: { job_key: job_data._key },
      })

      const min_progress_qt = job_data.last_phase
        ? 0
        : Math.max(0, job_data.qt_completed - resp.data.free_wip_qt_downstream)
      const max_progress_qt = job_data.first_phase
        ? job_data.qt_planned
        : Math.min(
            job_data.qt_completed + resp.data.free_wip_qt_upstream,
            job_data.qt_planned,
          )

      // Update modal state
      modals.editProgress.data = {
        job_key: job_data._key,
        phase_key: job_data.phase_key,
        work_order_key: job_data.wo_key,
        new_job_qt_completed: job_data.qt_completed,
        min_progress_qt,
        max_progress_qt,
        should_adjust_duration: true,
      }
      modals.editProgress.originalCompleted = job_data.qt_completed
      modals.editProgress.show = true

      // Legacy compatibility
      jobsTempData.value = modals.editProgress.data
      editJobProgress.value = job_data._key
    } catch (err) {
      window.alert(err)
    }
  }

  const cancelBatchAction = (job_data) => {
    modals.cancelBatch.jobKey = job_data._key
    modals.cancelBatch.workOrderKey = job_data.wo_key
    modals.cancelBatch.show = true

    // Legacy compatibility
    confirmCancelBatch.value = job_data._key
  }

  const resetJobAction = (job_data) => {
    modals.resetJob.jobKey = job_data._key
    modals.resetJob.workOrderKey = job_data.wo_key
    modals.resetJob.show = true

    // Legacy compatibility
    confirmResetJob.value = job_data._key
  }

  const resetEditing = () => {
    // Reset modal state
    modals.editTime.show = false
    modals.editProgress.show = false
    modals.cancelBatch.show = false
    modals.cancelBatch.workOrderKey = null
    modals.resetJob.show = false
    modals.resetJob.workOrderKey = null

    // Legacy compatibility
    editJobTime.value = null
    editJobProgress.value = null
    confirmCancelBatch.value = null
    confirmResetJob.value = null
    jobsTempData.value = {}
  }

  // Modal management functions
  const closeModal = (modalType) => {
    if (modals[modalType]) {
      modals[modalType].show = false
    }
    resetEditing()
  }

  const handleTimeModalSave = async (timeData) => {
    const new_job_duration =
      (timeData.hours * 3600 + timeData.minutes * 60 + timeData.seconds) * 1000

    try {
      await sendEvent({
        event_type: 'TIME_OVERRIDE_REQUESTED',
        event_data: {
          job_key: timeData._key,
          work_order_key: timeData.work_order_key,
          phase_key: timeData.phase_key,
          new_job_duration,
        },
      })

      closeModal('editTime')
      await store.dispatch('loadWorkOrderData', timeData.work_order_key)

      Notify.create({
        message: t('update_time_success'),
        color: 'theme-green',
        timeout: 1500,
        position: 'top',
      })
    } catch (err) {
      window.alert(err)
    }
  }

  const handleProgressModalSave = async (progressData) => {
    const new_qt_within_bounds =
      progressData.min_progress_qt <= progressData.new_job_qt_completed &&
      progressData.new_job_qt_completed <= progressData.max_progress_qt

    if (!new_qt_within_bounds) {
      window.alert(
        `Quantità deve essere fra ${progressData.min_progress_qt} e ${progressData.max_progress_qt}`,
      )
      return
    }

    try {
      const eventData = { ...progressData }
      delete eventData.max_progress_qt
      delete eventData.min_progress_qt

      await sendEvent({
        event_type: 'PROGRESS_OVERRIDE_REQUESTED',
        event_data: eventData,
      })

      closeModal('editProgress')
      await store.dispatch('loadWorkOrderData', progressData.work_order_key)

      Notify.create({
        message: t('update_progress_success'),
        color: 'theme-green',
        timeout: 1500,
        position: 'top',
      })
    } catch (error) {
      window.alert(error)
    }
  }

  const handleCancelBatchConfirm = async () => {
    try {
      await sendEvent({
        event_type: 'BATCH_CANCELED',
        event_data: {
          job_key: modals.cancelBatch.jobKey,
        },
      })

      const woKey = modals.cancelBatch.workOrderKey
      closeModal('cancelBatch')

      if (woKey) {
        await store.dispatch('loadWorkOrderData', woKey)
      }

      Notify.create({
        message: t('cancel_active_batch_success'),
        color: 'theme-green',
        timeout: 1500,
        position: 'top',
      })
    } catch (err) {
      window.alert(err)
    }
  }

  const handleResetJobConfirm = async () => {
    try {
      await sendEvent({
        event_type: 'JOB_RESET',
        event_data: {
          job_key: modals.resetJob.jobKey,
        },
      })

      const woKey = modals.resetJob.workOrderKey
      closeModal('resetJob')

      if (woKey) {
        await store.dispatch('loadWorkOrderData', woKey)
      }

      Notify.create({
        message: t('reset_job_success'),
        color: 'theme-green',
        timeout: 1500,
        position: 'top',
      })
    } catch (err) {
      window.alert(err)
    }
  }

  const forceProcessingTime = async (wo_key) => {
    try {
      const new_job_duration =
        (jobsTempData.value.hours * 3600 +
          jobsTempData.value.minutes * 60 +
          jobsTempData.value.seconds) *
        1000

      await sendEvent({
        event_type: 'TIME_OVERRIDE_REQUESTED',
        event_data: {
          job_key: jobsTempData.value._key,
          work_order_key: wo_key,
          phase_key: jobsTempData.value.phase_key,
          new_job_duration,
        },
      })

      resetEditing()
      await store.dispatch('loadWorkOrderData', wo_key)

      Notify.create({
        message: t('update_time_success'),
        color: 'theme-green',
        timeout: 1500,
        position: 'top',
      })
    } catch (err) {
      window.alert(err)
    }
  }

  const forceProgress = async (wo_key) => {
    try {
      const td = jobsTempData.value
      const new_qt_within_bounds =
        td.min_progress_qt <= td.new_job_qt_completed &&
        td.new_job_qt_completed <= td.max_progress_qt

      if (!new_qt_within_bounds) {
        // TODO: i18n
        window.alert(
          `Quantità deve essere fra ${td.min_progress_qt} e ${td.max_progress_qt}`,
        )
        // Set value to closest limit
        td.new_job_qt_completed =
          td.new_job_qt_completed < td.min_progress_qt
            ? td.min_progress_qt
            : td.max_progress_qt
        return
      }

      delete jobsTempData.value.max_progress_qt
      delete jobsTempData.value.min_progress_qt

      await sendEvent({
        event_type: 'PROGRESS_OVERRIDE_REQUESTED',
        event_data: jobsTempData.value,
      })

      resetEditing()
      await store.dispatch('loadWorkOrderData', wo_key)

      Notify.create({
        message: t('update_progress_success'),
        color: 'theme-green',
        timeout: 1500,
        position: 'top',
      })
    } catch (error) {
      window.alert(error)
    }
  }

  const cancelBatch = async (wo_key) => {
    try {
      await sendEvent({
        event_type: 'BATCH_CANCELED',
        event_data: {
          job_key: confirmCancelBatch.value,
        },
      })

      resetEditing()
      await store.dispatch('loadWorkOrderData', wo_key)

      Notify.create({
        message: t('cancel_active_batch_success'),
        color: 'theme-green',
        timeout: 1500,
        position: 'top',
      })
    } catch (err) {
      window.alert(err)
    }
  }

  const resetJob = async (wo_key) => {
    try {
      await sendEvent({
        event_type: 'JOB_RESET',
        event_data: {
          job_key: confirmResetJob.value,
        },
      })

      await store.dispatch('loadWorkOrderData', wo_key)
      resetEditing()

      Notify.create({
        message: t('reset_job_success'),
        color: 'theme-green',
        timeout: 1500,
        position: 'top',
      })
    } catch (err) {
      window.alert(err)
    }
  }

  // Action definitions
  const jobActions = computed(() => [
    {
      key: 'pause_job',
      label: t('pause_job'),
      labelCaption: t('pause_job_disabled'),
      icon: 'mdi-stop-circle-outline',
      isVisible: (job, userCanStopJob) => job.active && userCanStopJob,
      isDisabled: (job) => job.stage === 'created',
      action: pauseJob
    },
    {
      key: 'edit_time',
      label: t('update_time'),
      labelCaption: t('update_time_disabled'),
      icon: 'mdi-clock-edit-outline',
      isVisible: (job) => job.assigned_to && !job.active,
      isDisabled: (job) => job.stage === 'created',
      action: editJobTimeAction
    },
    {
      key: 'cancel_batch',
      label: t('cancel_active_batch'),
      labelCaption: t('cancel_active_batch_disabled'),
      icon: 'mdi-cube-off-outline',
      isVisible: (job) => job.assigned_to && !job.active,
      isDisabled: (job) => job.active_batch_qt === 0,
      action: cancelBatchAction
    },
    {
      key: 'edit_progress',
      label: t('update_progress'),
      labelCaption: t('update_progress_disabled'),
      icon: 'mdi-plus-minus-variant',
      isVisible: (job) => job.assigned_to && !job.active && !job.traceability_level,
      isDisabled: (job) => job.active_batch_qt > 0,
      action: editJobProgressAction
    },
    {
      key: 'reset_job',
      label: t('reset_job'),
      labelCaption: t('reset_job_disabled'),
      icon: 'mdi-backup-restore',
      isVisible: (job) => job.assigned_to && !job.active,
      isDisabled: (job) => job.stage === 'created' || job.active_batch_qt > 0,
      action: resetJobAction
    }
  ])

  const getVisibleJobActions = (job, userCanStopJob = false) => {
    return jobActions.value.filter(action =>
      action.isVisible(job, userCanStopJob)
    )
  }

    return {
    // Actions
    jobActions,
    getVisibleJobActions,

    // Modal state and management
    modals,
    closeModal,
    handleTimeModalSave,
    handleProgressModalSave,
    handleCancelBatchConfirm,
    handleResetJobConfirm,

    // Legacy state (for backward compatibility)
    editJobTime,
    editJobProgress,
    confirmCancelBatch,
    confirmResetJob,
    jobsTempData,

    // Legacy methods (for backward compatibility)
    resetEditing,
    forceProcessingTime,
    forceProgress,
    cancelBatch,
    resetJob
  }
}

/* ================================================
 * WORK ORDER ACTIONS
 * ================================================ */
export function useWorkOrderActions() {
  const { t } = useI18n()
  const store = useStore()

  // Work Order modal state
  const woModals = reactive({
    editProject: {
      show: false,
      data: {}
    },
    editQuantity: {
      show: false,
      data: {}
    },
    editStartDate: {
      show: false,
      data: {}
    },
    editDueDate: {
      show: false,
      data: {}
    },
    deleteWo: {
      show: false,
      data: {}
    },
    quantityRebalance: {
      show: false,
      data: {}
    }
  })

  // Action implementations
  const editProjectAction = (woData) => {
    woModals.editProject.data = {
      ...woData,
      temp_project_code: woData.project_code
    }
    woModals.editProject.show = true
  }

  const editQuantityAction = (woData) => {
    woModals.editQuantity.data = {
      ...woData,
      new_qt: woData.qt_planned,
      min_allowable_qt: Math.max(...woData.jobs.map(j => j.qt_completed + j.active_batch_qt))
    }
    woModals.editQuantity.show = true
  }

  const editStartDateAction = (woData) => {
    woModals.editStartDate.data = {
      ...woData,
      temp_date: woData.start_from
    }
    woModals.editStartDate.show = true
  }

  const editDueDateAction = (woData) => {
    woModals.editDueDate.data = {
      ...woData,
      temp_date: woData.due_by
    }
    woModals.editDueDate.show = true
  }

  const deleteWoAction = (woData) => {
    woModals.deleteWo.data = woData
    woModals.deleteWo.show = true
  }

  const closeWoModal = (modalType) => {
    if (woModals[modalType]) {
      woModals[modalType].show = false
      woModals[modalType].data = {}
    }
  }

  // Modal save handlers
  const handleProjectModalSave = async (projectData) => {
    try {
      const wo_update = {
        wo_key: projectData._key,
        new_project_code: projectData.temp_project_code
      }

      await store.dispatch('updateWorkOrder', wo_update)
      await store.dispatch('loadWorkOrderData', wo_update.wo_key)
      closeWoModal('editProject')

      Notify.create({
        message: t('project_update_success'),
        color: 'theme-green',
        timeout: 1500,
        position: 'top',
      })
    } catch (err) {
      console.error('Error updating project:', err)
    }
  }

  const handleQuantityModalSave = async (quantityData) => {
    // Instead of directly updating, show the quantity rebalance modal
    closeWoModal('editQuantity')

    woModals.quantityRebalance.data = {
      wo_key: quantityData._key,
      new_wo_qt: quantityData.new_qt,
      phase_data: computePhaseData(quantityData)
    }
    woModals.quantityRebalance.show = true
  }

  const handleDateModalSave = async (dateData, dateType) => {
    try {
      const wo_update = {
        wo_key: dateData._key
      }

      if (dateType === 'start_from') {
        wo_update.new_from_date = dateData.temp_date
      } else if (dateType === 'due_by') {
        wo_update.new_due_date = dateData.temp_date
      }

      await store.dispatch('updateWorkOrder', wo_update)
      await store.dispatch('loadWorkOrderData', wo_update.wo_key)
      closeWoModal(dateType === 'start_from' ? 'editStartDate' : 'editDueDate')

      Notify.create({
        message: t('date_update_success'),
        color: 'theme-green',
        timeout: 1500,
        position: 'top',
      })
    } catch (err) {
      console.error('Error updating date:', err)
    }
  }

  const handleDeleteWoConfirm = async () => {
    try {
      await api.delete(`work-order/${woModals.deleteWo.data._key}`)
      await store.dispatch('loadWorkOrders')
      closeWoModal('deleteWo')

      Notify.create({
        message: t('work_order.delete_success'),
        color: 'theme-green',
        timeout: 1500,
        position: 'top',
      })
    } catch (err) {
      console.error('Error deleting work order:', err)
    }
  }

  const handleQuantityRebalanceClose = () => {
    closeWoModal('quantityRebalance')
  }

  const workOrderActions = computed(() => [
    {
      key: 'edit_project',
      label: t('project_update'),
      icon: 'mdi-folder-edit-outline',
      isVisible: (wo) => wo.status !== 'closed' && !wo.active,
      isDisabled: () => false,
      action: editProjectAction
    },
    {
      key: 'edit_quantity',
      label: t('quantity.update'),
      icon: 'mdi-plus-minus-variant',
      isVisible: (wo) => wo.status !== 'closed',
      isDisabled: () => false,
      action: editQuantityAction
    },
    {
      key: 'edit_start_date',
      label: t('work_order.update_from_date'),
      icon: 'mdi-calendar-start',
      isVisible: (wo) => wo.status !== 'closed',
      isDisabled: () => false,
      action: editStartDateAction
    },
    {
      key: 'edit_due_date',
      label: t('work_order.update_due_date'),
      icon: 'mdi-calendar-end',
      isVisible: (wo) => wo.status !== 'closed',
      isDisabled: () => false,
      action: editDueDateAction
    },
    {
      key: 'delete_wo',
      label: t('work_order.delete_action'),
      icon: 'mdi-delete-outline',
      color: 'theme-red',
      isVisible: (wo) => wo.status === 'created',
      isDisabled: () => false,
      action: deleteWoAction
    }
  ])

  const getVisibleWorkOrderActions = (workOrder) => {
    return workOrderActions.value.filter(action =>
      action.isVisible(workOrder)
    )
  }

  return {
    workOrderActions,
    getVisibleWorkOrderActions,
    woModals,
    closeWoModal,
    handleProjectModalSave,
    handleQuantityModalSave,
    handleDateModalSave,
    handleDeleteWoConfirm,
    handleQuantityRebalanceClose
  }
}

/* ================================================
 * COMBINED ACTIONS
 * ================================================ */
export function useProductionAdminActions() {
  const jobActions = useJobActions()
  const workOrderActions = useWorkOrderActions()

  return {
    ...jobActions,
    ...workOrderActions
  }
}
