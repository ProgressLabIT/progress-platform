<template>
  <div>
    zio cane
    <q-btn
      color="white"
      text-color="black"
      label="Standard"
      @click="setDomain()"
    />
  </div>
</template>

<script setup>
import { Preferences } from '@capacitor/preferences';

async function setDomain() {
  console.log('ci sono');
  await Preferences.set({
    key: 'domain',
    value: 'http://localhostsss:8000',
  });
}
</script>
