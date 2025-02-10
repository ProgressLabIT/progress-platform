<template>
  <div class="col column q-gutter-md">
    <div class="text-h1">Giacenze</div>
      <q-space></q-space>
      <!-- <q-btn
        class="col-auto"
        color="theme-blue"
        label="Visualizza per prodotto"
        @click="$router.push({ name: 'InventoryProduct' })"
      /> -->

      <q-btn
        class="col-auto"
        color="theme-blue"
        label="Visualizza per posizione"
        @click="$router.push({ name: 'InventoryPosition' })"
      />
    </div>
</template>

<script setup>
import { useRouter } from 'vue-router';

const $router = useRouter();
</script>
