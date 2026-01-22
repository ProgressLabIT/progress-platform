<template>
  <div class="column q-gutter-md q-pa-md">
    <!-- Export/Import Actions -->
    <div class="col-auto row q-gutter-sm">
      <q-btn-dropdown
        :label="$t('export')"
        icon="mdi-download"
        color="primary"
        outline
        dense
        no-caps
        :loading="exporting"
      >
        <q-list>
          <q-item clickable v-close-popup @click="$emit('export-xlsx')">
            <q-item-section avatar>
              <q-icon name="mdi-file-excel" color="green" />
            </q-item-section>
            <q-item-section>Excel (.xlsx)</q-item-section>
          </q-item>
          <q-item clickable v-close-popup @click="$emit('export-csv')">
            <q-item-section avatar>
              <q-icon name="mdi-file-delimited" color="blue" />
            </q-item-section>
            <q-item-section>CSV (.csv)</q-item-section>
          </q-item>
        </q-list>
      </q-btn-dropdown>
      <q-btn
        v-if="sessionStatus === 'completed'"
        :label="$t('import')"
        icon="mdi-upload"
        color="primary"
        outline
        dense
        no-caps
        @click="$emit('import')"
      />
    </div>

    <q-separator />

    <div class="text-h5 uppercase">{{ $t('filter', 2) }}</div>

    <!-- Variance & only-with-variance -->
    <div class="col-auto row items-center">
      <div class="col-6">
        <q-checkbox
          :model-value="modelValue.onlyWithVariance"
          @update:model-value="updateFilter('onlyWithVariance', $event)"
          :label="$t('warehouse.counting.variance_only')"
          dense
        />
      </div>
      <div class="col-6">
        <!-- Has Notes -->
        <q-checkbox
          :model-value="modelValue.hasNotes"
          @update:model-value="updateFilter('hasNotes', $event)"
          :label="$t('warehouse.counting.with_notes_only')"
          dense
        />
      </div>
      <div class="col-6">
        <!-- Only Conflicts -->
        <q-checkbox
          :model-value="modelValue.onlyConflicts"
          @update:model-value="updateFilter('onlyConflicts', $event)"
          :label="$t('warehouse.counting.conflicts_only')"
          dense
        />
      </div>
      <div class="col-6">
        <!-- Only Errors -->
        <q-checkbox
          :model-value="modelValue.onlyErrors"
          @update:model-value="updateFilter('onlyErrors', $event)"
          :label="$t('warehouse.counting.errors_only')"
          dense
        />
      </div>
    </div>

    <div class="col-auto">
      <q-input
        :model-value="modelValue.variance"
        @update:model-value="updateFilter('variance', $event)"
        type="number"
        class="full-width"
        min="0"
        :max="modelValue.varianceType === 'percentage' ? 100 : null"
        :label="$t('warehouse.counting.variance_threshold')"
        stack-label
        dense
        filled
      >
        <template #append>
          <q-btn-toggle
            :model-value="modelValue.varianceType"
            @update:model-value="updateFilter('varianceType', $event)"
            map-options
            emit-value
            dense
            flat
            size="md"
            :options="[
              { label: $t('quantity.short'), value: 'absolute' },
              { label: '%', value: 'percentage' },
            ]"
          />
        </template>
      </q-input>
    </div>

    <!-- Position Level -->
    <div class="col-auto">
      <q-input
        :model-value="positionLevel"
        @update:model-value="$emit('update:positionLevel', Number($event))"
        type="number"
        :label="$t('warehouse.counting.position_level')"
        class="full-width"
        dense
        filled
        min="0"
      >
        <template #append>
          <q-btn
            :color="allLevels ? 'primary' : 'white-low'"
            size="sm"
            padding="xs md"
            outline
            dense
            @click="$emit('update:allLevels', !allLevels)"
          >
            <div class="q-mr-sm">{{ $t('all') }}</div>
            <q-icon name="mdi-family-tree" size="xs" />
          </q-btn>
        </template>
      </q-input>
    </div>

    <!-- Text & tag filters -->

    <!-- Product Tag Filter -->
    <BaseAutocompleteTag
      :value="modelValue.productTag"
      :key-only="true"
      :label="$t('search_tags')"
      dense
      @select="updateFilter('productTag', $event)"
    />

    <!-- User Filter -->
    <BaseAutocompleteUser
      :value="modelValue.userKey"
      :key-only="true"
      :operator-only="false"
      dense
      :label="$t('warehouse.counting.user')"
      @select="updateFilter('userKey', $event)"
    />

    <!-- Product Filter -->
    <q-input
      :model-value="modelValue.product"
      @update:model-value="updateFilter('product', $event)"
      :label="$t('product.label')"
      dense
      filled
      clearable
    />

    <!-- Serial Filter -->
    <q-input
      :model-value="modelValue.serial"
      @update:model-value="updateFilter('serial', $event)"
      :label="$t('serial')"
      dense
      filled
      clearable
    />

    <!-- Position / Path Filter -->
    <q-input
      :model-value="modelValue.position"
      @update:model-value="updateFilter('position', $event)"
      :label="$t('warehouse.inventory.position')"
      dense
      filled
      clearable
    />
    <q-toggle
      :model-value="modelValue.positionIncludePath"
      @update:model-value="updateFilter('positionIncludePath', $event)"
      :label="$t('warehouse.counting.include_path')"
      dense
    />
  </div>
</template>

<script setup>
import BaseAutocompleteTag from '@/components/BaseAutocompleteTag.vue';
import BaseAutocompleteUser from '@/components/BaseAutocompleteUser.vue';

/**
 * Filter sidebar component for count records table.
 *
 * Provides export/import buttons and filter controls for:
 * - Variance (threshold, only with variance)
 * - Notes, conflicts
 * - Position level aggregation
 * - Text filters (product, serial, position)
 * - Tag and user filters
 */

const props = defineProps({
  /**
   * Filter state object (v-model)
   */
  modelValue: {
    type: Object,
    required: true,
  },
  /**
   * Current position level (null when allLevels is true)
   */
  positionLevel: {
    type: Number,
    default: null,
  },
  /**
   * Whether "All levels" mode is active
   */
  allLevels: {
    type: Boolean,
    default: true,
  },
  /**
   * Session status - used to show/hide import button
   */
  sessionStatus: {
    type: String,
    default: null,
  },
  /**
   * Whether export is in progress
   */
  exporting: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits([
  'update:modelValue',
  'update:positionLevel',
  'update:allLevels',
  'export-xlsx',
  'export-csv',
  'import',
]);

/**
 * Update a single filter field and emit the updated object
 * @param {string} field - The filter field name
 * @param {*} value - The new value
 */
function updateFilter(field, value) {
  emit('update:modelValue', {
    ...props.modelValue,
    [field]: value,
  });
}
</script>
