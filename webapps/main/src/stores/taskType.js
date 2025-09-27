import { defineStore } from 'pinia'
import { api } from '@/boot/axios.js'

export const useTaskTypeStore = defineStore('taskType', {
  state: () => ({
    taskTypes: [],
    loading: false,
  }),

  getters: {
    getTaskTypeByKey: (state) => (key) => {
      return state.taskTypes.find((tt) => tt._key === key)
    },

    getActiveTaskTypes: (state) => {
      return state.taskTypes.filter((tt) => tt.active)
    },

    getTaskTypeByName: (state) => (name) => {
      return state.taskTypes.find((tt) => tt.name === name)
    },
  },

  actions: {
    async fetchTaskTypes(activeOnly = false) {
      this.loading = true
      try {
        const { data } = await api.get('/task-type', {
          params: { active_only: activeOnly }
        })
        this.taskTypes = data
      } catch (error) {
        console.error('Error fetching task types:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    async createTaskType(taskTypeData) {
      try {
        const { data } = await api.post('/task-type', taskTypeData)
        await this.fetchTaskTypes() // Refresh the list
        return data
      } catch (error) {
        console.error('Error creating task type:', error)
        throw error
      }
    },

    async updateTaskType(taskTypeData) {
      try {
        /*
         * taskTypeData includes `print_templates`, which is not part of the
         * task type model in the backend and the property will be ignored.
         * Templates must be updated separately.
         */

        const templateUpdates = (taskTypeData.print_templates || [])
          .filter(({ temp, trash }) => temp || trash)
          .map(({ _key, temp }) => ({
            type: temp ? 'add' : 'remove',
            context: 'task_type',
            context_key: taskTypeData._key,
            template_key: _key,
          }))

        const requests = [api.put(`/task-type/${taskTypeData._key}`, taskTypeData)]

        if (templateUpdates.length > 0) {
          requests.push(api.post('update-template-assignments', templateUpdates))
        }

        await Promise.all(requests)

        await this.fetchTaskTypes() // Refresh the list
      } catch (error) {
        console.error('Error updating task type:', error)
        throw error
      }
    },

    async deleteTaskType(taskTypeKey) {
      try {
        await api.delete(`/task-type/${taskTypeKey}`)
        await this.fetchTaskTypes() // Refresh the list
      } catch (error) {
        console.error('Error deleting task type:', error)
        throw error
      }
    },
  },
})
