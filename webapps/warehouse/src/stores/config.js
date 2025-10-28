import { defineStore } from 'pinia';
import { reactive, ref } from 'vue';
import { api } from 'src/boot/axios';

export const useConfigStore = defineStore('config', () => {
  const configDefaults = {
    companyName: 'Progress Platform',
    companyLogo: '/progresslab.svg',
    operationParameters: {
      max_offline: 60,
      parallel_job_allowed: true,
      display_phase_progress: false,
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
    mandatoryReasonForMovementTypes: [],
    enableInventoryManagement: false,
    defaultProductionPosition: null,
    defaultConsumptionPosition: null,
    productLabelTemplate: null,
    positionLabelTemplate: null,
    printers: [],
  };

  const isLoading = ref(true);
  const config = reactive({
    ...configDefaults,
  });

  async function loadAppConfig() {
    const { data } = await api.get('config');
    const appConfig = data.detail;

    // Handle fields that don't need strict type checks
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

    // Map API fields to config properties with type validation
    const configMappings = [
      { apiField: 'operator_cost', target: 'operatorCost', type: 'number' },
      { apiField: 'show_unassigned_jobs_to_operators', target: 'allowUnassignedJobs', type: 'boolean' },
      { apiField: 'allow_independent_reordering_of_job_queues', target: 'allowIndependentReorderingOfJobQueues', type: 'boolean' },
      { apiField: 'allow_serial_delete', target: 'allowSerialDelete', type: 'boolean' },
      { apiField: 'mandatory_reason_for_movement_types', target: 'mandatoryReasonForMovementTypes', type: 'object' },
      { apiField: 'enable_inventory_management', target: 'enableInventoryManagement', type: 'boolean' },
      { apiField: 'default_production_position', target: 'defaultProductionPosition', type: 'string' },
      { apiField: 'default_consumption_position', target: 'defaultConsumptionPosition', type: 'string' },
      { apiField: 'product_label_template', target: 'productLabelTemplate', type: 'string' },
      { apiField: 'position_label_template', target: 'positionLabelTemplate', type: 'string' },
    ];

    for (const { apiField, target, type } of configMappings) {
      const value = appConfig[apiField];
      if (value !== undefined && typeof value === type) {
        config[target] = value;
      }
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
        companyLogo !== null ? formData : undefined
      );
      const newPath = data.detail.file_path;
      configToUpdate.companyLogo = newPath || configDefaults.companyLogo;
    }

    await api.patch('config', {
      company_name: configToUpdate.companyName,
      operation_parameters: configToUpdate.operationParameters,
      serial_fields: configToUpdate.serialFields,
      operator_cost: configToUpdate.operatorCost,
      show_unassigned_jobs_to_operators: configToUpdate.allowUnassignedJobs,
      allow_independent_reordering_of_job_queues:
        configToUpdate.allowIndependentReorderingOfJobQueues,
      allow_serial_delete: configToUpdate.allowSerialDelete,
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
