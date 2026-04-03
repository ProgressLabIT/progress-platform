<template>
  <SettingsSection
    v-slot="{ editMode }"
    :title="$t('views.printersLibrary')"
    :save-fn="save"
    @cancel="cancel"
  >
    <PrintersTable
      v-model:printer_list="printers"
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
import PrintersTable from '@/components/settings/printers/PrintersTable.vue';
import { useConfigStore } from '@/stores/config';

const { config, updateAppConfig } = useConfigStore();

const printers = ref(cloneDeep(config.printers));
function cancel() {
  printers.value = cloneDeep(config.printers);
}
async function save() {
  await updateAppConfig({
    printers: printers.value,
  });
}
</script>
