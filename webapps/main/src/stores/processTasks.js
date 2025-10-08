import { defineStore } from 'pinia';
import { api } from '@/boot/axios';
import { Notify } from 'quasar';


export const useProcessTasksStore = defineStore('processTasks', {
  state: () => ({
    saved: [],
    temp: [],
  }),
  actions: {
    async fetchProcessTasks(product_key) {
      try {
      const response = await api.get(`/product/${product_key}/process/tasks`);
        this.saved = response.data;
        this.temp = response.data;
      } catch (error) {
        console.error(error);
        Notify.create({
          message: 'Error fetching process tasks: ' + error.response.data.detail,
          color: 'theme-red',
          timeout: 3000,
          position: 'top',
        });
      }
    },
    async saveTempProcessTasks(product_key, tasks) {
      try {
        const response = await api.put(`/product/${product_key}/process/tasks`, tasks);
        this.saved = response.data.detail;
        this.temp = response.data.detail;
        Notify.create({
          message: 'Process tasks saved successfully',
          color: 'theme-green',
          timeout: 2000,
          position: 'top',
        });
      } catch (error) {
        console.error(error);
        Notify.create({
          message: 'Error saving process tasks: ' + error.response.data.detail,
          color: 'theme-red',
          timeout: 3000,
          position: 'top',
        });
      }
    }
  },
});
