<template>
  <div class="row fit">
    <q-splitter v-model="splitterModel" class="fit">
    <!-- MAIN CONTENT -->
    <template #before>
      <div class="col absolute-full">
        <q-linear-progress v-if="loading" indeterminate absolute-top color="primary" />

        <!-- EMPTY STATE -->
        <div v-if="visibleAggregates.length === 0 && !loading" class="full-height row flex-center text-grey">
          <div class="text-center">
            <div>{{ $t('no_data') }}</div>
            <div v-if="discardedOnlyCount > 0" class="text-caption q-mt-sm">
              {{ $t('warehouse.counting.discarded_records_hidden', { count: discardedOnlyCount }) }}
            </div>
          </div>
        </div>

        <!-- RECORDS TABLE -->
        <q-table
          v-else
          :rows="filteredRecords"
          :columns="tableColumns"
          row-key="aggregateKey"
          flat
          dense
          virtual-scroll
          :rows-per-page-options="[0]"
          class="full-height my-sticky-header-table"
          table-class="text-high"
          table-header-class="uppercase surface1"
          card-class="surface1 no-shadow"
        >
        <!-- Product Column -->
        <template #body-cell-product="props">
          <q-td :props="props" style="max-width: 250px">
            <div class="text-weight-medium">{{ props.row.product.code }}</div>
            <div class="text-caption text-grey ellipsis">{{ props.row.product.description }}</div>
            <q-tooltip anchor="top middle" self="bottom middle" :delay="500">
              <div class="highlight">{{ props.row.product.code }}</div>
              <div>{{ props.row.product.description }}</div>
            </q-tooltip>
          </q-td>
        </template>

        <!-- Position Column -->
        <template #body-cell-position="props">
          <q-td :props="props">
            <div v-if="props.row.position">
              <span :class="{ 'text-strike text-low': props.row.position.deleted }">
                {{ props.row.position.code }}
              </span>
              <!-- Badge showing count of aggregated positions -->
              <q-badge
                v-if="props.row.aggregatedPositionKeys?.length > 1"
                color="primary"
                class="q-ml-xs"
              >
                {{ props.row.aggregatedPositionKeys.length }}
              </q-badge>
              <q-tooltip anchor="top middle" self="bottom middle" :delay="500">
                <template v-if="props.row.position.deleted">
                  <div class="text-theme-orange">{{ $t('position_deleted') }}</div>
                </template>
                <div>{{ props.row.pathString }}</div>
                <!-- Show aggregated positions if more than one -->
                <template v-if="props.row.aggregatedPositionCodes?.length > 1">
                  <q-separator class="q-my-xs" />
                  <div class="text-weight-bold">
                    {{ $t('warehouse.counting.includes_positions', { count: props.row.aggregatedPositionCodes.length }) }}
                  </div>
                  <div v-for="code in props.row.aggregatedPositionCodes.slice(0, 10)" :key="code" class="text-caption">
                    {{ code }}
                  </div>
                  <div v-if="props.row.aggregatedPositionCodes.length > 10" class="text-caption text-grey">
                    +{{ props.row.aggregatedPositionCodes.length - 10 }} {{ $t('more') }}
                  </div>
                </template>
              </q-tooltip>
            </div>
            <div v-else class="text-grey">-</div>
          </q-td>
        </template>

        <!-- User Column -->
        <template #body-cell-user="props">
          <q-td :props="props">
            <!-- Multiple users: show group icon -->
            <template v-if="props.row.hasMultipleUsers">
              <q-icon name="mdi-account-group" size="sm" color="primary">
                <q-tooltip anchor="top middle" self="bottom middle" :delay="500">
                  <div class="text-weight-bold q-mb-xs">{{ $t('warehouse.counting.multiple_users') }}</div>
                  <div v-for="userKey in props.row.userKeys" :key="userKey">
                    {{ store.getters.getUserByKey(userKey)?.name }}
                    {{ store.getters.getUserByKey(userKey)?.surname }}
                  </div>
                </q-tooltip>
              </q-icon>
            </template>
            <!-- Single user: show avatar -->
            <template v-else-if="props.row.user_key && !props.row.hasConflict">
              <BaseUserAvatar
                :user="store.getters.getUserByKey(props.row.user_key)"
                :show_name="false"
                dense
              />
              <q-tooltip anchor="top middle" self="bottom middle" :delay="500">
                {{ store.getters.getUserByKey(props.row.user_key)?.name }}
                {{ store.getters.getUserByKey(props.row.user_key)?.surname }}
              </q-tooltip>
            </template>
            <span v-else class="text-grey">-</span>
          </q-td>
        </template>

        <!-- Counted At Column -->
        <template #body-cell-counted_at="props">
          <q-td :props="props">
            <span v-if="props.row.counted_at && !props.row.hasConflict">
              {{ formatDate(props.row.counted_at) }}
            </span>
            <span v-else class="text-grey">-</span>
          </q-td>
        </template>

        <!-- System Qt Column -->
        <template #body-cell-system_qt="props">
          <q-td :props="props">
            {{ props.row.totalSystemQt ?? '-' }}
          </q-td>
        </template>

        <!-- Counted Qt Column -->
        <template #body-cell-counted_qt="props">
          <q-td :props="props">
            <div class="row items-center q-gutter-x-xs justify-end">
              <span v-if="props.row.totalCountedQt !== null">{{ props.row.totalCountedQt }}</span>
              <q-btn
                v-else-if="props.row.hasConflict"
                icon="mdi-alert"
                color="theme-orange"
                round
                size="xs"
                @click="openConflictDialog(props.row)"
              />
              <span v-else class="text-grey">-</span>
            </div>
          </q-td>
        </template>

        <!-- Delta Column -->
        <template #body-cell-delta="props">
          <q-td :props="props">
            <!-- Show question mark when quantities don't match (non-matching records) -->
            <template v-if="props.row.totalSystemQt === null || props.row.totalCountedQt === null">
              <span class="text-grey">?</span>
            </template>
            <template v-else-if="props.row.activeRecordKey">
              <!-- For products with serial keys, show serial-based delta -->
              <template v-if="props.row.serialDelta && (props.row.serialDelta.added.length > 0 || props.row.serialDelta.removed.length > 0)">
                <div class="row items-center q-gutter-x-xs justify-end weight-bold">

                  <!-- Added/Removed deltas -->
                  <span v-if="props.row.serialDelta.added.length > 0" class="text-theme-green">
                    +{{ props.row.serialDelta.added.length }}
                  </span>
                  <span v-if="props.row.serialDelta.removed.length > 0" class="text-theme-red">
                    -{{ props.row.serialDelta.removed.length }}
                  </span>
                  <span v-if="props.row.serialDelta.added.length === 0 && props.row.serialDelta.removed.length === 0" class="text-grey">
                    0
                  </span>

                  <!-- Tooltip with added/removed serial codes -->
                  <q-tooltip v-if="props.row.serialDelta.added.length > 0 || props.row.serialDelta.removed.length > 0">
                    <div v-if="props.row.serialDelta.added.length > 0" >
                      <strong>{{ $t('warehouse.counting.serials_added') }}:</strong>
                      <div v-for="serial in props.row.serialDelta.added" :key="serial">{{ serial }}</div>
                    </div>
                    <div class="q-mt-sm" v-if="props.row.serialDelta.added.length > 0 && props.row.serialDelta.removed.length > 0">
                    </div>
                    <div v-if="props.row.serialDelta.removed.length > 0">
                      <strong>{{ $t('warehouse.counting.serials_removed') }}:</strong>
                      <div v-for="serial in props.row.serialDelta.removed" :key="serial">{{ serial }}</div>
                    </div>
                  </q-tooltip>
                </div>
              </template>
              <!-- For non-serialized products, show quantity delta -->
              <template v-else>
                <span :class="getDeltaClass(props.row.delta)">
                  {{ formatDelta(props.row.delta) }}
                </span>
              </template>
            </template>
            <span v-else class="text-grey">-</span>
          </q-td>
        </template>

        <!-- Notes Column -->
        <template #body-cell-notes="props">
          <q-td :props="props">
            <template v-if="props.row.hasNotes">
              <q-icon name="mdi-note-text-outline" color="low" size="sm">
                <q-badge v-if="props.row.notesCount > 1" color="primary" floating>
                  {{ props.row.notesCount }}
                </q-badge>
                <q-tooltip anchor="top middle" self="bottom middle">
                  <div v-for="(note, idx) in props.row.allNotes" :key="idx">
                    {{ note }}
                  </div>
                  <q-separator v-if="idx < props.row.notesCount - 1" />
                </q-tooltip>
              </q-icon>
            </template>
          </q-td>
        </template>

        <!-- Conflict Column -->
        <template #body-cell-conflict="props">
          <q-td :props="props">
            <q-btn
              v-if="getDiscardedRecords(props.row).length > 0"
              round
              flat
              size="sm"
              dense
              icon="mdi-information-outline"
              @click="openConflictDialog(props.row)"
            >
              <q-tooltip>
                {{ $t('warehouse.counting.records_discarded', { count: getDiscardedRecords(props.row).length }) }}
              </q-tooltip>
            </q-btn>
          </q-td>
        </template>

        <!-- Table Footer - Row counts and discarded info -->
        <template #bottom>
          <div class="full-width q-py-sm text-caption text-grey row items-center">
            <!-- Discarded records info -->
            <div v-if="discardedOnlyCount > 0" class="row items-center q-gutter-x-xs">
              <q-icon name="mdi-information-outline" size="xs" />
              <span>{{ $t('warehouse.counting.discarded_records_hidden', { count: discardedOnlyCount }) }}</span>
            </div>
            <q-space />
            <!-- Row counts -->
            <div>
              {{ filteredRecords.length }} / {{ visibleAggregates.length }}
            </div>
          </div>
        </template>
        </q-table>
      </div>
    </template>

    <!-- FILTER SIDEBAR -->
    <template #after>
      <div class="column q-gutter-md q-pa-md">

        <!-- Export/Import Actions -->
        <div class="col-auto row q-gutter-sm">
          <q-btn-dropdown
            :label="$t('export')"
            icon="mdi-download"
            color="primary"
            outline
            dense
            no-caps
            :loading="exporting"
          >
            <q-list>
              <q-item clickable v-close-popup @click="handleExportXLSX">
                <q-item-section avatar>
                  <q-icon name="mdi-file-excel" color="green" />
                </q-item-section>
                <q-item-section>Excel (.xlsx)</q-item-section>
              </q-item>
              <q-item clickable v-close-popup @click="handleExportCSV">
                <q-item-section avatar>
                  <q-icon name="mdi-file-delimited" color="blue" />
                </q-item-section>
                <q-item-section>CSV (.csv)</q-item-section>
              </q-item>
            </q-list>
          </q-btn-dropdown>
          <q-btn
            :label="$t('import')"
            icon="mdi-upload"
            color="primary"
            outline
            dense
            no-caps
            @click="importDialogOpen = true"
          />
        </div>

        <q-separator />

        <div class="text-h5 uppercase">{{ $t('filter', 2) }}</div>

        <!-- Variance & only-with-variance -->
        <div class="col-auto row items-center">
          <div class="col-6">
            <q-checkbox
              v-model="filters.onlyWithVariance"
              :label="$t('warehouse.counting.variance_only')"
              dense
            />
          </div>
          <div class="col-6">
            <!-- Has Notes -->
            <q-checkbox
              v-model="filters.hasNotes"
              :label="$t('warehouse.counting.with_notes_only')"
              dense
            />
          </div>
          <div class="col-6">
            <!-- Only Conflicts -->
            <q-checkbox
              v-model="filters.onlyConflicts"
              :label="$t('warehouse.counting.conflicts_only')"
              dense
            />
          </div>
        </div>

        <div class="col-auto">
          <q-input
          v-model="filters.variance"
          type="number"
            class="full-width"
            min="0"
            :max="filters.varianceType === 'percentage' ? 100 : null"
            :label="$t('warehouse.counting.variance_threshold')"
            stack-label
            dense
            filled
          >
            <template #append>
              <q-btn-toggle
                v-model="filters.varianceType"
                map-options
                emit-value
                dense
                flat
                size="md"
                :options="[
                  { label: $t('quantity.short'), value: 'absolute' },
                  { label: '%', value: 'percentage' },
                ]"/>
            </template>
          </q-input>
        </div>

        <!-- Position Level -->
        <div class="col-auto">
          <q-input
            :model-value.number="positionLevel"
            @update:model-value="setPositionLevel"
            type="number"
            :label="$t('warehouse.counting.position_level')"
            class="full-width"
            dense
            filled
            min="0"
          >
            <template #append>
              <q-btn
                :color="allLevels ? 'primary' : 'white-low'"
                size="sm"
                padding="xs md"
                outline
                dense
                @click="allLevels = !allLevels">
                <div class="q-mr-sm">{{ $t('all') }}</div>
                <q-icon name="mdi-family-tree" size="xs" />
              </q-btn>
            </template>
          </q-input>
        </div>

        <!-- Text & tag filters -->

        <!-- Product Tag Filter -->
        <BaseAutocompleteTag
          :value="filters.productTag"
          :key-only="true"
          :label="$t('search_tags')"
          dense
          @select="val => (filters.productTag = val)"
        />

        <!-- User Filter -->
        <BaseAutocompleteUser
          :value="filters.userKey"
          :key-only="true"
          :operator-only="false"
          dense
          :label="$t('warehouse.counting.user')"
          @select="val => (filters.userKey = val)"
        />

        <!-- Product Filter -->
        <q-input
          v-model="filters.product"
          :label="$t('product.label')"
          dense
          filled
          clearable
        />

        <!-- Serial Filter -->
        <q-input
          v-model="filters.serial"
          :label="$t('serial')"
          dense
          filled
          clearable
        />

        <!-- Position / Path Filter -->
          <q-input
            v-model="filters.position"
            :label="$t('warehouse.inventory.position')"
            dense
            filled
            clearable
          />
          <q-toggle
            v-model="filters.positionIncludePath"
            :label="$t('warehouse.counting.include_path')"
            dense
          />
      </div>
    </template>
    </q-splitter>

    <!-- CONFLICT RESOLUTION DIALOG -->
    <CountRecordConflictDialog
      v-model="conflictDialogOpen"
      :aggregate="selectedConflictAggregate"
      @resolve="handleConflictResolved"
    />

    <!-- IMPORT DIALOG -->
    <CountRecordImportDialog
      v-model="importDialogOpen"
      :session-key="countSessionStore.currentSession"
      @imported="handleImportCompleted"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useStore } from 'vuex';
import { useCountSessionStore } from '@/stores/countSession';
import { api } from '@/boot/axios.js';
import { useWildcardToRegex } from '@/composables/useWildcardToRegex';
import CountRecordConflictDialog from '@/components/warehouse/counting/CountRecordConflictDialog.vue';
import CountRecordImportDialog from '@/components/warehouse/counting/CountRecordImportDialog.vue';
import BaseAutocompleteTag from '@/components/BaseAutocompleteTag.vue';
import BaseAutocompleteUser from '@/components/BaseAutocompleteUser.vue';
import BaseUserAvatar from '@/components/BaseUserAvatar.vue';
import { formatDateTime } from '@/lib/TimeHandling';
import { useCountRecordExport } from '@/composables/useCountRecordExport';

const { t: $t, locale } = useI18n();
const store = useStore();
const countSessionStore = useCountSessionStore();
const { wildcardToRegex } = useWildcardToRegex();

const splitterModel = ref(70);
// State
const displayMode = ref('pair');
const selectedLevel = ref(1);
const allLevels = ref(false);
const positionLevel = computed({
  get() {
    return allLevels.value ? null : selectedLevel.value;
  },
  set(value) {
    selectedLevel.value = value;
  },
});

const setPositionLevel = (value) => {
  selectedLevel.value = value;
  allLevels.value = false;
};

const conflictDialogOpen = ref(false);
const selectedConflictAggregate = ref(null);
const events = ref(null);
const importDialogOpen = ref(false);

// Export composable
const { exporting, exportToXLSX, exportToCSV } = useCountRecordExport();

// Filters
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

// Display mode options
const displayModeOptions = computed(() => [
  { label: $t('warehouse.counting.by_pair'), value: 'pair' },
  { label: $t('warehouse.counting.by_product'), value: 'product' },
  { label: $t('warehouse.counting.by_position_level'), value: 'position_level' },
]);


// Loading state from store
const loading = computed(() => countSessionStore.recordsLoading);

// Raw records from store
const rawRecords = computed(() => countSessionStore.records);

// Position lookup (for path-based search)
const positionLookup = computed(() => countSessionStore.positionLookup);

function getActiveRecord(row) {
  if (!row.activeRecordKey) return null;
  return row.records.find(r => r._key === row.activeRecordKey);
}

function getDiscardedRecords(row) {
  return row.records.filter(r => r.status === 'discarded');
}

// Table columns
const tableColumns = computed(() => [
  {
    name: 'product',
    label: $t('product.label'),
    field: 'product',
    align: 'left',
    sortable: true,
  },
  {
    name: 'position',
    label: $t('warehouse.inventory.position'),
    field: 'position',
    align: 'left',
    sortable: true,
  },
  {
    name: 'user',
    label: $t('warehouse.counting.user'),
    field: row => row.user_key,
    align: 'center',
  },
  {
    name: 'counted_at',
    label: $t('warehouse.counting.counted_at'),
    field: row => row.counted_at,
    align: 'left',
    sortable: true,
  },
  {
    name: 'system_qt',
    label: $t('warehouse.counting.system_qt'),
    field: row => row.totalSystemQt,
    align: 'right',
  },
  {
    name: 'counted_qt',
    label: $t('warehouse.counting.counted_qt'),
    field: row => row.totalCountedQt,
    align: 'right',
  },
  {
    name: 'delta',
    label: $t('warehouse.counting.delta'),
    field: row => row.delta,
    align: 'right',
    sortable: true,
  },
  {
    name: 'notes',
    label: $t('notes'),
    field: 'notes',
    align: 'center',
  },
  {
    name: 'conflict',
    label: '',
    field: 'conflict',
    align: 'center',
    style: 'width: 50px',
  },
]);

/**
 * Build a case-insensitive matcher using the shared wildcard-to-regex composable.
 * If pattern is empty/null, matcher always returns true.
 */
function buildWildcardMatcher(pattern) {
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
 * Determine the aggregate position key for a record based on the selected level.
 * - If allLevels is true: use the record's actual position (no level aggregation)
 * - If level is 0: aggregate at root (all positions for same product)
 * - If level >= 1: use the ancestor at that level, or actual position if shallower
 *
 * Note on levels:
 * - User expectation: IN = level 0, children of IN = level 1, grandchildren = level 2, etc.
 * - positionLookup.level: children of IN = level 0, grandchildren = level 1, etc.
 * - So: actualLevel = positionLookup.level + 1
 *
 * @param {Object} record - The count record
 * @param {Map} lookup - The positionLookup map
 * @returns {Object} { positionKey, positionCode, pathString }
 */
function getAggregatePosition(record, lookup) {
  // If "All" is toggled, use the actual position (most granular)
  // Path should NOT include IN (it's implied)
  if (allLevels.value) {
    return {
      positionKey: record.position_key,
      positionCode: record.position_code,
      pathString: record.position_path?.join(' > ') || record.position_code || '',
      deleted: record.position_deleted || false,
    };
  }

  const targetLevel = selectedLevel.value;

  // Level 0 means aggregate everything (total inventory for product)
  if (targetLevel === 0) {
    return {
      positionKey: 'IN',
      positionCode: 'IN',
      pathString: 'IN',
      deleted: false,
    };
  }

  // Fallback: use position_path from record (array of codes, excluding IN)
  // position_path[0] = level 1 position, position_path[1] = level 2 position, etc.
  // This is the most reliable source as it comes directly from the backend
  const path = record.position_path || [];

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
  // targetLevel 1 → path[0], targetLevel 2 → path[1], etc.
  const targetIndex = targetLevel - 1;
  const targetCode = path[targetIndex];

  // Try to get the position key from positionLookup using code
  // Build a code-to-key map from lookup if available
  let targetKey = targetCode; // Default to code if we can't find key
  if (lookup && lookup.size > 0) {
    for (const [key, data] of lookup.entries()) {
      if (data.code === targetCode) {
        targetKey = key;
        break;
      }
    }
  }

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
    const aggPos = getAggregatePosition(record, lookup);

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

    // Convert userKeys Set to array and determine if multiple users
    const userKeysArray = [...aggregate.userKeys];
    aggregate.userKeys = userKeysArray;
    aggregate.hasMultipleUsers = userKeysArray.length > 1;

    // Determine user and timestamp to display
    const isAggregatingMultiplePositions = aggregate.aggregatedPositionKeys.size > 1;

    if (aggregate.hasConflict || aggregate.hasMultipleUsers) {
      // Don't show single user/timestamp when there's conflict or multiple users
      aggregate.user_key = null;
      aggregate.counted_at = null;
    } else if (userKeysArray.length === 1) {
      aggregate.user_key = userKeysArray[0];
      // If single user but multiple positions, don't show timestamp
      if (isAggregatingMultiplePositions) {
        aggregate.counted_at = null;
      } else {
        // Single user, single position - use the most recent timestamp
        const latestRecord = nonDiscardedRecords.sort(
          (a, b) => new Date(b.counted_at) - new Date(a.counted_at)
        )[0];
        aggregate.counted_at = latestRecord?.counted_at || null;
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

/**
 * Apply filters to visible aggregated records
 */
const filteredRecords = computed(() => {
  let result = visibleAggregates.value;

  // Pre-build wildcard matchers
  const productMatcher = buildWildcardMatcher(filters.value.product);
  const serialMatcher = buildWildcardMatcher(filters.value.serial);
  const positionMatcher = buildWildcardMatcher(filters.value.position);

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

// Methods
async function loadRecords() {
  try {
    await countSessionStore.loadRecords(null, { // current session is stored in the store
      include_started: false,
    });
  } catch (error) {
    console.error('Error loading records:', error);
  }
}

function getDeltaClass(delta) {
  if (delta === null || delta === undefined) return 'text-grey';
  if (delta > 0) return 'text-theme-green text-weight-bold';
  if (delta < 0) return 'text-theme-red text-weight-bold';
  return 'text-grey';
}

function formatDelta(delta) {
  if (delta === null || delta === undefined) return '-';
  if (delta > 0) return `+${delta}`;
  return String(delta);
}

function formatDate(date) {
  return formatDateTime(
    date,
    locale.value,
    { dateStyle: 'short', timeStyle: 'short' }
  );
}

function openConflictDialog(aggregate) {
  selectedConflictAggregate.value = aggregate;
  conflictDialogOpen.value = true;
}

async function handleConflictResolved() {
  // Reload records after conflict resolution
  await loadRecords();
  conflictDialogOpen.value = false;
  selectedConflictAggregate.value = null;
}

// Export/Import handlers
function getUserName(userKey) {
  const user = store.getters.getUserByKey(userKey);
  if (user) {
    return `${user.name || ''} ${user.surname || ''}`.trim() || userKey;
  }
  return userKey || '';
}

function handleExportXLSX() {
  const sessionKey = countSessionStore.currentSession;
  const sessionCode = countSessionStore.sessionData?.code || sessionKey;
  exportToXLSX(sessionKey, sessionCode, getUserName);
}

function handleExportCSV() {
  const sessionKey = countSessionStore.currentSession;
  const sessionCode = countSessionStore.sessionData?.code || sessionKey;
  exportToCSV(sessionKey, sessionCode, getUserName);
}

async function handleImportCompleted() {
  // Reload records after import
  await loadRecords();
}

// Load records on mount
onMounted(() => {
  loadRecords();
  // Load position hierarchy to enable level-based aggregation
  countSessionStore.loadPositions();

  // Subscribe to inventory notifications so records update automatically
  const eventURL = `${api.defaults.baseURL}/notification/inventory-notification`;
  events.value = new EventSource(eventURL, {
    withCredentials: false,
  });
  events.value.addEventListener('inventory-notification', () => {
    loadRecords();
  });
});

onBeforeUnmount(() => {
  if (events.value) {
    events.value.close();
  }
});

// Reload when display mode changes
watch(displayMode, () => {
  // Records stay the same, just re-aggregate
});

watch(filters, () => {
  loadRecords();
});
</script>
