<template>
  <q-page class="q-px-md q-py-lg column fit">
    <router-view></router-view>
  </q-page>
</template>

<script setup>
import { ref } from 'vue';
import { api } from 'src/boot/axios';

const loading = ref(true);

function loadData() {
  api.get('/movement-list', { params: { type: 'receipt' }}).then((response) => {
    console.log(response);
  }).catch((error) => {
    console.error(error);
  }).finally(() => {
    loading.value = false;
  });
}

loadData();
</script>
