import { computed } from 'vue';
import { cloneDeep } from 'lodash';
import { useI18n } from 'vue-i18n';
import { storeToRefs } from 'pinia';
import { useConfigStore } from '@/stores/config';

export function useUserPreferencesOptions() {
  const { availableLocales } = useI18n();
  const { config } = storeToRefs(useConfigStore());

  const localeOptions = computed(() =>
    availableLocales.map((l) => ({ label: l, value: l })),
  );

  const themeOptions = [
    { slot: 'light', value: 'light' },
    { slot: 'dark', value: 'dark' },
  ];

  const displayFontOptions = [
    { slot: 'orbitron', value: 'orbitron' },
    { slot: 'red-hat-display', value: 'red-hat-display' },
  ];

  const printerOptions = computed(() =>
    cloneDeep(config.value?.printers ?? []).map((p) => ({
      label: p.name,
      value: `${p.host}:${p.port}`,
    })),
  );

  return { localeOptions, themeOptions, displayFontOptions, printerOptions };
}
