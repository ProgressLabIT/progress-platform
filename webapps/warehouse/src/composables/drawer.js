import { computed } from 'vue';
import { useStore } from 'vuex';

export function useDrawer() {
  const store = useStore();

  const drawerModel = computed({
    get: () => store.state.show_drawer,
    set: (value) => store.commit('SHOW_DRAWER', value),
  });

  return {
    drawerModel,
  };
}
