<template>
  <BaseModalForm
    :show="modelValue"
    :loading="loading"
    :handle-close="handleClose"
    @submit="handleResolve"
    @cancel="handleClose"
  >
    <template #title>
      <div class="row items-center justify-between full-width">
        <span>{{ $t('warehouse.counting.select_count') }}</span>
        <!-- Navigation indicator when multiple conflicts -->
        <q-badge v-if="conflictingPairs.length > 1" color="primary" class="q-ml-md">
          {{ currentIndex + 1 }} / {{ conflictingPairs.length }}
        </q-badge>
      </div>
    </template>

    <template #form>
      <div class="column q-gutter-md">
        <!-- Product/Position Info for current pair -->
        <div v-if="currentPair" class="q-mb-md">
          <div class="text-subtitle1 text-weight-medium">{{ currentPair.product.code }}</div>
          <div class="text-caption text-grey">{{ currentPair.product.description }}</div>
          <div v-if="currentPair.position" class="text-caption q-mt-xs">
            <q-icon name="mdi-map-marker" size="xs" class="q-mr-xs" />
            {{ currentPair.position.code }}
            <span v-if="currentPair.pathString" class="text-grey q-ml-xs">
              ({{ currentPair.pathString }})
            </span>
          </div>
        </div>

        <q-separator />

        <!-- Count Records List for current pair -->
        <q-list v-if="currentNonDiscardedRecords.length" separator class="q-mt-none">
          <q-item
            v-for="record in currentNonDiscardedRecords"
            :key="record._key"
            clickable
            :active="selectedRecordKey === record._key"
            active-class="text-white"
            @click="selectedRecordKey = record._key"
          >
            <q-item-section avatar>
              <q-radio
                v-model="selectedRecordKey"
                :val="record._key"
                color="primary"
              />
            </q-item-section>

            <q-item-section>
              <q-item-label>
                <span class="text-weight-medium">{{ $t('warehouse.counting.counted_qt') }}:</span>
                {{ record.counted_qt }}
              </q-item-label>
              <q-item-label caption>
                <span class="text-weight-medium">{{ $t('warehouse.counting.system_qt') }}:</span>
                {{ record.system_qt }}
                <span class="q-ml-md" :class="getDeltaClass(record)">
                  {{ $t('warehouse.counting.delta') }}: {{ formatDelta(record) }}
                </span>
              </q-item-label>
              <q-item-label caption class="q-mt-xs">
                <q-icon name="mdi-clock-outline" size="xs" class="q-mr-xs" />
                {{ formatDate(record.counted_at) }}
              </q-item-label>
              <q-item-label v-if="record.notes" caption class="q-mt-xs text-italic">
                <q-icon name="mdi-note-text" size="xs" class="q-mr-xs" />
                {{ record.notes }}
              </q-item-label>
            </q-item-section>
            <q-item-section side>
              <BaseUserAvatar
                :user="store.getters.getUserByKey(record.user_key)"
                :show_name="false"
              />
            </q-item-section>
          </q-item>
        </q-list>

        <div v-else class="text-grey text-center q-pa-md">
          {{ $t('no_data') }}
        </div>

        <!-- Discarded Records Info for current pair -->
        <div v-if="currentDiscardedRecords.length > 0" class="q-mt-md">
          <q-expansion-item
            :label="$t('warehouse.counting.discarded_records', { count: currentDiscardedRecords.length })"
            header-class="text-grey"
            dense
          >
            <q-list separator dense>
              <q-item v-for="record in currentDiscardedRecords" :key="record._key" class="text-grey">
                <q-item-section>
                  <q-item-label>
                    {{ $t('warehouse.counting.counted_qt') }}: {{ record.counted_qt }}
                  </q-item-label>
                  <q-item-label caption>
                    {{ formatDate(record.counted_at) }}
                  </q-item-label>
                </q-item-section>
                <q-item-section side>
                  <q-badge color="grey">
                    {{ record.status }}
                  </q-badge>
                </q-item-section>
              </q-item>
            </q-list>
          </q-expansion-item>
        </div>
      </div>
    </template>

    <template #actions>
      <div class="row full-width items-center q-gutter-md">
        <!-- Navigation arrows -->
        <template v-if="conflictingPairs.length > 1">
          <q-btn
            v-if="currentIndex > 0"
            icon="mdi-arrow-left-bold"
            color="theme-blue"
            flat
            round
            @click="goToPrevious"
          />
          <q-btn
            v-if="currentIndex < conflictingPairs.length - 1"
            icon="mdi-arrow-right-bold"
            color="theme-blue"
            flat
            round
            @click="goToNext"
          />
        </template>

        <q-space />

        <q-btn
          :label="$t('cancel')"
          color="theme-grey"
          flat
          @click="handleClose"
        />
        <q-btn
          :label="isLastConflict ? $t('warehouse.counting.discard_others') : $t('warehouse.counting.resolve_and_next')"
          color="theme-orange"
          :loading="loading"
          :disable="!selectedRecordKey || currentNonDiscardedRecords.length < 2"
          @click="handleResolve"
        />
      </div>
    </template>
  </BaseModalForm>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useStore } from 'vuex';
import { Notify } from 'quasar';
import { useCountSessionStore } from '@/stores/countSession';
import BaseModalForm from '@/components/BaseModalForm.vue';
import { DateTime } from 'luxon';
import BaseUserAvatar from '@/components/BaseUserAvatar.vue';

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  /**
   * The aggregate object from the parent.
   * Used to extract conflicting pairs at the product/position level.
   */
  aggregate: {
    type: Object,
    default: null,
  },
});

const emit = defineEmits(['update:modelValue', 'resolve']);

const { t: $t } = useI18n();
const store = useStore();
const countSessionStore = useCountSessionStore();

const loading = ref(false);
const selectedRecordKey = ref(null);
const currentIndex = ref(0);

/**
 * Extract conflicting pairs from the aggregate.
 * A pair is a unique product_key + position_key combination.
 * A conflict exists when there are multiple non-discarded records with different counted_qt.
 */
const conflictingPairs = computed(() => {
  if (!props.aggregate) return [];

  // Group records by original product/position pair
  const pairMap = new Map();

  for (const record of props.aggregate.records) {
    const pairKey = `${record.product_key}_${record.position_key}`;

    if (!pairMap.has(pairKey)) {
      pairMap.set(pairKey, {
        pairKey,
        product: {
          key: record.product_key,
          code: record.product_code,
          description: record.product_description,
        },
        position: record.position_key ? {
          key: record.position_key,
          code: record.position_code,
        } : null,
        pathString: record.position_path?.join(' > ') || '',
        records: [],
      });
    }

    pairMap.get(pairKey).records.push(record);
  }

  // Filter to only pairs that have conflicts (multiple non-discarded with different counts)
  const pairs = [];
  for (const pair of pairMap.values()) {
    const nonDiscarded = pair.records.filter(r => r.status !== 'discarded');
    if (nonDiscarded.length > 1) {
      const firstQt = nonDiscarded[0].counted_qt;
      const hasConflict = !nonDiscarded.every(r => r.counted_qt === firstQt);
      if (hasConflict) {
        pairs.push(pair);
      }
    }
  }

  return pairs;
});

// Current pair being resolved
const currentPair = computed(() => {
  if (conflictingPairs.value.length === 0) return null;
  return conflictingPairs.value[currentIndex.value] || null;
});

// Records for current pair
const currentNonDiscardedRecords = computed(() => {
  if (!currentPair.value) return [];
  return currentPair.value.records.filter(r => r.status !== 'discarded');
});

const currentDiscardedRecords = computed(() => {
  if (!currentPair.value) return [];
  return currentPair.value.records.filter(r => r.status === 'discarded');
});

// Check if this is the last conflict to resolve
const isLastConflict = computed(() => {
  return currentIndex.value >= conflictingPairs.value.length - 1;
});

// Watch for dialog open to reset state
watch(
  () => props.modelValue,
  (isOpen) => {
    if (isOpen) {
      currentIndex.value = 0;
      preselectRecord();
    }
  }
);

// Watch for index change to preselect record
watch(currentIndex, () => {
  preselectRecord();
});

// Methods
function preselectRecord() {
  if (currentNonDiscardedRecords.value.length > 0) {
    // Pre-select the most recent record
    const sorted = [...currentNonDiscardedRecords.value].sort(
      (a, b) => new Date(b.counted_at) - new Date(a.counted_at)
    );
    selectedRecordKey.value = sorted[0]?._key || null;
  } else {
    selectedRecordKey.value = null;
  }
}

function goToPrevious() {
  if (currentIndex.value > 0) {
    currentIndex.value--;
  }
}

function goToNext() {
  if (currentIndex.value < conflictingPairs.value.length - 1) {
    currentIndex.value++;
  }
}

function handleClose() {
  emit('update:modelValue', false);
}

async function handleResolve() {
  if (!selectedRecordKey.value) return;

  loading.value = true;

  try {
    // Discard all non-selected records for the current pair
    const recordKeysToDiscard = currentNonDiscardedRecords.value
      .filter(r => r._key !== selectedRecordKey.value)
      .map(r => r._key);

    await countSessionStore.discardRecords(recordKeysToDiscard);

    // Update local state - mark records as discarded
    for (const key of recordKeysToDiscard) {
      const record = currentPair.value.records.find(r => r._key === key);
      if (record) {
        record.status = 'discarded';
      }
    }

    if (isLastConflict.value) {
      // All conflicts resolved
      Notify.create({
        message: $t('warehouse.counting.conflict_resolved'),
        color: 'theme-green',
      });
      emit('resolve');
    } else {
      // Move to next conflict
      Notify.create({
        message: $t('warehouse.counting.conflict_resolved_next'),
        color: 'theme-green',
        timeout: 1500,
      });
      currentIndex.value++;
    }
  } catch (error) {
    console.error('Error resolving conflict:', error);
    Notify.create({
      type: 'negative',
      message: error.response?.data?.detail?.message || $t('error'),
      color: 'theme-red',
    });
  } finally {
    loading.value = false;
  }
}

function getDeltaClass(record) {
  const delta = (record.counted_qt ?? 0) - (record.system_qt ?? 0);
  if (delta > 0) return 'text-theme-green';
  if (delta < 0) return 'text-theme-red';
  return 'text-grey';
}

function formatDelta(record) {
  const delta = (record.counted_qt ?? 0) - (record.system_qt ?? 0);
  if (delta > 0) return `+${delta}`;
  return String(delta);
}

function formatDate(date) {
  if (!date) return '-';
  return DateTime.fromISO(date).toFormat('dd/MM/yyyy HH:mm');
}
</script>

<style scoped lang="sass">
.text-theme-green
  color: var(--theme-green)

.text-theme-red
  color: var(--theme-red)
</style>
