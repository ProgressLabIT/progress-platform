<template>
  <SlideUpCard
    :model-value="true"
    :persistent="countStarted"
    height="600px"
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
        <!-- HEADING -->
        <div class="row items-center q-mt-md">
          <div class="col-auto text-h3 q-mr-sm">
            {{ blindMode ? $t('enter_serials') : $t('select_serials') }}
          </div>
          <q-chip v-if="countingStore.tempSerials.length" size="xs" color="theme-grey">
            <div class="smaller highlight">{{ countingStore.tempSerials.length }}</div>
          </q-chip>
        </div>

        <!-- SERIAL INPUT -->
        <div class="col-auto row">
          <q-input
            filled
            for="serial-input"
            autofocus
            clearable
            class="col"
            input-class="text-uppercase"
            :model-value="newSerialCode"
            @update:model-value="(value) => newSerialCode = value?.toUpperCase() || ''"
            @keyup.enter="() => toggleItem(newSerialCode)"
          >
          </q-input>
          <q-btn
            color="theme-blue"
            unelevated
            padding="xs md"
            icon="mdi-plus"
            class="col-auto q-ml-md"
            :loading="loading || validatingSerial"
            :disabled="!newSerialCode?.length || validatingSerial"
            @click="() => toggleItem(newSerialCode)"
          />
        </div>

        <!-- SELECT/UNSELECT ALL - ONLY NON-BLIND WITH EXISTING SERIALS -->
        <div v-if="!blindMode && existingSerials.length > 0" class="row items-center q-gutter-x-sm">
          <div class="text-h6">{{ $t('existing_serials') }}</div>
          <q-space></q-space>
          <q-btn color="theme-grey" size="xs" padding="xs md" icon="mdi-checkbox-multiple-blank-outline" @click="() => toggleAll(false)" />
          <q-btn color="theme-blue" size="xs" padding="xs md" icon="mdi-checkbox-multiple-marked" @click="() => toggleAll(true)" />
        </div>

        <!-- SERIALS LIST -->
        <q-scroll-area class="col">
          <div class="col-auto row q-gutter-sm">
            <q-card
              v-for="serial in displayedSerials"
              :key="serial"
              flat
              :bordered="!blindMode && existingSerials.includes(serial) && !countingStore.tempSerials.includes(serial)"
              class="q-pa-sm"
              :class="{'bg-theme-green highlight': countingStore.tempSerials.includes(serial)}"
              @click="toggleItem(serial)"
            >
              {{ serial }}
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
        <div class="row q-gutter-sm">
          <q-btn
            color="theme-blue"
            class="col"
            :label="$t('save')"
            :disabled="countingStore.tempSerials.length === 0 || loading"
            @click="saveCount"
          />
        </div>
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
import { ref, computed, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { Notify } from 'quasar';
import { api } from '@/boot/axios';
import { useCountingStore } from '@/stores/counting';
import { sendEvent } from '@/composables/event';
import { store } from '@/boot/store';
import SlideUpCard from '@/components/SlideUpCard.vue';

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
const newSerialCode = ref('');
const loading = ref(false);
const existingSerials = ref([]);
const countStarted = ref(false);
const startingCount = ref(false);
const countRecordKey = ref(null);
const showCancelConfirmation = ref(false);
const cancelingCount = ref(false);
const notes = ref('');
const validatingSerial = ref(false);

const displayedSerials = computed(() => {
  if (props.blindMode) {
    // In blind mode, show only entered serials
    return countingStore.tempSerials;
  } else {
    // In non-blind mode, show existing serials from inventory
    return existingSerials.value;
  }
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
  countingStore.tempSerials = [];
  notes.value = '';

  // Only skip confirmation if count is already active AND belongs to current user
  const currentUserKey = store.state.session.user._key;
  const isActiveCountByCurrentUser = props.item.counting === true && props.item.count_by === currentUserKey;

  if (isActiveCountByCurrentUser) {
    // Load the count record key for cancellation
    await loadCountRecord();
    countStarted.value = true;
    // Load existing serials if in non-blind mode
    if (!props.blindMode) {
      loadExistingSerials();
    }
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

    // Load existing serials after count is started (for non-blind mode, only for existing inventory)
    if (!props.blindMode && hasInventoryKeys) {
      await loadExistingSerials();
    }

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
        serials_only: true
      }
    });
    existingSerials.value = response.data.map(inv => inv.serial_code).filter(Boolean).sort();
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

async function toggleItem(serialCode) {
  // If no serial code is provided, notify the user
  if (!serialCode?.length) {
    Notify.create({
      position: 'top',
      color: 'theme-orange',
      message: $t('invalid_serial'),
      timeout: 1500
    });
    return;
  }

  // If the serial code is already selected, unselect it
  const index = countingStore.tempSerials.indexOf(serialCode);
  if (index !== -1) {
    countingStore.tempSerials.splice(index, 1);
    Notify.create({
      position: 'top',
      color: 'theme-grey',
      message: $t('serial_removed_single', { serial: serialCode }),
      timeout: 1500
    });
  } else {
    // Validate serial exists in the database
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
          message: $t('serial_not_found', { serial: serialCode }),
          timeout: 2000
        });
        validatingSerial.value = false;
        return;
      }

      // In non-blind mode with existing serials, check if serial is in the list
      if (!props.blindMode && existingSerials.value.length > 0 && !existingSerials.value.includes(serialCode)) {
        Notify.create({
          position: 'top',
          color: 'theme-orange',
          message: $t('serial_not_in_expected_list', { serial: serialCode }),
          timeout: 2000
        });
      } else {
        countingStore.tempSerials.push(serialCode);
        Notify.create({
          position: 'top',
          color: 'theme-green',
          message: $t('serial_added'),
          timeout: 1500
        });
      }
    } catch (error) {
      console.error('Error validating serial:', error);
      Notify.create({
        position: 'top',
        color: 'theme-orange',
        message: $t('error_validating_serial'),
        timeout: 2000
      });
    } finally {
      validatingSerial.value = false;
    }
  }

  newSerialCode.value = '';
  document.getElementById('serial-input')?.focus();
}

function toggleAll(select) {
  if (select) {
    countingStore.tempSerials = [...existingSerials.value];
    Notify.create({
      position: 'top',
      color: 'theme-green',
      message: `${countingStore.tempSerials.length} seriali selezionati`,
      timeout: 1500
    });
  } else {
    countingStore.tempSerials = [];
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
    inventory_key: props.item._key,
    product_key: props.item.product_key,
    position_key: props.item.position_key || props.item.path?.[props.item.path.length - 1]?.position_key,
    serial_key: props.item.serial_key,
    quantity_original: existingSerials.value.length,
    quantity_counted: countingStore.tempSerials.length,
    serials_counted: [...countingStore.tempSerials],
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
  countingStore.tempSerials = [];
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
    countingStore.tempSerials = [];
    notes.value = '';
    emit('close');
  }
}
</script>

<style lang="scss" scoped>
</style>


