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
        <!-- FORM TITLE -->
        <q-card-section class="column">
          <div class="text-h2 display highlight">
            {{ component_code }}
          </div>
          <div class="text-body1">
            {{ bom_line.component_description }}
          </div>
        </q-card-section>

        <NoDataAlert v-if="!batch_serials">
          {{ $t('serial_field.noData') }}
        </NoDataAlert>

        <q-card-section v-else class="column q-gutter-y-md">
          <template v-for="serial in batch_serials" :key="serial._id">
            <div class="row q-mb-md">
              <div class="col">
                <BaseAutocompleteSerial
                  v-model="serialModel[serial._id]"
                  :initial_values="initialModel[serial._id]"
                  :label="
                    $capitalize(
                      [$t('serial'), serial?.code || serial._key].join(' '),
                    )
                  "
                  :hint="$t('serial_autocomplete_hint', { minChars: 3 })"
                  :product_key="component_key"
                  :loading="loading"
                  :can_create="true"
                  :selection_qt="component_per_product"
                  :filter_used="true"
                  :filtered_values="booked_serials"
                  :disable="disableSerialField(serial)"
                  @select="(selection) => onSerialSelection(selection, serial._id)"
                >
                </BaseAutocompleteSerial>
              </div>
              <div
                v-if="
                  !replace_serials[serial._id] &&
                  phase_key === bom_line?.phase_key
                "
                class="col-auto q-ml-md"
              >
                <q-btn
                  flat
                  round
                  icon="mdi-pencil"
                  :disable="phase_key !== bom_line?.phase_key"
                  @click="replace_serials[serial._id] = true"
                />
              </div>
            </div>
            <q-input
              class="q-mt-sm"
              v-if="replace_serials[serial._id]"
              v-model="replace_serials_reason[serial._id]"
              label="Ragione della modifica"
              filled
            />
            <q-separator class="q-my-md" />

          </template>
        </q-card-section>

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
    traceability_enabled: {
      type: Boolean,
      default: true,
    },
    bom_line: {
      type: Object,
      default: null,
    },
    batch_key: {
      type: String,
      default: null,
    },
    phase_key: {
      type: String,
      required: true,
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
      initialModel: [],
      initialValues: [],
      batch_serials: [],
      replace_serials: [],
      replace_serials_reason: [],
      loading: false,
      booked_serials: [],
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
    component_code() {
      return this.bom_line.component_code;
    },
    component_key() {
      return this.bom_line.component_key;
    },
    component_per_product() {
      if (this.traceability_enabled) {
        return this.bom_line.qt;
      } else {
        return this.bom_line?.batch_qt;
      }
    },
  },

  watch: {
    show: {
      handler() {
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

    async fakeBatchSerials() {
      this.loading = true;

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
      this.initialModel = [];
      this.initialValues = [];
      this.replace_serials = [];
      this.booked_serials = [];
      for (const serial of this.batch_serials) {
        if (!this.serialModel[serial._id]) {
          this.serialModel[serial._id] = [];
          this.initialModel[serial._id] = [];
          this.replace_serials[serial._id] = false;
          this.replace_serials_reason[serial._id] = null;
        }
        for (const child of serial.children) {
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
              this.initialModel[serial._id].push(serial_link);
            } else {
              this.serialModel[serial._id] = serial_link;
              this.initialModel[serial._id] = serial_link;
            }
            this.booked_serials.push(child.code);
            this.initialValues.push({
              parent_serial_key: serial._key,
              child_serial_key: child._key,
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

    disableSerialField(serial) {
      const full_quantity_recorded =
        this.component_per_product === 1
          ? this.serialModel[serial._id] && this.serialModel[serial._id]?._key
          : this.serialModel[serial._id]?.length >= this.component_per_product;
      const not_replaced = !this.replace_serials[serial._id];
      const different_phase = this.phase_key !== this.bom_line?.phase_key;
      return (full_quantity_recorded && not_replaced) || different_phase;
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
    },

    cancel() {
      this.initFormData();
      this.$emit('close');
    },

    ensureAndSave(link_data, serial_consumed, parent_serial, child_serial) {
      if (serial_consumed.find((str) => str === child_serial._key)) {
        return false;
      }
      serial_consumed.push(child_serial._key);
      link_data.push({
        parent_serial_key: parent_serial._key,
        child_serial_key: child_serial._key,
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
      for (const parent_serial of this.batch_serials) {
        if (this.serialModel[parent_serial._id]) {
          if (Array.isArray(this.serialModel[parent_serial._id])) {
            for (const child_serial of this.serialModel[parent_serial._id]) {
              if (
                !this.ensureAndSave(
                  link_data,
                  serial_consumed,
                  parent_serial,
                  child_serial,
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
                parent_serial,
                this.serialModel[parent_serial._id],
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
            el.parent_serial_key === inital_data.parent_serial_key &&
            el.child_serial_key === inital_data.child_serial_key,
        );
        if (!found) {
          let reason =
            this.replace_serials_reason['Serial/' + inital_data.parent_serial_key];
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
      };
      for (const link of link_data) {
        await this.$api.post('event', {
          ...event,
          ...link,
        });
      }
      this.saving = false;
      this.$emit('close');
    },
  },
};
</script>
