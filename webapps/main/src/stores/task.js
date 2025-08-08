import { defineStore } from 'pinia'
import { api } from '@/boot/axios.js'
import { sendEvent } from '@/composables/event.js'

export const useTaskStore = defineStore('task', {
  state: () => ({
    tasks: [],
    loading: false,
  }),

  getters: {
    getTaskByKey: (state) => (key) => {
      return state.tasks.find((task) => task._key === key)
    },

    getTasksByStatus: (state) => (status) => {
      return state.tasks.filter((task) => task.status === status)
    },

    getTasksByAssignee: (state) => (userKey) => {
      return state.tasks.filter((task) =>
        task.assigned_to && task.assigned_to.includes(userKey)
      )
    },

    getPendingTasks: (state) => {
      return state.tasks.filter((task) => task.status === 'pending')
    },

    getCompletedTasks: (state) => {
      return state.tasks.filter((task) => task.status === 'completed')
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

    async appendTasks(searchParams = {}) {
      try {
        const { data } = await api.get('/task', {
          params: searchParams
        })
        // Append new tasks, avoiding duplicates
        data.forEach(newTask => {
          const existingIndex = this.tasks.findIndex(task => task._key === newTask._key)
          if (existingIndex === -1) {
            this.tasks.push(newTask)
          }
        })
        return data
      } catch (error) {
        console.error('Error appending tasks:', error)
        throw error
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
        await this.fetchTasks() // Refresh the list
        return response.data
      } catch (error) {
        console.error('Error creating task:', error)
        throw error
      }
    },

    async updateTask(taskKey, updateData) {
      try {
        const { data } = await api.patch(`/task/${taskKey}`, updateData)
        // Update task in local state
        const taskIndex = this.tasks.findIndex(task => task._key === taskKey)
        if (taskIndex !== -1) {
          this.tasks[taskIndex] = { ...this.tasks[taskIndex], ...updateData }
        }
        return data
      } catch (error) {
        console.error('Error updating task:', error)
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
  },
})
