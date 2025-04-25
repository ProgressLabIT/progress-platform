<template>
  <div class="col column q-gutter-md">
    <div class="text-h1">Giacenze</div>
      <q-space></q-space>

      <q-btn
        class="col-auto"
        color="theme-blue"
        :label="t('product')"
        @click="$router.push({ name: 'InventoryProduct' })"
      />
      <q-btn
        class="col-auto"
        color="theme-green"
        :label="t('serial', 2)"
        @click="$router.push({ name: 'InventorySerial' })"
      />
      <q-btn
        class="col-auto"
        color="theme-grey"
        :label="t('position')"
        @click="$router.push({ name: 'InventoryPosition' })"
      />
    </div>
</template>

<script setup>
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();

const $router = useRouter();
</script>
