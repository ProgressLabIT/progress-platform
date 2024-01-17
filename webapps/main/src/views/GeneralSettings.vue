<template>
  <LoadingSignal v-if="isLoading" />
  <div v-else class="row full-height">
    <div class="full-height column col-3">
      <div class="col-2 full-height column">
        <q-tabs vertical color="white" class="col">
          <q-route-tab
            v-for="tab in sections"
            :key="tab"
            :to="{ name: tab }"
            class="display"
          >
            {{ $t(`views.${tab}`) }}
          </q-route-tab>
        </q-tabs>

        <q-space />

        <q-btn
          v-if="!editMode"
          :loading="isLoading"
          :label="$t('edit')"
          color="theme-blue"
          class="q-ma-md"
          @click="editMode = true"
        />
        <div v-else class="q-pa-md column">
          <q-btn
            :label="$t('save')"
            color="theme-green"
            class="q-mb-sm"
            @click="save"
          />

          <q-btn :label="$t('cancel')" color="theme-grey" @click="cancel" />
        </div>
      </div>
    </div>

    <q-separator vertical />

    <div class="col full-height">
      <router-view v-model="configModel" :edit-mode="editMode" />
    </div>
  </div>
</template>

<script setup>
import { cloneDeep } from 'lodash';
import { storeToRefs } from 'pinia';
import { ref } from 'vue';
import LoadingSignal from '@/components/LoadingSignal.vue';
import { useConfigStore } from '@/stores/config';

const sections = ['companyDetails', 'defaultPhaseParams'];

const configStore = useConfigStore();
const { isLoading, config } = storeToRefs(configStore);
const { updateAppConfig } = configStore;

const editMode = ref(false);
const configModel = ref(cloneDeep(config.value));
function cancel() {
  editMode.value = false;
  configModel.value = cloneDeep(config.value);
}
async function save() {
  await updateAppConfig(configModel.value);
  editMode.value = false;
}
</script>
