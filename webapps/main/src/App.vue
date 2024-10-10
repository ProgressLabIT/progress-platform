<template>
  <div :style="CSSVars">
    <router-view />
  </div>
</template>

<script>
import { DateTime as DT } from 'luxon';
import { defineComponent } from 'vue';
import CSSVars from '@/mixins/CSSVars.js';

export default defineComponent({
  name: 'App',

  mixins: [CSSVars],
  computed: {
    store() {
      return this.$store.state;
    },
  },

  created() {
    // Save vuex state in localStorage before refresh or tab close
    window.addEventListener('beforeunload', async () => {
      if (this.$route.name != 'login') {
        localStorage.setItem(
          'TEMP_SESSION',
          JSON.stringify({
            ...this.$store.state,
            last_interaction: DT.utc().toMillis(),
          }),
        );
      }
    });
  },
});
</script>
