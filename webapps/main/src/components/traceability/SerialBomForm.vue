<template>
  <BaseDialog
    :show="show"
    @close="
      {
        saving = false;
        $emit('close');
      }
    "
  >
    <q-card
      square
      class="surface1 q-pa-md"
      style="min-width: 600px; max-width: 800px"
    >
      <q-form ref="serial-form">
        <!-- FORM TITLE -->
        <q-card-section>
          <div class="row justify-between items-center">
            <div class="text-h2 display highlight text-center">
              {{ $t('serial') + ' #' + serial_labels[index] }}
            </div>
            <div
              v-if="!batch_serials[index]?.code ?? false"
              class="text-italic text-body2 q-ml-md text-low"
            >
              (TEMP ID)
            </div>
          </div>
        </q-card-section>

        <NoDataAlert v-if="!bom_components">
          {{ $t('serial_field.noData') }}
        </NoDataAlert>

        <template v-else>
          <template
            v-for="component in bom_components"
            :key="component.component_key"
          >
            <BaseAutocompleteSerial
              v-if="component.traceability_level !== null"
              v-model="
                serialModel[getComponentLineKey(component.component_key)]
              "
              :initial_values="
                initalModel[getComponentLineKey(component.component_key)]
              "
              :label="
                $capitalize([$t('serial'), component.component_code].join(' '))
              "
              :hint="$t('serial_autocomplete_hint', { minChars: 3 })"
              :loading="loading"
              :product_key="component.component_key"
              :can_create="true"
              :selection_qt="qt[component.component_key]"
              :filter_used="true"
              :filtered_values="booked_serials[component.component_key]"
              :disable="
                ((serialModel[getComponentLineKey(component.component_key)]
                  ?.length >= qt[component.component_key] ||
                  (qt[component.component_key] === 1 &&
                    serialModel[getComponentLineKey(component.component_key)]
                      ?._key)) &&
                  !replace_serials[
                    getComponentLineKey(component.component_key)
                  ]) ||
                phase_key !== component.phase_key
              "
              @select="
                (selection) =>
                  onSerialSelection(
                    selection,
                    component.component_key,
                    getComponentLineKey(component.component_key),
                  )
              "
            >
            </BaseAutocompleteSerial>
            <q-btn
              v-if="
                component.traceability_level !== null &&
                !replace_serials[getComponentLineKey(component.component_key)]
              "
              flat
              round
              icon="mdi-pencil"
              :disable="phase_key !== component.phase_key"
              @click="
                replace_serials[getComponentLineKey(component.component_key)] =
                  true
              "
            />
            <q-input
              v-if="
                replace_serials[getComponentLineKey(component.component_key)] &&
                phase_key === component.phase_key
              "
              v-model="
                replace_serials_reason[
                  getComponentLineKey(component.component_key)
                ]
              "
              filled
              dense
            />
            <!-- FORM BODY -->
          </template>
        </template>

        <!-- FORM ACTIONS    navigation -->
        <q-card-section>
          <div class="row q-gutter-md">
            <template v-if="batch_serials.length > 1">
              <q-btn
                v-if="index > 0"
                icon="mdi-arrow-left-bold"
                color="theme-blue"
                @click="index = index - 1"
              >
              </q-btn>
              <q-btn
                v-if="index < batch_serials.length - 1"
                icon="mdi-arrow-right-bold"
                color="theme-blue"
                @click="index = index + 1"
              >
              </q-btn>
            </template>
            <q-btn
              v-if="batch_serials"
              color="theme-orange"
              :label="$t('save')"
              :loading="saving"
              @click="
                () => {
                  save();
                }
              "
            >
            </q-btn>

            <q-space />

            <q-btn color="theme-grey" :label="$t('cancel')" @click="cancel">
            </q-btn>
          </div>
        </q-card-section>
      </q-form>
    </q-card>
  </BaseDialog>
</template>

<script>
import { mapState } from 'vuex';
import BaseAutocompleteSerial from '@/components/BaseAutocompleteSerial.vue';
import BaseDialog from '@/components/BaseDialog.vue';
import NoDataAlert from '@/components/NoDataAlert.vue';

import { timestamp } from '@/lib/TimeHandling.js';

export default {
  name: 'SerialBomForm',

  components: {
    BaseDialog,
    BaseAutocompleteSerial,
    NoDataAlert,
  },

  props: {
    show: {
      type: Boolean,
      default: true,
    },
    traceability_enabled: {
      type: Boolean,
      default: true,
    },
    batch_key: {
      type: String,
      required: true,
    },
    wo_key: {
      type: String,
      required: true,
    },
    phase_key: {
      type: String,
      required: true,
    },

    bom_components: {
      type: Object,
      default: null,
    },
  },

  emits: ['close'],

  data() {
    return {
      saving: false,
      enableSave: false,
      serialModel: [],
      initalModel: [],
      qt: [],
      initialValues: [],
      serial_ids: [],
      serial_labels: [],
      batch_serials: [],
      replace_serials: [],
      booked_serials: [],
      replace_serials_reason: [],
      loading: false,
      index: 0,
    };
  },

  computed: {
    ...mapState({
      faked_batch_serials: (state) =>
        state.traceability.current_batch_faked_serials,
    }),
    session_data() {
      return this.$store.state.session;
    },
  },

  watch: {
    show: {
      handler() {
        this.index = 0;
        this.initFormData();
        if (!this.show) {
          return;
        }
        if (this.traceability_enabled) {
          this.getBatchSerials();
        } else {
          this.fakeBatchSerials();
        }
      },
    },
  },

  methods: {
    getComponentLineKey(component_key) {
      return [this.serial_ids[this.index], component_key].join(' ');
    },

    async getBatchSerials() {
      this.loading = true;
      const { data: batch_serials } = await this.$api.get('serial-batch', {
        params: {
          batch_key: this.batch_key,
        },
      });

      this.batch_serials = batch_serials;
      this.fillInitialData();

      this.loading = false;
    },

    async fakeBatchSerials() {
      this.loading = true;

      /*this.batch_serials = [];
      for (var i = 0; i < this.batch_qty ? this.batch_qty : false; i++) {
        this.batch_serials.push({
          _id: `fake${{ i }}`,
          _key: `fake${{ i }}`,
          _code: `ITEM ${{ i }}`,
          childs: [],
        });
      }*/
      await this.$store.dispatch('fakeBatchSerials', {
        batch_key: this.batch_key,
      });

      this.batch_serials = this.faked_batch_serials;

      this.fillInitialData();

      this.loading = false;
    },

    async initFormData() {
      this.saving = false;
      this.enableSave = false;
    },

    fillInitialData() {
      this.serialModel = [];
      this.initalModel = [];
      this.initialValues = [];
      this.serial_ids = [];
      this.qt = [];
      this.replace_serials = [];
      this.booked_serials = [];
      for (const component of this.bom_components) {
        if (this.traceability_enabled) {
          this.qt[component.component_key] = component.qt;
        } else {
          this.qt[component.component_key] = component.batch_qt;
        }
      }
      for (const serial of this.batch_serials) {
        this.serial_ids.push(serial._id);
        this.serial_labels.push(serial?.code || serial._key);
        for (const component of this.bom_components) {
          const key = [serial._id, component.component_key].join(' ');
          if (!this.serialModel[key]) {
            this.serialModel[key] = [];
            this.initalModel[key] = [];
            this.replace_serials[key] = false;
            this.replace_serials_reason[key] = null;
          }
        }

        for (const child of serial.childs) {
          const key = [serial._id, child.product_key].join(' ');
          if (!this.serialModel[key]) {
            this.serialModel[key] = [];
            this.initalModel[key] = [];
            this.replace_serials[key] = false;
            this.replace_serials_reason[key] = null;
          }
          let serial_link = {
            _key: child._key,
            label: child.code,
            product_key: child.product_key,
            wo_key: child.wo_key,
            value: child._key,
          };
          if (this.qt[child.product_key] > 1) {
            this.serialModel[key].push(serial_link);
            this.initalModel[key].push(serial_link);
          } else {
            this.serialModel[key] = serial_link;
            this.initalModel[key] = serial_link;
          }

          this.initialValues.push({
            from_serial: serial._key,
            to_serial: child._key,
            wo_key: child.wo_key,
            reason: null,
            replaced: true,
            component_key: child.product_key,
            batch_key: this.batch_key,
          });
          if (!this.booked_serials[child.product_key]) {
            this.booked_serials[child.product_key] = [];
          }
          this.booked_serials[child.product_key].push(child.code);
        }
      }
    },

    onSerialSelection(selectedSerials, component_key, selected_key) {
      let temp_booked_serials = [];

      if (Array.isArray(selectedSerials)) {
        for (const serial of selectedSerials) {
          temp_booked_serials.push(serial.label);
        }
      } else if (selectedSerials) {
        temp_booked_serials.push(selectedSerials.label);
      }

      for (const serial_from of this.batch_serials) {
        for (const component of this.bom_components) {
          if (component?.component_key === component_key) {
            const key = [serial_from._id, component.component_key].join(' ');
            if (this.serialModel[key] && selected_key !== key) {
              if (Array.isArray(this.serialModel[key])) {
                for (const serial_to of this.serialModel[key]) {
                  temp_booked_serials.push(serial_to.label);
                }
              } else {
                temp_booked_serials.push(this.serialModel[key].label);
              }
            }
          }
        }
      }
      this.booked_serials[component_key] = temp_booked_serials;
    },

    cancel() {
      this.initFormData();
      this.$emit('close');
    },

    ensureAndSave(
      link_data,
      serial_consumed,
      component_key,
      serial_from,
      serial_to,
    ) {
      if (serial_consumed.find((str) => str === serial_to._key)) {
        return false;
      }
      serial_consumed.push(serial_to._key);
      link_data.push({
        wo_key: this.wo_key,
        component_key: component_key,
        batch_key: this.batch_key,
        from_serial: serial_from._key,
        to_serial: serial_to._key,
        reason: null,
        replaced: false,
      });
      return true;
    },

    async save() {
      this.saving = true;

      let link_data = [];
      let initial_values = this.initialValues;
      let serial_consumed = [];
      for (const serial_from of this.batch_serials) {
        for (const component of this.bom_components) {
          const key = [serial_from._id, component.component_key].join(' ');
          if (this.serialModel[key]) {
            if (Array.isArray(this.serialModel[key])) {
              for (const serial_to of this.serialModel[key]) {
                if (
                  !this.ensureAndSave(
                    link_data,
                    serial_consumed,
                    component.component_key,
                    serial_from,
                    serial_to,
                  )
                ) {
                  window.alert(this.$t('serial_field.component_reused'));
                  this.saving = false;
                  return;
                }
              }
            } else {
              if (
                !this.ensureAndSave(
                  link_data,
                  serial_consumed,
                  component.component_key,
                  serial_from,
                  this.serialModel[key],
                )
              ) {
                window.alert(this.$t('serial_field.component_reused'));
                this.saving = false;
                return;
              }
            }
          }
        }
      }

      for (const inital_data of initial_values) {
        const found = link_data.some(
          (el) =>
            el.from_serial === inital_data.from_serial &&
            el.to_serial === inital_data.to_serial,
        );
        if (!found) {
          const serial_key = [
            'Serial/' + inital_data.from_serial,
            inital_data.component_key,
          ].join(' ');
          let reason = this.replace_serials_reason[serial_key];
          if (!reason) {
            window.alert(this.$t('serial_field.missing_reason'));
            this.saving = false;
            return;
          }

          link_data.push({
            ...inital_data,
            reason: reason,
          });
        }
      }

      const event = {
        event_type: 'SERIAL_LINKED',
        user_key: this.session_data.session_key,
        timestamp: timestamp(),
        wo_key: this.wo_key,
        batch_key: this.batch_key,
        serial_link_data: link_data,
      };

      await this.$api.post('event', event);
      this.saving = false;
      this.$emit('close');
    },
  },
};
</script>
