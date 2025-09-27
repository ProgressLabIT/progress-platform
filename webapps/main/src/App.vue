<template>
  <div :style="CSSVars">
    <router-view />
  </div>
</template>

<script setup>
import { DateTime as DT } from 'luxon';
import { onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { useStore } from 'vuex';
import { useCSSVars } from '@/composables/useCSSVars.js';
import { useTaskStorePersistence } from '@/stores/task.js';

const $store = useStore();
const $route = useRoute();

// Use the CSSVars composable
const { CSSVars } = useCSSVars();

// Set up task store persistence (automatically handles restore/save)
useTaskStorePersistence();

onMounted(() => {
  // Task store persistence is automatically handled by useTaskStorePersistence
  // It will restore on mount and save before unload

  // Save vuex state in localStorage before refresh or tab close
  window.addEventListener('beforeunload', async () => {
    if ($route.name != 'login') {
      localStorage.setItem(
        'TEMP_SESSION',
        JSON.stringify({
          ...$store.state,
          last_interaction: DT.utc().toMillis(),
        }),
      );
    }
  });
});
</script>
