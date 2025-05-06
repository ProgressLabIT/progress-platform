<template>
  <q-btn
    v-if="!edit_mode"
    v-touch-hold.mouse="progress_button.altAction"
    :disabled="!job.active"
    square
    :style="`background-color: ${progress_button_color}`"
    class="fit"
    @click="handleClick"
    @dblclick="handleDoubleClick"
  >
    <div class="row items-center absolute-full">
      <div class="col-1 offset-2">
        <q-icon size="lg" :name="progress_button.icon" />
      </div>
      <div class="col display medium offset-1 text-left q-pr-lg">
        <span>{{ progress_button.text }}</span>
      </div>
    </div>
  </q-btn>
  <template v-else>
    <div class="row col-4 full-height q-col-gutter-x-sm q-pr-none">
      <div class="col">
        <q-btn
          :style="`background-color: ${$theme.green}aa`"
          square
          height="auto"
          class="fit"
          @click="saveStepData"
        >
          <span>{{ $t('save') }}</span>
        </q-btn>
      </div>

      <div class="col">
        <q-btn
          :style="`background-color: ${$theme.grey}aa`"
          square
          height="auto"
          class="fit"
          @click="discardTempStepData"
        >
          <span>{{ $t('cancel') }}</span>
        </q-btn>
      </div>
    </div>
  </template>
</template>

<script>
import { Dialog } from 'quasar';
import { mapState } from 'vuex';

import QuantityPickerDialog from '@/components/QuantityPickerDialog.vue';
import SerialBatchDeclareSerialNumber from '@/components/job/SerialBatchDeclareSerialNumber.vue';
import SerialBatchSelectionDialog from '@/components/job/SerialBatchSelectionDialog.vue';
import eventMixin from '@/mixins/event.js';

export default {
  name: 'ProgressBtn',

  mixins: [eventMixin],

  data() {
    return {
      clickTimer: null,
      bom_destination: { name: 'jobBom' },
      step_destination: { name: 'jobSteps' },
    };
  },

  computed: {
    ...mapState({
      job: (state) => state.traceability.working_job_data,
      batch_data: (state) => state.traceability.current_batch_data?.step_data,
      current_batch_serials: (state) =>
        state.traceability.current_batch_serials,
    }),

    progress_button_color() {
      let color = undefined;
      if (!this.job.active) {
        color = this.$theme.surface2;
      } else if (this.job.critical) {
        color = this.$theme.red;
      } else if (this.current_step_done) {
        color = this.$theme.blue;
      } else {
        color = this.$theme.green;
      }

      return color + 'aa';
    },

    progress_button() {
      const complete_step = this.current_step_done
        ? {
            icon: 'mdi-pencil',
            text: this.$t('edit'),
            action: this.toggleStepEditMode,
            altAction: this.toggleStepEditMode,
          }
        : {
            icon: 'mdi-check',
            text: this.$t('job.complete_step'),
            action: this.completeStep,
            altAction: this.completeStep,
          };

      const declare_batch = {
        icon: 'mdi-plus',
        text:
          this.job.parameters.production_batch_qt == 1
            ? this.$t('job.complete_piece')
            : this.$t('job.complete_batch'),
        action: this.declareBatch,
        altAction: this.declareBatch,
      };

      return 'parameters' in this.job && this.job.parameters.step_check
        ? complete_step
        : declare_batch;
    },

    current_step_done() {
      const currentStep = this.batch_data?.find(
        ({ _key }) => _key === this.current_step_key,
      );

      return currentStep?.done ?? false;
    },

    current_step_form_fields() {
      const currentStep = this.job.step_sequence?.find(
        ({ _key }) => _key === this.current_step_key,
      );

      return currentStep?.form_fields ?? [];
    },

    current_batch_form_fields() {
      let form_fields = [];
      for (const step of this.job.step_sequence) {
        for (const field of step.form_fields) {
          form_fields.push({ ...field, step_key: step._key });
        }
      }

      return form_fields;
    },

    completed_steps_count() {
      return this.batch_data
        ? this.batch_data.reduce((total, current) => total + current.done, 0)
        : 0;
    },

    current_step_is_last() {
      return this.completed_steps_count === this.job.step_sequence.length - 1;
    },

    current_step_data() {
      const currentStep = this.batch_data?.find(
        ({ _key }) => _key === this.current_step_key,
      );

      return currentStep?.form_data ?? [];
    },

    current_batch_is_last() {
      const remaining_qt = this.job.qt_planned - this.job.qt_completed;
      return this.job.active_batch_qt === remaining_qt;
    },

    active_batch_key() {
      return this.job.active_batch_key;
    },

    product_key() {
      return this.job.product_key;
    },

    confirm_batch_done_message() {
      return this.$t('job.alerts.batch_confirm');
    },

    confirm_job_done_message() {
      return this.$t('job.alerts.job_complete_confirm');
    },

    confirm_stop_session_message() {
      return this.$t('job.alerts.next_batch_not_available');
    },

    session_data() {
      return this.$store.state.session;
    },

    traceability_enabled() {
      return this.$store.state.traceability.working_job_data
        ?.traceability_level;
    },

    edit_mode() {
      return this.$store.getters.isCurrentStepEditMode();
    },

    current_step_key: {
      get() {
        return this.$store.state.traceability.current_step_key;
      },
      set(key) {
        this.$store.dispatch('goToStep', key);
      },
    },
  },

  watch: {
    'job.active': {
      handler() {
        if (this.job.active === false && this.edit_mode === true) {
          this.discardTempStepData();
        }
      },
    },
  },

  mounted() {
    this.goToNextUndoneStep();
    this.$store.dispatch('setStepEditMode', false);
  },

  methods: {
    // The single click handler gets triggered on double click as well, so we use a trick to differentiate them
    handleClick({ detail: clickCount }) {
      if (clickCount !== 1 || this.clickTimer !== null) {
        return;
      }

      this.clickTimer = setTimeout(async () => {
        await this.progress_button.action();
        this.resetClickTimer();
      }, 300);
    },
    handleDoubleClick() {
      this.resetClickTimer();
      this.progress_button.altAction?.();
    },
    resetClickTimer() {
      if (this.clickTimer) {
        clearTimeout(this.clickTimer);
      }
      this.clickTimer = null;
    },

    field_value(field_key) {
      const data = this.current_step_data?.find(
        ({ form_field_key }) => form_field_key === field_key,
      );

      return data?.value ?? null;
    },

    batch_field_value(field_key) {
      for (const step_data of this.batch_data) {
        const data = step_data.form_data?.find(
          ({ form_field_key }) => form_field_key === field_key,
        );
        if (data) {
          return data?.value;
        }
      }

      return null;
    },

    async ensureBatchSerialCounter() {
      let missing_counter = false;

      await this.$store.dispatch('reloadBatchSerials', {
        active_batch_key: this.active_batch_key,
      });

      this.current_batch_serials.forEach((serial) => {
        let counter = serial.counter_key;
        let serialNo = serial.serial_code;
        if (!counter && !serialNo) {
          missing_counter = true;
        }
      });

      if (missing_counter) {
        let updated_serials = await this.decleareSerialNoForBatch();
        let still_missing_counter = false;

        if (updated_serials.length <= 0) {
          return false;
        }

        let promises = [];
        updated_serials.forEach(async (serial) => {
          promises.push(
            this.postSerialUpdate(serial),
          );
        });

        await Promise.all(promises);

        await this.$store.dispatch('reloadBatchSerials', {
          active_batch_key: this.active_batch_key,
        });

        this.current_batch_serials.forEach((serial) => {
          let counter = serial.counter_key;
          let serialNo = serial.serial_code;
          if (!counter && !serialNo) {
            still_missing_counter = true;
          }
        });

        return !still_missing_counter;
      } else {
        return true;
      }
    },

    async postSerialUpdate(serial) {
      await this.sendEvent({
        event_type: 'SERIAL_UPDATED',
        event_data: serial
      });
    },

    async decleareSerialNoForBatch() {
      return new Promise((resolve) => {
        Dialog.create({
          component: SerialBatchDeclareSerialNumber,
          componentProps: {
            batch_serials: this.current_batch_serials,
            product_key: this.product_key,
          },
        })
          .onOk((updated_serials) => {
            resolve(updated_serials);
          })
          .onCancel(() => {
            resolve([]);
          });
      });
    },

    checkMissingSerials() {
      const has_bom = !!this.job?.wo_bom?.length;

      const all_serials_filled_in = this.job.wo_bom.every((bom_line) => {
        const traceability_required = !!bom_line.traceability_level;

        const same_phase = bom_line?.phase_key == this.job?.phase_key;

        const serials_declared = bom_line.declared_serials?.length;
        const serials_required = (bom_line?.qt ?? 0) * this.job.active_batch_qt;

        const bom_line_pass =
          !traceability_required ||
          serials_declared === serials_required ||
          !same_phase;
        return bom_line_pass;
      });

      return has_bom && !all_serials_filled_in;
    },

    ensureMandatoryFields() {
      const all_mandatory_fields_filled = this.current_step_form_fields.every(
        (field) => {
          const value = this.field_value(field._key);
          const type = this.$store.getters.getCustomFieldByKey(
            field.custom_field_key,
          )?.type;
          const field_filled_in =
            type === 'ternary'
              ? // ternary field can be true or false, but must be filled in
                [true, false].includes(value)
              : // All other values must not be false, null/undefined or empty string.
                ![null, undefined, '', [], false].includes(value);
          return !field.mandatory || field_filled_in;
        },
      );
      return all_mandatory_fields_filled;
    },

    async completeStep() {
      // Check all fields are either not mandatory or if it is, the value is existing

      if (!this.ensureMandatoryFields()) {
        window.alert(this.$t('fill_mandatory_fields'));
        this.$router.push(this.step_destination);
        return;
      }

      // Values will change after committing mutation save to use for navigation later on
      const current_step_was_last = this.current_step_is_last;
      const current_batch_was_last = this.current_batch_is_last;

      if (current_step_was_last) {
        const missing_serials = this.checkMissingSerials();
        if (missing_serials) {
          window.alert(this.$t('batch_declare_component_serials'));
          this.$router.push(this.bom_destination);
          return;
        }
      }

      let can_proceed = true;

      if (current_step_was_last) {
        can_proceed = window.confirm(this.confirm_batch_done_message);
        if (can_proceed && current_batch_was_last) {
          can_proceed = window.confirm(this.confirm_job_done_message);
        } else if (can_proceed && !this.job.next_batch_available) {
          can_proceed = window.confirm(this.confirm_stop_session_message);
        }
        if (can_proceed) {
          const serialCodeOk = await this.ensureBatchSerialCounter();
          if (
            this.traceability_enabled &&
            !serialCodeOk
          ) {
            window.alert(this.$t('declare_all_serials'));
            return;
          }
        }
      }

      // Missing mandatory fields has already been ensured
      if (can_proceed) {
        try {
          await this.$store.dispatch('completeStep', {
            stepKey: this.current_step_key,
          });

          if (current_step_was_last) {
            if (current_batch_was_last || !this.job.next_batch_available) {
              this.$router.push({ name: 'userJobs' });
              return;
            } else {
              if (this.traceability_enabled && !this.job.first_phase) {
                // Select new serials and start new batch
                const selected_serials = await this.selectSerialBatch();
                await this.$store.dispatch('resumeJob', {
                  batch_serials: selected_serials,
                });
              }
            }
          }
          // Go to first step that is not done.
          // This works with both force_order mode active or not
          this.goToNextUndoneStep();
        } catch (error) {
          console.error('Error completing step:', error);
          return
        }
      }
    },

    async declareBatch() {
      let can_proceed = true;
      const current_batch_was_last = this.current_batch_is_last;

      let mandatory_step_missed = undefined;

      if (!this.job.parameters.step_check) {
        const all_mandatory_fields_filled =
          this.current_batch_form_fields.every((field) => {
            const value = this.batch_field_value(field._key);
            const type = this.$store.getters.getCustomFieldByKey(
              field.custom_field_key,
            )?.type;
            const field_not_mandatory = !field.mandatory;
            const field_filled_in =
              type === 'ternary'
                ? // ternary field can be true or false, but must be filled in
                  [true, false].includes(value)
                : // All other values must not be false, null/undefined or empty string.
                  !!value;
            let field_ok = field_not_mandatory || field_filled_in;
            if (!field_ok) {
              mandatory_step_missed = field.step_key;
            }
            return field_ok;
          });

        if (!all_mandatory_fields_filled) {
          window.alert(this.$t('fill_mandatory_fields'));
          if (mandatory_step_missed) {
            this.$router.push(this.step_destination);
            this.goToMissingMandatoryFieldStep(mandatory_step_missed);
          }
          return;
        }
      }

      if (this.checkMissingSerials()) {
        window.alert(this.$t('batch_declare_component_serials'));
        this.$router.push(this.bom_destination);
        return;
      }

      if (
        this.traceability_enabled &&
        !(await this.ensureBatchSerialCounter())
      ) {
        window.alert(this.$t('declare_all_serials'));
        return;
      }

      if (current_batch_was_last) {
        can_proceed = window.confirm(this.confirm_job_done_message);
      } else if (!this.job.next_batch_available) {
        can_proceed = window.confirm(this.confirm_stop_session_message);
      }

      if (can_proceed) {
        try {
          await this.$store.dispatch('declareBatch', {
            batch_qt: this.job.active_batch_qt,
            send_step_data: !this.job.parameters.step_check,
          });

          if (this.traceability_enabled && !this.job.first_phase) {
            // Select new serials and start new batch
            const selected_serials = await this.selectSerialBatch();
            await this.$store.dispatch('resumeJob', {
              batch_serials: selected_serials,
            });
          }

          if (current_batch_was_last ||
            (!this.job.next_batch_available && !this.job.active_batch_qt)
            ) {
            this.$router.push({ name: 'userJobs' });
          }
        } catch (error) {
          console.error('Error declaring batch:', error);
        }
      }
    },

    async getCustomBatchInput({ initialValue, max }) {
      return new Promise((resolve) => {
        Dialog.create({
          component: QuantityPickerDialog,
          componentProps: {
            initialValue,
            max,
          },
        })
          .onOk((quantity) => {
            resolve(quantity);
          })
          .onCancel(() => {
            resolve(0);
          });
      });
    },

    async selectSerialBatch() {
      const remainingTotalQuantity =
        this.job.qt_planned - this.job.qt_completed;

      const { data: available_serials } = await this.$api.get('/wip-serial', {
        params: {
          phase_key: this.job.phase_key,
          wo_key: this.job.wo_key,
        },
      });

      return await new Promise((resolve) => {
        Dialog.create({
          component: SerialBatchSelectionDialog,
          componentProps: {
            available_serials: available_serials.map((s) => ({
              label: s.serial_code,
              value: s.serial_key,
            })),
            selected_serials: [],
            max_quantity: remainingTotalQuantity,
          },
        })
          .onOk((selected_serials) => resolve(selected_serials))
          .onCancel(() => resolve(false));
      });
    },
    /**
     * Go to the first step that is not done or that does not have a data entry.
     */
    goToNextUndoneStep() {
      for (const step of this.job.step_sequence) {
        const batchStep = this.batch_data?.find(
          ({ _key }) => _key === step._key,
        );

        // If the step is not done or doesn't have a data entry, go to it
        if (!batchStep?.done) {
          this.$store.dispatch('goToStep', step._key);
          return;
        }
      }

      const firstStep = this.job.step_sequence[0];
      if (firstStep) {
        this.$store.dispatch('goToStep', firstStep._key);
        return;
      }

      console.warn('No steps found, cannot go to any step');
      this.$store.dispatch('goToStep', undefined);
    },

    goToMissingMandatoryFieldStep(step_key) {
      this.$store.dispatch('goToStep', step_key);
      return;
    },

    async saveStepData() {
      if (!this.ensureMandatoryFields()) {
        window.alert(this.$t('fill_mandatory_fields'));
        return;
      }
      await this.$store.dispatch('editStepData', {
        stepKey: this.current_step_key,
      });
      this.toggleStepEditMode(false);
    },

    async discardTempStepData() {
      if (
        window.confirm(
          'This will discard unsaved data and reload the original step. Do you want to continue?',
        )
      ) {
        await this.$store.dispatch('reloadBatchData');
        this.toggleStepEditMode(false);
      }
    },

    toggleStepEditMode(editMode) {
      if (editMode == undefined) {
        editMode = !this.edit_mode;
      }
      this.$store.dispatch('setStepEditMode', editMode);
    },
  },
};
</script>
