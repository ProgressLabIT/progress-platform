import { Quasar } from 'quasar';
import { boot } from 'quasar/wrappers';
import { watch } from 'vue';
import { createI18n } from 'vue-i18n';
import messages from '@/i18n';
import { store } from '@/boot/store.js';

// Detect locale can be in the form of en-US, it-IT, etc.
const detectedLocale = Quasar.lang.getLocale();
const rawLocale = detectedLocale ?? 'it';
const locale = rawLocale.startsWith('it') ? 'it' : 'en';

const i18n = createI18n({
  legacy: false, // Use Composition API mode
  locale,
  globalInjection: true,
  messages,
});

export { i18n };

export default boot(({ app }) => {
  // Safely access store state with optional chaining
  const preferredLocale = store?.state?.session?.user?.preferences?.locale;

  if (preferredLocale) {
    i18n.global.locale.value = preferredLocale;
  }

  watch(i18n.global.locale, async (locale) => {
    // Only update if store is available
    if (store && store.dispatch) {
      await store.dispatch('updatePreferences', { locale });
    }
  });

  // Make sure the user's preferred locale is always in sync with the i18n instance
  watch(
    () => store?.state?.session?.user?.preferences?.locale,
    (preferredLocale) => {
      if (preferredLocale && preferredLocale !== i18n.global.locale.value) {
        i18n.global.locale.value = preferredLocale;
      }
    },
  );

  // Set i18n instance on app
  app.use(i18n);
});
