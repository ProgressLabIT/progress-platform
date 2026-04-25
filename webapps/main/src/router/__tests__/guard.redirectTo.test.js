import { describe, it, expect, vi } from 'vitest';

vi.mock('quasar', () => ({ Quasar: { lang: { getLocale: () => 'en' } } }));
vi.mock('quasar/wrappers', () => ({ route: (fn) => fn }));
vi.mock('@/i18n/en.js', () => ({ default: {} }));
vi.mock('@/i18n/it.js', () => ({ default: {} }));
vi.mock('@/composables/taskNavigation.js', () => ({
  extractEntityFromRoute: vi.fn(),
  handleEntityNavigation: vi.fn(),
}));
vi.mock('@/boot/store.js', () => ({ store: {} }));
vi.mock('../routes', () => ({ default: [] }));

import { resolveLoginRedirect } from '@/router/index.js';

describe('resolveLoginRedirect', () => {
  it('returns { path } form when redirect_to is present', () => {
    expect(resolveLoginRedirect({ redirect_to: '/app/production/jobs/abc' }, 'userHub'))
      .toEqual({ path: '/app/production/jobs/abc' });
  });
  it('returns { name: userHomepage } when redirect_to is absent', () => {
    expect(resolveLoginRedirect({}, 'userHub')).toEqual({ name: 'userHub' });
  });
  it('returns { name: userHomepage } when redirect_to is empty string', () => {
    expect(resolveLoginRedirect({ redirect_to: '' }, 'userHub')).toEqual({ name: 'userHub' });
  });
  it('passes any path prefix verbatim to { path }', () => {
    expect(resolveLoginRedirect({ redirect_to: '/app/operator/job/42' }, 'userHub'))
      .toEqual({ path: '/app/operator/job/42' });
  });
  it('honors legacy home_page preference when redirect_to absent', () => {
    expect(resolveLoginRedirect({}, 'productionRoot')).toEqual({ name: 'productionRoot' });
  });
});
