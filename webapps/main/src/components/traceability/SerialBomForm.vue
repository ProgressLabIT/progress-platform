<template>
  <BaseDialog :show="show">
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
              {{ serial_labels[index] }}
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
                serialModel[
                  [serial_ids[index], component.component_key].join(' ')
                ]
              "
              :initial_values="
                serialModel[
                  [serial_ids[index], component.component_key].join(' ')
                ]
              "
              :label="
                $capitalize(
                  [$t('serial'), component.component_description].join(' '),
                )
              "
              :product_key="component.component_key"
              :loading="loading"
              :can_create="true"
              :selection_qt="component_qt[component.component_key]"
              :filter_used="true"
              :filtered_values="booked_serials"
              :disable="
                serialModel[
                  [serial_ids[index], component.component_key].join(' ')
                ]?.length >= component_qt[component.component_key] &&
                !replace_serials[
                  [serial_ids[index], component.component_key].join(' ')
                ]
              "
              @select="
                (selection) =>
                  onSerialSelection(
                    selection,
                    [serial_ids[index], component.component_key].join(' '),
                  )
              "
            >
            </BaseAutocompleteSerial>
            <q-btn
              v-if="
                component.traceability_level !== null &&
                !replace_serials[
                  [serial_ids[index], component.component_key].join(' ')
                ]
              "
              flat
              round
              icon="mdi-pencil"
              @click="
                replace_serials[
                  [serial_ids[index], component.component_key].join(' ')
                ] = true
              "
            />
            <q-input
              v-if="
                replace_serials[
                  [serial_ids[index], component.component_key].join(' ')
                ]
              "
              v-model="
                replace_serials_reason[
                  [serial_ids[index], component.component_key].join(' ')
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
    batch_key: {
      type: String,
      required: true,
    },
    wo_key: {
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
      component_qt: [],
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
    session_data() {
      return this.$store.state.session;
    },
  },

  watch: {
    show: {
      handler() {
        this.index = 0;
        this.initFormData();
        if (this.show) {
          this.getBatchSerials();
        }
      },
    },
  },

  methods: {
    getComponentModel() {
      return [];
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

    async initFormData() {
      this.saving = false;
      this.enableSave = false;
    },

    fillInitialData() {
      this.serialModel = [];
      this.initialValues = [];
      this.serial_ids = [];
      this.component_qt = [];
      this.replace_serials = [];
      this.booked_serials = [];
      for (const component of this.bom_components) {
        this.component_qt[component.component_key] = component.component_qt;
      }
      for (const serial of this.batch_serials) {
        this.serial_ids.push(serial._id);
        this.serial_labels.push(serial?.code | serial._key);
        for (const component of this.bom_components) {
          const key = [serial._id, component.component_key].join(' ');
          if (!this.serialModel[key]) {
            this.serialModel[key] = [];
            this.replace_serials[key] = false;
            this.replace_serials_reason[key] = null;
          }
        }

        for (const child of serial.childs) {
          const key = [serial._id, child.product_key].join(' ');
          if (!this.serialModel[key]) {
            this.serialModel[key] = [];
            this.replace_serials[key] = false;
            this.replace_serials_reason[key] = null;
          }
          this.serialModel[key].push({
            _key: child._key,
            label: child.code,
            product_key: child.product_key,
            wo_key: child.wo_key,
            value: child._key,
          });
          this.initialValues.push({
            from_serial: serial._key,
            to_serial: child._key,
            wo_key: child.wo_key,
            reason: null,
            replaced: true,
            component_key: child.product_key,
            batch_key: this.batch_key,
          });
          this.booked_serials.push(child.code);
        }
      }
    },

    onSerialSelection(selectedSerials, selected_key) {
      let temp_booked_serials = [];

      for (const serial of selectedSerials) {
        temp_booked_serials.push(serial.label);
      }

      for (const serial_from of this.batch_serials) {
        for (const component of this.bom_components) {
          const key = [serial_from._id, component.component_key].join(' ');
          if (this.serialModel[key] && selected_key !== key) {
            for (const serial_to of this.serialModel[key]) {
              temp_booked_serials.push(serial_to.label);
            }
          }
        }
      }

      this.booked_serials = temp_booked_serials;
    },

    cancel() {
      this.initFormData();
      this.$emit('close');
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
            for (const serial_to of this.serialModel[key]) {
              if (serial_consumed.find((str) => str === serial_to._key)) {
                window.alert(this.$t('serial_field.component_reused'));
                this.saving = false;
                return;
              }
              serial_consumed.push(serial_to._key);
              link_data.push({
                wo_key: this.wo_key,
                component_key: component.component_key,
                batch_key: this.batch_key,
                from_serial: serial_from._key,
                to_serial: serial_to._key,
                reason: null,
                replaced: false,
              });
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
