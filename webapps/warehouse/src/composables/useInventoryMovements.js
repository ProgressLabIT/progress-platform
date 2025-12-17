import { ref, computed } from 'vue';
import { api } from '@/boot/axios';

/**
 * Composable to load inventory movements for a given product/position
 * after a specific timestamp (typically last count `counted_at`).
 *
 * Params:
 * - productKey: string
 * - positionKey: string (Position key, NOT full _id)
 * - startFrom: ISO datetime string
 */
export function useInventoryMovements({ productKey, positionKey, startFrom }) {
  const movements = ref([]);
  const loadingMovements = ref(false);
  const loadError = ref(null);

  const hasMovements = computed(() => movements.value.length > 0);

  async function loadMovements() {
    // Only load when we have the minimal required identifiers
    if (!productKey || !positionKey || !startFrom) {
      movements.value = [];
      return;
    }

    loadingMovements.value = true;
    loadError.value = null;

    try {
      const { data } = await api.get('/movement', {
        params: {
          product_key: productKey,
          position_from: positionKey,
          position_to: positionKey,
          position_filter_operator: 'OR',
          start_from: startFrom,
          limit: 200,
        },
      });

      movements.value = Array.isArray(data) ? data : [];
    } catch (error) {
      console.error('Error loading movements for count item:', error);
      loadError.value = error;
      movements.value = [];
    } finally {
      loadingMovements.value = false;
    }
  }

  return {
    movements,
    loadingMovements,
    hasMovements,
    loadError,
    loadMovements,
  };
}

