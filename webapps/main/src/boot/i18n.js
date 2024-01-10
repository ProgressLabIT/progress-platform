import { Quasar } from 'quasar';
import { boot } from 'quasar/wrappers';
import { watch } from 'vue';
import { createI18n } from 'vue-i18n';
import messages from '@/i18n';

export default boot(({ app, store }) => {
  const preferredLocale = store.state.session.user.preferences.locale;
  // Detect locale can be in the form of en-US, it-IT, etc.
  const detectedLocale = Quasar.lang.getLocale();
  const rawLocale = preferredLocale ?? detectedLocale ?? 'it';
  const locale = rawLocale.startsWith('it') ? 'it' : 'en';

  const i18n = createI18n({
    locale,
    globalInjection: true,
    messages,
  });

  watch(i18n.global.locale, async (locale) => {
    await store.dispatch('updatePreferences', { locale });
  });

  // Make sure the user's preferred locale is always in sync with the i18n instance
  watch(
    () => store.state.session.user.preferences.locale,
    (preferredLocale) => {
      if (preferredLocale && preferredLocale !== i18n.global.locale) {
        i18n.global.locale.value = preferredLocale;
      }
    },
  );

  // Set i18n instance on app
  app.use(i18n);
});
