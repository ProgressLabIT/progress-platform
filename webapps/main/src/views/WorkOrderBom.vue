<template>
  <div class="column full-height full-width justify-between q-pa-md">
    <div class="row justify-between">
      <div class="col-4">
        <q-input
          v-model="searchText"
          :label="$capitalize($t('search'))"
          filled
          dense
          placeholder="Codice o Descrizione"
          append-icon="mdi-magnify"
        />
      </div>

      <div class="col-3">
        <BaseAutocompletePositions
          :model-value="outputPositionKey"
          :label="$t('warehouse.output_position')"
          :disable="!editMode"
          key-only
          dense
          @select="(positionKey) => udpateBomLinePosition(props.row, positionKey)"
        />
      </div>
      <q-btn v-if="!editMode" size="sm" color="theme-blue" @click="toggleEdit">
        {{ $t('bom.edit') }}
      </q-btn>

      <div v-else class="row q-gutter-sm">
        <q-btn color="theme-green" size="sm" :loading="saving" @click="saveChanges">
          {{ $t('save') }}
        </q-btn>
        <q-btn :disabled="saving" size="sm" color="theme-grey" @click="cancelChanges">
          {{ $t('cancel') }}
        </q-btn>
      </div>
    </div>

    <q-table
      id="product-bom"
      ref="wo-bom-table"
      v-model:selected="deleteLines"
      square
      row-key="table_key"
      class="my-sticky-header-table col text-body1 q-mt-md"
      card-class="surface1 no-shadow"
      wrap-cells
      virtual-scroll
      hide-no-data
      hide-bottom
      :selection="editMode ? 'multiple' : 'none'"
      table-header-class="low-text"
      :rows="filteredBom"
      :columns="tableHeaders"
      :pagination="{ rowsPerPage: 0 }"
      :rows-per-page-options="[0]"
      :virtual-scroll-sticky-size-start="48"
    >

      <template #body-cell-manage_inventory="props">
        <q-td class="text-center">
          <BaseAutocompletePositions
            :model-value="props.row.consumption_options?.consumption_position_key"
            :label="$t('warehouse.inventory.position')"
            :disable="!editMode"
            key-only
            dense
            @select="(positionKey) => udpateBomLinePosition(props.row, positionKey)"
          />
        </q-td>
      </template>

      <template #body-cell-code="{ value }">
        <div class="nowrap">{{ value }}</div>
      </template>
    </q-table>

    <!-- BOTTOM ROW -->
    <q-card flat class="col-auto surface1">
      <q-separator />
      <div
        class="row full-width items-center justify-between q-px-md"
        style="height: 48px"
      >
        <div class="col-4">
          <q-btn
            v-show="editMode"
            size="sm"
            padding="xs lg"
            color="theme-red"
            icon="mdi-delete"
            :label="$t('bom.delete_selected')"
            @click="removeBomLines"
          >
          </q-btn>
        </div>

        <div class="smaller col-4 text-center">
          {{ filteredBom.length }} {{ $t('of') }} {{ tempBom.length }}
          {{ $t('element', 2).toUpperCase() }}
        </div>

        <div class="col-4 row justify-end">
          <q-btn
            v-show="editMode"
            size="sm"
            padding="xm lg"
            color="theme-blue"
            icon="mdi-plus"
            :label="$t('bom.add_line')"
            @click="openItemSearch"
          >
          </q-btn>
        </div>
      </div>
    </q-card>

    <BaseDialog :show="showProductCatalog">
      <q-card style="max-width: 700px" class="surface1 q-pa-md">
        <q-card-section class="display text-h3 highlight">
          {{ $t('add') }} {{ $t('product.label', 2) }}
        </q-card-section>
        <q-card-section>
          <div class="row q-col-gutter-md items-center">
            <q-select
              v-model="newLinePhase"
              class="col-4"
              filled
              use-input
              dense
              input-debounce="0"
              :options="filteredProcess"
              :label="$capitalize($t('phase.short'))"
              option-label="alias"
              popup-content-class="text-capitalize"
              @filter="filterPhases"
            >
            </q-select>

            <!-- PRODUCT -->
            <BaseAutocompleteProduct
              :model-value="newLineProduct"
              :label="$capitalize($t('code') + ' / ' + $t('description'))"
              input-class="text-capitalize"
              filled
              class="col-6"
              :loading="catalogLoading"
              use-input
              :dense="true"
              @select="(selection) => loadProduct(selection)"
            />

            <q-input
              v-model="newLineQt"
              v-model.number="newLineQt"
              dense
              filled
              class="col-2"
              type="number"
              step="1"
              min="1"
              :label="$t('quantity.short')"
            >
            </q-input>
          </div>
        </q-card-section>

        <div class="row q-col-gutter-md q-pa-md">
          <div class="col-6">
            <q-btn
              class="full-width"
              color="theme-blue"
              :label="$t('add')"
              @click="addItem"
            >
            </q-btn>
          </div>
          <div class="col-6">
            <q-btn
              class="full-width"
              color="theme-grey"
              :label="$t('cancel')"
              @click="showProductCatalog = false"
            >
            </q-btn>
          </div>
        </div>
      </q-card>
    </BaseDialog>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { useI18n } from 'vue-i18n';

import { api } from '@/boot/axios.js';
import BaseDialog from '@/components/BaseDialog.vue';
import multiMatch from '@/lib/MultiFieldSearch.js';
import { useConfigStore } from '@/stores/config';
import BaseAutocompletePositions from 'components/BaseAutocompletePositions.vue';
import BaseAutocompleteProduct from 'components/BaseAutocompleteProduct.vue';

// Setup store and route
const { t, capitalize } = useI18n();
const { config } = useConfigStore();

// Define emits
const emit = defineEmits(['changesSaved', 'changesCanceled']);

const props = defineProps({
  wo_data: {
    type: Object,
    required: true,
  },
});


// Reactive state
const searchText = ref('');
const deleteLines = ref([]);
const showProductCatalog = ref(false);
const catalogLoading = ref(false);
const productCatalog = ref([]);
const newLineProduct = ref({});
const newLinePhase = ref({});
const newLineQt = ref(null);
const newLineConsumptionOptions = ref(null);
const saving = ref(false);
const filteredProcess = ref(null);
const tempBom = ref([]);
const outputPositionKey = ref(props.wo_data.output_position_key);

// Get phase name and key from job list to populate the dropdown
const processPhases = computed(() => {
  return Array.from(new Set(props.wo_data.jobs.map((job) => ({
    _key: job.phase_key,
    alias: job.phase_alias,
  }))));
});

const tableHeaders = computed(() => {
  let columns = [
    {
      name: 'component_code',
      field: 'component_code',
      label: t('code').toUpperCase(),
      align: 'left',
    },
    {
      name: 'component_description',
      field: 'component_description',
      label: t('description').toUpperCase(),
      align: 'left',
      style: 'width: 35%',
    },
    {
      name: 'phase_name',
      field: 'phase_name',
      label: t('phase.short').toUpperCase(),
      align: 'left',
    },
    {
      name: 'qt',
      field: 'qt',
      label: t('quantity.short').toUpperCase(),
      align: 'left',
    },
  ];

  if (config.enableInventoryManagement) {
    columns.push({
      name: 'manage_inventory',
      field: 'manage_inventory',
      label: t('warehouse.bom_options').toUpperCase(),
      align: 'center',
    });
  }

  return columns;
});

const editMode = ref(false);

function initTempBom() {
  tempBom.value = props.wo_data.wo_bom.map((i) => {
    return { ...i, table_key: i.component_key + i.phase_key };
  });
}

initTempBom();

const filteredBom = computed(() => {
  const fieldsToSearch = [
    'component_code',
    'component_description',
    'phase_name',
  ];
  return tempBom.value.filter((line) => {
    return multiMatch(searchText.value, line, fieldsToSearch);
  });
});

// Watch effects
watch(showProductCatalog, () => {
  newLineProduct.value = null;
  newLineQt.value = null;
  newLinePhase.value = null;
  newLineConsumptionOptions.value = null;
});

watch(props.wo_data, initTempBom, { deep: true });

// Methods
const toggleEdit = () => {
  if (editMode.value == false) {
    editMode.value = true;
  } else {
    editMode.value = false;
    deleteLines.value = [];
  }
};

const openItemSearch = () => {
  catalogLoading.value = true;
  showProductCatalog.value = true;

  api.get('product').then((resp) => {
    productCatalog.value = resp.data;
  });
  catalogLoading.value = false;
};

const udpateBomLinePosition = (line, positionKey) => {
  tempBom.value = tempBom.value.map((i) => {
    if (i.component_key === line.component_key && i.phase_key === line.phase_key) {
      i.consumption_options.consumption_position_key = positionKey;
    }
    return i;
  });
};

const filterPhases = (value, update) => {
  if (value === '') {
    update(() => {
      filteredProcess.value = [...processPhases.value];
    });
    return;
  }
  update(() => {
    const needle = value.toLowerCase();
    filteredProcess.value = processPhases.value.filter((o) => {
      const include = o.phase_alias.toLowerCase().includes(needle);
      return include;
    });
  });
};

const loadProduct = (selection) => {
  newLineProduct.value = selection;
};

const removeBomLines = () => {
  const linesToDelete = deleteLines.value.map((l) => l.table_key);
  const newBom = tempBom.value.filter(
    (line) => !linesToDelete.includes(line.table_key),
  );
  tempBom.value = newBom;
  deleteLines.value = [];
};

const addItem = () => {
  const isDuplicate = tempBom.value.some((line) => {
    return (
      line.component_key == newLineProduct.value._key &&
      (line.phase_key == newLinePhase.value?._key ?? null)
    );
  });

  if (!newLineQt.value || newLineQt.value <= 0) {
    window.alert(capitalize(t('bom.alerts.quantity_negative')));
  } else if (!isDuplicate) {
    const newLine = {
      component_key: newLineProduct.value._key,
      component_code: newLineProduct.value.code,
      component_description: newLineProduct.value.description,
      consumption_options: newLineConsumptionOptions.value || {},
      qt: newLineQt.value,
      phase_name: newLinePhase.value?.alias ?? null,
      phase_key: newLinePhase.value?._key ?? null,
      table_key:
        newLineProduct.value._key + (newLinePhase.value?._key ?? null),
    };

    tempBom.value = [...tempBom.value, newLine];
    showProductCatalog.value = false;
  } else {
    window.alert(capitalize(t('bom.alerts.line_exists')));
  }
};

const cancelChanges = () => {
  initTempBom();
  editMode.value = false;
  deleteLines.value = [];
  emit('changesCanceled');
};

const saveChanges = () => {
  saving.value = true;

  api.patch(`work-order/${props.wo_data._key}`, {
    new_bom: tempBom.value,
    new_output_position_key: outputPositionKey.value,
  }).then(() => {
    emit('refresh');
    editMode.value = false;
  }).finally(() => {
    saving.value = false;
  });
};
</script>

<style lang="sass">
#product-bom
  .q-table__top,
  .q-table__bottom,
  thead tr:first-child th /* bg color is important for th; just specify one */
    background-color: var(--surface-1)

  tbody:last-child .absolute-bottom
    background-color: var(--surface-1)
    z-index: 999
</style>
