<template>
  <div class="q-pa-md">

    <!-- OPTIONS -->
    <div class="row justify-center">
      <q-btn-toggle
        v-model="view"
        spread
        size="sm"
        :options="[
          {label: t('phase.step', 2), value: 'step'},
          {label: t('form', 2), value: 'form'}
        ]"
      />
    </div>


  <!-- FILTERS -->

    <div class="text-h5 text-uppercase low-text">
      {{  t('filter', 2) }}
    </div>

    <div class="row q-col-gutter-sm q-mt-sm">

      <!-- BY SERIAL -->
      <div v-if="traceabilityEnabled" class="col">
        <q-select
          ref="serial_filter"
          v-model="selectedSerial"
          filled
          dense
          use-input
          clearable
          :options="serials.options"
          option-label="name"
          option-value="_key"
          emit-value
          map-options
          :label="$capitalize(t('serial', 1))"
          class="q-mb-md"
          popup-content-class="surface1"
          @filter="filterSerial"
        >
        </q-select>
      </div>

      <!-- BY PHASE -->
      <div class="col">
        <q-select
          ref="phase_filter"
          v-model="selectedPhase"
          filled
          dense
          use-input
          clearable
          :options="phases.options"
          option-label="name"
          option-value="_key"
          emit-value
          map-options
          :label="$capitalize(t('phase.phase', 1))"
          class="q-mb-md"
          popup-content-class="surface1"
          @filter="filterPhase"
        >
        </q-select>
      </div>

      <!-- BY JOB -->
      <div class="col">
        <q-select
          ref="job_filter"
          v-model="selectedJob"
          filled
          dense
          use-input
          clearable
          :options="jobs.options"
          option-label="name"
          option-value="_key"
          emit-value
          map-options
          :label="$capitalize(t('job.label', 1))"
          class="q-mb-md"
          popup-content-class="surface1"
          @filter="filterJob"
        >
        </q-select>
      </div>

      <!-- BY OPERATOR -->
      <div class="col">
        <BaseAutocompleteUser
          :placeholder="$capitalize(t('operator'))"
          dense
          :show-avatar="false"
          class="q-mb-md"
          key-only
          :value="selectedOperator"
          :user-keys="operator_keys"
          @select="(selection) => (selectedOperator = selection)"
        >
        </BaseAutocompleteUser>
      </div>

      <!-- BY FIELD -->
      <div class="col" v-if="view === 'form'">
        <q-select
          ref="field_filter"
          v-model="selectedField"
          filled
          dense
          use-input
          clearable
          :options="fields.options"
          option-value="_key"
          emit-value
          map-options
          :label="$capitalize(t('field', 1))"
          class="q-mb-md"
          popup-content-class="surface1"
          @filter="filterField"
        >
          <template #option="scope">
            <q-item v-bind="scope.itemProps">
              <q-item-section>
                <q-item-label>
                  {{ scope.opt.label }}
                </q-item-label>
              </q-item-section>
              <q-item-section side>
                <q-item-label caption>
                  {{ scope.opt.phase }}
                </q-item-label>
              </q-item-section>
            </q-item>
          </template>
        </q-select>
      </div>
    </div>

    <q-separator class="q-my-md" />

    <div class="column col full-height">
      <!-- MAIN CONTENT -->
        <WorkOrderTraceabilityData
          v-if="wo_traceability_data.length"
          :wo_traceability_data="wo_traceability_data"
          :view="view"
          :filters="filters"
        >
        </WorkOrderTraceabilityData>
        <NoDataAlert v-else />
      </div>

    </div>
</template>

<script setup>
import { computed, ref, reactive } from 'vue';
import BaseAutocompleteUser from '@/components/BaseAutocompleteUser.vue';
import NoDataAlert from '@/components/NoDataAlert.vue';
import WorkOrderTraceabilityData from '@/components/workorderscreen/WorkOrderTraceabilityData.vue';
import { useI18n } from 'vue-i18n';
import { api } from '@/boot/axios';
import { useStore } from 'vuex';

const { t } = useI18n();

const store = useStore();

// Props
const props = defineProps({
  wo_data: {
    type: Object,
    required: true,
  },
});

// Refs
const view = ref('step');

const execution_data = ref([]);
const wo_field_data = ref([]);

const fields = reactive({
  list: [],
  options: [],
});

const phases = reactive({
  list: [],
  options: [],
});

const serials = reactive({
  list: [],
  options: [],
});

const jobs = reactive({
  list: [],
  options: [],
});

const operator_keys = ref(undefined);


// Query models
const selectedOperator = ref(undefined);
const selectedPhase = ref(undefined);
const selectedSerial = ref(undefined);
const selectedJob = ref(undefined);
const selectedField = ref(undefined);

// Computed
const filters = computed(() => ({
  selectedPhase: selectedPhase.value,
  selectedSerial: selectedSerial.value,
  selectedOperator: selectedOperator.value,
  selectedJob: selectedJob.value,
  selectedField: selectedField.value,
}));

const traceabilityEnabled = store.state.workorder.wo_data.traceability_level

function getItemSet(data, key, name) {
  return data.reduce((acc, item) => {
    if (!acc.some(i => i._key === item[key])) {
      acc.push({
        _key: item[key],
        name: item[name ?? key],
      });
    }
    return acc;
  }, []);
}

async function getTraceabilityData() {
  const resp = await api.get(`work-order/${props.wo_data._key}/traceability`);
  execution_data.value = resp.data.detail;

  phases.list = getItemSet(execution_data.value, 'phase_key', 'phase_alias');
  phases.options = phases.list;

  jobs.list = getItemSet(execution_data.value, 'job_key', 'job_key');
  jobs.options = jobs.list;

  operator_keys.value = getItemSet(execution_data.value, 'operator_key').map(o => o._key);

  fields.list = execution_data.value.reduce((acc, data) => {
    data.form_fields.forEach((field) => {
      if (!acc.some(f => f._key === field.form_field_key)) {
        acc.push({
          label: field.field_label,
          phase: data.phase_alias,
          _key: field.form_field_key,
          name: field.field_label + ' ' + data.phase_alias,
        })
      }
    });
    return acc;
  }, []);
  fields.options = fields.list;

  if (traceabilityEnabled) {
    serials.list = getItemSet(execution_data.value, 'serial_key', 'serial_code');
    serials.options = serials.list;
  }

  wo_field_data.value = execution_data.value.flatMap(
    (data) => data.form_fields.map((field) => ({
      ...field,
      operator_key: data.operator_key,
      operator_username: data.operator_username,
      timestamp: data.timestamp,
      phase_key: data.phase_key,
      phase_alias: data.phase_alias,
      job_key: data.job_key,
      step_key: data.step_key,
      step_title: data.step_title,
      batch_key: data.batch_key,
      batch_qt: data.batch_qt,
      serial_code: data.serial_code,
      serial_key: data.serial_key
    })
  ));
}

getTraceabilityData();

const wo_traceability_data = computed(() => {
  if (view.value === 'step') {
    return execution_data.value;
  }
  return wo_field_data.value;
});


function filterOptions(value, update, field) {
  if (value === '') {
    update(() => {
      field.options = field.list;
    });
  }

  update(() => {
    const needle = value.toLowerCase();
    field.options = field.list.filter((option) =>
      option.name.toLowerCase().includes(needle)
    );
  });
}

const filterPhase = (value, update) => filterOptions(value, update, phases);
const filterJob = (value, update) => filterOptions(value, update, jobs);
const filterField = (value, update) => filterOptions(value, update, fields);
const filterSerial = (value, update) => filterOptions(value, update, serials);




</script>
