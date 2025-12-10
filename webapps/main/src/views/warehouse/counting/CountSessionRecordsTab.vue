<template>
  <div class="row fit">
    <q-splitter v-model="splitterModel" class="fit">
    <!-- MAIN CONTENT -->
    <template #before>
      <div class="col absolute-full">
        <q-linear-progress v-if="loading" indeterminate absolute-top color="primary" />

        <!-- EMPTY STATE -->
        <div v-if="aggregatedRecords.length === 0 && !loading" class="full-height row flex-center text-grey">
          {{ $t('no_data') }}
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
          </q-td>
        </template>

        <!-- Position Column -->
        <template #body-cell-position="props">
          <q-td :props="props">
            <span v-if="props.row.position">{{ props.row.position.code }}</span>
            <span v-else class="text-grey">-</span>
          </q-td>
        </template>

        <!-- Counted Qt Column -->
        <template #body-cell-counted_qt="props">
          <q-td :props="props">
            {{ props.row.activeRecord?.counted_qt ?? '-' }}
          </q-td>
        </template>

        <!-- Delta Column -->
        <template #body-cell-delta="props">
          <q-td :props="props">
            <template v-if="props.row.hasConflict">
              <q-btn icon="mdi-alert" color="theme-orange" round size="xs" @click="openConflictDialog(props.row)" />
            </template>
            <template v-else-if="props.row.activeRecord">
              <!-- For products with serial keys, show serial-based delta -->
              <template v-if="props.row.serialDelta && (props.row.serialDelta.added.length > 0 || props.row.serialDelta.removed.length > 0)">
                <div class="row items-center q-gutter-x-xs justify-end">
                  <span v-if="props.row.serialDelta.added.length > 0" class="text-theme-green">
                    +{{ props.row.serialDelta.added.length }}
                  </span>
                  <span v-if="props.row.serialDelta.removed.length > 0" class="text-theme-red">
                    -{{ props.row.serialDelta.removed.length }}
                  </span>
                  <span v-if="props.row.serialDelta.added.length === 0 && props.row.serialDelta.removed.length === 0" class="text-grey">
                    0
                  </span>
                  <q-tooltip v-if="props.row.serialDelta.added.length > 0 || props.row.serialDelta.removed.length > 0">
                    <div v-if="props.row.serialDelta.added.length > 0">
                      <strong>{{ $t('warehouse.counting.serials_added') }}:</strong>
                      <div v-for="serial in props.row.serialDelta.added" :key="serial">{{ serial }}</div>
                    </div>
                    <div v-if="props.row.serialDelta.removed.length > 0" class="q-mt-sm">
                      <strong>{{ $t('warehouse.counting.serials_removed') }}:</strong>
                      <div v-for="serial in props.row.serialDelta.removed" :key="serial">{{ serial }}</div>
                    </div>
                  </q-tooltip>
                </div>
              </template>
              <!-- For non-serialized products, show quantity delta -->
              <template v-else>
                <span :class="getDeltaClass(props.row.activeRecord.delta)">
                  {{ formatDelta(props.row.activeRecord.delta) }}
                </span>
              </template>
            </template>
            <span v-else class="text-grey">-</span>
          </q-td>
        </template>

        <!-- Serials Column -->
        <template #body-cell-serials="props">
          <q-td :props="props">
            <template v-if="props.row.product.traceability_level === 'complete' && props.row.activeRecord">
              <div class="row items-center q-gutter-x-xs">
                <!-- Added/Removed deltas -->
                <span v-if="props.row.serialDelta.added.length > 0" class="text-theme-green">
                  +{{ props.row.serialDelta.added.length }}
                </span>
                <span v-if="props.row.serialDelta.removed.length > 0" class="text-theme-red">
                  -{{ props.row.serialDelta.removed.length }}
                </span>

                <!-- Tooltip with added/removed serial codes -->
                <q-tooltip v-if="props.row.serialDelta.added.length > 0 || props.row.serialDelta.removed.length > 0">
                  <div v-if="props.row.serialDelta.added.length > 0">
                    <strong>{{ $t('warehouse.counting.serials_added') }}:</strong>
                    <div v-for="serial in props.row.serialDelta.added" :key="serial">{{ serial }}</div>
                  </div>
                  <div v-if="props.row.serialDelta.removed.length > 0" class="q-mt-sm">
                    <strong>{{ $t('warehouse.counting.serials_removed') }}:</strong>
                    <div v-for="serial in props.row.serialDelta.removed" :key="serial">{{ serial }}</div>
                  </div>
                </q-tooltip>
              </div>
            </template>
            <span v-else class="text-grey">-</span>
          </q-td>
        </template>

        <!-- Notes Column -->
        <template #body-cell-notes="props">
          <q-td :props="props">
            <template v-if="props.row.hasNotes">
              <q-icon name="mdi-note-text" color="primary" size="sm">
                <q-badge v-if="props.row.notesCount > 1" color="primary" floating>
                  {{ props.row.notesCount }}
                </q-badge>
              </q-icon>
              <q-tooltip>
                <div v-for="(note, idx) in props.row.allNotes" :key="idx" class="q-mb-xs">
                  {{ note }}
                </div>
              </q-tooltip>
            </template>
          </q-td>
        </template>

        <!-- Conflict Column -->
        <template #body-cell-conflict="props">
          <q-td :props="props">
            <q-btn
              v-if="props.row.discardedRecords.length > 0"
              round
              flat
              size="sm"
              dense
              icon="mdi-information-outline"
              @click="openConflictDialog(props.row)"
            >
              <q-tooltip>
                {{ $t('warehouse.counting.records_discarded', { count: props.row.discardedRecords.length }) }}
              </q-tooltip>
            </q-btn>
          </q-td>
        </template>
        </q-table>
      </div>
    </template>

    <!-- FILTER SIDEBAR -->
    <template #after>
      <div class="column q-gutter-md q-pa-md">

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
        </div>

        <div class="col-auto row items-center justify-between">
          <div class="col-8">
            <q-input
              v-model="filters.variance"
              type="number"
              min="0"
              :max="filters.varianceType === 'percentage' ? 100 : null"
              :label="$t('warehouse.counting.variance_threshold')"
              stack-label
              dense
              filled
            />
          </div>
          <div class="col-auto q-ml-md">
            <q-btn-toggle
              v-model="filters.varianceType"
              map-options
              emit-value

              dense
              padding="xs md"
              :options="[
                { label: $t('quantity.short'), value: 'absolute' },
                { label: '%', value: 'percentage' },
              ]">
            </q-btn-toggle>
          </div>
        </div>

        <!-- Position Level -->
        <div class="col-auto row items-center justify-between">
          <div class="col-8">
            <q-input
              :model-value.number="positionLevel"
              @update:model-value="setPositionLevel"
              type="number"
              :label="$t('warehouse.counting.position_level')"
              dense
              filled
              min="1"
            />
          </div>

          <div class="col-auto q-ml-md">
            <q-btn
              :color="allLevels ? 'primary' : 'white-low'"
              size="sm"
              padding="xs md"
              dense
              @click="allLevels = !allLevels">
              <div class="q-mr-sm">{{ $t('all') }}</div>
              <q-icon name="mdi-family-tree" size="xs" />
            </q-btn>
          </div>
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
import BaseAutocompleteTag from '@/components/BaseAutocompleteTag.vue';

const { t: $t } = useI18n();
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

// Filters
const filters = ref({
  variance: null,
  varianceType: 'absolute',
  onlyWithVariance: false,
  hasNotes: false,
  product: '',
  serial: '',
  position: '',
  positionIncludePath: false,
  productTag: null,
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
    name: 'system_qt',
    label: $t('warehouse.counting.system_qt'),
    field: row => row.activeRecord?.system_qt,
    align: 'right',
    sortable: true,
  },
  {
    name: 'counted_qt',
    label: $t('warehouse.counting.counted_qt'),
    field: row => row.activeRecord?.counted_qt,
    align: 'right',
    sortable: true,
  },
  {
    name: 'delta',
    label: $t('warehouse.counting.delta'),
    field: row => row.activeRecord?.delta,
    align: 'right',
    sortable: true,
  },
  {
    name: 'serials',
    label: $t('serials'),
    field: 'serials',
    align: 'center',
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
 * Aggregate records by product/position pair
 */
const aggregatedRecords = computed(() => {
  const records = rawRecords.value;
  if (!records || records.length === 0) return [];

  const aggregateMap = new Map();

  for (const record of records) {
    // Build aggregate key based on display mode
    let aggregateKey;
    if (displayMode.value === 'pair') {
      aggregateKey = `${record.product_key}_${record.position_key}`;
    } else if (displayMode.value === 'product') {
      aggregateKey = record.product_key;
    } else {
      // position_level mode - would need position hierarchy data
      // For now, fall back to pair mode
      aggregateKey = `${record.product_key}_${record.position_key}`;
    }

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
        position: record.position_key ? {
          key: record.position_key,
          code: record.position_code,
        } : null,
        records: [],
        activeRecord: null,
        discardedRecords: [],
        hasConflict: false,
        hasNotes: false,
        notesCount: 0,
        allNotes: [],
        serialDelta: { added: [], removed: [] },
      });
    }

    const aggregate = aggregateMap.get(aggregateKey);
    aggregate.records.push(record);

    // Collect notes
    if (record.notes) {
      aggregate.allNotes.push(record.notes);
      aggregate.notesCount++;
      aggregate.hasNotes = true;
    }

    // Categorize records
    if (record.status === 'discarded') {
      aggregate.discardedRecords.push(record);
    }
  }

  // Process each aggregate to determine active record and conflicts
  for (const aggregate of aggregateMap.values()) {
    const nonDiscardedRecords = aggregate.records.filter(r => r.status !== 'discarded');

    if (nonDiscardedRecords.length === 0) {
      // All records discarded, use the most recent discarded one for display
      aggregate.activeRecord = aggregate.discardedRecords[0] || null;
    } else if (nonDiscardedRecords.length === 1) {
      aggregate.activeRecord = nonDiscardedRecords[0];
    } else {
      // Multiple non-discarded records - check if they match
      const firstQt = nonDiscardedRecords[0].counted_qt;
      const allMatch = nonDiscardedRecords.every(r => r.counted_qt === firstQt);

      if (allMatch) {
        // All counts match, use the first one
        aggregate.activeRecord = nonDiscardedRecords[0];
      } else {
        // Conflict - different counts
        aggregate.hasConflict = true;
        // Show the most recent one but mark as conflict
        aggregate.activeRecord = nonDiscardedRecords.sort(
          (a, b) => new Date(b.counted_at) - new Date(a.counted_at)
        )[0];
      }
    }

    // Calculate serial delta for products with serial keys
    if (aggregate.activeRecord) {
      const hasSystemSerials = aggregate.activeRecord.system_serial_keys && aggregate.activeRecord.system_serial_keys.length > 0;
      const hasCountedSerials = aggregate.activeRecord.counted_serial_keys && aggregate.activeRecord.counted_serial_keys.length > 0;

      if (hasSystemSerials || hasCountedSerials) {
        const systemSerialsCodes = new Set(aggregate.activeRecord.system_serials.map(s => s.serial_code) || []);
        const countedSerialsCodes = new Set(aggregate.activeRecord.counted_serials.map(s => s.serial_code) || []);

        aggregate.serialDelta = {
          added: [...countedSerialsCodes].filter(s => !systemSerialsCodes.has(s)),
          removed: [...systemSerialsCodes].filter(s => !countedSerialsCodes.has(s)),
        };
      }
    }

    // Calculate delta for active record
    if (aggregate.activeRecord) {
      aggregate.activeRecord.delta = (aggregate.activeRecord.counted_qt ?? 0) - (aggregate.activeRecord.system_qt ?? 0);
    }
  }

  return Array.from(aggregateMap.values());
});

/**
 * Apply filters to aggregated records
 */
const filteredRecords = computed(() => {
  let result = aggregatedRecords.value;

  // Pre-build wildcard matchers
  const productMatcher = buildWildcardMatcher(filters.value.product);
  const serialMatcher = buildWildcardMatcher(filters.value.serial);
  const positionMatcher = buildWildcardMatcher(filters.value.position);

  // Variance filter
  if (filters.value.variance !== null && filters.value.variance !== '') {
    const threshold = Number(filters.value.variance);
    result = result.filter(r => {
      if (!r.activeRecord) return false;
      const delta = Math.abs(r.activeRecord.delta || 0);
      if (filters.value.varianceType === 'percentage') {
        const systemQt = r.activeRecord.system_qt || 1;
        const percentVariance = (delta / systemQt) * 100;
        return percentVariance >= threshold;
      }
      return delta >= threshold;
    });
  }

  // Only with variance filter
  if (filters.value.onlyWithVariance) {
    result = result.filter((r) => {
      const delta = r.activeRecord?.delta;
      return delta !== null && delta !== undefined && delta !== 0;
    });
  }

  // Has notes filter
  if (filters.value.hasNotes) {
    result = result.filter(r => r.hasNotes);
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

  // Serial filter
  if (filters.value.serial) {
    result = result.filter(r => {
      const allSerials = [
        ...(r.activeRecord?.system_serial_keys || []),
        ...(r.activeRecord?.counted_serial_keys || []),
      ];
      return allSerials.some(s => serialMatcher(s));
    });
  }

  // Position filter
  if (filters.value.position) {
    result = result.filter(r => {
      if (!r.position) return false;
      const lookup = positionLookup.value;
      const posData = lookup ? lookup.get(r.position.key) : null;
      const pathString = posData?.pathString || r.position.code;

      if (filters.value.positionIncludePath) {
        return positionMatcher(pathString);
      }
      return positionMatcher(r.position.code);
    });
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

// Load records on mount
onMounted(() => {
  loadRecords();

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
