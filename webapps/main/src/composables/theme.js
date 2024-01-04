import { createSharedComposable } from '@vueuse/core';
import { Dark, LocalStorage } from 'quasar';
import { ref, watch } from 'vue';
import { useStore } from 'vuex';

import { dark, light } from '@/boot/theme.js';

// TODO: Add system-based theme detection (?)
/**
 * The theme is persisted in local storage and is 'dark' by default.
 * Call this during the boot process to ensure everything is set up as early as possible.
 */
export const useTheme = createSharedComposable((store = useStore()) => {
  /** @type {import('vue').Ref<'dark' | 'light'>} */
  const theme = ref(LocalStorage.getItem('theme') ?? 'dark');

  watch(
    theme,
    (theme) => {
      LocalStorage.set('theme', theme);
      document.body.setAttribute('progress-theme', theme);
      const isDark = theme === 'dark';
      store.dispatch('changeTheme', isDark ? dark : light);
      Dark.set(isDark);
    },
    { immediate: true },
  );

  return { theme };
});
