<template>
  <div class="q-pa-md">
    <!-- FILTERS -->
    <div class="text-h5 text-uppercase low-text">
      {{  $t('filter', 2) }}
    </div>

    <div class="row q-col-gutter-sm q-mt-sm">
       <!-- BY SERIAL -->
      <div class="col">
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
          :label="$capitalize($t('serial', 1))"
          class="q-mb-md"
          popup-content-class="surface1"
          @filter="serialSerial"
        >
        </q-select>
      </div>

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
          :label="$capitalize($t('phase.phase', 1))"
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
          :label="$capitalize($t('job.label', 1))"
          class="q-mb-md"
          popup-content-class="surface1"
          @filter="filterJob"
        >
        </q-select>
      </div>

      <!-- BY OPERATOR -->
      <div class="col">
        <BaseAutocompleteUser
          :placeholder="$capitalize($t('operator'))"
          dense
          :show-avatar="false"
          class="q-mb-md"
          key-only
          :value="operator_selected"
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
          option-label="name"
          option-value="_key"
          emit-value
          map-options
          :label="$capitalize($t('field', 1))"
          class="q-mb-md"
          popup-content-class="surface1"
          @filter="filterField"
        >
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

<script>
import BaseAutocompleteUser from '@/components/BaseAutocompleteUser.vue';
import NoDataAlert from '@/components/NoDataAlert.vue';
import WorkOrderTraceabilityData from '@/components/workorderscreen/WorkOrderTraceabilityData.vue';
import multiMatch from '@/lib/MultiFieldSearch.js';
import queryModel from '@/lib/queryModelFactory.js';

const header_plus_footer_height = 80;

export default {
  name: 'WorkOrderTraceability',

  components: {
    BaseAutocompleteUser,
    NoDataAlert,
    WorkOrderTraceabilityData,
  },

  props: {
    wo_data: {
      type: Object,
      required: true,
    },
  },

  data() {
    return {
      phase_search_text: undefined,
      serial_search_text: undefined,
      job_search_text: undefined,
      field_search_text: undefined,
      operator_search_text: undefined,
      editing: false,
      saving: false,
      showFilterDrawer: false,
      wo_field_data: undefined,
      field_list: undefined,
      phase_list: undefined,
      serial_list: undefined,
      job_list: undefined,
    };
  },

  computed: {
    // Filters

    operator_selected: queryModel(String, 'operator', undefined),
    phase_selected: queryModel(String, 'phase_alias', undefined),
    serial_selected: queryModel(String, 'serial', undefined),
    job_selected: queryModel(String, 'job', undefined),
    field_selected: queryModel(String, 'field', undefined),

    _this() {
      return this;
    },

    filters() {
      return {
        phase_alias: this.phase_selected,
        serial: this.serial_selected,
        operator_key: this.operator_selected,
        job_selected: this.job_selected,
        field_selected: this.field_selected,
      };
    },

    filters_active() {
      return Object.entries(this.filters).filter(([, value]) => {
        return !!value;
      }).length;
    },

    operator_list() {
      return this.$store.getters.operator_list();
    },

    filtered_operators() {
      return this.operator_list.filter((o) =>
        multiMatch(this.operator_search_text, o, ['name', 'surname']),
      );
    },

    filtered_phases() {
      return this.phase_search_text
        ? this.phase_list.filter((d) =>
            d.name.toLowerCase().includes(this.phase_search_text),
          )
        : this.phase_list;
    },

    filtered_serial() {
      return this.serial_search_text
        ? this.serial_list.filter((d) =>
            d.name.toLowerCase().includes(this.serial_search_text),
          )
        : this.serial_list;
    },

    filtered_job() {
      return this.job_search_text
        ? this.job_list.filter((d) =>
            d.name.toLowerCase().includes(this.job_search_text),
          )
        : this.job_list;
    },

    filtered_field() {
      return this.field_search_text
        ? this.field_list.filter((d) =>
            d.name.toLowerCase().includes(this.field_search_text),
          )
        : this.field_list;
    },
  },

  created() {
    this.$api
      .get('wo-serials', {
        params: {
          work_order_key: this.wo_data._key,
        },
      })
      .then((resp) => {
        let wo_field_data = [];
        let phases = new Map([]);
        let serials = new Map([]);
        let jobs = new Map([]);
        let fields = new Map([]);
        if (resp.data) {
          for (const serial of resp.data) {
            for (const data of serial.data) {
              wo_field_data.push({
                serial_key: serial._key,
                serial_code: serial.code,
                created: this.formatSerialDateTime(serial?.created),
                created_by: serial.created_by,
                product_code: serial.product_code,
                product_key: serial.product_key,
                wo_code: serial.wo_code,
                custom_field_key: data.custom_field_key,
                field_label: data.custom_field_name,
                field_type: data.custom_field_type,
                custom_field_value: this.getFieldValue(data),
                batch_key: serial.batch_key,
                job_key: serial.job_key,
                phase_key: data.phase_key,
                phase_alias: data.phase_alias,
                phase_description: data.phase_description,
                step_key: data.step_key,
                step_title: data.step_title,
                step_description: data.step_description,
                user: `${serial.user_name} ${serial.user_surname}`,
              });

              if (!phases.has(data.phase_key)) {
                phases.set(data.phase_key, {
                  name: data.phase_alias,
                  _key: data.phase_key,
                });
              }

              if (!serials.has(serial._key)) {
                serials.set(serial._key, {
                  name: serial.code,
                  _key: serial._key,
                });
              }

              if (!jobs.has(data.job_key)) {
                jobs.set(data.job_key, {
                  name: serial.job_key,
                  _key: serial.job_key,
                });
              }

              if (!fields.has(data.custom_field_key)) {
                fields.set(data.custom_field_key, {
                  name: data.custom_field_name,
                  _key: data.custom_field_key,
                });
              }
            }
          }
        }

        this.wo_field_data = wo_field_data;
        this.phase_list = Array.from(phases.values());
        this.serial_list = Array.from(serials.values());
        this.job_list = Array.from(jobs.values());
        this.field_list = Array.from(fields.values());
      });
  },

  methods: {
    updateHeight() {
      this.content_height =
        document.documentElement.clientHeight - header_plus_footer_height;
    },

    setSearch(text) {
      this.search_string = text;
    },

    resetFilters() {
      this.$router.replace({ query: null });
    },

    formatSerialDateTime(datetime) {
      const config = {
        year: '2-digit',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      };
      return this.$capitalize(
        this.$formatDateTime(datetime, this.$i18n.locale, config),
      );
    },

    getFieldValue(data) {
      if (!data || !data.custom_field_type) {
        return '';
      }
      switch (data.custom_field_type) {
        case 'text':
        case 'number':
        case 'boolean':
        case 'ternary':
          return data.value;

        case 'choice':
          return data.value?.value;
        case 'date':
          return data.value;
        case 'time':
          return data.value;
        case 'files': {
          if (!data.value) {
            return '';
          }
          return Array.prototype.join.call(
            data.value?.map((file) => {
              return file.name;
            }),
            '.',
          );
        }

        default:
          break;
      }
      return data.value;
    },

    async filterPhase(val, update) {
      update(() => {
        this.phase_search_text = val.toLowerCase();
      });
    },

    async filterSerial(val, update) {
      update(() => {
        this.serial_search_text = val.toLowerCase();
      });
    },

    async filterJob(val, update) {
      update(() => {
        this.job_search_text = val.toLowerCase();
      });
    },

    async filterField(val, update) {
      update(() => {
        this.field_search_text = val.toLowerCase();
      });
    },

    async filterOperator(val, update) {
      update(() => {
        this.operator_search_text = val.toLowerCase();
      });
    },
  },
};
</script>
