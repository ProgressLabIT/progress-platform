<template>
  <LoadingSignal v-if="isLoading" />
  <div v-else class="row full-height">
    <div class="col-3 full-height column">
      <div
        class="row q-mt-md q-px-lg q-py-sm text-h6 text-uppercase weight-bold"
      >
        <div class="col-6">
          {{ $t('settings.section') }}
        </div>
      </div>

      <q-separator />

      <!-- TODO: Use q-list ? -->
      <div class="scroll col">
        <div
          v-for="(section, index) in sections"
          :key="section"
          class="pointer q-px-lg q-py-xs medium"
          :class="{
            'alternate-row': index % 2 === 0,
            'bg-blue-backdrop': section === $route.name,
          }"
          style="white-space: nowrap"
          @click="$router.push({ name: section })"
        >
          {{ $capitalizeAll($t(`views.${section}`)) }}
        </div>
      </div>
    </div>

    <q-separator vertical />

    <div class="col full-height">
      <router-view />
    </div>
  </div>
</template>

<script setup>
import { storeToRefs } from 'pinia';
import LoadingSignal from '@/components/LoadingSignal.vue';
import { useConfigStore } from '@/stores/config';

const sections = ['labelPrintTemplates'];

const { isLoading } = storeToRefs(useConfigStore());
</script>
