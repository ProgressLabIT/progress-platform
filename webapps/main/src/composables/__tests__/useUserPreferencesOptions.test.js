import { createPinia, setActivePinia } from 'pinia';
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('vue-i18n', () => ({
  useI18n: () => ({ availableLocales: ['en', 'it'] }),
}));

vi.mock('@/stores/config', () => ({
  useConfigStore: () => ({
    config: {
      printers: [{ name: 'HP LaserJet', host: '10.0.0.1', port: 9100 }],
    },
  }),
}));

vi.mock('pinia', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    storeToRefs: (store) => {
      const { ref } = require('vue');
      return { config: ref(store.config) };
    },
  };
});

import { useUserPreferencesOptions } from '../useUserPreferencesOptions';

describe('useUserPreferencesOptions', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it('returns object with all 4 option keys', () => {
    const opts = useUserPreferencesOptions();
    expect(opts).toHaveProperty('localeOptions');
    expect(opts).toHaveProperty('themeOptions');
    expect(opts).toHaveProperty('displayFontOptions');
    expect(opts).toHaveProperty('printerOptions');
  });

  it('themeOptions is a static array with light and dark', () => {
    const { themeOptions } = useUserPreferencesOptions();
    expect(themeOptions).toEqual([
      { slot: 'light', value: 'light' },
      { slot: 'dark', value: 'dark' },
    ]);
  });

  it('displayFontOptions is a static array with orbitron and red-hat-display', () => {
    const { displayFontOptions } = useUserPreferencesOptions();
    expect(displayFontOptions).toEqual([
      { slot: 'orbitron', value: 'orbitron' },
      { slot: 'red-hat-display', value: 'red-hat-display' },
    ]);
  });

  it('localeOptions maps availableLocales to {label, value}', () => {
    const { localeOptions } = useUserPreferencesOptions();
    expect(localeOptions.value).toEqual([
      { label: 'en', value: 'en' },
      { label: 'it', value: 'it' },
    ]);
  });

  it('printerOptions maps config.printers to {label, value}', () => {
    const { printerOptions } = useUserPreferencesOptions();
    expect(printerOptions.value).toEqual([
      { label: 'HP LaserJet', value: '10.0.0.1:9100' },
    ]);
  });
});
