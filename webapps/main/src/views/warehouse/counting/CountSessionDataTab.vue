<template>
    <div class="column q-gutter-y-lg q-pa-md">

      <div class="row items-center q-gutter-x-xl">
        <div class="text-body2 text-low col-auto">
          {{ $t('warehouse.counting.type') }}
        </div>

        <div class="col-auto">
          <q-btn-toggle
            v-model="sessionDataModel.type"
            :options="sessionTypeOptions"
            size="12px"
            padding="xs md"
            :disable="!canEditType"
          />
        </div>
      </div>


      <div class="col-auto">
        <q-input
          v-model="sessionDataModel.code"
          filled
          :label="$capitalize($t('code'))"
          :hint="$t('warehouse.counting.code_hint')"
          :disable="!canEditCode"
        />
      </div>

      <q-input
        v-model="sessionDataModel.description"
        filled
        autogrow
        :label="$t('description')"
        :disable="!canEditDescription"
      />

      <div class="row q-gutter-md">
        <q-input
          v-model="sessionDataModel.scheduled_start"
          filled
          mask="####-##-##"
          :label="$t('warehouse.counting.scheduled_start')"
          :placeholder="$t('date_format')"
          input-class="cursor-pointer"
          class="col"
          label-slot
          clearable
          stack-label
          :disable="!canEditScheduledStart"
        >
          <template #append>
            <q-icon name="mdi-calendar" />
          </template>
          <q-popup-proxy v-if="canEditScheduledStart" anchor="center middle" self="center middle" @hide="blur">
            <q-date
              v-model="sessionDataModel.scheduled_start"
              mask="YYYY-MM-DD"
              minimal
            >
              <div class="row items-center justify-end">
                <q-btn v-close-popup :label="$t('close')" color="primary" flat />
              </div>
            </q-date>
          </q-popup-proxy>
          <template #label>
            {{ $t('warehouse.counting.scheduled_start') }}
          </template>
        </q-input>
        <q-input
          v-model="sessionDataModel.scheduled_end"
          filled
          mask="####-##-##"
          :label="$t('warehouse.counting.scheduled_end')"
          :placeholder="$t('date_format')"
          input-class="cursor-pointer"
          class="col"
          label-slot
          clearable
          stack-label
          :disable="!canEditScheduledEnd"
        >
          <template #append>
            <q-icon name="mdi-calendar" />
          </template>
          <q-popup-proxy v-if="canEditScheduledEnd" anchor="center middle" self="center middle" @hide="blur">
            <q-date
              v-model="sessionDataModel.scheduled_end"
              mask="YYYY-MM-DD"
              minimal
              :options="scheduledEndDateOptions"
            >
              <div class="row items-center justify-end">
                <q-btn v-close-popup :label="$t('close')" color="primary" flat />
              </div>
            </q-date>
          </q-popup-proxy>
          <template #label>
            {{ $t('warehouse.counting.scheduled_end') }}
          </template>
        </q-input>
      </div>

      <div class="row items-center q-gutter-x-md">
        <q-checkbox
          v-model="sessionDataModel.blind_quantities"
          :label="$t('warehouse.counting.blind_quantities')"
          :disable="!canEditBlindMode"
        />
        <q-checkbox
          v-model="sessionDataModel.blind_serials"
          :label="$t('warehouse.counting.blind_serials')"
          :disable="!canEditBlindMode"
        />
      </div>
    </div>
</template>

<script setup>
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';

const sessionDataModel = defineModel('sessionData', {
  type: Object,
  required: true,
});

const props = defineProps({
  sessionStatus: {
    type: String,
    default: 'planned',
  },
});

const { t: $t } = useI18n();

const sessionTypeOptions = computed(() => [
  { label: $t('warehouse.counting.by_product'), value: 'product' },
  { label: $t('warehouse.counting.by_position'), value: 'position' },
]);

// Computed flags for field restrictions based on status
const isStarted = computed(() => props.sessionStatus === 'started');
const isCompleted = computed(() => ['completed', 'applied', 'canceled'].includes(props.sessionStatus));

// Fields that can be edited:
// - PLANNED: All fields
// - STARTED: Only description and scheduled_end
// - COMPLETED/APPLIED/CANCELED: None
const canEditType = computed(() => !isStarted.value && !isCompleted.value);
const canEditCode = computed(() => !isStarted.value && !isCompleted.value);
const canEditBlindMode = computed(() => !isStarted.value && !isCompleted.value);
const canEditScheduledStart = computed(() => !isStarted.value && !isCompleted.value);
const canEditDescription = computed(() => !isCompleted.value);
const canEditScheduledEnd = computed(() => !isCompleted.value);

// Date options for scheduled_end: disable dates before scheduled_start
const scheduledEndDateOptions = computed(() => {
  return (date) => {
    if (!sessionDataModel.value.scheduled_start) {
      return true; // Allow all dates if no start date is set
    }
    // Disable dates that are before scheduled_start
    // Quasar date options uses YYYY/MM/DD format, while our model uses YYYY-MM-DD
    // We standardize to YYYY/MM/DD for comparison
    const start = sessionDataModel.value.scheduled_start.replaceAll('-', '/');
    return date >= start;
  };
});

function blur() {
  document.activeElement.blur();
}
</script>

