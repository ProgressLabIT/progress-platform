<template>
  <div class="col column q-col-gutter-y-sm">
    <div class="row col-auto q-col-gutter-sm">
      <div class="col-6">
        <SearchOrScan
          v-model="serialCodeFilter"
          label="Seriale"
          @update:model-value="search"
        />
      </div>
      <div class="col-6">
        <q-input
          filled
          dense
          clearable
          input-class="text-uppercase"
          label="Prodotto"
          :debounce="300"
          v-model="productCodeFilter"
          @update:model-value="search"
        >
          <template #append>
            <q-icon name="mdi-filter" />
          </template>
        </q-input>
      </div>
    </div>

    <div class="col-auto row items-center q-gutter-x-sm q-my-sm text-h6">
      <div>{{ $t('results') }}</div>
      <q-chip size="xs" color="theme-grey">
        <div class="smaller highlight">{{ serialList.length }}</div>
      </q-chip>
      <q-space />
      <template v-if="results.length > 0">
        <q-btn
          v-if="!editMode"
          @click="editMode = true"
          size="11px"
          padding="xs sm"
          :label="$t('edit')"
          color="theme-blue"
        />
        <template v-if="editMode">
          <q-btn
            @click="exitEditMode"
            size="11px"
            padding="xs sm"
            :label="$t('cancel')"
            color="theme-grey"
          />
          <q-btn
            @click="deleteDialogShow = true"
            size="11px"
            padding="xs sm"
            :label="$t('delete')"
            color="theme-red"
          />
        </template>
    </template>
    </div>

    <q-scroll-area class="col column">
        <q-card
          v-for="item in serialList"
          :key="item._key"
          v-ripple="editMode"
          bordered
          flat
          class="q-px-md q-py-md q-mb-sm row items-center"
          :class="selectedSerials.includes(item) ? 'bg-theme-orange' : 'surface2'"
          @click="editMode ? toggleSerial(item) : null"
        >
          <div class="col">
            <div class="text-h6 text-low">{{ item.product_code }}</div>
            <div class="text-body1 highlight">{{ item.serial_code }}</div>
            <div class="text-caption">{{ item.path.map(p => p.position_code).join(' → ') || 'IN' }}</div>
          </div>
          <div class="col-auto" v-if="editMode">
            <q-icon :name="selectedSerials.includes(item) ? 'mdi-checkbox-marked-circle' : 'mdi-circle-outline'" size="md" color="text-low" />
          </div>
        </q-card>
    </q-scroll-area>

    <!-- DELETE DIALOG -->
    <SlideUpCard v-model="deleteDialogShow" >
      <div class="column q-gutter-y-md">
        <div class="text-h3">
          {{ $t('serial_remove_confirm') }}
        </div>

        <ul class="text-body1">
          <li v-for="serial in selectedSerials" :key="serial._key">
            {{ serial.product_code }} - {{ serial.serial_code }}
          </li>
        </ul>

        <q-space />

        <!-- Reason input -->
        <q-input
          v-model="deleteReason"
          :label="$t('movement_reason')"
          autogrow
          filled
          stack-label
          label-slot
        >
          <template #label>
            {{ $t('movement_reason') }}
            <span v-if="config.mandatoryReasonForMovementTypes?.includes('adjustment')" class="text-theme-red"> * </span>
          </template>
        </q-input>

        <div class="row justify-between">
          <q-btn :label="$t('cancel')" color="theme-grey" @click="deleteDialogShow = false" />
          <q-btn :label="$t('confirm')" color="theme-red" :disabled="mandatoryReasonNotSet" @click="deleteSelected" />
        </div>
      </div>

    </SlideUpCard>

  </div>
</template>

<script setup>
import { Notify } from 'quasar';
import { sendEventsBulk } from '@/composables/bulkEvent';
import { ref, computed } from 'vue';
import SearchOrScan from '@/components/SearchOrScan.vue';
import { api } from 'app/src/boot/axios';
import { useI18n } from 'vue-i18n';
import SlideUpCard from '@/components/SlideUpCard.vue';
import { useConfigStore } from '@/stores/config';

const { t: $t } = useI18n();
const { config } = useConfigStore();
const serialCodeFilter = ref('');
const productCodeFilter = ref('');
const results = ref([]);
const editMode = ref(false);
const deleteDialogShow = ref(false);
const deleteReason = ref('');

const serialList = computed(() => {
  return results.value.filter(s => s.product_code.includes(productCodeFilter.value));
});

const selectedSerials = ref([]);

const toggleSerial = (serial) => {
  if (selectedSerials.value.includes(serial)) {
    selectedSerials.value = selectedSerials.value.filter(s => s !== serial);
  } else {
    selectedSerials.value.push(serial);
  }
}

function search() {
  api.get('inventory', { params: {
    serial_search: serialCodeFilter.value,
    product_search: productCodeFilter.value,
    serials_only: true
  }})
  .then(response => {
    results.value = response.data;
  })
  .catch(error => {
    Notify.create({
      message: error.response.data.message,
      position: 'top',
      color: 'red',
      icon: 'error',
    });
  });
}

const exitEditMode = () => {
  editMode.value = false;
  selectedSerials.value = [];
}

const deleteSelected = async () => {
  const baseEvent = {
    event_type: 'MOVEMENT_COMPLETED',
    movement_type: 'adjustment',
    qt_planned: -1,
    qt_confirmed: -1
  }
  const events = selectedSerials.value.map(serial => {
    const position_key = [...serial.path].pop().position_key
    return {
      ...baseEvent,
      position_from: position_key,
      position_to: position_key,
      product_key: serial.product_key,
      serial_key: serial.serial_key,
      reason: deleteReason.value
    }
  })
  const serial_codes = selectedSerials.value.map(s => s.serial_code).join(', ')
  await sendEventsBulk(events)
  selectedSerials.value = [];
  search();
  Notify.create({
    message: $t('serial_removed', { serials: serial_codes }),
    position: 'top',
    color: 'theme-green',
  });
  deleteDialogShow.value = false;
};

const mandatoryReasonNotSet = computed(() => {
  return config.mandatoryReasonForMovementTypes?.includes('adjustment') && deleteReason.value.length === 0;
});

</script>

<style lang="scss" scoped>
</style>
