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
              {{ component_code }}
            </div>
          </div>
        </q-card-section>

        <NoDataAlert v-if="!batch_serials">
          {{ $t('serial_field.noData') }}
        </NoDataAlert>

        <template v-else>
          <template v-for="serial in batch_serials" :key="serial._id">
            <!-- FORM BODY -->
            <BaseAutocompleteSerial
              v-model="serialModel[serial._id]"
              :initial_values="serialModel[serial._id]"
              :label="
                $capitalize(
                  [$t('serial'), serial?.code | serial._key].join(' '),
                )
              "
              :product_key="component_key"
              :loading="loading"
              :can_create="true"
              :selection_qt="component_per_product"
              :filter_used="true"
              :filtered_values="booked_serials"
              :disable="
                serialModel[serial._id]?.length >= component_per_product &&
                !replace_serials[serial._id]
              "
              @select="(selection) => onSerialSelection(selection, serial._id)"
            >
            </BaseAutocompleteSerial>
            <q-btn
              v-if="!replace_serials[serial._id]"
              flat
              round
              icon="mdi-pencil"
              @click="replace_serials[serial._id] = true"
            />
            <q-input
              v-if="replace_serials[serial._id]"
              v-model="replace_serials_reason[serial._id]"
              filled
              dense
            />
          </template>
        </template>

        <!-- FORM ACTIONS    navigation -->
        <q-card-section>
          <div class="row q-gutter-md">
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
  name: 'BomComponentSerialForm',

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
    bom_line: {
      type: Object,
      required: true,
    },
    batch_key: {
      type: String,
      default: null,
    },
    wo_key: {
      type: String,
      required: true,
    },
  },

  emits: ['close'],

  data() {
    return {
      saving: false,
      enableSave: false,
      serialModel: [],
      initialValues: [],
      batch_serials: [],
      replace_serials: [],
      replace_serials_reason: [],
      loading: false,
      booked_serials: [],
    };
  },

  computed: {
    session_data() {
      return this.$store.state.session;
    },
    component_code() {
      return this.bom_line.component_code;
    },
    component_key() {
      return this.bom_line.component_key;
    },
    component_per_product() {
      return this.bom_line.batch_qt;
    },
  },

  watch: {
    show: {
      handler() {
        this.initFormData();
        if (this.show) {
          this.getBatchSerials();
        }
      },
    },
  },

  methods: {
    async getBatchSerials() {
      if (!this.batch_key) {
        return;
      }
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
      this.replace_serials = [];
      this.booked_serials = [];
      for (const serial of this.batch_serials) {
        if (!this.serialModel[serial._id]) {
          this.serialModel[serial._id] = [];
          this.replace_serials[serial._id] = false;
          this.replace_serials_reason[serial._id] = null;
        }
        for (const child of serial.childs) {
          if (child.product_key === this.component_key) {
            let serial_link = {
              _key: child._key,
              label: child.code,
              product_key: child.product_key,
              wo_key: child.wo_key,
              value: child._key,
            };
            if (this.component_per_product > 1) {
              this.serialModel[serial._id].push(serial_link);
            } else {
              this.serialModel[serial._id] = serial_link;
            }
            this.booked_serials.push(child.code);
            this.initialValues.push({
              from_serial: serial._key,
              to_serial: child._key,
              wo_key: child.wo_key,
              component_key: child.product_key,
              batch_key: this.batch_key,
              replaced: true,
              reason: null,
            });
          }
        }
      }
    },

    onSerialSelection(selectedSerials, selected_key) {
      let temp_booked_serials = new Array();

      if (Array.isArray(selectedSerials)) {
        for (const serial of selectedSerials) {
          temp_booked_serials.push(serial.label);
        }
      } else if (selectedSerials) {
        temp_booked_serials.push(selectedSerials.label);
      }

      for (const serial of this.batch_serials) {
        if (this.serialModel[serial._id] && selected_key !== serial._id) {
          if (Array.isArray(this.serialModel[serial._id])) {
            for (const serial_to of this.serialModel[serial._id]) {
              temp_booked_serials.push(serial_to.label);
            }
          } else {
            temp_booked_serials.push(this.serialModel[serial._id].label);
          }
        }
      }

      this.booked_serials = temp_booked_serials;
      console.log(this.booked_serials);
    },

    cancel() {
      this.initFormData();
      this.$emit('close');
    },

    ensureAndSave(link_data, serial_consumed, serial_from, serial_to) {
      if (serial_consumed.find((str) => str === serial_to._key)) {
        return false;
      }
      serial_consumed.push(serial_to._key);
      link_data.push({
        from_serial: serial_from._key,
        to_serial: serial_to._key,
        wo_key: this.wo_key,
        component_key: this.component_key,
        batch_key: this.batch_key,
        replaced: false,
      });
      return true;
    },

    async save() {
      this.saving = true;

      let link_data = [];
      let serial_consumed = [];
      let initial_values = this.initialValues;
      for (const serial_from of this.batch_serials) {
        if (this.serialModel[serial_from._id]) {
          if (Array.isArray(this.serialModel[serial_from._id])) {
            for (const serial_to of this.serialModel[serial_from._id]) {
              if (
                !this.ensureAndSave(
                  link_data,
                  serial_consumed,
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
                serial_from,
                this.serialModel[serial_from._id],
              )
            ) {
              window.alert(this.$t('serial_field.component_reused'));
              this.saving = false;
              return;
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
          let reason =
            this.replace_serials_reason['Serial/' + inital_data.from_serial];
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
