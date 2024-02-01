<template>
  <SettingsSection
    v-slot="{ editMode }"
    :title="$t('views.otherSettings')"
    @cancel="cancel"
    @save="save"
  >
    <div class="column q-gutter-y-lg">
      <q-input
        v-model.number="configModel.operatorCost"
        type="number"
        :label="$t('settings.operatorCost.label')"
        :hint="$capitalize($t('user.hourly_cost'))"
        :readonly="!editMode"
        :rules="[
          (val) => val >= 0 || $t('settings.operatorCost.mustBePositive'),
        ]"
        filled
        style="max-width: 400px"
      />

      <q-toggle
        v-model="configModel.allowUnassignedJobs"
        :label="$t('settings.allowUnassignedJobs')"
        :disable="!editMode"
      />

      <q-toggle
        v-model="configModel.allowIndependentReorderingOfJobQueues"
        :label="$t('settings.allowIndependentReorderingOfJobQueues')"
        :disable="!editMode"
      />
    </div>
  </SettingsSection>
</template>

<script setup>
import { cloneDeep } from 'lodash';
import { ref } from 'vue';
import SettingsSection from '@/components/SettingsSection.vue';
import { useConfigStore } from '@/stores/config';

const { config, updateAppConfig } = useConfigStore();

const configModel = ref(cloneDeep(config));
function cancel() {
  configModel.value = cloneDeep(config);
}
async function save() {
  await updateAppConfig({
    operatorCost: configModel.value.operatorCost,
    allowUnassignedJobs: configModel.value.allowUnassignedJobs,
    allowIndependentReorderingOfJobQueues:
      configModel.value.allowIndependentReorderingOfJobQueues,
  });
}
</script>
