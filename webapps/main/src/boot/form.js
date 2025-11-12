import { boot } from 'quasar/wrappers';
import { watch } from 'vue';
import { store } from '@/boot/store.js';

export default boot(async () => {
  // Make sure custom fields are ready before the app starts
  // If not logged in, wait until logged in for once
  const stop = watch(
    () => store?.getters?.isLoggedIn,
    async (isLoggedIn) => {
      if (!isLoggedIn) {
        return;
      }

      await store?.dispatch('getCustomFields');
      stop();
    },
    {
      immediate: true,
    },
  );
});
