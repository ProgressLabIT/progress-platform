/**
 * Composable for filtering aggregated count records.
 *
 * Provides filter state and computed filtered results with support for:
 * - Variance threshold (absolute/percentage)
 * - Text filters with wildcard matching
 * - Boolean filters (notes, conflicts, variance)
 * - Tag and user filters
 *
 * @module useCountRecordFilters
 */

import { ref, computed } from 'vue';
import { useWildcardToRegex } from '@/composables/useWildcardToRegex';

/**
 * @typedef {Object} FilterState
 * @property {number|null} variance - Variance threshold value
 * @property {'absolute'|'percentage'} varianceType - Type of variance calculation
 * @property {boolean} onlyWithVariance - Only show records with delta != 0
 * @property {boolean} onlyConflicts - Only show records with conflicts
 * @property {boolean} hasNotes - Only show records with notes
 * @property {string} product - Product code/description filter
 * @property {string} serial - Serial code filter
 * @property {string} position - Position code filter
 * @property {boolean} positionIncludePath - Also match ancestors/children in position filter
 * @property {string|null} productTag - Product tag key filter
 * @property {string|null} userKey - User key filter
 */

/**
 * Build a case-insensitive matcher using the shared wildcard-to-regex composable.
 * If pattern is empty/null, matcher always returns true.
 *
 * @param {string|null} pattern - The wildcard pattern to match
 * @param {Function} wildcardToRegex - The regex converter function
 * @returns {Function} A matcher function that tests strings against the pattern
 */
function buildWildcardMatcher(pattern, wildcardToRegex) {
  if (!pattern) {
    return () => true;
  }

  const regex = wildcardToRegex(pattern.toString().trim());
  if (!regex) {
    return () => true;
  }

  return (text) => {
    if (text == null) return false;
    return regex.test(String(text));
  };
}

/**
 * Composable for count record filtering logic.
 *
 * @param {import('vue').ComputedRef<Array>} visibleAggregates - Visible aggregates from aggregation composable
 * @returns {Object} Filter state and helpers
 */
export function useCountRecordFilters(visibleAggregates) {
  const { wildcardToRegex } = useWildcardToRegex();

  /**
   * Filter state with all filter criteria
   */
  const filters = ref({
    variance: null,
    varianceType: 'absolute',
    onlyWithVariance: false,
    onlyConflicts: false,
    hasNotes: false,
    product: '',
    serial: '',
    position: '',
    positionIncludePath: false,
    productTag: null,
    userKey: null,
  });

  /**
   * Reset all filters to default values
   */
  const resetFilters = () => {
    filters.value = {
      variance: null,
      varianceType: 'absolute',
      onlyWithVariance: false,
      onlyConflicts: false,
      hasNotes: false,
      product: '',
      serial: '',
      position: '',
      positionIncludePath: false,
      productTag: null,
      userKey: null,
    };
  };

  /**
   * Apply filters to visible aggregated records
   */
  const filteredRecords = computed(() => {
    let result = visibleAggregates.value;

    // Pre-build wildcard matchers
    const productMatcher = buildWildcardMatcher(filters.value.product, wildcardToRegex);
    const serialMatcher = buildWildcardMatcher(filters.value.serial, wildcardToRegex);
    const positionMatcher = buildWildcardMatcher(filters.value.position, wildcardToRegex);

    // Variance filter
    if (filters.value.variance !== null && filters.value.variance !== '') {
      const threshold = Number(filters.value.variance);
      result = result.filter(r => {
        if (!r.activeRecordKey) return false;
        const delta = Math.abs(r.delta || r.serialDelta?.added?.length + r.serialDelta?.removed?.length || 0);
        if (filters.value.varianceType === 'percentage') {
          const systemQt = r.totalSystemQt || 1;
          const percentVariance = (delta / systemQt) * 100;
          return percentVariance >= threshold;
        }
        return delta >= threshold;
      });
    }

    // Only with variance filter
    if (filters.value.onlyWithVariance) {
      result = result.filter((r) => {
        const delta = Math.abs(r.delta || r.serialDelta?.added?.length + r.serialDelta?.removed?.length || 0);
        return delta > 0;
      });
    }

    // Has notes filter
    if (filters.value.hasNotes) {
      result = result.filter(r => r.hasNotes);
    }

    // Only conflicts filter
    if (filters.value.onlyConflicts) {
      result = result.filter(r => r.hasConflict);
    }

    // Product tag filter
    if (filters.value.productTag) {
      const selectedTagKey = filters.value.productTag;
      result = result.filter((r) =>
        (r.product.tags || []).some(tag => tag._key === selectedTagKey)
      );
    }

    // Product filter
    if (filters.value.product) {
      result = result.filter(r =>
        productMatcher(r.product.code) ||
        productMatcher(r.product.description)
      );
    }

    // Serial filter - use aggregated serial sets
    if (filters.value.serial) {
      result = result.filter(r => {
        // Check all serials across all records in the aggregate
        for (const record of r.records) {
          const allSerials = [
            ...(record.system_serial_keys || []),
            ...(record.counted_serial_keys || []),
          ];
          if (allSerials.some(s => serialMatcher(s))) {
            return true;
          }
        }
        return false;
      });
    }

    // Position filter
    if (filters.value.position) {
      result = result.filter(r => {
        if (!r.position) return false;

        // Always check the aggregate position code
        if (positionMatcher(r.position.code)) {
          return true;
        }

        // If include path toggle is active, also match ancestors and underlying positions
        if (filters.value.positionIncludePath) {
          // Check the path string of the aggregate position
          if (positionMatcher(r.pathString)) {
            return true;
          }

          // Check each individual position code in the path
          // The path is stored as "Code1 > Code2 > Code3", split and check each
          const pathCodes = r.pathString?.split(' > ') || [];
          if (pathCodes.some(code => positionMatcher(code))) {
            return true;
          }

          // Also check all underlying position codes (when aggregating multiple positions)
          if (r.aggregatedPositionCodes?.some(code => positionMatcher(code))) {
            return true;
          }

          // Check paths of all underlying records
          for (const record of r.records) {
            if (record.position_path?.some(code => positionMatcher(code))) {
              return true;
            }
          }
        }

        return false;
      });
    }

    // User filter - check if user is in the aggregate's userKeys array
    if (filters.value.userKey) {
      result = result.filter(r => r.userKeys?.includes(filters.value.userKey));
    }

    return result;
  });

  return {
    filters,
    filteredRecords,
    resetFilters,
  };
}
