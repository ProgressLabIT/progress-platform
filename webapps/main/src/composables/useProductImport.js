import { ref } from 'vue';

export function useProductImport() {
  const importing = ref(false);
  const showImportDialog = ref(false);

  return { importing, showImportDialog };
}
