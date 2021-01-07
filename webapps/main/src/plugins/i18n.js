import Vue from "vue";
import VueI18n from "vue-i18n";

Vue.use(VueI18n);

// create a messages object with an entry for each json file in the ./locales folder
function loadLocaleMessages() {
  
  const locales = require.context(
    "@/locales",
    true,
    /[A-Za-z0-9-_,\s]+\.js$/i
  );

  const messages = {};
  
  locales.keys().forEach(key => {
    const locale = key.split("/")[1].split('.')[0]
    import(`@/locales/${locale}.js`).then(m => {
      messages[locale] = m.default
    })
  })
  
  return messages;
}

export const i18n = new VueI18n({
  locale: process.env.VUE_APP_I18N_LOCALE || "it",
  fallbackLocale: process.env.VUE_APP_I18N_FALLBACK_LOCALE || "it",
  messages: loadLocaleMessages()
});
