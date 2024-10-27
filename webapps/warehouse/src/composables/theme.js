import { createSharedComposable } from '@vueuse/core';
import { Dark } from 'quasar';
import { computed, watch } from 'vue';
import { useStore } from 'vuex';

import { dark, light } from 'src/boot/theme.js';

// TODO: Add system-based theme detection (?)
/**
 * The theme is persisted in local storage and is 'dark' by default.
 * Call this during the boot process to ensure everything is set up as early as possible.
 */
export const useTheme = createSharedComposable((store = useStore()) => {
  /** @type {import('vue').ComputedRef<'dark' | 'light'>} */
  const theme = computed(
    () => store.state.session.user.preferences.theme || 'dark'
  );

  async function setTheme(theme) {
    await store.dispatch('updatePreferences', { theme });
  }

  function applyTheme(newTheme) {
    document.body.setAttribute('progress-theme', newTheme);
    const isDark = newTheme === 'dark';
    store.dispatch('changeTheme', isDark ? dark : light);
    Dark.set(isDark);
  }

  watch(theme, applyTheme, { immediate: true });

  return { theme, setTheme };
});
