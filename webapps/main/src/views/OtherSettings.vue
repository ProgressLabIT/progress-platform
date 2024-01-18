<template>
  <div class="fit q-pa-lg scroll">
    <div class="row item-center">
      <div class="text-h2 display q-pb-sm">Other</div>

      <q-space />

      <template v-if="editMode">
        <q-btn
          size="12px"
          color="theme-blue"
          class="q-ml-auto"
          :label="$t('save')"
          @click="save"
        />
        <q-btn
          size="12px"
          class="q-ml-md"
          color="theme-grey"
          :label="$t('cancel')"
          @click="cancel"
        />
      </template>
      <BaseTooltipIcon
        v-else
        icon="mdi-pencil"
        :tooltip="$capitalize($t('edit'))"
        :color="$theme.blue"
        @icon-click="editMode = true"
      />
    </div>

    <q-input
      v-model.number="configModel.operatorCost"
      type="number"
      :label="$t('settings.operatorCost.label')"
      :hint="$capitalize($t('user.hourly_cost'))"
      :readonly="!editMode"
      :rules="[(val) => val >= 0 || $t('settings.operatorCost.mustBePositive')]"
    />

    <q-toggle
      v-model="configModel.allowUnassignedJobs"
      :label="$t('settings.allowUnassignedJobs')"
      :disable="!editMode"
      class="q-mt-md"
    />
  </div>
</template>

<script setup>
import { cloneDeep } from 'lodash';
import { ref } from 'vue';
import BaseTooltipIcon from '@/components/BaseTooltipIcon.vue';
import { useConfigStore } from '@/stores/config';

const { config, updateAppConfig } = useConfigStore();

const editMode = ref(false);
const configModel = ref(cloneDeep(config));
function cancel() {
  editMode.value = false;
  configModel.value = cloneDeep(config);
}
async function save() {
  await updateAppConfig({
    operatorCost: configModel.value.operatorCost,
    allowUnassignedJobs: configModel.value.allowUnassignedJobs,
  });
  editMode.value = false;
}
</script>
