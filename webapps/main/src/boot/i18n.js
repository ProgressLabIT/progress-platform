import { LocalStorage, Quasar } from 'quasar';
import { boot } from 'quasar/wrappers';
import { watch } from 'vue';
import { createI18n } from 'vue-i18n';
import messages from '@/i18n';

export default boot(({ app }) => {
  const storedLocale = LocalStorage.getItem('locale');
  // Detect locale can be in the form of en-US, it-IT, etc.
  const detectedLocale = Quasar.lang.getLocale();
  const rawLocale = storedLocale ?? detectedLocale ?? 'it';
  const locale = rawLocale.startsWith('it') ? 'it' : 'en';

  const i18n = createI18n({
    locale,
    globalInjection: true,
    messages,
  });

  watch(
    i18n.global.locale,
    (locale) => {
      LocalStorage.set('locale', locale);
    },
    { immediate: true },
  );

  // Set i18n instance on app
  app.use(i18n);
});
