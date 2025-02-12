<template>
  <LoadingSignal v-if="isLoading" />
  <SettingsSection
    v-else
    title="Warehouse Settings"
    v-slot="{ editMode }"
    :saveFn="save"
    @cancel="cancel"
  >
    <div class="column q-gutter-y-md">
      <q-toggle
        v-model="configModel.enableInventoryManagement"
        :label="$t('settings.enableInventoryManagement')"
        :disable="!editMode"
    />

    <template v-if="configModel.enableInventoryManagement">
      <!-- Default production position -->
      <BaseAutocompletePositions
        :label="$t('settings.defaultProductionPosition')"
        :value="configModel.defaultProductionPosition"
        key-only
        :disable="!editMode"
        @select="(position) => (configModel.defaultProductionPosition = position)"
      />
      <!-- Default consumption position -->
      <BaseAutocompletePositions
        :label="$t('settings.defaultConsumptionPosition')"
        :value="configModel.defaultConsumptionPosition"
        key-only
        :disable="!editMode"
        @select="(position) => (configModel.defaultConsumptionPosition = position)"
      />
      <!-- Product label template -->
      <BaseAutocompleteTemplate
        :label="$t('settings.productLabelTemplate')"
        :value="configModel.productLabelTemplate"
        key-only
        :disable="!editMode"
        :dense="false"
        @select="(template) => (configModel.productLabelTemplate = template)"
      />
      <!-- Position label template -->
      <BaseAutocompleteTemplate
        :label="$t('settings.positionLabelTemplate')"
        :value="configModel.positionLabelTemplate"
        key-only
        :dense="false"
        :disable="!editMode"
          @select="(template) => (configModel.positionLabelTemplate = template)"
        />
      </template>
    </div>
  </SettingsSection>
</template>

<script setup>
import { cloneDeep } from 'lodash';
import { ref } from 'vue';
import LoadingSignal from '@/components/LoadingSignal.vue';
import { useConfigStore } from '@/stores/config';
import SettingsSection from '@/components/SettingsSection.vue';
import BaseAutocompleteTemplate from '@/components/BaseAutocompleteTemplate.vue';
import BaseAutocompletePositions from '@/components/BaseAutocompletePositions.vue';

const { isLoading, config, updateAppConfig } = useConfigStore();

const configModel = ref(cloneDeep(config));

function cancel() {
  configModel.value = cloneDeep(config);
}

async function save() {
  await updateAppConfig({
    enableInventoryManagement: configModel.value.enableInventoryManagement,
    defaultProductionPosition: configModel.value.defaultProductionPosition,
    defaultConsumptionPosition: configModel.value.defaultConsumptionPosition,
    productLabelTemplate: configModel.value.productLabelTemplate,
    positionLabelTemplate: configModel.value.positionLabelTemplate,
  });
}

</script>
