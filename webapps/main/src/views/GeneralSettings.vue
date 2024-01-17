<template>
  <LoadingSignal v-if="isLoading" />
  <div v-else class="row full-height">
    <div class="full-height column col-3">
      <div class="col-2 full-height column">
        <q-tabs vertical color="white">
          <q-route-tab
            v-for="tab in sections"
            :key="tab"
            :to="{ name: tab }"
            class="display"
          >
            {{ $t(`views.${tab}`) }}
          </q-route-tab>
        </q-tabs>
      </div>
    </div>

    <q-separator vertical />

    <div class="col full-height">
      <router-view />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import LoadingSignal from '@/components/LoadingSignal.vue';

const isLoading = ref(false);
const sections = ['companyDetails', 'defaultPhaseParams'];
</script>
