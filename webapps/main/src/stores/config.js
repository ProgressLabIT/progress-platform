import { defineStore } from 'pinia';
import { reactive, ref } from 'vue';
import { api } from '@/boot/axios';

export const useConfigStore = defineStore('config', () => {
  const configDefaults = {
    companyName: 'Progress Platform',
    companyLogo: '/progresslab.svg',
    operationParameters: {
      max_offline: 60,
      parallel_job_allowed: true,
      display_job_timer: false,
      step_check: false,
      step_check_force_order: false,
      production_batch_qt: 1,
      auto_new_batch: true,
      unsupervised_work_allowed: false,
      std_processing_time: 60,
    },
    serialFields: [],
    operatorCost: 0,
    allowUnassignedJobs: true,
    allowIndependentReorderingOfJobQueues: false,
    allowSerialDelete: false,
    enableInventoryManagement: false,
    allowSerialCodeEdit: false,
    allowPositionDelete: true,
    printers: [],
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
    if (appConfig.default_operation_parameters) {
      config.operationParameters = appConfig.default_operation_parameters;
    }
    if (appConfig.serial_fields) {
      config.serialFields = appConfig.serial_fields;
    }
    if (appConfig.printers) {
      config.printers = appConfig.printers;
    }
    if (typeof appConfig.operator_cost === 'number') {
      config.operatorCost = appConfig.operator_cost;
    }
    if (typeof appConfig.show_unassigned_jobs_to_operators === 'boolean') {
      config.allowUnassignedJobs = appConfig.show_unassigned_jobs_to_operators;
    }
    if (
      typeof appConfig.allow_independent_reordering_of_job_queues === 'boolean'
    ) {
      config.allowIndependentReorderingOfJobQueues =
        appConfig.allow_independent_reordering_of_job_queues;
    }
    if (typeof appConfig.allow_serial_delete === 'boolean') {
      config.allowSerialDelete = appConfig.allow_serial_delete;
    }
    if (typeof appConfig.enable_inventory_management === 'boolean') {
      config.enableInventoryManagement = appConfig.enable_inventory_management;
    }
    if (typeof appConfig.allow_serial_code_edit === 'boolean') {
      config.allowSerialCodeEdit = appConfig.allow_serial_code_edit;
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
      operation_parameters: configToUpdate.operationParameters,
      serial_fields: configToUpdate.serialFields,
      printers: configToUpdate.printers,
      operator_cost: configToUpdate.operatorCost,
      show_unassigned_jobs_to_operators: configToUpdate.allowUnassignedJobs,
      allow_independent_reordering_of_job_queues:
        configToUpdate.allowIndependentReorderingOfJobQueues,
      allow_serial_delete: configToUpdate.allowSerialDelete,
      allow_serial_code_edit: configToUpdate.allowSerialCodeEdit,
      enable_inventory_management: configToUpdate.enableInventoryManagement,
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
