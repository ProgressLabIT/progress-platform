<template>
  <SettingsSection
    v-slot="{ editMode }"
    :title="$t('views.serialFieldSettings')"
    :save-fn="save"
    @cancel="cancel"
  >
    <SerialFieldLibrary
      :field_list="serialFields"
      process-has-steps
      :edit-mode="editMode"
      dense
    />
  </SettingsSection>
</template>

<script setup>
import { cloneDeep } from 'lodash';
import { ref } from 'vue';
import SettingsSection from '@/components/SettingsSection.vue';
import SerialFieldLibrary from '@/components/settings/SerialFieldLibrary.vue';
import { useConfigStore } from '@/stores/config';

const { config, updateAppConfig } = useConfigStore();

const serialFields = ref(cloneDeep(config.serialFields));
function cancel() {
  serialFields.value = cloneDeep(config.serialFields);
}
async function save() {
  await updateAppConfig({
    serialFields: serialFields.value,
  });
}
</script>
