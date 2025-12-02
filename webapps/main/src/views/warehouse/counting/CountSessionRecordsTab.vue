<template>
  <div class="column full-height">
    <!-- HEADER / TOOLBAR -->
    <div class="col-auto q-pa-md row items-center justify-between">
      <div class="row items-center q-gutter-x-md">
        <!-- Display Mode -->
        <q-select
          v-model="displayMode"
          :options="displayModeOptions"
          :label="$t('warehouse.counting.display_mode')"
          dense
          outlined
          emit-value
          map-options
          style="min-width: 180px"
        />
        <!-- Position Level (only for position_level mode) -->
        <q-input
          v-if="displayMode === 'position_level'"
          v-model.number="positionLevel"
          type="number"
          :label="$t('warehouse.counting.position_level')"
          dense
          outlined
          min="1"
          style="width: 100px"
        />
      </div>
      <div class="row items-center q-gutter-x-sm">
        <!-- Filter Toggle -->
        <q-btn
          :icon="showFilters ? 'mdi-filter-off' : 'mdi-filter'"
          flat
          round
          dense
          @click="showFilters = !showFilters"
        >
          <q-tooltip>{{ $t('filters') }}</q-tooltip>
        </q-btn>
        <!-- Refresh -->
        <q-btn
          icon="mdi-refresh"
          flat
          round
          dense
          @click="loadRecords"
        >
          <q-tooltip>{{ $t('refresh') }}</q-tooltip>
        </q-btn>
      </div>
    </div>

    <!-- FILTERS PANEL -->
    <q-slide-transition>
      <div v-if="showFilters" class="col-auto q-px-md q-pb-md">
        <div class="row q-gutter-md items-end">
          <!-- Variance Filter -->
          <div class="row items-center q-gutter-x-sm">
            <q-input
              v-model.number="filters.variance"
              type="number"
              :label="$t('warehouse.counting.variance_filter')"
              dense
              outlined
              style="width: 120px"
            />
            <q-toggle
              v-model="filters.varianceIsPercent"
              :label="filters.varianceIsPercent ? '%' : $t('warehouse.counting.absolute')"
              dense
            />
          </div>
          <!-- Has Notes -->
          <q-checkbox
            v-model="filters.hasNotes"
            :label="$t('warehouse.counting.has_notes')"
            dense
          />
          <!-- Product Filter -->
          <q-input
            v-model="filters.product"
            :label="$t('product')"
            dense
            outlined
            clearable
            style="width: 200px"
          />
          <!-- Serial Filter -->
          <q-input
            v-model="filters.serial"
            :label="$t('serial')"
            dense
            outlined
            clearable
            style="width: 200px"
          />
          <!-- Position Filter -->
          <div class="row items-center q-gutter-x-sm">
            <q-input
              v-model="filters.position"
              :label="$t('position')"
              dense
              outlined
              clearable
              style="width: 200px"
            />
            <q-toggle
              v-model="filters.positionIncludePath"
              :label="$t('warehouse.counting.include_path')"
              dense
            />
          </div>
        </div>
      </div>
    </q-slide-transition>

    <q-separator />

    <!-- CONTENT -->
    <div class="col relative-position">
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
        class="full-height"
        table-class="text-high"
        card-class="background no-shadow"
      >
        <!-- Product Column -->
        <template #body-cell-product="props">
          <q-td :props="props">
            <div class="text-weight-medium">{{ props.row.product.code }}</div>
            <div class="text-caption text-grey">{{ props.row.product.description }}</div>
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
              <q-icon name="mdi-help-circle" color="warning" size="sm" />
            </template>
            <template v-else-if="props.row.activeRecord">
              <span :class="getDeltaClass(props.row.activeRecord.delta)">
                {{ formatDelta(props.row.activeRecord.delta) }}
              </span>
            </template>
            <span v-else class="text-grey">-</span>
          </q-td>
        </template>

        <!-- Serials Column -->
        <template #body-cell-serials="props">
          <q-td :props="props">
            <template v-if="props.row.product.traceability_level === 'complete' && props.row.activeRecord">
              <div class="row items-center q-gutter-x-xs">
                <span v-if="props.row.serialDelta.added.length > 0" class="text-theme-green">
                  +{{ props.row.serialDelta.added.length }}
                </span>
                <span v-if="props.row.serialDelta.removed.length > 0" class="text-theme-red">
                  -{{ props.row.serialDelta.removed.length }}
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
              v-if="props.row.hasConflict"
              icon="mdi-alert-circle"
              color="warning"
              flat
              round
              dense
              @click="openConflictDialog(props.row)"
            >
              <q-tooltip>{{ $t('warehouse.counting.conflict_detected') }}</q-tooltip>
            </q-btn>
            <q-icon
              v-else-if="props.row.discardedRecords.length > 0"
              name="mdi-check-circle"
              color="positive"
              size="sm"
            >
              <q-tooltip>
                {{ $t('warehouse.counting.records_discarded', { count: props.row.discardedRecords.length }) }}
              </q-tooltip>
            </q-icon>
          </q-td>
        </template>
      </q-table>
    </div>

    <!-- CONFLICT RESOLUTION DIALOG -->
    <CountRecordConflictDialog
      v-model="conflictDialogOpen"
      :aggregate="selectedConflictAggregate"
      @resolve="handleConflictResolved"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useStore } from 'vuex';
import { useCountSessionStore } from '@/stores/countSession';
import CountRecordConflictDialog from '@/components/warehouse/counting/CountRecordConflictDialog.vue';

const { t: $t } = useI18n();
const store = useStore();
const countSessionStore = useCountSessionStore();

// State
const showFilters = ref(false);
const displayMode = ref('pair');
const positionLevel = ref(1);
const conflictDialogOpen = ref(false);
const selectedConflictAggregate = ref(null);

// Filters
const filters = ref({
  variance: null,
  varianceIsPercent: false,
  hasNotes: false,
  product: '',
  serial: '',
  position: '',
  positionIncludePath: false,
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

// Table columns
const tableColumns = computed(() => [
  {
    name: 'product',
    label: $t('product'),
    field: 'product',
    align: 'left',
    sortable: true,
  },
  {
    name: 'position',
    label: $t('position'),
    field: 'position',
    align: 'left',
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

    // Calculate serial delta for traceable products
    if (aggregate.product.traceability_level === 'complete' && aggregate.activeRecord) {
      const systemSerials = new Set(aggregate.activeRecord.system_serial_keys || []);
      const countedSerials = new Set(aggregate.activeRecord.counted_serial_keys || []);

      aggregate.serialDelta = {
        added: [...countedSerials].filter(s => !systemSerials.has(s)),
        removed: [...systemSerials].filter(s => !countedSerials.has(s)),
      };
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

  // Variance filter
  if (filters.value.variance !== null && filters.value.variance !== '') {
    const threshold = Number(filters.value.variance);
    result = result.filter(r => {
      if (!r.activeRecord) return false;
      const delta = Math.abs(r.activeRecord.delta || 0);
      if (filters.value.varianceIsPercent) {
        const systemQt = r.activeRecord.system_qt || 1;
        const percentVariance = (delta / systemQt) * 100;
        return percentVariance >= threshold;
      }
      return delta >= threshold;
    });
  }

  // Has notes filter
  if (filters.value.hasNotes) {
    result = result.filter(r => r.hasNotes);
  }

  // Product filter
  if (filters.value.product) {
    const search = filters.value.product.toLowerCase();
    result = result.filter(r =>
      r.product.code?.toLowerCase().includes(search) ||
      r.product.description?.toLowerCase().includes(search)
    );
  }

  // Serial filter
  if (filters.value.serial) {
    const search = filters.value.serial.toLowerCase();
    result = result.filter(r => {
      const allSerials = [
        ...(r.activeRecord?.system_serial_keys || []),
        ...(r.activeRecord?.counted_serial_keys || []),
      ];
      return allSerials.some(s => s.toLowerCase().includes(search));
    });
  }

  // Position filter
  if (filters.value.position) {
    const search = filters.value.position.toLowerCase();
    result = result.filter(r => {
      if (!r.position) return false;
      if (filters.value.positionIncludePath) {
        // TODO: Include position path in search when hierarchy data is available
        return r.position.code?.toLowerCase().includes(search);
      }
      return r.position.code?.toLowerCase().includes(search);
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
});

// Reload when display mode changes
watch(displayMode, () => {
  // Records stay the same, just re-aggregate
});
</script>

<style scoped lang="sass">
.text-theme-green
  color: var(--theme-green)

.text-theme-red
  color: var(--theme-red)
</style>

