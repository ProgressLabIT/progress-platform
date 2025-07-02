<template>
  <div class="absolute-full column">
    <q-table
      id="job-bom"
      ref="bom"
      class="my-sticky-header-table col"
      card-class="surface1 shadow-0"
      row-key="line_key"
      virtual-scroll
      :loading="loading"
      :rows="bom"
      :columns="columns"
      :pagination="{ rowsPerPage: 0 }"
      :rows-per-page-options="[0]"
      :virtual-scroll-sticky-size-start="48"
      no-data-label="I didn't find anything for you"
      hide-bottom
    >
      <template v-if="!bom.length" #top-row>
        <div class="text-low absolute-center">
          {{ t('no_data') }}
        </div>
      </template>
      <template #body-cell-description="props">
        <q-td style="text-wrap: wrap">
          {{ props.value }}
        </q-td>
      </template>
      <template #body-cell-serials="props">
        <q-td :props="props">
          <template v-if="props.row.traceability_level !== null && props.row.phase_key === job.phase_key">
            <span class="q-mr-sm">
              <q-icon
                v-if="
                  job.active_batch_qt &&
                  props.row.declared_serials.length === props.row.batch_qt
                "
                name="mdi-check-circle"
                color="theme-green"
              />
              <q-icon
                v-else-if="props.row.traceability_level"
                name="mdi-asterisk-circle-outline"
                color="theme-red"
              />
              <!-- <q-icon
                v-else-if="
                  job.active_batch_qt &&
                  props.row.declared_serials.length < props.row.batch_qt
                "
                name="mdi-circle-outline"
                color="theme-white"
              /> -->
            </span>
            <q-btn
              v-if="props.value !== null && props.row.traceability_level !== null"
              size="sm"
              color="theme-blue"
              :loading="loading"
              :disable="!job.active_batch_key || !job.active"
              @click="serial_form_bom_line = props.row"
            >
              {{
                props.row.phase_key === job.phase_key ? t('edit') : t('view')
              }}
            </q-btn>
          </template>
        </q-td>
      </template>
    </q-table>

    <BomComponentSerialForm
      :show="!!serial_form_bom_line"
      :bom_line="serial_form_bom_line"
      :batch_key="job.active_batch_key"
      :wo_key="job.wo_key"
      :phase_key="job.phase_key"
      :traceability_enabled="traceability_enabled"
      mode="new"
      @select="updateSerialSelection"
      @close="
        () => {
          serial_form_bom_line = null;
          refreshBom();
        }
      "
    />

    <q-separator />

    <div
      class="row items-center col-auto q-px-md text-body2 q-col-qutter-md q-pa-md"
    >
      <div class="col">
        <span class="q-mr-3">
          {{ $capitalize(t('bom.quantity_type.radio_label')) }}
        </span>
        <q-radio
          v-for="qt_type in qt_types"
          :key="qt_type"
          v-model="quantity_type"
          :val="qt_type"
          :label="t('bom.quantity_type.' + qt_type).toUpperCase()"
        >
        </q-radio>
        <q-space />
        <span class="q-mr-3">
          {{ $capitalize(t('bom.bom_type.radio_label')) }}
        </span>
        <q-radio
          v-for="b_type in bom_types"
          :key="b_type"
          v-model="bom_type"
          :val="b_type"
          :label="t('bom.bom_type.' + b_type).toUpperCase()"
        >
        </q-radio>
      </div>
      <div v-if="requiresComponentSerials" class="col-auto">
        <q-btn
          size="md"
          padding="lg xl"
          color="theme-blue"
          :loading="loading"
          :disable="!job.active_batch_key"
          @click="show_all_serial_form = true"
        >
          {{ t('serial_field.bom_component') }}
        </q-btn>
      </div>
    </div>

    <SerialBomForm
      v-if="show_all_serial_form"
      :show="show_all_serial_form"
      :batch_key="job.active_batch_key ? job.active_batch_key : null"
      :wo_key="job.wo_key"
      :phase_key="job.phase_key"
      mode="new"
      :traceability_enabled="traceability_enabled"
      :bom="bom"
      @select="updateSerialSelection"
      @reset="initBomSerials"
      @close="
        () => {
          show_all_serial_form = false;
          refreshBom();
        }
      "
    >
    </SerialBomForm>
  </div>
</template>

<script setup>
import { ref, computed, defineProps } from 'vue';
import { useI18n } from 'vue-i18n';
import { useStore } from 'vuex';
import BomComponentSerialForm from 'app/src/components/traceability/BomComponentSerialForm.vue';
import SerialBomForm from 'app/src/components/traceability/SerialBomForm.vue';

const props = defineProps({
  job: {
    type: Object,
    required: true,
  },
});

const store = useStore();
const { t } = useI18n();
const quantity_type = ref('job');
const qt_types = ['item', 'batch', 'job'];
const bom_type = ref('job_bom');
const bom_types = ['job_bom', 'wo_bom'];
const serial_form_bom_line = ref(null);
const show_all_serial_form = ref(false);
const loading = ref(false);

const columns = computed(() => {
  // TODO: refactor into mixin / composition function, used also in ProductBoM
  return [
    {
      name: 'code',
      field: 'component_code',
      sortable: true,
      label: t('code').toUpperCase(),
      align: 'left',
    },
    {
      name: 'description',
      field: 'component_description',
      sortable: true,
      label: t('description').toUpperCase(),
      align: 'left',
    },
    {
      name: 'phase_name',
      sortable: true,
      field: 'phase_name',
      label: t('phase.short', 1).toUpperCase(),
      align: 'left',
    },
    {
      name: 'qt',
      sortable: true,
      field: display_qt.value,
      label: t('quantity.short').toUpperCase(),
    },
    {
      name: 'serials',
      field: 'serials',
      label: t('serial', 2).toUpperCase(),
    },
  ];
});

const display_qt = computed(() => {
  return {
    item: 'qt',
    batch: 'batch_qt',
    job: 'job_qt',
  }[quantity_type.value];
});

const bom = computed(() => {
  if (!props.job?.wo_bom) {
    refreshBom();
  }
  return (props.job.wo_bom || [])
    .filter((i) => {
      return bom_type.value === 'wo_bom'
        ? true
        : i.phase_key === props.job.phase_key;
    })
    .map((i) => {
      // line quantity is per item
      return {
        ...i,
        line_key: i.phase_key + '_' + i.component_key,
        batch_qt: i.qt * props.job.active_batch_qt,
        job_qt: i.qt * props.job.qt_planned,
      };
    });
});

const traceability_enabled = computed(() => {
  return !!store.state.traceability.working_job_data.traceability_level;
});

const requiresComponentSerials = computed(() => {
  return props.job.active && props.job.active_batch_qt && props.job.wo_bom.some(i => i.traceability_level && i.phase_key === props.job.phase_key);
});

// Utility function to create a serial link
const createSerialLink = ({childSerial, parentSerialKey, componentKey}) => ({
  _key: childSerial?._key,
  code: childSerial?.code,
  parent_serial_key: parentSerialKey,
  wo_key: props.job.wo_key,
  job_key: props.job._key,
  component_key: componentKey,
  batch_key: props.job.active_batch_key,
  phase_key: props.job.phase_key,
})

// Update serial selection for a bom line
const updateSerialSelection = ({selection, bomLine, parentSerialKey}) => {
  console.log('updateSerialSelection', {selection, bomLine, parentSerialKey})

  let newSerialLinks
  if (selection === null) {
    newSerialLinks = []
  } else if (bomLine.qt > 1) {
    newSerialLinks = selection.map(childSerial => createSerialLink({childSerial, parentSerialKey, componentKey: bomLine.component_key}))
  } else {
    newSerialLinks = [createSerialLink({childSerial: selection, parentSerialKey, componentKey: bomLine.component_key})]
  }

  // Update store
  store.commit('UPDATE_BOM_LINE_COMPONENT_SERIALS', {
    phaseKey: bomLine.phase_key,
    componentKey: bomLine.component_key,
    lineSerialLinks: newSerialLinks,
    parentSerialKey,
  });
};

async function refreshWO() {
  await store.dispatch('loadWorkingJobData', props.job._key);
  loading.value = false;
}

function refreshBom() {
  loading.value = true;
  refreshWO();
}
</script>

<style lang="sass">
#job-bom
  .q-table__top,
  .q-table__bottom,
  thead tr:first-child th /* bg color is important for th; just specify one */
    background-color: var(--surface-1)

  thead tr th
    position: sticky
    z-index: 1
  /* this will be the loading indicator */
  thead tr:last-child th
    /* height of all previous header rows */
    top: 48px
  thead tr:first-child th
    top: 0
</style>
