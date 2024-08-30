<template>
  <div class="absolute-full column">
    <NoDataAlert v-if="!bom.length">
      {{ $t('bom.missing') }}
    </NoDataAlert>

    <template v-else>
      <q-table
        id="job-bom"
        ref="bom"
        class="my-sticky-header-table col"
        card-class="surface1 shadow-0"
        row-key="_key"
        virtual-scroll
        :loading="loading"
        :rows="bom"
        :columns="columns"
        :pagination="{ rowsPerPage: 0 }"
        :rows-per-page-options="[0]"
        :virtual-scroll-sticky-size-start="48"
        hide-bottom
      >
        <template #body-cell-description="props">
          <q-td style="text-wrap: wrap">
            {{ props.value }}
          </q-td>
        </template>
        <template #body-cell-serials="props">
          <q-td :props="props">
            <q-btn
              v-if="
                props.value !== null &&
                props.row.traceability_level !== null &&
                traceability_enabled
              "
              size="sm"
              color="theme-blue"
              :loading="loading"
              :disable="!job.active_batch_key"
              @click="show_serial_form = props.row"
            >
              {{ $t('edit') }}
            </q-btn>
          </q-td>
        </template>
      </q-table>

      <BomComponentSerialForm
        :show="!!show_serial_form"
        :bom_line="show_serial_form"
        :batch_key="job.active_batch_key"
        :wo_key="job.wo_key"
        mode="new"
        @close="
          () => {
            show_serial_form = false;
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
            {{ $capitalize($t('bom.quantity_type.radio_label')) }}
          </span>
          <q-radio
            v-for="qt_type in qt_types"
            :key="qt_type"
            v-model="quantity_type"
            :val="qt_type"
            :label="$t('bom.quantity_type.' + qt_type).toUpperCase()"
          >
          </q-radio>
          <q-space />
          <span class="q-mr-3">
            {{ $capitalize($t('bom.bom_type.radio_label')) }}
          </span>
          <q-radio
            v-for="b_type in bom_types"
            :key="b_type"
            v-model="bom_type"
            :val="b_type"
            :label="$t('bom.bom_type.' + b_type).toUpperCase()"
          >
          </q-radio>
        </div>
        <div v-if="traceability_enabled" class="col-auto">
          <q-btn
            size="md"
            padding="lg xl"
            color="theme-blue"
            :loading="loading"
            :disable="!job.active_batch_key"
            @click="show_all_serial_form = true"
          >
            {{ $t('serial_field.bom_component') }}
          </q-btn>
        </div>
      </div>

      <SerialBomForm
        :show="show_all_serial_form === true"
        :batch_key="job.active_batch_key"
        :wo_key="job.wo_key"
        mode="new"
        :bom_components="bom"
        @close="
          () => {
            show_all_serial_form = false;
            refreshBom();
          }
        "
      >
      </SerialBomForm>

      <!-- INSERT HEREoa DIALOG FOR COMPONENT LOT REGISTRATION -->
      <!-- <BaseModalForm :show="show_lot_input" @cancel="show_lot_input = false">
        <template v-slot:title>
          REGISTRAZIONE LOTTI MATERIALI
        </template>

        <template v-slot:form>
          <v-container>
            <v-row v-for="item in components" :key="item" align="center">
              <v-col cols="4">{{ item }}</v-col>
              <v-col cols="6" offset="2">
                <v-autocomplete :items="lots">
                </v-autocomplete>
              </v-col>
            </v-row>
          </v-container>
        </template>
      </BaseModalForm> -->
    </template>
  </div>
</template>

<script>
// import BaseModalForm from '@/components/BaseModalForm.vue'
import NoDataAlert from '@/components/NoDataAlert.vue';
import BomComponentSerialForm from 'app/src/components/traceability/BomComponentSerialForm.vue';
import SerialBomForm from 'app/src/components/traceability/SerialBomForm.vue';

export default {
  name: 'WorkSessionBom',

  components: {
    //  BaseModalForm,
    NoDataAlert,
    BomComponentSerialForm,
    SerialBomForm,
  },

  props: {
    job: {
      type: Object,
      required: true,
    },
  },

  data() {
    return {
      quantity_type: 'batch',
      qt_types: ['item', 'batch', 'job'],
      bom_type: 'job_bom',
      bom_types: ['job_bom', 'wo_bom'],
      show_lot_input: false,
      show_serial_form: false,
      show_all_serial_form: false,
      loading: false,
    };
  },

  computed: {
    columns() {
      // TODO: refactor into mixin / composition function, used also in ProductBoM
      return [
        {
          name: 'code',
          field: 'component_code',
          label: this.$t('code').toUpperCase(),
          align: 'left',
        },
        {
          name: 'description',
          field: 'component_description',
          label: this.$t('description').toUpperCase(),
          align: 'left',
        },
        {
          name: 'phase_name',
          field: 'phase_name',
          label: this.$t('phase.short', 1).toUpperCase(),
          align: 'left',
        },
        {
          name: 'qt',
          field: this.display_qt,
          label: this.$t('quantity.short').toUpperCase(),
        },
        {
          name: 'serials',
          field: 'serials',
          label: this.$t('serials').toUpperCase(),
        },
      ];
    },

    bom() {
      return Object.hasOwn(this.job, this.bom_type)
        ? this.job.wo_bom
            .filter((i) => {
              return this.bom_type === 'wo_bom'
                ? true
                : i.phase_key === this.job.phase_key;
            })
            .map((i) => {
              // line quantity is per item
              return {
                ...i,
                batch_qt: i.qt * this.job.active_batch_qt,
                job_qt: i.qt * this.job.qt_planned,
                component_qt: i.qt,
              };
            })
        : [];
    },

    display_qt() {
      return {
        item: 'qt',
        batch: 'batch_qt',
        job: 'job_qt',
      }[this.quantity_type];
    },

    traceability_enabled() {
      return !!this.$store.state.traceability.working_job_data
        .traceability_level;
    },
  },

  methods: {
    refreshBom() {
      this.loading = true;
      this.refreshWO();
    },

    async refreshWO() {
      await this.$store.dispatch('loadWorkingJobData', this.job._key);
      this.loading = false;
    },
  },
};
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
