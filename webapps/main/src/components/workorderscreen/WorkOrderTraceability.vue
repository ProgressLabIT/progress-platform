<template>
  <div class="q-pa-md">
    <!-- FILTERS -->
    <div class="text-h5 text-uppercase low-text">
      {{  t('filter', 2) }}
    </div>

    <div class="row q-col-gutter-sm q-mt-sm">
       <!-- BY SERIAL -->
      <!-- <div class="col">
        <q-select
          v-if="wo_data.traceability_level"
          ref="serial_filter"
          v-model="serial_selected"
          filled
          dense
          use-input
          clearable
          :options="serial_list"
          option-label="name"
          option-value="_key"
          emit-value
          map-options
          :label="$capitalize(t('serial', 1))"
          class="q-mb-md"
          popup-content-class="surface1"
          @filter="serialSerial"
        >
        </q-select>
      </div> -->

      <!-- BY PHASE -->
      <div class="col">
        <q-select
          ref="phase_filter"
          v-model="phase_selected"
          filled
          dense
          use-input
          clearable
          :options="phase_list"
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
          v-model="job_selected"
          filled
          dense
          use-input
          clearable
          :options="job_list"
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
          :value="operator_selected"
          :user-keys="operator_keys"
          @select="(selection) => (operator_selected = selection)"
        >
        </BaseAutocompleteUser>
      </div>

      <!-- BY FIELD -->
      <div class="col">
        <q-select
          ref="field_filter"
          v-model="field_selected"
          filled
          dense
          use-input
          clearable
          :options="field_list"
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

    <div class="column col full-height">
      <!-- MAIN CONTENT -->
        <WorkOrderTraceabilityData
          v-if="wo_field_data"
          :wo_field_data="wo_field_data"
          :filters="filters"
        >
        </WorkOrderTraceabilityData>
        <NoDataAlert v-else />
      </div>

    </div>
</template>

<script setup>
import { ref, computed } from 'vue';
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
const phase_search_text = ref(undefined);
// const serial_search_text = ref(undefined);
const job_search_text = ref(undefined);
const field_search_text = ref(undefined);
const wo_field_data = ref([]);
const field_list = ref(undefined);
const phase_list = ref(undefined);
const serial_list = ref(undefined);
const job_list = ref(undefined);
const operator_keys = ref(undefined);

// Query models
const operator_selected = ref(undefined);
const phase_selected = ref(undefined);
// const serial_selected = ref(String, 'serial', undefined);
const job_selected = ref(undefined);
const field_selected = ref(undefined);

// Computed
const filters = computed(() => ({
  phase_alias: phase_selected.value,
  // serial: serial_selected.value,
  operator_key: operator_selected.value,
  job_selected: job_selected.value,
  field_selected: field_selected.value,
}));

const traceabilityEnabled = store.state.workorder.traceability_level

function getTraceabilityData() {
  api.get(`work-order/${props.wo_data._key}/traceability`).then((resp) => {
    let phases = new Map([]);
    let jobs = new Map([]);
    let fields = new Map([]);
    let serials = new Map([]);
    let operators = new Set();
    resp.data.detail.forEach((data) => {
      if (!phases.has(data.phase_key)) {
        phases.set(data.phase_key, {
          name: data.phase_alias,
          _key: data.phase_key,
        });
      }

      if (!jobs.has(data.job_key)) {
        jobs.set(data.job_key, {
          name: data.job_key,
          _key: data.job_key,
        });
      }

      if (!fields.has(data.form_field_key)) {
        fields.set(data.form_field_key, {
          label: data.field_label,
          phase: data.phase_alias,
          _key: data.custom_field_key,
        });
      }

      if (traceabilityEnabled && !serials.has(data.serial_key)) {
        serials.set(data.serial_key, {
          name: data.serial_code,
          _key: data.serial_key,
        });
      }

      if (!operators.has(data.operator_key)) {
        operators.add(data.operator_key);
      }

      wo_field_data.value.push(data)
    });

    phase_list.value = Array.from(phases.values());
    job_list.value = Array.from(jobs.values());
    field_list.value = Array.from(fields.values());
    operator_keys.value = Array.from(operators);
    if (traceabilityEnabled) {
      serial_list.value = Array.from(serials.values());
    }
  });
}

getTraceabilityData();


const filterPhase = async (val, update) => {
  update(() => {
    phase_search_text.value = val.toLowerCase();
  });
};

// const serialSerial = async (val, update) => {
//   update(() => {
//     serial_search_text.value = val.toLowerCase();
//   });
// };

const filterJob = async (val, update) => {
  update(() => {
    job_search_text.value = val.toLowerCase();
  });
};

const filterField = async (val, update) => {
  update(() => {
    field_search_text.value = val.toLowerCase();
  });
};

</script>
