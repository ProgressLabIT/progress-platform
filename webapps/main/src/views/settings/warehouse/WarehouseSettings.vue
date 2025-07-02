<template>
  <LoadingSignal v-if="isLoading" />
  <SettingsSection
    v-else
    v-slot="{ editMode }"
    title="Warehouse Settings"
    :save-fn="save"
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
      <BaseAutocompletePosition
        :label="$t('settings.defaultProductionPosition')"
        :value="configModel.defaultProductionPosition"
        key-only
        clearable
        :disable="!editMode"
        @select="(position) => (configModel.defaultProductionPosition = position)"
      />
      <!-- Default consumption position -->
      <BaseAutocompletePosition
        :label="$t('settings.defaultConsumptionPosition')"
        :value="configModel.defaultConsumptionPosition"
        key-only
        clearable
        :disable="!editMode"
        @select="(position) => (configModel.defaultConsumptionPosition = position)"
      />
      <!-- Product label template -->
      <!-- <BaseAutocompleteTemplate
        :label="$t('settings.productLabelTemplate')"
        :value="configModel.productLabelTemplate"
        key-onlyx
        clearable
        :disable="!editMode"
        :dense="false"
        @select="(template) => (configModel.productLabelTemplate = template)"
      /> -->
      <!-- Position label template -->
      <!-- <BaseAutocompleteTemplate
        :label="$t('settings.positionLabelTemplate')"
        :value="configModel.positionLabelTemplate"
        clearable
        key-only
        :dense="false"
        :disable="!editMode"
          @select="(template) => (configModel.positionLabelTemplate = template)"
        /> -->
      </template>
    </div>
  </SettingsSection>
</template>

<script setup>
import { cloneDeep } from 'lodash';
import { ref } from 'vue';
import BaseAutocompletePosition from '@/components/BaseAutocompletePosition.vue';
import LoadingSignal from '@/components/LoadingSignal.vue';
import SettingsSection from '@/components/SettingsSection.vue';
import { useConfigStore } from '@/stores/config';

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
