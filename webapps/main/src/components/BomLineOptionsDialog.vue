<template>
  <BaseDialog :show="show" @close.stop="handleClose">
    <q-card style="min-width: 300px; max-width: 70vw" class="surface1 q-pa-md column">
      <q-tabs
        v-model="activeTab"
        active-color="theme-blue"
        dense
        indicator-color="theme-blue"
      >
        <q-tab name="options" :label="$t('warehouse.consumption_options.label')" />
        <q-tab name="extra" :label="$t('extra_data')" />
      </q-tabs>

      <q-separator />

      <q-tab-panels v-model="activeTab">
        <q-tab-panel name="options" class="surface1 q-px-none q-py-lg">
          <BaseAutocompletePosition
            :model-value="localConsumptionOptions?.consumption_position_key"
            :label="$t('warehouse.consumption_options.consumption_position_key')"
            key-only
            @select="updateConsumptionPosition"
          />
        </q-tab-panel>

        <q-tab-panel name="extra" class="surface1 q-px-none q-py-lg">
          <JsonEditor
            v-model="extraJson"
            :label="$t('extra_data')"
            :rows="10"
            @validation-error="extraJsonError = $event"
          />
        </q-tab-panel>
      </q-tab-panels>

      <div class="row q-col-gutter-md">
        <div class="col-6">
          <q-btn
            class="full-width"
            color="theme-blue"
            :label="$t('save')"
            @click="handleSave"
          />
        </div>
        <div class="col-6">
          <q-btn
            class="full-width"
            color="theme-grey"
            :label="$t('cancel')"
            @click="handleClose"
          />
        </div>
      </div>
    </q-card>
  </BaseDialog>
</template>

<script setup>
import { ref, watch } from 'vue';
import { cloneDeep } from 'lodash';
import BaseDialog from '@/components/BaseDialog.vue';
import BaseAutocompletePosition from '@/components/BaseAutocompletePosition.vue';
import JsonEditor from '@/components/JsonEditor.vue';

const props = defineProps({
  show: {
    type: Boolean,
    default: false,
  },
  consumptionOptions: {
    type: Object,
    default: () => ({}),
  },
  extraData: {
    default: null,
  },
});

const emit = defineEmits(['save', 'close', 'update:position']);

// Local state
const activeTab = ref('options');
const consumptionPositionKey = ref(null);
const extraJson = ref('');
const extraJsonError = ref(false);

// Watch for prop changes to update local state
watch(() => props.show, (newShow) => {
  if (newShow) {
    // Initialize local state when dialog opens
    consumptionPositionKey.value = cloneDeep(props.consumptionOptions?.consumption_position_key || null);

    // Initialize extra JSON
    const extraData = props.extraData || null;
    extraJson.value = extraData ? JSON.stringify(extraData, null, 2) : '';
    extraJsonError.value = false;
    activeTab.value = 'options';
  }
}, { immediate: true });

const updateConsumptionPosition = (position_key) => {
  consumptionPositionKey.value = position_key ?? null;
  // Emit position update for parent to add to position data cache
  emit('update:position', position_key);
};

const handleSave = () => {
  try {
    // Validate JSON
    let parsedExtraData = null;
    if (extraJson.value.trim()) {
      parsedExtraData = JSON.parse(extraJson.value);
    }
    extraJsonError.value = false;

    // Emit save event with both consumption options and extra data
    emit('save', {
      consumption_position_key: consumptionPositionKey.value,
      extra_data: parsedExtraData,
    });
  } catch (err) {
    if (err instanceof SyntaxError) {
      extraJsonError.value = true;
    } else {
      window.alert(err);
    }
  }
};

const handleClose = () => {
  emit('close');
};
</script>

