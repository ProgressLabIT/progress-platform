import { describe, it, expect, vi } from 'vitest';

vi.mock('@/boot/axios.js', () => ({ api: {} }));
vi.mock('@/lib/appRouter', () => ({ getAppRouter: () => ({}) }));
vi.mock('vue-cookies', () => ({ default: { get: vi.fn(), set: vi.fn(), remove: vi.fn() } }));

import session from '@/store/session.js';

function makeState({ home_page = '', scope = '' } = {}) {
  return { user: { preferences: { home_page } }, scope };
}

describe('session.userHomepage getter', () => {
  it('returns user.preferences.home_page when set (operatorRoot)', () => {
    expect(session.getters.userHomepage(makeState({ home_page: 'operatorRoot', scope: 'operator' }))).toBe('operatorRoot');
  });
  it('returns user.preferences.home_page when set (productionRoot legacy honored)', () => {
    expect(session.getters.userHomepage(makeState({ home_page: 'productionRoot', scope: 'production' }))).toBe('productionRoot');
  });
  it("returns 'userHub' when home_page is empty string", () => {
    expect(session.getters.userHomepage(makeState({ home_page: '', scope: 'operator' }))).toBe('userHub');
  });
  it("returns 'userHub' when home_page is undefined", () => {
    expect(session.getters.userHomepage(makeState({ home_page: undefined, scope: 'operator' }))).toBe('userHub');
  });
  it("returns 'userHub' for every scope variant (no role-specific fallback remains)", () => {
    for (const scope of ['operator', 'production', 'admin', 'library', 'quality', 'traceability', 'warehouse', 'reporting', 'task', '']) {
      expect(session.getters.userHomepage(makeState({ home_page: '', scope }))).toBe('userHub');
    }
  });
});
