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
    // If undefined, don't update. If null, delete. Otherwise, update.
    const { companyLogo } = configToUpdate;
    if (companyLogo !== undefined) {
      const formData = new FormData();
      formData.append('file', companyLogo);
      const { data } = await api.put(
        'config/company_logo/file',
        companyLogo !== null ? formData : undefined,
      );
      const newPath = data.detail.file_path;
      configToUpdate.companyLogo = newPath || configDefaults.companyLogo;
    }

    await api.patch('config', {
      company_name: configToUpdate.companyName,
    });

    Object.assign(config, configToUpdate);
  }

  return {
    config,
    configDefaults,
    isLoading,
    updateAppConfig,
  };
});
