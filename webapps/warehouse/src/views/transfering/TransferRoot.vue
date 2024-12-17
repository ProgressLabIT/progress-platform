<template>
  <q-page class="q-px-md q-py-lg column fit">

    <!-- HERE SHOW TRANSFER REQUESTS (PLANNED MOVEMENTS) -->
    <div class="text-h1">Trasferimenti pianificati</div>

    <q-space></q-space>
    <!-- BUTTON FOR MANUAL TRANSFER -->
    <q-btn
      :label="$t('transfer_new')"
      color="primary"
      @click="router.push({ name: 'TransferManual' })"
    />

    <router-view></router-view>

  </q-page>
</template>

<script setup>
import { useRouter } from 'vue-router';

const router = useRouter();
</script>
