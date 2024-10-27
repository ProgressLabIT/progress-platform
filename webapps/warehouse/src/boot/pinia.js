import { until } from '@vueuse/core';
import { createPinia, storeToRefs } from 'pinia';
import { boot } from 'quasar/wrappers';
import { useConfigStore } from 'src/stores/config';

export default boot(async ({ app }) => {
  const pinia = createPinia();

  app.use(pinia);

  // Can't use a separate boot file as we can't get the pinia instance there
  // After migrating from Vuex to Pinia completely, we will be able to use
  // the `store` property from the boot context
  const { isLoading } = storeToRefs(useConfigStore(pinia));
  await until(isLoading).toBe(false);
});
