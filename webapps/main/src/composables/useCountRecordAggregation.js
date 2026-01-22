/**
 * Composable for aggregating count records by product and position level.
 *
 * Handles level-based position aggregation where records are grouped by their
 * ancestor position at a specified hierarchy level. Supports "All levels" mode
 * for granular (non-aggregated) view.
 *
 * @module useCountRecordAggregation
 */

import { ref, computed } from 'vue';

/**
 * @typedef {Object} AggregatePosition
 * @property {string} positionKey - The position key for aggregation
 * @property {string} positionCode - The position code
 * @property {string} pathString - Human-readable path string (e.g., "Zone-A > Aisle-1")
 * @property {boolean} deleted - Whether the position has been deleted
 */

/**
 * @typedef {Object} Aggregate
 * @property {string} aggregateKey - Unique key combining product and position
 * @property {Object} product - Product data (key, code, description, traceability_level, tags)
 * @property {Object|null} position - Position data (key, code, deleted)
 * @property {string} pathString - Human-readable position path
 * @property {Array} records - Original records in this aggregate
 * @property {number|null} totalSystemQt - Sum of system quantities (null if records conflict)
 * @property {number|null} totalCountedQt - Sum of counted quantities (null if records conflict)
 * @property {number|null} delta - Difference between counted and system quantities
 * @property {Set} allSystemSerialCodes - Union of system serial codes
 * @property {Set} allCountedSerialCodes - Union of counted serial codes
 * @property {Object} serialDelta - Added/removed serials
 * @property {boolean} hasConflict - Whether records have conflicting counted quantities
 * @property {boolean} hasNotes - Whether any record has notes
 * @property {number} notesCount - Total notes count
 * @property {Array} allNotes - All notes from records
 * @property {Array} userKeys - Unique user keys who counted
 * @property {boolean} hasMultipleUsers - Whether multiple users counted
 * @property {string|null} user_key - User key (only if single user, no conflict)
 * @property {Date|null} counted_at - Timestamp (only if single user, times match)
 * @property {Array} aggregatedPositionKeys - Position keys included in aggregate
 * @property {Array} aggregatedPositionCodes - Position codes included in aggregate
 * @property {string|null} activeRecordKey - Key of most recent non-discarded record
 * @property {Object} coverage - Coverage tracking for incomplete position counts
 * @property {boolean} hasError - Whether any record has error_details
 * @property {Array<string>} allErrorDetails - All error details from records in this aggregate
 * @property {string|null} errorMessage - First error message (for backward compatibility)
 * @property {string|null} error_details - First error details (for backward compatibility)
 */

/**
 * Determine the aggregate position key for a record based on the selected level.
 *
 * Level concept:
 * - User level 0: Root (IN) - aggregate all positions
 * - User level 1: First-level children of IN
 * - User level 2+: Deeper levels
 * - "All levels": Use actual position (no aggregation)
 *
 * @param {Object} record - The count record
 * @param {Map} lookup - The positionLookup map
 * @param {boolean} allLevelsValue - Whether "All levels" mode is active
 * @param {number} selectedLevelValue - The selected aggregation level
 * @returns {AggregatePosition} Position data for aggregation
 */
function getAggregatePosition(record, lookup, allLevelsValue, selectedLevelValue) {
  // If "All" is toggled, use the actual position (most granular)
  // Path should NOT include IN (it's implied)
  if (allLevelsValue) {
    return {
      positionKey: record.position_key,
      positionCode: record.position_code,
      pathString: record.position_path?.join(' > ') || record.position_code || '',
      deleted: record.position_deleted || false,
    };
  }

  const targetLevel = Number(selectedLevelValue);

  // Level 0 means aggregate everything (total inventory for product)
  if (targetLevel === 0) {
    return {
      positionKey: 'IN',
      positionCode: 'IN',
      pathString: 'IN',
      deleted: false,
    };
  }

  // Use position_path (codes) and position_path_keys (keys) from record
  // position_path[0] = level 1 position code, position_path[1] = level 2 position code, etc.
  // position_path_keys[0] = level 1 position key, etc.
  const path = record.position_path || [];
  const pathKeys = record.position_path_keys || [];

  if (path.length === 0) {
    // No path data, use actual position
    return {
      positionKey: record.position_key,
      positionCode: record.position_code,
      pathString: record.position_code || '',
      deleted: record.position_deleted || false,
    };
  }

  // The actual level of this position is path.length (since path excludes IN which is level 0)
  const actualLevel = path.length;

  if (actualLevel <= targetLevel) {
    // Position is at or shallower than target level, use actual position
    // Path string should not include IN
    return {
      positionKey: record.position_key,
      positionCode: record.position_code,
      pathString: path.join(' > '),
      deleted: record.position_deleted || false,
    };
  }

  // Position is deeper than target level, use position at target level from path
  // targetLevel 1 → index 0, targetLevel 2 → index 1, etc.
  const targetIndex = targetLevel - 1;
  const targetCode = path[targetIndex];
  const targetKey = pathKeys[targetIndex] || targetCode; // Fallback to code if keys missing

  // Build path string up to target level (not including IN)
  const pathString = path.slice(0, targetLevel).join(' > ');

  // Get additional data from lookup if available
  const targetData = lookup?.get(targetKey);

  return {
    positionKey: targetKey,
    positionCode: targetCode,
    pathString: pathString,
    deleted: targetData?.deleted || false,
  };
}

/**
 * Get the active (non-discarded) record from an aggregate row
 * @param {Aggregate} row - The aggregate row
 * @returns {Object|null} The active record or null
 */
export function getActiveRecord(row) {
  if (!row.activeRecordKey) return null;
  return row.records.find(r => r._key === row.activeRecordKey);
}

/**
 * Get discarded records from an aggregate row
 * @param {Aggregate} row - The aggregate row
 * @returns {Array} Array of discarded records
 */
export function getDiscardedRecords(row) {
  return row.records.filter(r => r.status === 'discarded');
}

/**
 * Composable for count record aggregation logic.
 *
 * @param {import('vue').ComputedRef<Array>} rawRecords - Raw records from store
 * @param {import('vue').ComputedRef<Map>} positionLookup - Position lookup map from store
 * @param {import('vue').ComputedRef<Set>} completedPositions - Set of completed position keys
 * @returns {Object} Aggregation state and helpers
 */
export function useCountRecordAggregation(rawRecords, positionLookup, completedPositions) {
  // State
  const selectedLevel = ref(null);
  const allLevels = ref(true);

  /**
   * Computed position level that returns null when "All levels" is active
   */
  const positionLevel = computed({
    get() {
      return allLevels.value ? null : selectedLevel.value;
    },
    set(value) {
      selectedLevel.value = value;
    },
  });

  /**
   * Set position level and disable "All levels" mode
   * @param {number} value - The level to set
   */
  const setPositionLevel = (value) => {
    selectedLevel.value = Number(value);
    allLevels.value = false;
  };

  /**
   * Aggregate records by product and position (at selected level).
   * Supports level-based aggregation where records are grouped by their ancestor position
   * at the specified hierarchy level.
   */
  const aggregatedRecords = computed(() => {
    const records = rawRecords.value;
    if (!records || records.length === 0) return [];

    const lookup = positionLookup.value;
    const aggregateMap = new Map();

    for (const record of records) {
      // Determine aggregate position based on level settings
      const aggPos = getAggregatePosition(record, lookup, allLevels.value, selectedLevel.value);

      // Build aggregate key: product + aggregated position
      const aggregateKey = `${record.product_key}_${aggPos.positionKey}`;

      if (!aggregateMap.has(aggregateKey)) {
        aggregateMap.set(aggregateKey, {
          aggregateKey,
          product: {
            key: record.product_key,
            code: record.product_code,
            description: record.product_description,
            traceability_level: record.product_traceability_level,
            tags: record.product_tags || [],
          },
          position: aggPos.positionKey ? {
            key: aggPos.positionKey,
            code: aggPos.positionCode,
            deleted: aggPos.deleted,
          } : null,
          records: [],
          pathString: aggPos.pathString,
          // Aggregated quantities (set to matching value if all records match, null otherwise)
          totalSystemQt: null,
          totalCountedQt: null,
          delta: null,
          // Serial tracking for aggregation
          allSystemSerialCodes: new Set(),
          allCountedSerialCodes: new Set(),
          serialDelta: { added: [], removed: [] },
          // Conflict and notes
          hasConflict: false,
          hasNotes: false,
          notesCount: 0,
          allNotes: [],
          // Error tracking
          hasError: false,
          allErrorDetails: [],
          errorMessage: null,
          error_details: null,
          // User tracking for multi-user display
          userKeys: new Set(),
          hasMultipleUsers: false,
          user_key: null,
          counted_at: null,
          // Track unique positions being aggregated
          aggregatedPositionKeys: new Set(),
          aggregatedPositionCodes: new Set(),
          // For compatibility with existing code
          activeRecordKey: null,
        });
      }

      const aggregate = aggregateMap.get(aggregateKey);
      aggregate.records.push(record);

      // Track aggregated positions
      if (record.position_key) {
        aggregate.aggregatedPositionKeys.add(record.position_key);
        aggregate.aggregatedPositionCodes.add(record.position_code);
      }

      // Collect notes
      if (record.notes) {
        aggregate.allNotes.push(record.notes);
        aggregate.notesCount++;
        aggregate.hasNotes = true;
      }

      // Collect error details
      if (record.error_details) {
        aggregate.allErrorDetails.push(record.error_details);
        aggregate.hasError = true;
      }

      // Track users
      if (record.user_key) {
        aggregate.userKeys.add(record.user_key);
      }

      // Collect serials for union (only from non-discarded records)
      if (record.status !== 'discarded') {
        // Collect serials for union
        if (record.system_serials) {
          record.system_serials.forEach(s => aggregate.allSystemSerialCodes.add(s.serial_code));
        }
        if (record.counted_serials) {
          record.counted_serials.forEach(s => aggregate.allCountedSerialCodes.add(s.serial_code));
        }
      }
    }

    // Process each aggregate to finalize calculations
    for (const aggregate of aggregateMap.values()) {
      const nonDiscardedRecords = aggregate.records.filter(r => r.status !== 'discarded');

      // Group records by their ORIGINAL product+position pair (base pair)
      // This is important: conflicts only occur when multiple records exist for the SAME base pair
      // When aggregating across different positions, we should SUM the quantities
      const pairMap = new Map();
      for (const record of nonDiscardedRecords) {
        const pairKey = `${record.product_key}_${record.position_key}`;
        if (!pairMap.has(pairKey)) {
          pairMap.set(pairKey, []);
        }
        pairMap.get(pairKey).push(record);
      }

      // Process each base pair: check for conflicts and get representative values
      let totalSystemQt = 0;
      let totalCountedQt = 0;
      let hasConflict = false;

      for (const [pairKey, pairRecords] of pairMap.entries()) {
        if (pairRecords.length > 1) {
          // Multiple records for the same base pair - check if they match
          const firstSystemQt = pairRecords[0].system_qt ?? null;
          const firstCountedQt = pairRecords[0].counted_qt ?? null;

          const allSystemQtMatch = pairRecords.every(r => (r.system_qt ?? null) === firstSystemQt);
          const allCountedQtMatch = pairRecords.every(r => (r.counted_qt ?? null) === firstCountedQt);

          if (!allCountedQtMatch) {
            // Conflict: same product+position has different counted quantities
            hasConflict = true;
          }

          // Use the matching value (or first value if they match)
          // If they don't match, we still need a value for summing - use null to indicate conflict
          if (allSystemQtMatch && firstSystemQt !== null) {
            totalSystemQt += firstSystemQt;
          }
          if (allCountedQtMatch && firstCountedQt !== null) {
            totalCountedQt += firstCountedQt;
          } else if (!allCountedQtMatch) {
            // Can't sum counted quantities when there's a conflict
            totalCountedQt = null;
          }
        } else {
          // Single record for this base pair - no conflict possible
          const record = pairRecords[0];
          totalSystemQt += record.system_qt || 0;
          if (totalCountedQt !== null) {
            totalCountedQt += record.counted_qt || 0;
          }
        }
      }

      aggregate.hasConflict = hasConflict;
      aggregate.totalSystemQt = pairMap.size > 0 ? totalSystemQt : null;
      aggregate.totalCountedQt = hasConflict ? null : (pairMap.size > 0 ? totalCountedQt : null);

      // Calculate aggregated delta (only if both quantities are available)
      if (aggregate.totalSystemQt !== null && aggregate.totalCountedQt !== null) {
        aggregate.delta = aggregate.totalCountedQt - aggregate.totalSystemQt;
      } else {
        aggregate.delta = null;
      }

      // Calculate serial delta from unioned sets
      if (aggregate.allSystemSerialCodes.size > 0 || aggregate.allCountedSerialCodes.size > 0) {
        aggregate.serialDelta = {
          added: [...aggregate.allCountedSerialCodes].filter(s => !aggregate.allSystemSerialCodes.has(s)),
          removed: [...aggregate.allSystemSerialCodes].filter(s => !aggregate.allCountedSerialCodes.has(s)),
        };
      }

      // Recalculate users from non-discarded records only
      const activeUserKeys = new Set();
      for (const record of nonDiscardedRecords) {
        if (record.user_key) {
          activeUserKeys.add(record.user_key);
        }
      }
      const userKeysArray = [...activeUserKeys];
      aggregate.userKeys = userKeysArray;
      aggregate.hasMultipleUsers = userKeysArray.length > 1;

      // Determine user and timestamp to display
      if (aggregate.hasConflict || aggregate.hasMultipleUsers) {
        // Don't show single user/timestamp when there's conflict or multiple users
        aggregate.user_key = null;
        aggregate.counted_at = null;
      } else if (userKeysArray.length === 1) {
        aggregate.user_key = userKeysArray[0];

        // Show timestamp if:
        // 1. There's only one non-discarded record, OR
        // 2. All records' timestamps match at the minute level
        if (nonDiscardedRecords.length === 1) {
          aggregate.counted_at = nonDiscardedRecords[0]?.counted_at || null;
        } else if (nonDiscardedRecords.length > 1) {
          // Check if all timestamps match at the minute level
          const timestamps = nonDiscardedRecords
            .map(r => r.counted_at)
            .filter(Boolean)
            .map(ts => {
              const d = new Date(ts);
              // Truncate to minute by zeroing out seconds and milliseconds
              return new Date(d.getFullYear(), d.getMonth(), d.getDate(), d.getHours(), d.getMinutes()).getTime();
            });

          const allMatchAtMinute = timestamps.length > 0 &&
            timestamps.every(ts => ts === timestamps[0]);

          if (allMatchAtMinute) {
            // Use the most recent timestamp
            const latestRecord = nonDiscardedRecords.sort(
              (a, b) => new Date(b.counted_at) - new Date(a.counted_at)
            )[0];
            aggregate.counted_at = latestRecord?.counted_at || null;
          } else {
            aggregate.counted_at = null;
          }
        } else {
          aggregate.counted_at = null;
        }
      }

      // Set activeRecordKey for compatibility (use most recent non-discarded)
      if (nonDiscardedRecords.length > 0) {
        const latestRecord = nonDiscardedRecords.sort(
          (a, b) => new Date(b.counted_at) - new Date(a.counted_at)
        )[0];
        aggregate.activeRecordKey = latestRecord._key;
      } else if (aggregate.records.length > 0) {
        // All discarded - use most recent discarded
        const latestDiscarded = aggregate.records.filter(r => r.status === 'discarded').sort(
          (a, b) => new Date(b.counted_at) - new Date(a.counted_at)
        )[0];
        aggregate.activeRecordKey = latestDiscarded?._key || null;
      }

      // Convert position Sets to arrays for template use
      aggregate.aggregatedPositionKeys = [...aggregate.aggregatedPositionKeys];
      aggregate.aggregatedPositionCodes = [...aggregate.aggregatedPositionCodes];

      // Coverage tracking: check if the aggregated position has been fully counted
      // Only relevant when aggregating (not in "All levels" mode)
      const completedPositionsSet = completedPositions.value;
      const positionKey = aggregate.position?.key;
      aggregate.coverage = {
        positionKey: positionKey,
        isComplete: positionKey ? completedPositionsSet.has(positionKey) : false,
        // In "All levels" mode, coverage is implicit (each row is granular)
        isAggregated: !allLevels.value,
      };
    }

    return Array.from(aggregateMap.values());
  });

  /**
   * Filter aggregatedRecords to only show those with active (non-discarded) records
   */
  const visibleAggregates = computed(() => {
    return aggregatedRecords.value.filter(aggregate => {
      return aggregate.records.some(r => r.status !== 'discarded');
    });
  });

  /**
   * Count of aggregates that only have discarded records (hidden from view)
   */
  const discardedOnlyCount = computed(() => {
    return aggregatedRecords.value.filter(aggregate => {
      return !aggregate.records.some(r => r.status !== 'discarded');
    }).length;
  });

  return {
    // State
    allLevels,
    selectedLevel,
    positionLevel,
    setPositionLevel,

    // Computed
    aggregatedRecords,
    visibleAggregates,
    discardedOnlyCount,

    // Helpers
    getActiveRecord,
    getDiscardedRecords,
  };
}
