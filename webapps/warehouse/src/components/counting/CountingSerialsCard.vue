<template>
  <SlideUpCard
    :model-value="true"
    :persistent="countStarted"
    height="90vh"
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

      <!-- ZERO COUNT CONFIRMATION -->
      <template v-else-if="showZeroCountConfirmation">
        <q-space></q-space>
        <div class="col-auto text-center">
          <div class="text-h5 q-mb-sm">{{ $t('confirm_zero_count') }}</div>
          <div class="text-body2 text-low q-mb-md">{{ $t('confirm_zero_count_message') }}</div>
        </div>
        <q-space></q-space>
        <div class="row q-gutter-sm">
          <q-btn
            color="theme-grey"
            class="col"
            :label="$t('no')"
            @click="showZeroCountConfirmation = false"
          />
          <q-btn
            color="theme-blue"
            class="col"
            :label="$t('yes')"
            :loading="loading"
            @click="saveCount"
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
          display-mode="serial"
        />

        <!-- HEADING -->
        <div class="row items-center q-mt-md">
          <div class="col-auto text-h3 q-mr-sm">
            {{ blindMode ? $t('enter_serials') : $t('select_serials') }}
          </div>
          <q-chip v-if="selectedSerialKeys.length" size="xs" color="theme-grey">
            <div class="smaller highlight">{{ selectedSerialKeys.length }}</div>
          </q-chip>
        </div>

        <!-- SERIAL INPUT -->
        <div class="col-auto row">
          <q-input
            filled
            for="serial-input"
            autofocus
            clearable
            dense
            class="col"
            debounce="300"
            input-class="text-uppercase"
            :model-value="codeSearch"
            @update:model-value="codeSearch = $event.toUpperCase()"
            @keyup.enter="() => toggleItem({ serial_code: codeSearch })"
            @keyup.tab="() => toggleItem({ serial_code: codeSearch })"
          >
          </q-input>
          <q-btn
            color="theme-blue"
            unelevated
            padding="xs md"
            icon="mdi-plus"
            class="col-auto q-ml-md"
            :loading="loading || validatingSerial"
            :disabled="!codeSearch?.length || validatingSerial"
            @click="() => toggleItem({ serial_code: codeSearch })"
          />
        </div>

        <!-- SELECT/UNSELECT ALL - ONLY NON-BLIND WITH EXISTING SERIALS -->
        <div v-if="!blindMode && displayedSerials.length > 0" class="row items-center q-gutter-x-sm">
          <div class="text-h6">
            {{ $t('existing_serials') }}
            <span v-if="addedSerials.length > 0">{{ ' ' + $t('added') }}</span>
          </div>
          <q-space></q-space>
          <q-btn color="theme-grey" size="xs" padding="xs md" icon="mdi-checkbox-multiple-blank-outline" @click="() => toggleAll(false)"  />
          <q-btn color="theme-blue" size="xs" padding="xs md" icon="mdi-checkbox-multiple-marked" @click="() => toggleAll(true)" :disabled="allExistingSelected"/>
        </div>

        <!-- SERIALS LIST -->
        <q-scroll-area class="col">
          <div class="col-auto row q-gutter-sm">
            <q-card
              v-for="serial in displayedSerials"
              :key="serial.serial_key"
              flat
              bordered
              class="q-pa-sm"
              :class="{'bg-theme-green highlight': selectedSerialKeys.some(s => s === serial.serial_key), 'bg-theme-grey highlight': addedSerials.some(s => s.serial_key === serial.serial_key)}"
              @click="toggleItem(serial)"
            >
              {{ serial.serial_code }}
            </q-card>
            <q-card v-if="moreSerials > 0" :key="`more-serials`" flat bordered class="q-pa-sm">
              +{{ moreSerials }}
            </q-card>
          </div>
        </q-scroll-area>

        <!-- NOTES FIELD -->
        <div class="col-auto">
          <q-input
            v-model="notes"
            filled
            type="textarea"
            :label="$t('notes')"
            :placeholder="$t('notes_placeholder')"
            rows="3"
            autogrow
          />
        </div>

        <!-- ACTIONS -->
        <q-btn
          v-if="selectedSerialKeys.length === 0"
          color="theme-blue"
          outline
          :label="$t('confirm_zero_count')"
          :disabled="loading"
          @click="showZeroCountConfirmation = true"
        />
        <q-btn
          v-else
          color="theme-blue"
          :label="$t('save')"
          :disabled="selectedSerialKeys.length === 0 || loading"
          @click="saveCount"
        />
        <q-btn
          color="theme-grey"
          :label="$t('cancel')"
          :disable="loading"
          @click="showCancelConfirmation = true"
        />
      </template>
    </div>
  </SlideUpCard>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { Notify } from 'quasar';
import { api } from '@/boot/axios';
import { useCountingStore } from '@/stores/counting';
import { sendEvent } from '@/composables/event';
import { store } from '@/boot/store';
import SlideUpCard from '@/components/SlideUpCard.vue';
import { useInventoryMovements } from '@/composables/useInventoryMovements';
import CountMovementsCallout from '@/components/counting/CountMovementsCallout.vue';

const props = defineProps({
  item: {
    type: Object,
    required: true
  },
  blindMode: {
    type: Boolean,
    default: true
  }
});

const emit = defineEmits(['close']);

const { t: $t } = useI18n();
const countingStore = useCountingStore();
const loading = ref(false);
const existingSerials = ref([]);
const selectedSerialKeys = ref([]);
const addedSerials = ref([]);
const countStarted = ref(false);
const startingCount = ref(false);
const countRecordKey = ref(null);
const showCancelConfirmation = ref(false);
const cancelingCount = ref(false);
const showZeroCountConfirmation = ref(false);
const notes = ref('');
const validatingSerial = ref(false);
const codeSearch = ref('');

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

const totalSerials = computed(() => {
  const nonBlindCount = existingSerials.value.length + addedSerials.value.length;
  const blindCount = selectedSerialKeys.value.length;
  return props.blindMode ? blindCount : nonBlindCount;
});

const moreSerials = computed(() => {
  return totalSerials.value - displayedSerials.value.length;
})

const displayedSerials = computed(() => {
  // baseSerials represent those already in the position.
  // If blind mode, only show the serials that are already selected
  const baseSerials = props.blindMode ? existingSerials.value.filter(s => selectedSerialKeys.value.includes(s.serial_key)) : existingSerials.value;
  // add serials counted but not in position and filter by search
  return [...baseSerials, ...addedSerials.value].filter(serial => serial.serial_code.includes(codeSearch.value));
});


watch(displayedSerials, (newVal) => {
  // Handle automatic selection when the filter fully matches the only serial found
  if (newVal.length === 1 && newVal[0].serial_code === codeSearch.value) {
    toggleItem(newVal[0]);
    codeSearch.value = '';
    document.getElementById('serial-input')?.focus();
  }
});

const allExistingSelected = computed(() => {
  return existingSerials.value.every(s => selectedSerialKeys.value.includes(s.serial_key));
});

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
    }
  } catch (e) {
    console.error('Error loading count record:', e);
    // Silently fail - this is just to retrieve the count record key for cancellation
  }
  return null;
}


onMounted(async () => {
  // Reset temp serials and notes when opening the card
  notes.value = '';

  // Trust the counting status from CountingPositionBrowser
  // It already knows if the item is being counted by the current user
  const currentUserKey = store.state.session.user._key;
  const isActiveCountByCurrentUser = props.item.counting === true && props.item.count_by === currentUserKey;

  if (isActiveCountByCurrentUser) {
    // Load the count record key for cancellation (needed even if we trust props)
    await loadCountRecord();
    countStarted.value = true;
    // Load existing serials and pre-select from last count if available
    await loadExistingSerials();
    await preSelectLastCountSerials();
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

    // Load existing serials after count is started (only for existing inventory)
    if (hasInventoryKeys) {
      await loadExistingSerials();
    }

    // Pre-select serials from last count if available
    await preSelectLastCountSerials();

    Notify.create({
      message: $t('count_started_success'),
      color: 'theme-green',
      position: 'top',
      timeout: 1500
    });
  } catch (error) {
    console.error('Error starting count:', error);
    Notify.create({
      message: $t('count_started_error'),
      color: 'theme-orange',
      position: 'top',
      timeout: 2000
    });
  } finally {
    startingCount.value = false;
  }
}

async function loadExistingSerials() {
  try {
    loading.value = true;
    const response = await api.get('/inventory', {
      params: {
        product_key: props.item.product_key,
        position_key: props.item.position_key || props.item.path?.[props.item.path.length - 1]?.position_key,
        serials_only: true,
        limit: null
      }
    });
    existingSerials.value = response.data;
    // Initialize filteredSerials with all existing serials
  } catch (error) {
    console.error('Error loading existing serials:', error);
    Notify.create({
      position: 'top',
      color: 'theme-orange',
      message: $t('error_loading_serials'),
      timeout: 1500
    });
  } finally {
    loading.value = false;
  }
}

// Pre-select serials from the last completed count record
async function preSelectLastCountSerials() {
  const lastSerialKeys = props.item.lastCountRecord?.counted_serial_keys;
  if (!lastSerialKeys?.length) return;

  const existingKeys = new Set(existingSerials.value.map(s => s.serial_key));

  // Pre-select serials that exist in the position
  const existingFromLastCount = lastSerialKeys.filter(k => existingKeys.has(k));
  selectedSerialKeys.value = [...existingFromLastCount];

  // Fetch and add serials that are not in the position (were added from elsewhere)
  const missingKeys = lastSerialKeys.filter(k => !existingKeys.has(k));
  if (missingKeys.length > 0) {
    // Fetch each missing serial individually using the /serial/{key} endpoint
    // This ensures we get the exact serial we're looking for
    for (const serialKey of missingKeys) {
      try {
        const response = await api.get(`/serial/${serialKey}`);
        if (response.data) {
          // Add to addedSerials (shows as "added") and select them
          addedSerials.value.push({ serial_key: response.data._key, serial_code: response.data.code });
          selectedSerialKeys.value.push(response.data._key);
        }
      } catch (error) {
        console.error('Error fetching serial:', serialKey, error);
      }
    }
  }
}

async function getSerialKey(serialCode) {

  if (!serialCode?.length) {
    Notify.create({
      position: 'top',
      color: 'theme-orange',
      message: $t('serial_not_valid'),
      timeout: 2000
    });
    return false;
  }

  // Check if the serial is already in the position
  const serialInPostion = existingSerials.value.find(serial => serial.serial_code === serialCode);
  if (serialInPostion) {
    return {
      serial_key: serialInPostion.serial_key,
      added: false
    };
  }

  // Check if the serial is registered in the database
  validatingSerial.value = true;
  try {
    const response = await api.get('/serial-code', {
      params: {
        serial_code: serialCode,
        product_key: props.item.product_key
      }
    });

    if (!response.data || response.data.length === 0) {
      Notify.create({
        position: 'top',
        color: 'theme-orange',
        message: $t('serial_not_found', { serial: serialCode.toUpperCase() }),
        timeout: 2000
      });
      return undefined;
    }

    return {
      serial_key: response.data[0]._key,
      added: true
    };

  } catch (error) {
    console.error('Error validating serial:', error);
    Notify.create({
      position: 'top',
      color: 'theme-orange',
      message: $t('error_validating_serial'),
      timeout: 2000
    });
    return undefined;

  } finally {
    validatingSerial.value = false;
  }
}

async function toggleItem(serialItem) {
  // If no serial code is provided, notify the user
  if (!serialItem?.serial_code) {
    Notify.create({
      position: 'top',
      color: 'theme-orange',
      message: $t('invalid_serial'),
      timeout: 1500
    });
    return;
  }

  // If the serial code is already selected, unselect it
  // Must check if the serial is in the addedSerials list and remove it from there too if it is
  const index = selectedSerialKeys.value.findIndex(s => s === serialItem.serial_key);
  if (index !== -1) {
    selectedSerialKeys.value.splice(index, 1);
    if (addedSerials.value.some(s => s.serial_key === serialItem.serial_key)) {
      addedSerials.value = addedSerials.value.filter(s => s.serial_key !== serialItem.serial_key);
    }
    Notify.create({
      position: 'top',
      color: 'theme-grey',
      message: $t('serial_removed_single', { serial: serialItem.serial_code }),
      timeout: 1500
    });
  } else {
    // Validate serial exists
    const foundSerial = serialItem.serial_key ? { serial_key: serialItem.serial_key, added: false } : await getSerialKey(serialItem.serial_code);
    if (!foundSerial) {
      codeSearch.value = '';
      document.getElementById('serial-input')?.focus();
      return
    }
    const toAdd = {
      serial_code: serialItem.serial_code,
      serial_key: foundSerial.serial_key,
    }
    if (foundSerial.added) {
      addedSerials.value.push(toAdd);
    }
    selectedSerialKeys.value.push(toAdd.serial_key);
    Notify.create({
      position: 'top',
      color: 'theme-green',
      message: $t('serial_added'),
      timeout: 1500
    });
  }
  codeSearch.value = '';
  document.getElementById('serial-input')?.focus();
}

function toggleAll(select) {
  if (select) {
    selectedSerialKeys.value = [...existingSerials.value.map(s => s.serial_key), ...addedSerials.value.map(s => s.serial_key)];
    Notify.create({
      position: 'top',
      color: 'theme-green',
      message: `${selectedSerialKeys.value.length} seriali selezionati`,
      timeout: 1500
    });
  } else {
    selectedSerialKeys.value = [];
    addedSerials.value = [];
    Notify.create({
      position: 'top',
      color: 'theme-grey',
      message: `Seriali rimossi`,
      timeout: 1500
    });
  }
}

function saveCount() {
  const countData = {
    count_key: countRecordKey.value,
    count_qt: selectedSerialKeys.value.length,
    count_serial_keys: [...selectedSerialKeys.value],
    notes: notes.value || null,
  };

  countingStore.saveCount(countData);

  Notify.create({
    message: $t('count_saved'),
    color: 'theme-green',
    position: 'top',
  });

  // Close without confirmation since the count was saved
  emit('close');
}

function handleClose() {
  // This is only called when dialog is actually closing (not counting, or via button clicks)
  selectedSerialKeys.value = [];
  emit('close');
}

async function cancelCount() {
  cancelingCount.value = true;

  try {
    // Check if count record exists
    if (!countRecordKey.value) {
      Notify.create({
        message: 'Cannot cancel: count record not found. Please refresh the page.',
        color: 'negative',
        position: 'top',
        timeout: 3000
      });
      cancelingCount.value = false;
      return;
    }

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
    selectedSerialKeys.value = [];
    notes.value = '';
    emit('close');
  }
}
</script>


