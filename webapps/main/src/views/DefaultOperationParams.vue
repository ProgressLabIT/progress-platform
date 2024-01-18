<template>
  <div class="fit q-pa-lg scroll">
    <div class="row item-center">
      <div class="text-h2 display q-pb-sm">Default Operation Parameters</div>

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

    <ProcessParameters
      v-model="operationParameters"
      process-has-steps
      :edit-mode="editMode"
      dense
    />
  </div>
</template>

<script setup>
import { cloneDeep } from 'lodash';
import { ref } from 'vue';
import BaseTooltipIcon from '@/components/BaseTooltipIcon.vue';
import ProcessParameters from '@/components/ProcessParameters.vue';
import { useConfigStore } from '@/stores/config';

const { config, updateAppConfig } = useConfigStore();

const editMode = ref(false);
const operationParameters = ref(cloneDeep(config.operationParameters));
function cancel() {
  editMode.value = false;
  operationParameters.value = cloneDeep(config.operationParameters);
}
async function save() {
  await updateAppConfig({
    operationParameters: operationParameters.value,
  });
  editMode.value = false;
}
</script>
