import { ref } from 'vue';
import { api } from '@/boot/axios';

/**
 * @typedef {Object} UsePrintTemplatesParams
 * @property {string} context
 * @property {string} contextKey
 */

/**
 * @param {UsePrintTemplatesParams}
 */
export function usePrintTemplates({ context, contextKey } = {}) {
  const templates = ref([]);
  const isLoading = ref(false);
  const isError = ref(false);

  async function fetchTemplates() {
    isLoading.value = true;
    try {
      const { data } = await api.get('print-template', {
        params: {
          context,
          context_key: contextKey,
        },
      });
      templates.value = data;
      isError.value = false;
    } catch (error) {
      isError.value = true;
      throw error;
    } finally {
      isLoading.value = false;
    }
  }
  fetchTemplates();

  return {
    templates,
    fetchTemplates,
    isLoading,
    isError,
  };
}
