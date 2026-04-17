<template>
  <LoadingSignal v-if="isLoading" />
  <q-splitter v-else v-model="splitter_model" class="absolute-full">
    <template #before>
      <div class="full-height column">
        <div
          class="row q-mt-md q-px-lg q-py-sm text-h6 text-uppercase weight-bold"
        >
          <div class="col ellipsis">
            {{ $t('settings.section') }}
          </div>
        </div>

        <q-separator />

        <q-scroll-area class="col">
          <div
            v-for="(section, index) in sections"
            :key="section"
            class="pointer q-px-lg q-py-xs medium ellipsis"
            :class="{
              'alternate-row': index % 2 === 0,
              'bg-blue-backdrop': section === $route.name,
            }"
            @click="$router.push({ name: section })"
          >
            {{ $capitalizeAll($t(`views.${section}`)) }}
          </div>
        </q-scroll-area>
      </div>
    </template>

    <template #after>
      <div class="col full-height">
        <router-view />
      </div>
    </template>
  </q-splitter>
</template>

<script setup>
import { ref } from 'vue';
import { storeToRefs } from 'pinia';
import LoadingSignal from '@/components/LoadingSignal.vue';
import { useConfigStore } from '@/stores/config';

const splitter_model = ref(30);

const sections = [
  'companyDetails',
  'defaultOperationParameters',
  'serialFieldSettings',
  'apiTokenSettings',
  'printTemplateLibrary',
  'printersLibrary',
  'warehouseSettings',
  'otherSettings',
];

const { isLoading } = storeToRefs(useConfigStore());
</script>
