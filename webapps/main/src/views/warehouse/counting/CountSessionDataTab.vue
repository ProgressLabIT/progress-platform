<template>
    <div class="column q-gutter-y-lg q-pa-md">

      <div class="row items-center q-gutter-x-xl">
        <div class="text-body2 text-low col-auto">
          {{ $t('warehouse.counting.type') }}
        </div>

        <div class="col-auto">
          <q-btn-toggle
            :model-value="sessionData.type"
            @update:model-value="$emit('update:sessionData', { ...sessionData, type: $event })"
            :options="sessionTypeOptions"
            size="12px"
            padding="xs md"
          />
        </div>
      </div>


      <div class="col-auto">
        <q-input
          :model-value="sessionData.code"
          @update:model-value="$emit('update:sessionData', { ...sessionData, code: $event })"
          filled
          :label="$capitalize($t('code'))"
          :hint="$t('warehouse.counting.code_hint')"
        />
      </div>

      <q-input
        :model-value="sessionData.description"
        @update:model-value="$emit('update:sessionData', { ...sessionData, description: $event })"
        filled
        autogrow
        :label="$t('description')"
      />

      <div class="row q-gutter-md">
        <q-input
          :model-value="sessionData.scheduled_start"
          @update:model-value="$emit('update:sessionData', { ...sessionData, scheduled_start: $event })"
          filled
          :label="$t('warehouse.counting.scheduled_start')"
          :placeholder="$t('date_format')"
          input-class="cursor-pointer"
          class="col"
          label-slot
          stack-label
        >
          <template #append>
            <q-icon name="mdi-calendar" />
          </template>
          <q-popup-proxy anchor="center middle" self="center middle" @hide="blur">
            <q-date
              :model-value="sessionData.scheduled_start"
              @update:model-value="$emit('update:sessionData', { ...sessionData, scheduled_start: $event })"
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
          :model-value="sessionData.scheduled_end"
          @update:model-value="$emit('update:sessionData', { ...sessionData, scheduled_end: $event })"
          filled
          :label="$t('warehouse.counting.scheduled_end')"
          :placeholder="$t('date_format')"
          input-class="cursor-pointer"
          class="col"
          label-slot
          stack-label
        >
          <template #append>
            <q-icon name="mdi-calendar" />
          </template>
          <q-popup-proxy anchor="center middle" self="center middle" @hide="blur">
            <q-date
              :model-value="sessionData.scheduled_end"
              @update:model-value="$emit('update:sessionData', { ...sessionData, scheduled_end: $event })"
              minimal
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

      <q-checkbox
        :model-value="sessionData.blind_mode"
        @update:model-value="$emit('update:sessionData', { ...sessionData, blind_mode: $event })"
        :label="$t('warehouse.counting.blind_mode')"
      />
    </div>
</template>

<script setup>
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';

const props = defineProps({
  sessionData: {
    type: Object,
    required: true,
  },
});

defineEmits(['update:sessionData']);

const { t: $t } = useI18n();

const sessionTypeOptions = computed(() => [
  { label: $t('warehouse.counting.by_product'), value: 'product' },
  { label: $t('warehouse.counting.by_position'), value: 'position' },
]);

function blur() {
  document.activeElement.blur();
}
</script>

