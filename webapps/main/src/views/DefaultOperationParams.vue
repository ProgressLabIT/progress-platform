<template>
  <SettingsSection
    v-slot="{ editMode }"
    :title="$t('views.defaultOperationParameters')"
    :save-fn="save"
    @cancel="cancel"
  >
    <ProcessParameters
      v-model="operationParameters"
      process-has-steps
      :edit-mode="editMode"
      dense
    />
  </SettingsSection>
</template>

<script setup>
import { cloneDeep } from 'lodash';
import { ref } from 'vue';
import ProcessParameters from '@/components/ProcessParameters.vue';
import SettingsSection from '@/components/SettingsSection.vue';
import { useConfigStore } from '@/stores/config';

const { config, updateAppConfig } = useConfigStore();

const operationParameters = ref(cloneDeep(config.operationParameters));
function cancel() {
  operationParameters.value = cloneDeep(config.operationParameters);
}
async function save() {
  await updateAppConfig({
    operationParameters: operationParameters.value,
  });
}
</script>
