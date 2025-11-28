<template>
  <BaseModalForm
    :show="modelValue"
    :loading="loading"
    :handle-close="handleClose"
    @submit="handleResolve"
    @cancel="handleClose"
  >
    <template #title>
      {{ $t('warehouse.counting.select_count') }}
    </template>

    <template #form>
      <div class="column q-gutter-md">
        <!-- Product/Position Info -->
        <div v-if="aggregate" class="q-mb-md">
          <div class="text-subtitle1 text-weight-medium">{{ aggregate.product.code }}</div>
          <div class="text-caption text-grey">{{ aggregate.product.description }}</div>
          <div v-if="aggregate.position" class="text-caption q-mt-xs">
            <q-icon name="mdi-map-marker" size="xs" class="q-mr-xs" />
            {{ aggregate.position.code }}
          </div>
        </div>

        <q-separator />

        <!-- Count Records List -->
        <q-list v-if="nonDiscardedRecords.length" separator>
          <q-item
            v-for="record in nonDiscardedRecords"
            :key="record._key"
            clickable
            :active="selectedRecordKey === record._key"
            active-class="bg-primary text-white"
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
                <template v-if="getUserName(record)">
                  <q-icon name="mdi-account" size="xs" class="q-ml-md q-mr-xs" />
                  {{ getUserName(record) }}
                </template>
              </q-item-label>
              <q-item-label v-if="record.notes" caption class="q-mt-xs text-italic">
                <q-icon name="mdi-note-text" size="xs" class="q-mr-xs" />
                {{ record.notes }}
              </q-item-label>
            </q-item-section>

            <q-item-section side>
              <q-badge :color="getStatusColor(record.status)">
                {{ record.status }}
              </q-badge>
            </q-item-section>
          </q-item>
        </q-list>

        <div v-else class="text-grey text-center q-pa-md">
          {{ $t('no_data') }}
        </div>

        <!-- Discarded Records Info -->
        <div v-if="discardedRecords.length > 0" class="q-mt-md">
          <q-expansion-item
            :label="$t('warehouse.counting.discarded_records', { count: discardedRecords.length })"
            header-class="text-grey"
            dense
          >
            <q-list separator dense>
              <q-item v-for="record in discardedRecords" :key="record._key" class="text-grey">
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
      <q-btn
        :label="$t('cancel')"
        color="theme-grey"
        flat
        @click="handleClose"
      />
      <q-btn
        :label="$t('warehouse.counting.discard_others')"
        color="primary"
        :loading="loading"
        :disable="!selectedRecordKey || nonDiscardedRecords.length < 2"
        @click="handleResolve"
      />
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

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  aggregate: {
    type: Object,
    default: null,
  },
});

const emit = defineEmits(['update:modelValue', 'resolve']);

const { t: $t } = useI18n();
const store = useStore(); // Used for getUserByKey
const countSessionStore = useCountSessionStore();

const loading = ref(false);
const selectedRecordKey = ref(null);

// Computed
const nonDiscardedRecords = computed(() => {
  if (!props.aggregate) return [];
  return props.aggregate.records.filter(r => r.status !== 'discarded');
});

const discardedRecords = computed(() => {
  if (!props.aggregate) return [];
  return props.aggregate.discardedRecords || [];
});

// Watch for dialog open to reset selection
watch(
  () => props.modelValue,
  (isOpen) => {
    if (isOpen && props.aggregate) {
      // Pre-select the most recent record
      const sorted = [...nonDiscardedRecords.value].sort(
        (a, b) => new Date(b.counted_at) - new Date(a.counted_at)
      );
      selectedRecordKey.value = sorted[0]?._key || null;
    }
  }
);

// Methods
function handleClose() {
  emit('update:modelValue', false);
}

async function handleResolve() {
  if (!selectedRecordKey.value) return;

  loading.value = true;

  try {
    // Discard all non-selected records using bulk event
    const recordKeysToDiscard = nonDiscardedRecords.value
      .filter(r => r._key !== selectedRecordKey.value)
      .map(r => r._key);

    await countSessionStore.discardRecords(recordKeysToDiscard);

    Notify.create({
      message: $t('warehouse.counting.conflict_resolved'),
      color: 'theme-green',
    });

    emit('resolve');
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

function getUserName(record) {
  if (!record.user_key) return null;
  const user = store.getters.getUserByKey(record.user_key);
  return user?.name || user?.username || record.user_key;
}

function getStatusColor(status) {
  switch (status) {
    case 'completed': return 'positive';
    case 'submitted': return 'info';
    case 'confirmed': return 'positive';
    case 'started': return 'warning';
    case 'discarded': return 'grey';
    default: return 'grey';
  }
}
</script>

<style scoped lang="sass">
.text-theme-green
  color: var(--theme-green)

.text-theme-red
  color: var(--theme-red)
</style>

