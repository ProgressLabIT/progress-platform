import { computed } from 'vue';
import { useQuasar } from 'quasar';

export function useCSSVars() {
  const $q = useQuasar();

  const CSSVars = computed(() => {
    return {
      '--text-high': $q.dark.isActive
        ? 'rgba(255,255,255,.87)'
        : 'rgba(0,0,0,.87)',
      '--text-low': $q.dark.isActive
        ? 'rgba(255,255,255,.6)'
        : 'rgba(0,0,0,.6)',
      '--bg-color': $q.dark.isActive ? '#131E21' : '#eee',
      '--surface-1': $q.dark.isActive ? '#1f2a2d' : '#fafafa',
      '--surface-2': $q.dark.isActive ? '#242e31' : '#fff',
    };
  });

  return {
    CSSVars,
  };
}
