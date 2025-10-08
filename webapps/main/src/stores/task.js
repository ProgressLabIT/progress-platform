import { defineStore } from 'pinia'
import { Notify, Dialog } from 'quasar'
import { api } from '@/boot/axios.js'
import { sendEvent } from '@/composables/event.js'
import { useStorePersistence } from '@/composables/reStore.js'

export const useTaskStore = defineStore('task', {
  state: () => ({
    tasks: [],
    activeTaskKey: null,
    loading: false,
    ignoredEntities: [], // Entities ignored for current active task
  }),

  getters: {
    getTaskByKey: (state) => (key) => {
      return state.tasks.find((task) => task._key === key)
    },

    getActiveTask: (state) => {
      return state.tasks.find((task) => task._key === state.activeTaskKey)
    },

    getTasksByStatus: (state) => (status) => {
      return state.tasks.filter((task) => task.status === status)
    },

    getTasksByAssignee: (state) => (userKey) => {
      return state.tasks.filter((task) =>
        task.assigned_to && task.assigned_to.includes(userKey)
      )
    },

    isEntityIgnored: (state) => (entityType, entityKey) => {
      const entityId = `${entityType}:${entityKey}`
      return state.ignoredEntities.includes(entityId)
    },
  },

  actions: {
    async fetchTasks(searchParams = {}) {
      this.loading = true
      try {
        const { data } = await api.get('/task', {
          params: searchParams
        })
        this.tasks = data
        return data
      } catch (error) {
        console.error('Error fetching tasks:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    async getTaskData(taskKey) {
      try {
        const { data } = await api.get(`/task/${taskKey}`)
        return data
      } catch (error) {
        console.error('Error fetching task data:', error)
        throw error
      }
    },

    async createTask(taskData) {
      try {
        // Task creation is handled through the event system
        const eventData = {
          task_type_key: taskData.type,
          title: taskData.title,
          description: taskData.description,
          assigned_to: taskData.assigned_to || [],
          start_from: taskData.start_from || null,
          due_by: taskData.due_by || null,
        }
        const response = await sendEvent({
          event_type: 'TASK_CREATED',
          event_data: eventData
        })
        return response.data
      } catch (error) {
        console.error('Error creating task:', error)
        throw error
      }
    },

    async completeTask(taskKey) {
      try {
        const response = await sendEvent({ event_type: 'TASK_COMPLETED', event_data: { task_key: taskKey } })
        Notify.create({
          message: 'Task completed successfully',
          color: 'theme-green',
          timeout: 2000,
          position: 'top',
        })
        return response.data
      } catch (error) {
        console.error('Error completing task:', error)
        Notify.create({
          message: 'Error completing task',
          color: 'theme-red',
          timeout: 3000,
          position: 'top',
        })
      }
      finally {
        if (this.activeTaskKey === taskKey) {
          this.deactivateTask()
        }
      }
    },

    async completeTaskWithConfirmation(taskKey, t) {
      return new Promise((resolve) => {
        Dialog.create({
          title: t('task_complete'),
          message: t('task_complete_confirmation'),
          color: 'theme-green',
          ok: {
            label: t('complete'),
            color: 'theme-green'
          },
          cancel: {
            label: t('cancel'),
            color: 'theme-grey'
          }
        }).onOk(async () => {
          try {
            await this.completeTask(taskKey)
            resolve(true)
          } catch (error) {
            resolve(false)
          }
        }).onCancel(() => {
          resolve(false)
        })
      })
    },

    async dismissTaskWithConfirmation(t) {
      return new Promise((resolve) => {
        Dialog.create({
          title: t('dismiss_task'),
          message: t('dismiss_task_confirmation'),
          color: 'theme-orange',
          ok: {
            label: t('dismiss'),
            color: 'theme-orange'
          },
          cancel: {
            label: t('cancel'),
            color: 'theme-grey'
          }
        }).onOk(() => {
          this.deactivateTask()
          resolve(true)
        }).onCancel(() => {
          resolve(false)
        })
      })
    },

    async reopenTaskWithConfirmation(taskKey, t) {
      return new Promise((resolve) => {
        Dialog.create({
          title: t('task_reopen'),
          message: t('task_reopen_confirmation') || 'Are you sure you want to reopen this task?',
          color: 'theme-green',
          ok: {
            label: t('reopen'),
            color: 'theme-green'
          },
          cancel: {
            label: t('cancel'),
            color: 'theme-grey'
          }
        }).onOk(async () => {
          try {
            await sendEvent({
              event_type: 'TASK_REOPENED',
              event_data: {
                task_key: taskKey,
              }
            })

            Notify.create({
              message: t('task_reopen_success') || 'Task reopened successfully',
              color: 'theme-green',
              timeout: 2000,
              position: 'top',
            })
            resolve(true)
          } catch (error) {
            console.error('Error reopening task:', error)
            Notify.create({
              message: t('errors.status_update_err') || 'Error reopening task',
              color: 'theme-red',
              timeout: 3000,
              position: 'top',
            })
            resolve(false)
          }
        }).onCancel(() => {
          resolve(false)
        })
      })
    },

    async cancelTaskWithConfirmation(taskKey, t) {
      return new Promise((resolve) => {
        Dialog.create({
          title: t('task_cancel'),
          message: t('task_cancel_confirmation'),
        }).onOk(async () => {
          try {
            await sendEvent({
              event_type: 'TASK_CANCELED',
              event_data: {
                task_key: taskKey,
              }
            })

            Notify.create({
              message: t('task_cancel_success') || 'Task cancelled successfully',
              color: 'theme-green',
              timeout: 2000,
              position: 'top',
            })
            resolve(true)
          } catch (error) {
            console.error('Error cancelling task:', error)
            Notify.create({
              message: t('errors.cancel_err') || 'Error cancelling task',
              color: 'theme-red',
              timeout: 3000,
              position: 'top',
            })
            resolve(false)
          }
        }).onCancel(() => {
          resolve(false)
        })
      })
    },

    async toggleTaskStatusWithConfirmation(task, t) {
      const isClosing = task.status === 'open'
      if (isClosing) {
        return await this.completeTaskWithConfirmation(task._key, t)
      } else {
        return await this.reopenTaskWithConfirmation(task._key, t)
      }
    },

    async refreshTaskData(taskKey) {
      try {
        const { data } = await api.get(`/task/${taskKey}`)
        // Update the task in the local tasks array
        const taskIndex = this.tasks.findIndex(task => task._key === taskKey)
        if (taskIndex !== -1) {
          this.tasks[taskIndex] = data
        }
        return data
      } catch (error) {
        console.error('Error refreshing task data:', error)
        throw error
      }
    },

    async deleteTask(taskKey) {
      try {
        await api.delete(`/task/${taskKey}`)
        // Remove task from local state
        const taskIndex = this.tasks.findIndex(task => task._key === taskKey)
        if (taskIndex !== -1) {
          this.tasks.splice(taskIndex, 1)
        }
      } catch (error) {
        console.error('Error deleting task:', error)
        throw error
      }
    },

    // Task activation/deactivation methods
    setActiveTask(taskKey) {
      const oldTaskKey = this.activeTaskKey
      this.activeTaskKey = taskKey

      // Clear ignored entities when switching tasks
      if (oldTaskKey !== taskKey) {
        this.clearIgnoredEntities()
      }
    },

    deactivateTask() {
      this.activeTaskKey = null
      this.clearIgnoredEntities()
    },

    // Ignored entities management
    addIgnoredEntity(entityType, entityKey) {
      const entityId = `${entityType}:${entityKey}`
      if (!this.ignoredEntities.includes(entityId)) {
        this.ignoredEntities.push(entityId)
      }
    },

    removeIgnoredEntity(entityType, entityKey) {
      const entityId = `${entityType}:${entityKey}`
      const index = this.ignoredEntities.indexOf(entityId)
      if (index > -1) {
        this.ignoredEntities.splice(index, 1)
      }
    },

    clearIgnoredEntities() {
      this.ignoredEntities = []
    },

    getIgnoredEntities() {
      return [...this.ignoredEntities]
    },
  },
})

// Helper function to set up task store persistence
export function useTaskStorePersistence() {
  const taskStore = useTaskStore()

  return useStorePersistence(taskStore, {
    excludeKeys: ['loading'], // Don't persist loading state
    expirationMinutes: 30,    // 30 minute session timeout
  })
}
