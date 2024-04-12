<template>
  <q-page-container class="absolute-full">
    <q-page class="q-px-md q-pb-md column full-height">
      <!-- TAB LINKS -->
      <q-tabs
        class="transparent text-low col-auto"
        active-class="text-high weight-bold"
        align="left"
        shrink
        dense
        indicator-color="primary"
      >
        <q-route-tab
          v-for="(view, index) in adminViews"
          :key="index"
          :to="{ name: view }"
          class="display"
        >
          {{ $t(`views.${view}`) }}
        </q-route-tab>
      </q-tabs>
      <q-card class="surface1 col" square>
        <router-view v-slot="{ Component }" class="">
          <component :is="Component" class="full-height" />
        </router-view>
      </q-card>
    </q-page>
  </q-page-container>
</template>

<script setup>
const adminViews = [
  'generalSettings',
  'userLibrary',
  'operationLibrary',
  'issueTypeLibrary',
  'formFieldLibrary',
  'flowLibrary',
  'printTemplateLibrary',
];
</script>
