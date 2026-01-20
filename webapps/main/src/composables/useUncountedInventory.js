/**
 * Composable for tracking and fetching uncounted inventory.
 *
 * When aggregating records at a specific level (not "All levels" mode), the displayed
 * data may not represent the complete inventory picture because some positions may not
 * have been counted. This composable adds visibility into inventory that exists in
 * positions that weren't counted.
 *
 * @module useUncountedInventory
 */

import { ref, computed, watch } from 'vue';

/**
 * @typedef {Object} UncountedData
 * @property {number|null} qt - The uncounted quantity
 * @property {Array<{key: string, code: string, quantity: number}>} positions - Uncounted positions
 * @property {boolean} loading - Whether data is being fetched
 * @property {string|null} error - Error message if fetch failed
 */

/**
 * Composable for uncounted inventory fetching and display logic.
 *
 * @param {import('vue').ComputedRef<Array>} visibleAggregates - Visible aggregates from aggregation composable
 * @param {import('vue').Ref<boolean>} allLevels - Whether "All levels" mode is active
 * @param {Object} countSessionStore - The Pinia count session store
 * @returns {Object} Uncounted inventory helpers
 */
export function useUncountedInventory(visibleAggregates, allLevels, countSessionStore) {
  // Track if fetching is in progress to prevent concurrent fetch loops
  const fetchingUncounted = ref(false);

  /**
   * Get cached uncounted inventory data for an aggregate row
   * @param {Object} row - The aggregate row
   * @returns {UncountedData|null} Cached data or null
   */
  function getUncountedData(row) {
    if (!row.position?.key || !row.product?.key) return null;
    return countSessionStore.getUncountedInventory(row.position.key, row.product.key);
  }

  /**
   * Get uncounted quantity for display in the table
   * @param {Object} row - The aggregate row
   * @returns {number|null} The uncounted quantity or null if not available
   */
  function getUncountedQt(row) {
    // If position is fully counted, uncounted = 0
    if (row.coverage?.isComplete) return 0;
    const data = getUncountedData(row);
    return data?.qt ?? null;
  }

  /**
   * Get total system quantity (system_qt from records + uncounted)
   * @param {Object} row - The aggregate row
   * @returns {number|null} The total system quantity or null if not available
   */
  function getTotalSystemQt(row) {
    const systemQt = row.totalSystemQt;
    if (systemQt === null) return null;

    // If position is fully counted, total = system
    if (row.coverage?.isComplete) return systemQt;

    const uncountedQt = getUncountedQt(row);
    if (uncountedQt === null) return null;

    return systemQt + uncountedQt;
  }

  /**
   * Check if uncounted data is currently loading for a row
   * @param {Object} row - The aggregate row
   * @returns {boolean} True if loading
   */
  function isUncountedLoading(row) {
    if (row.coverage?.isComplete) return false;
    const data = getUncountedData(row);
    return data?.loading ?? false;
  }

  /**
   * Check if uncounted data fetch had an error
   * @param {Object} row - The aggregate row
   * @returns {string|null} Error message or null
   */
  function getUncountedError(row) {
    const data = getUncountedData(row);
    return data?.error ?? null;
  }

  /**
   * Get uncounted positions for tooltip display
   * @param {Object} row - The aggregate row
   * @returns {Array<{key: string, code: string, quantity: number}>} Uncounted positions
   */
  function getUncountedPositions(row) {
    if (row.coverage?.isComplete) return [];
    const data = getUncountedData(row);
    return data?.positions ?? [];
  }

  /**
   * Retry fetching uncounted inventory for a row
   * @param {Object} row - The aggregate row
   * @returns {Promise<void>}
   */
  async function retryUncountedFetch(row) {
    if (!row.position?.key || !row.product?.key) return;
    try {
      await countSessionStore.fetchUncountedInventory(
        row.position.key,
        row.product.key,
        row.aggregatedPositionKeys || []
      );
    } catch (error) {
      console.error('Error retrying uncounted fetch:', error);
    }
  }

  /**
   * Get effective delta for display.
   * When aggregating with incomplete coverage, uses total system quantity
   * instead of just counted system quantity.
   * @param {Object} row - The aggregate row
   * @returns {number|null} The effective delta
   */
  function getEffectiveDelta(row) {
    // If in "All levels" mode, use the regular delta
    if (allLevels.value) {
      return row.delta;
    }

    // If position is fully counted, use regular delta
    if (row.coverage?.isComplete) {
      return row.delta;
    }

    // When aggregating with incomplete coverage, use total system quantity
    const totalSystemQt = getTotalSystemQt(row);
    const countedQt = row.totalCountedQt;

    if (totalSystemQt === null || countedQt === null) {
      return null;
    }

    return countedQt - totalSystemQt;
  }

  /**
   * Aggregates that need uncounted inventory data fetched.
   * Only includes rows that:
   * - Are aggregated (not in "All levels" mode)
   * - Have incomplete coverage
   * - Don't already have cached data
   */
  const aggregatesNeedingFetch = computed(() => {
    if (allLevels.value) return []; // No fetching needed in "All levels" mode

    return visibleAggregates.value.filter(agg => {
      // Skip if position is fully counted
      if (agg.coverage?.isComplete) return false;

      // Skip if missing position or product key
      if (!agg.position?.key || !agg.product?.key) return false;

      // Skip if already cached (not in error state)
      const cached = countSessionStore.getUncountedInventory(agg.position.key, agg.product.key);
      if (cached && !cached.error && !cached.loading) return false;

      // Skip if currently loading
      if (cached?.loading) return false;

      return true;
    });
  });

  /**
   * Sequential fetch of uncounted inventory for visible aggregates.
   * Processes one at a time to avoid overwhelming the backend.
   */
  async function fetchUncountedInventorySequentially() {
    if (fetchingUncounted.value) return; // Already fetching

    const toFetch = aggregatesNeedingFetch.value;
    if (toFetch.length === 0) return;

    fetchingUncounted.value = true;

    try {
      for (const agg of toFetch) {
        // Re-check if still needs fetching (could have been fetched by retry)
        const cached = countSessionStore.getUncountedInventory(agg.position.key, agg.product.key);
        if (cached && !cached.error && !cached.loading) continue;

        try {
          await countSessionStore.fetchUncountedInventory(
            agg.position.key,
            agg.product.key,
            agg.aggregatedPositionKeys || []
          );
        } catch (error) {
          // Error is already stored in cache, continue with next
          console.warn('Failed to fetch uncounted inventory:', error);
        }
      }
    } finally {
      fetchingUncounted.value = false;
    }
  }

  // Watch for aggregates needing fetch and trigger sequential fetching
  watch(
    aggregatesNeedingFetch,
    (newVal) => {
      if (newVal.length > 0) {
        fetchUncountedInventorySequentially();
      }
    },
    { immediate: true }
  );

  return {
    // State
    fetchingUncounted,

    // Helpers
    getUncountedData,
    getUncountedQt,
    getTotalSystemQt,
    isUncountedLoading,
    getUncountedError,
    getUncountedPositions,
    retryUncountedFetch,
    getEffectiveDelta,

    // Internal (exposed for testing)
    aggregatesNeedingFetch,
    fetchUncountedInventorySequentially,
  };
}
