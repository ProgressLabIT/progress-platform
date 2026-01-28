<template>
  <SlideUpCard
    :model-value="true"
    :persistent="countStarted"
    height="95vh"
  >
    <div class="col column q-gutter-y-sm">
      <!-- ITEM INFO -->
      <div class="col-auto">
        <div class="text-h6 q-mb-sm">{{ $t('product') }}</div>
        <div class="text-h3">{{ item.product_code }}</div>
        <div class="text-body2 q-mt-xs">{{ item.product_description }}</div>
        <div class="text-caption q-mt-sm text-low">
          {{ item.path?.map(p => p.position_code).join(' → ') || item.position_code || 'IN' }}
        </div>
      </div>

      <!-- START COUNT CONFIRMATION -->
      <template v-if="!countStarted">
        <q-space></q-space>
        <div class="col-auto text-center">
          <div class="text-h5 q-mb-md">{{ $t('start_count_question') }}</div>
        </div>
        <q-space></q-space>
        <q-btn
          color="theme-blue"
          :label="$t('start_count')"
          :loading="startingCount"
          @click="startCount"
        />
        <q-btn
          color="theme-grey"
          :label="$t('cancel')"
          :disable="startingCount"
          @click="$emit('close')"
        />
      </template>

      <!-- CANCEL CONFIRMATION -->
      <template v-else-if="showCancelConfirmation">
        <q-space></q-space>
        <div class="col-auto text-center">
          <div class="text-h5 q-mb-sm">{{ $t('confirm_cancel_count') }}</div>
          <div class="text-body2 text-low q-mb-md">{{ $t('confirm_cancel_count_message') }}</div>
        </div>
        <q-space></q-space>
        <div class="row q-gutter-sm">
          <q-btn
            color="theme-grey"
            class="col"
            :label="$t('no')"
            @click="showCancelConfirmation = false"
          />
          <q-btn
            color="theme-orange"
            class="col"
            :label="$t('yes')"
            :loading="cancelingCount"
            @click="cancelCount"
          />
        </div>
      </template>

      <!-- COUNTING UI -->
      <template v-else>

        <!-- MOVEMENTS CALLOUT -->
        <CountMovementsCallout
          :movements="movements"
          :loading-movements="loadingMovements"
          :show-movements-callout="showMovementsCallout"
          display-mode="quantity"
        />

        <!-- QUANTITY SELECTOR -->
        <QuantitySelector
          v-model="countedQuantity"
          :heading="blindMode ? $t('counted_quantity') : $t('adjust_quantity')"
          show-buttons
          class="col"
        >
          <template #heading>
            <div class="col">
              <div class="text-h3">{{ blindMode ? $t('counted_quantity') : $t('adjust_quantity') }}</div>
              <div v-if="!blindMode" class="text-body2 text-low q-mt-xs">
                {{ $t('original_quantity') }}: {{ roundQuantity(item.quantity) }}
              </div>
            </div>
            <div v-if="!blindMode" class="col-auto highlight">
              <q-chip
                size="md"
                :color="adjustmentQuantity === 0 ? 'theme-grey' : (adjustmentQuantity > 0 ? 'theme-green' : 'theme-orange')"
                :label="(adjustmentQuantity > 0 ? '+' : '') + roundQuantity(adjustmentQuantity)"
                class="full-width"
              />
            </div>
          </template>
        </QuantitySelector>

        <!-- NOTES FIELD -->
        <div class="col-auto">
          <q-input
            v-model="notes"
            filled
            dense
            :label="$t('notes')"
            autogrow
          />
        </div>

        <!-- ACTIONS -->
        <div class="row q-gutter-sm">
          <q-btn
            v-if="!blindMode"
            color="theme-blue"
            outline
            class="col"
            :label="$t('reset')"
            @click="countedQuantity = item.quantity"
          />
          <q-btn
            color="theme-blue"
            class="col"
            :label="$t('save')"
            @click="saveCount"
          />
        </div>
        <q-btn
          color="theme-grey"
          :label="$t('cancel')"
          @click="showCancelConfirmation = true"
        />
      </template>
    </div>
  </SlideUpCard>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { Notify } from 'quasar';
import { useCountingStore } from '@/stores/counting';
import { sendEvent } from '@/composables/event';
import { api } from '@/boot/axios';
import { store } from '@/boot/store';
import SlideUpCard from '@/components/SlideUpCard.vue';
import QuantitySelector from '@/components/QuantitySelector.vue';
import { useInventoryMovements } from '@/composables/useInventoryMovements';
import CountMovementsCallout from '@/components/counting/CountMovementsCallout.vue';
import { roundQuantity } from '@/lib/rounding';

const props = defineProps({
  item: {
    type: Object,
    required: true
  },
});

const emit = defineEmits(['close']);

const { t: $t } = useI18n();
const countingStore = useCountingStore();
const countedQuantity = ref(0);
const countStarted = ref(false);
const startingCount = ref(false);
const countRecordKey = ref(null);
const showCancelConfirmation = ref(false);
const cancelingCount = ref(false);
const notes = ref('');

const blindMode = computed(() => countingStore.sessionData?.blind_quantities ?? true);
const adjustmentQuantity = computed(() => {
  if (blindMode.value) {
    return 0;
  }
  return countedQuantity.value - props.item?.quantity;
});

const effectivePositionKey = computed(() => {
  return (
    props.item.position_key ||
    props.item.path?.[props.item.path.length - 1]?.position_key ||
    null
  );
});

const lastCountedAt = computed(() => props.item.lastCountRecord?.counted_at || null);

const {
  movements,
  loadingMovements,
  hasMovements,
  loadMovements,
} = useInventoryMovements({
  productKey: props.item.product_key,
  positionKey: effectivePositionKey.value,
  startFrom: lastCountedAt.value,
});

const showMovementsCallout = computed(
  () => !!lastCountedAt.value && hasMovements.value,
);

async function loadCountRecord() {
   // Attempt to retrieve count record if existing, in case of page reload or previous count session
  try {
    const { data } = await api.get('/inventory/count-record', {
      params: {
        product_key: props.item.product_key,
        position_key: props.item.position_key || props.item.path?.[props.item.path.length - 1]?.position_key,
        count_session_key: countingStore.sessionData?._key
      }
    });
    if (Array.isArray(data)) {
      const startedRecord = data.filter(record => record.status === 'started')[0];
      if (startedRecord) {
        countRecordKey.value = startedRecord._key;
        return startedRecord;
      }
    } else {
      Notify.create({
        message: $t('count_record_quantity_error') || 'Error: count record not found or multiple records returned.',
        color: 'negative',
        position: 'top',
        timeout: 3000
      });
    }
  } catch (_e) {
    Notify.create({
      message: $t('count_record_key_fetch_error') || 'Error fetching count record key.',
      color: 'negative',
      position: 'top',
      timeout: 3000
    });
  }
  return null;
}

onMounted(async () => {
  // Initialize quantity: use last count if available, otherwise system quantity (or 0 in blind mode)
  countedQuantity.value = props.item.lastCountRecord?.counted_qt
    ?? (blindMode.value ? 0 : props.item.quantity);
  notes.value = '';

  // Only skip confirmation if count is already active AND belongs to current user
  const currentUserKey = store.state.session.user._key;
  const isActiveCountByCurrentUser = props.item.counting === true && props.item.count_by === currentUserKey;

  if (isActiveCountByCurrentUser) {
    // Load the count record key for cancellation
    await loadCountRecord();
    countStarted.value = true;
  }

  // Load movements only if the item has already been counted by the user
  if (lastCountedAt.value && effectivePositionKey.value && props.item.product_key) {
    await loadMovements();
  }
  // Otherwise, show the confirmation dialog (default behavior)
});

async function startCount() {
  startingCount.value = true;

  try {
    const hasInventoryKeys = props.item.inventory_keys && props.item.inventory_keys.length > 0;
    const eventData = {
      inventory_count_session_key: countingStore.sessionData?._key,
      assignment_key: props.item.assignment_key || null,
    };

    if (hasInventoryKeys) {
      eventData.inventory_keys = props.item.inventory_keys;
    } else {
      eventData.product_key = props.item.product_key;
      eventData.position_key = props.item.position_key || props.item.path?.[props.item.path.length - 1]?.position_key;
    }

    const response = await sendEvent({
      event_type: 'COUNT_STARTED',
      event_data: eventData
    });

    countRecordKey.value = response.data?.detail?.count_record_key;
    countStarted.value = true;

    Notify.create({
      message: $t('count_started_success'),
      color: 'theme-green',
      position: 'top',
      timeout: 1500
    });
  } catch (error) {
    console.error('Error starting count:', error);
    // Error notification is already handled by sendEvent
  } finally {
    startingCount.value = false;
  }
}

async function cancelCount() {
  cancelingCount.value = true;

  try {
    const hasInventoryKeys = props.item.inventory_keys && props.item.inventory_keys.length > 0;
    const eventData = {
      count_key: countRecordKey.value,
    };

    if (hasInventoryKeys) {
      eventData.inventory_keys = props.item.inventory_keys;
    } else {
      eventData.inventory_keys = [];
    }

    await sendEvent({
      event_type: 'COUNT_CANCELED',
      event_data: eventData
    });

    Notify.create({
      message: $t('count_canceled'),
      color: 'theme-grey',
      position: 'top',
      timeout: 1500
    });
  } catch (error) {
    console.error('Error canceling count:', error);
  } finally {
    cancelingCount.value = false;
    notes.value = '';
    emit('close');
  }
}

function saveCount() {
  const countData = {
    count_key: countRecordKey.value,
    count_qt: roundQuantity(countedQuantity.value),
    count_serial_keys: [],
    notes: notes.value || null,
  };

  countingStore.saveCount(countData);
  emit('close');
}
</script>

