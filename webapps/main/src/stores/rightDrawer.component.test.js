import { setActivePinia, createPinia } from 'pinia';
import { beforeEach, describe, expect, it } from 'vitest';
import { useRightDrawerStore } from './rightDrawer.js';

describe('useRightDrawerStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it('initializes isOpen to false', () => {
    const store = useRightDrawerStore();
    expect(store.isOpen).toBe(false);
  });

  it('open() sets isOpen to true', () => {
    const store = useRightDrawerStore();
    store.open();
    expect(store.isOpen).toBe(true);
  });

  it('close() sets isOpen to false even when already closed', () => {
    const store = useRightDrawerStore();
    store.close();
    expect(store.isOpen).toBe(false);
    store.open();
    store.close();
    expect(store.isOpen).toBe(false);
  });

  it('toggle() flips from false to true then true to false', () => {
    const store = useRightDrawerStore();
    store.toggle();
    expect(store.isOpen).toBe(true);
    store.toggle();
    expect(store.isOpen).toBe(false);
  });

  it('open() is idempotent', () => {
    const store = useRightDrawerStore();
    store.open();
    store.open();
    expect(store.isOpen).toBe(true);
  });
});
