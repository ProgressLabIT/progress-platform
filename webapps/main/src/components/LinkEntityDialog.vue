<template>
  <BaseDialog :show="props.show" @close="handleClose">
    <q-card class="surface1 q-pa-md">
      <q-card-section>
        <div class="text-h6 display highlight">{{ $t('link_entity') }}</div>
      </q-card-section>

      <q-card-section>
        <!-- Entity Type Selection -->
        <div class="q-mb-md">
          <div class="text-body2 q-mb-sm text-weight-medium">{{ $t('select_entity_type') }}</div>
          <q-select
            v-model="selectedEntityType"
            :options="entityTypeOptions"
            emit-value
            map-options
            :label="$t('entity_type')"
            :placeholder="$t('select_entity_type')"
            color="theme-blue"
            filled
            class="full-width"
          />
        </div>

        <!-- Entity Selection -->
        <div class="q-mb-md">
          <div class="text-body2 q-mb-sm text-weight-medium">{{ $t('select_entity') }}</div>

          <!-- Work Order Autocomplete -->
          <BaseAutocompleteWorkOrder
            v-if="selectedEntityType === 'work_order'"
            v-model:value="selectedEntity"
            :label="$t('work_order.long')"
            :disable-keys="excludeLinkKeys('work_order')"
            @select="onEntitySelect"
          />

          <!-- Issue Autocomplete -->
          <BaseAutocompleteIssue
            v-else-if="selectedEntityType === 'issue'"
            v-model:value="selectedEntity"
            :label="$t('issue')"
            :disable-keys="excludeLinkKeys('issue')"
            @select="onEntitySelect"
          />

          <!-- Serial Autocomplete -->
          <BaseAutocompleteSerial
            v-else-if="selectedEntityType === 'serial'"
            v-model:value="selectedEntity"
            include_unreleased
            :show-link-status="false"
            :show-inventory-status="false"
            show-product-code
            show-product-description
            :label="$t('serial')"
            :disable-keys="excludeLinkKeys('serial')"
            @select="onEntitySelect"
          />

          <!-- Product Autocomplete -->
          <BaseAutocompleteProduct
            v-else-if="selectedEntityType === 'product'"
            v-model:value="selectedEntity"
            :label="$t('product.label')"
            :disable-keys="excludeLinkKeys('product')"
            @select="onEntitySelect"
          />

          <!-- Task Autocomplete -->
          <BaseAutocompleteTask
            v-else-if="selectedEntityType === 'task'"
            v-model:value="selectedEntity"
            :label="$t('task')"
            :disable-keys="excludeLinkKeys('task')"
            @select="onEntitySelect"
          />
        </div>
      </q-card-section>

      <q-card-actions align="right" class="q-pa-md">
        <q-btn
          flat
          :label="$t('cancel')"
          color="theme-grey"
          @click="handleClose"
        />
        <q-btn
          unelevated
          :label="$t('link')"
          color="theme-blue"
          :disable="!selectedEntity"
          :loading="saving"
          @click="handleSave"
        />
      </q-card-actions>
    </q-card>
  </BaseDialog>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRoute } from 'vue-router';
import BaseAutocompleteIssue from './BaseAutocompleteIssue.vue';
import BaseAutocompleteProduct from './BaseAutocompleteProduct.vue';
import BaseAutocompleteSerial from './BaseAutocompleteSerial.vue';
import BaseAutocompleteTask from './BaseAutocompleteTask.vue';
import BaseAutocompleteWorkOrder from './BaseAutocompleteWorkOrder.vue';
import BaseDialog from './BaseDialog.vue';

const props = defineProps({
  show: {
    type: Boolean,
    required: true,
  },
  saving: {
    type: Boolean,
    default: false,
  },
  existingLinks: {
    type: Array,
    default: () => [],
  },
});

const selectedEntityType = defineModel('selectedEntityType', {
  type: String,
  default: null
});

const emit = defineEmits(['save', 'close']);

const { t: $t } = useI18n();
const route = useRoute();
const selectedEntity = ref(null);

const entityTypeOptions = computed(() => [
  { label: $t('work_order.long'), value: 'work_order' },
  { label: $t('issue'), value: 'issue' },
  { label: $t('serial'), value: 'serial' },
  { label: $t('product.label'), value: 'product' },
  { label: $t('task'), value: 'task' },
]);

function onEntitySelect(entity) {
  selectedEntity.value = entity;
}

function handleSave() {
  if (selectedEntity.value) {
    emit('save', {
      entityType: selectedEntityType.value,
      entity: selectedEntity.value,
    });
  }
}


function excludeLinkKeys(type) {
  const base = props.existingLinks.filter(link => link.type === type).map(link => link.key);
  if (type === 'task') {
    return [route.params.taskKey, ...base];
  }
  return base;
}

function handleClose() {
  // Reset form state
  selectedEntity.value = null;
  emit('close');
}
</script>
