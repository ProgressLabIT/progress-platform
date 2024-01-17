import { defineStore } from 'pinia';
import { reactive, ref } from 'vue';
import { api } from '@/boot/axios';

export const useConfigStore = defineStore('config', () => {
  const configDefaults = {
    companyName: 'Progress Platform',
    companyLogo: '/progresslab.svg',
  };

  const isLoading = ref(true);
  const config = reactive({
    ...configDefaults,
  });

  async function loadAppConfig() {
    const { data } = await api.get('config');
    const appConfig = data.detail;

    if (appConfig.company_name) {
      config.companyName = appConfig.company_name;
    }
    if (appConfig.company_logo) {
      config.companyLogo = appConfig.company_logo;
    }
  }
  void (async () => {
    try {
      isLoading.value = true;
      await loadAppConfig();
      isLoading.value = false;
    } catch (error) {
      console.error('Failed to load app config, will use defaults', error);
    }
  })();

  async function updateAppConfig(configToUpdate) {
    if (configToUpdate.companyLogo) {
      const formData = new FormData();
      formData.append('file', configToUpdate.companyLogo);
      const { data } = await api.put('config/company_logo/file', formData);
      configToUpdate.companyLogo = data.detail.file_path;
    }

    await api.patch('config', {
      company_name: configToUpdate.companyName,
    });

    Object.assign(config, configToUpdate);
  }

  return {
    config,
    isLoading,
    updateAppConfig,
  };
});
