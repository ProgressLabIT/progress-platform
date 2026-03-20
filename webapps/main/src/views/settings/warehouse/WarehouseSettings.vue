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

      <div class="text-body1 q-mt-xl">
        {{ $t('settings.mandatoryReasonForMovementTypes') }}
      </div>
      <div class="row q-gutter-x-lg">
        <div
          v-for="movement in ['receipt', 'shipment', 'transfer', 'adjustment']"
          :key="movement"
          class="col-auto">
          <q-checkbox
            :model-value="(configModel.mandatoryReasonForMovementTypes ?? []).includes(movement)"
            :label="$t(`warehouse.movement.${movement}`)"
            :disable="!editMode"
            @update:model-value="updateMandatoryReasonForMovementTypes(movement)"
          />
        </div>
      </div>
    </template>

    <!-- Label template assignment (independent of inventory management toggle) -->
    <BaseAutocompleteTemplate
      :label="$t('settings.productLabelTemplate')"
      :value="configModel.productLabelTemplate"
      key-only
      clearable
      :disable="!editMode"
      :dense="false"
      @select="(template) => (configModel.productLabelTemplate = template)"
    />
    <BaseAutocompleteTemplate
      :label="$t('settings.positionLabelTemplate')"
      :value="configModel.positionLabelTemplate"
      key-only
      clearable
      :disable="!editMode"
      :dense="false"
      @select="(template) => (configModel.positionLabelTemplate = template)"
    />
    </div>
  </SettingsSection>
</template>

<script setup>
import { cloneDeep } from 'lodash';
import { ref } from 'vue';
import BaseAutocompletePosition from '@/components/BaseAutocompletePosition.vue';
import BaseAutocompleteTemplate from '@/components/BaseAutocompleteTemplate.vue';
import LoadingSignal from '@/components/LoadingSignal.vue';
import SettingsSection from '@/components/SettingsSection.vue';
import { useConfigStore } from '@/stores/config';

const { isLoading, config, updateAppConfig } = useConfigStore();

const configModel = ref(cloneDeep(config));

function cancel() {
  configModel.value = cloneDeep(config);
}

async function save() {
  const update = {
    enableInventoryManagement: configModel.value.enableInventoryManagement,
    defaultProductionPosition: configModel.value.defaultProductionPosition,
    defaultConsumptionPosition: configModel.value.defaultConsumptionPosition,
    productLabelTemplate: configModel.value.productLabelTemplate,
    positionLabelTemplate: configModel.value.positionLabelTemplate,
    mandatoryReasonForMovementTypes: configModel.value.mandatoryReasonForMovementTypes,
  }
  console.log(update);
  await updateAppConfig(update);
}

function updateMandatoryReasonForMovementTypes(movement) {
  if (!configModel.value.mandatoryReasonForMovementTypes) {
    configModel.value.mandatoryReasonForMovementTypes = [];
  }
  if (configModel.value.mandatoryReasonForMovementTypes.includes(movement)) {
    configModel.value.mandatoryReasonForMovementTypes.splice(configModel.value.mandatoryReasonForMovementTypes.indexOf(movement), 1);
  } else {
    configModel.value.mandatoryReasonForMovementTypes.push(movement);
  }
  console.log(configModel.value.mandatoryReasonForMovementTypes);
}
</script>
