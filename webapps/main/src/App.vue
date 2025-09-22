<template>
  <div :style="CSSVars">
    <router-view />
  </div>
</template>

<script setup>
import { onMounted } from 'vue';
import { useStore } from 'vuex';
import { useRoute } from 'vue-router';
import { DateTime as DT } from 'luxon';
import { useCSSVars } from '@/composables/useCSSVars.js';

const $store = useStore();
const $route = useRoute();

// Use the CSSVars composable
const { CSSVars } = useCSSVars();

onMounted(() => {
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
