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
            <div v-if="props.row.position" class="row items-center no-wrap">
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
              <!-- Coverage indicator (only shown when aggregating, not in "All levels" mode) -->
              <q-icon
                v-if="props.row.coverage?.isAggregated"
                :name="props.row.coverage.isComplete ? 'mdi-check-circle' : 'mdi-alert-circle-outline'"
                :color="props.row.coverage.isComplete ? 'positive' : 'warning'"
                size="xs"
                class="q-ml-xs"
              >
                <q-tooltip>
                  {{ props.row.coverage.isComplete
                    ? $t('warehouse.counting.position_fully_counted')
                    : $t('warehouse.counting.position_not_fully_counted')
                  }}
                </q-tooltip>
              </q-icon>
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

        <!-- Uncounted Qt Column (only visible when aggregating) -->
        <template #body-cell-uncounted_qt="props">
          <q-td :props="props">
            <!-- If position is fully counted, show 0 -->
            <template v-if="props.row.coverage?.isComplete">
              <span class="text-grey">0</span>
            </template>
            <!-- Loading state -->
            <template v-else-if="isUncountedLoading(props.row)">
              <q-spinner-tail size="xs" color="primary" />
            </template>
            <!-- Error state -->
            <template v-else-if="getUncountedError(props.row)">
              <q-icon
                name="mdi-alert-circle-outline"
                color="negative"
                size="xs"
                class="cursor-pointer"
                @click="retryUncountedFetch(props.row)"
              >
                <q-tooltip>
                  {{ getUncountedError(props.row) }}
                  <br />
                  {{ $t('click_to_retry') }}
                </q-tooltip>
              </q-icon>
            </template>
            <!-- Value with tooltip showing positions -->
            <template v-else>
              <span :class="{ 'text-warning': getUncountedQt(props.row) > 0 }">
                {{ getUncountedQt(props.row) ?? '-' }}
              </span>
              <!-- Tooltip with uncounted positions -->
              <q-tooltip
                v-if="getUncountedPositions(props.row).length > 0"
                anchor="top middle"
                self="bottom middle"
                :delay="500">
                <div class="text-weight-bold q-mb-xs">
                  {{ $t('warehouse.counting.uncounted_positions') }}
                </div>
                <div
                  v-for="pos in getUncountedPositions(props.row).slice(0, 10)"
                  :key="pos.key"
                  class="row justify-between q-gutter-x-md"
                >
                  <span>{{ pos.code }}</span>
                  <span class="text-weight-medium">{{ pos.quantity }}</span>
                </div>
                <div v-if="getUncountedPositions(props.row).length > 10" class="text-caption text-grey q-mt-xs">
                  +{{ getUncountedPositions(props.row).length - 10 }} {{ $t('more') }}
                </div>
              </q-tooltip>
            </template>
          </q-td>
        </template>

        <!-- Total System Qt Column (only visible when aggregating) -->
        <template #body-cell-total_system_qt="props">
          <q-td :props="props">
            <!-- If position is fully counted, show same as system qt -->
            <template v-if="props.row.coverage?.isComplete">
              {{ props.row.totalSystemQt ?? '-' }}
            </template>
            <!-- Loading state -->
            <template v-else-if="isUncountedLoading(props.row)">
              <q-spinner-tail size="xs" color="primary" />
            </template>
            <!-- Error state -->
            <template v-else-if="getUncountedError(props.row)">
              <span class="text-grey">?</span>
            </template>
            <!-- Value -->
            <template v-else>
              {{ getTotalSystemQt(props.row) ?? '-' }}
            </template>
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
            <!-- Loading uncounted inventory - show spinner (only when aggregating) -->
            <template v-else-if="!allLevels && isUncountedLoading(props.row)">
              <q-spinner-tail size="xs" color="primary" />
            </template>
            <!-- Error fetching uncounted - show question mark (only when aggregating) -->
            <template v-else-if="!allLevels && getUncountedError(props.row) && !props.row.coverage?.isComplete">
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
                <span :class="getDeltaClass(getEffectiveDelta(props.row))">
                  {{ formatDelta(getEffectiveDelta(props.row)) }}
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
      <CountRecordFilterSidebar
        v-model="filters"
        :position-level="selectedLevel"
        :all-levels="allLevels"
        :session-status="countSessionStore.sessionData?.status"
        :exporting="exporting"
        @update:position-level="setPositionLevel"
        @update:all-levels="allLevels = $event"
        @export-xlsx="handleExportXLSX"
        @export-csv="handleExportCSV"
        @import="importDialogOpen = true"
      />
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
import { useQuasar, Notify } from 'quasar';
import { useCountSessionStore } from '@/stores/countSession';
import { api } from '@/boot/axios.js';

// Composables
import { useCountRecordAggregation, getDiscardedRecords } from '@/composables/useCountRecordAggregation';
import { useCountRecordFilters } from '@/composables/useCountRecordFilters';
import { useUncountedInventory } from '@/composables/useUncountedInventory';
import { useCountRecordExport } from '@/composables/useCountRecordExport';

// Components
import CountRecordConflictDialog from '@/components/warehouse/counting/CountRecordConflictDialog.vue';
import CountRecordImportDialog from '@/components/warehouse/counting/CountRecordImportDialog.vue';
import CountRecordFilterSidebar from '@/components/warehouse/counting/CountRecordFilterSidebar.vue';
import BaseUserAvatar from '@/components/BaseUserAvatar.vue';

// Utils
import { formatDateTime } from '@/lib/TimeHandling';

const { t: $t, locale } = useI18n();
const $q = useQuasar();
const store = useStore();
const countSessionStore = useCountSessionStore();

// ============================================================
// UI STATE
// ============================================================

const splitterModel = ref(70);
const conflictDialogOpen = ref(false);
const selectedConflictAggregate = ref(null);
const events = ref(null);
const importDialogOpen = ref(false);

// ============================================================
// STORE DATA (reactive)
// ============================================================

const loading = computed(() => countSessionStore.recordsLoading);
const rawRecords = computed(() => countSessionStore.records);
const positionLookup = computed(() => countSessionStore.positionLookup);
const completedPositions = computed(() => countSessionStore.completedPositions);

// ============================================================
// COMPOSABLES
// ============================================================

// Aggregation composable
const {
  allLevels,
  selectedLevel,
  setPositionLevel,
  visibleAggregates,
  discardedOnlyCount,
} = useCountRecordAggregation(rawRecords, positionLookup, completedPositions);

// Filter composable
const { filters, filteredRecords } = useCountRecordFilters(visibleAggregates);

// Uncounted inventory composable
const {
  getUncountedQt,
  getTotalSystemQt,
  isUncountedLoading,
  getUncountedError,
  getUncountedPositions,
  retryUncountedFetch,
  getEffectiveDelta,
} = useUncountedInventory(visibleAggregates, allLevels, countSessionStore);

// Export composable
const { exporting, exportToXLSX, exportToCSV } = useCountRecordExport();

// ============================================================
// TABLE COLUMNS
// ============================================================

const tableColumns = computed(() => {
  const columns = [
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
  ];

  // Add uncounted and total system columns only when aggregating (not in "All levels" mode)
  if (!allLevels.value) {
    columns.push(
      {
        name: 'uncounted_qt',
        label: $t('warehouse.counting.uncounted_qt'),
        field: row => getUncountedQt(row),
        align: 'right',
      },
      {
        name: 'total_system_qt',
        label: $t('warehouse.counting.total_system_qt'),
        field: row => getTotalSystemQt(row),
        align: 'right',
      },
    );
  }

  columns.push(
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
  );

  return columns;
});

// ============================================================
// DISPLAY HELPERS
// ============================================================

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

// ============================================================
// DATA LOADING
// ============================================================

async function loadRecords() {
  let timer10s = null;
  let timer20s = null;
  let timeoutOccurred = false;

  try {
    $q.loading.show({
      message: 'Fetching records...',
      boxClass: 'bg-grey-2 text-grey-9',
      spinnerColor: 'primary'
    });

    // Timer for "Please wait" message after 10s
    timer10s = setTimeout(() => {
      if ($q.loading.isActive) {
        $q.loading.show({
          message: 'Please wait... Processing large dataset.',
          boxClass: 'bg-grey-2 text-grey-9',
          spinnerColor: 'primary'
        });
      }
    }, 10000);

    // Timer for timeout error after 20s
    timer20s = setTimeout(() => {
      timeoutOccurred = true;
      $q.loading.hide();
      Notify.create({
        type: 'negative',
        message: 'Request timed out. The dataset is too large or the connection is slow. Please try filtering your search.'
      });
    }, 20000);

    await countSessionStore.loadRecords(null, { // current session is stored in the store
      include_started: false,
      limit: 0, // Fetch effectively "all" records (backend limit is 500 by default)
    });

    // Allow a small delay for reactivity (aggregation) to kick in before hiding loader
    // This ensures the spinner stays visible during the heavy computation
    await new Promise(resolve => setTimeout(resolve, 100));

  } catch (error) {
    if (!timeoutOccurred) {
      console.error('Error loading records:', error);
      Notify.create({
        type: 'negative',
        message: 'Failed to load records'
      });
    }
  } finally {
    clearTimeout(timer10s);
    clearTimeout(timer20s);
    if (!timeoutOccurred) {
      $q.loading.hide();
    }
  }
}

// ============================================================
// CONFLICT DIALOG
// ============================================================

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

// ============================================================
// EXPORT/IMPORT HANDLERS
// ============================================================

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

// ============================================================
// LIFECYCLE
// ============================================================

onMounted(() => {
  loadRecords();
  // Load position hierarchy to enable level-based aggregation
  countSessionStore.loadPositions();
  // Load completed positions for coverage tracking
  countSessionStore.loadCompletedPositions();

  // Subscribe to inventory notifications so records update automatically
  const eventURL = `${api.defaults.baseURL}/notification/inventory-notification`;
  events.value = new EventSource(eventURL, {
    withCredentials: false,
  });
  events.value.addEventListener('inventory-notification', () => {
    loadRecords();
    // Also refresh completed positions when inventory changes
    countSessionStore.loadCompletedPositions();
  });
});

onBeforeUnmount(() => {
  if (events.value) {
    events.value.close();
  }
});

// ============================================================
// WATCHERS
// ============================================================

// Reload records when filters change (for server-side filtering if needed)
watch(filters, () => {
  loadRecords();
});

// Clear uncounted cache when inventory changes (via SSE notification)
// This is handled by watching the records/completedPositions changes
watch(
  () => countSessionStore.records,
  () => {
    // Clear cache when records change - inventory may have moved
    countSessionStore.clearUncountedInventoryCache();
  }
);

// Set level to null when toggling allLevels to true
watch(allLevels, (newValue) => {
  if (newValue) {
    selectedLevel.value = null;
  }
});
</script>
