import { storeToRefs } from 'pinia';

import { useRightDrawerStore } from '@/stores/rightDrawer';

export function useRightDrawer() {
  const store = useRightDrawerStore();
  const { isOpen } = storeToRefs(store);

  return {
    isOpen,
    open: store.open,
    close: store.close,
    toggle: store.toggle,
  };
}
