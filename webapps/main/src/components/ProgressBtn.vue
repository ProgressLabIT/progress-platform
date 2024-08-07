<template>
  <q-btn
    v-touch-hold.mouse="progress_button.altAction"
    square
    :style="`background-color: ${progress_button_color}`"
    :disable="!progress_button_active"
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
</template>

<script>
import { Dialog, Loading } from 'quasar';
import { mapState } from 'vuex';
import { timestamp } from '@/lib/TimeHandling.js';
import { api } from 'boot/axios';
import SerialBatchDeclareSerialNumber from '@/components/job/SerialBatchDeclareSerialNumber.vue';
import SerialBatchSelectionDialog from '@/components/job/SerialBatchSelectionDialog.vue';
import QuantityPickerDialog from '@/components/QuantityPickerDialog.vue';

export default {
  name: 'ProgressBtn',

  data() {
    return {
      clickTimer: null,
    };
  },

  computed: {
    ...mapState({
      job: (state) => state.traceability.working_job_data,
      batch_data: (state) => state.traceability.current_batch_data.step_data,
    }),

    progress_button_active() {
      return this.job.active && !this.current_step_done;
    },

    progress_button_color() {
      return this.progress_button_active
        ? (this.job.critical ? this.$theme.red : this.$theme.green) + 'aa'
        : this.$theme.surface2;
    },

    progress_button() {
      const complete_step = {
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
        altAction: this.declareCustomBatch,
      };

      return ('parameters' in this.job && this.job.parameters.step_check)
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

    current_step_key: {
      get() {
        return this.$store.state.traceability.current_step_key;
      },
      set(key) {
        this.$store.dispatch('goToStep', key);
      },
    },
  },

  mounted() {
    this.goToNextUndoneStep();
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

    serialsToOptions(serials) {
      let options = [];

      for (const serial of serials) {
        options.push({
          value: serial.serial_key,
          label: serial.serial_code,
        });
      }

      return options;
    },

    serialsInitialSelection(serials) {
      let options = [];

      for (const serial of serials) {
        if (serial.active) {
          options.push(serial.serial_key);
        }
      }

      return options;
    },

    optionsToSerial(batch_serials, options) {
      let serials = [];

      for (const serial of batch_serials) {
        serials.push({
          serial_key: serial.serial_key,
          serial_code: serial.serial_code,
          active: options.includes(serial.serial_key),
        });
      }

      return serials;
    },

    async ensureBatchSerialCounter(batch_serials) {
      /*const { data: batch_serials } = await this.$api.get('serial-wo-job', {
        params: {
          batch_key: this.job.active_batch_key,
        },
      });*/

      let missing_counter = false;
      batch_serials.forEach((serial) => {
        let counter = serial.counter_key;
        let serialNo = serial.code;
        if (!counter && !serialNo) {
          missing_counter = true;
        }
      });

      if (missing_counter) {
        let updated_serials =
          await this.decleareSerialNoForBatch(batch_serials);
        let still_missing_counter = false;

        if (updated_serials.length <= 0) {
          return false;
        }

        const user = this.session_data.user._key;
        updated_serials.forEach((serial) => {
          this.postSerialUpdate(serial, user);
        });

        updated_serials.forEach((serial) => {
          let counter = serial.counter_key;
          let serialNo = serial.code;
          if (!counter && !serialNo) {
            still_missing_counter = true;
          }
        });

        return !still_missing_counter;
      } else {
        return true;
      }
    },

    async postSerialUpdate(serial, user) {
      serial.updated_by = `User/${user}`; // temporarily hardcoding DB id
      const event = {
        event_type: 'SERIAL_UPDATED',
        user_key: user,
        user_session_key: this.session_data.session_key,
        timestamp: timestamp(),
        serial_data: serial,
      };
      await this.$api.post('event', event);
    },

    async decleareSerialNoForBatch(batch_serials) {
      return new Promise((resolve) => {
        Dialog.create({
          component: SerialBatchDeclareSerialNumber,
          componentProps: {
            batch_serials,
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

    serialToBatch(batch_serials) {
      let serials = [];

      for (const serial of batch_serials) {
        serials.push({
          serial_key: serial._key,
          serial_code: serial.code,
          active: true,
        });
      }

      return serials;
    },

    async completeStep() {
      let missing_mandatory_fields = false;

      this.current_step_form_fields.forEach((field) => {
        let value = this.field_value(field._key);

        let type = this.$store.getters.getCustomFieldByKey(
          field.custom_field_key,
        )?.type;

        if (
          type !== 'ternary' &&
          field.mandatory &&
          (!value || value === null || value === '')
        ) {
          missing_mandatory_fields = true;
        }
      });

      if (missing_mandatory_fields) {
        window.alert(this.$t('fill_mandatory_fields'));
        return;
      }

      // Values will change after committing mutation save to use for navigation later on
      const current_step_was_last = this.current_step_is_last;
      const current_batch_was_last = this.current_batch_is_last;
      const { data: batch_serials } = await api.get('serial-wo-job', {
        params: {
          wo_key: this.job.wo_key,
          job_key: this.job._key,
        },
      });

      if (current_step_was_last) {
        if (!(await this.ensureBatchSerialCounter(batch_serials))) {
          window.alert(this.$t('declare_all_serials'));
          return;
        }
      }

      let can_proceed = true;

      if (current_step_was_last) {
        can_proceed = window.confirm(this.confirm_batch_done_message);

        if (can_proceed && !this.job.next_batch_available) {
          if (current_batch_was_last) {
            can_proceed = window.confirm(this.confirm_job_done_message);
          } else {
            can_proceed = window.confirm(this.confirm_stop_session_message);
          }
        }
      }

      if (can_proceed && !missing_mandatory_fields) {
        await this.$store.dispatch('completeStep', {
          stepKey: this.current_step_key,
        });

        if (current_step_was_last && current_batch_was_last) {
          this.$router.push({ name: 'userJobs' });
        } else if (current_step_was_last || this.job.parameters.step_check) {
          // Go to first step that is not done.
          // This works with both force_order mode active or not
          this.goToNextUndoneStep();
        }
      }
    },

    traceability_enabled() {
      return (
        this.$store.state.workorder?.wo_data?.traceability_level &&
        this.$store.state.workorder.wo_data.traceability_level !== 'none'
      );
    },

    async declareBatch() {
      let can_proceed = true;
      const current_batch_was_last = this.current_batch_is_last;

      let missing_serial = false;
      for (const job_bom of this.job.job_bom) {
        if (job_bom?.traceability_mandatory) {
          let declared = job_bom?.serials_declared_qt | 0;
          let required = (job_bom?.qt | 0) * this.job.active_batch_qt;
          missing_serial |= declared < required;
        }
      }

      if (missing_serial && this.traceability_enabled()) {
        window.alert(this.$t('batch_declare_component_serials'));
        return;
      }

      if (current_batch_was_last) {
        can_proceed = window.confirm(this.confirm_job_done_message);
      } else if (!this.job.next_batch_available) {
        can_proceed = window.confirm(this.confirm_stop_session_message);
      }

      if (can_proceed) {
        await this.$store.dispatch('declareBatch', {
          batch_qt: this.job.active_batch_qt,
        });
        if (
          current_batch_was_last ||
          (!this.job.next_batch_available && !this.job.active_batch_qt)
        ) {
          this.$router.push({ name: 'userJobs' });
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

    async selectSerialBatch(batch_serials, selected_serials) {
      return new Promise((resolve) => {
        Dialog.create({
          component: SerialBatchSelectionDialog,
          componentProps: {
            batch_serials,
            selected_serials,
          },
        })
          .onOk((selected_serials) => {
            resolve(selected_serials);
          })
          .onCancel(() => {
            resolve([]);
          });
      });
    },

    async getCustomQuantity() {
      const remainingTotalQuantity =
        this.job.qt_planned - this.job.qt_completed;

      Loading.show();
      const { data } = await api.get('/wip', {
        params: { job_key: this.job._key },
      });
      Loading.hide();
      const maxDeclarableQuantity = this.job.first_phase
        ? remainingTotalQuantity
        : Math.min(
            data.free_wip_qt_upstream + this.job.active_batch_qt,
            remainingTotalQuantity,
          );

      let batchQuantity = await this.getCustomBatchInput({
        initialValue: this.job.active_batch_qt,
        max: maxDeclarableQuantity,
      });

      return {
        batchQuantity: batchQuantity,
        remainingTotalQuantity: remainingTotalQuantity,
        maxDeclarableQuantity: maxDeclarableQuantity,
      };
    },

    async declareCustomBatch() {
      let customQty = await this.getCustomQuantity();

      if (customQty.batchQuantity === 0) {
        return;
      }

      let missing_serial = false;
      for (const job_bom of this.job.job_bom) {
        if (job_bom?.traceability_mandatory) {
          let declared = job_bom?.serials_declared_qt | 0;
          let required = (job_bom?.qt | 0) * customQty;
          missing_serial |= declared < required;
        }
      }

      if (missing_serial && this.traceability_enabled()) {
        // TODO: Make sure alert is only if traceability is mandatory
        window.alert(this.$t('batch_declare_component_serials'));
        return;
      }

      let willStopSession = false;
      const isCompletingJob =
        customQty.batchQuantity === customQty.remainingTotalQuantity;
      if (isCompletingJob) {
        if (!window.confirm(this.confirm_job_done_message)) {
          return;
        }
        willStopSession = true;
      } else if (
        !this.job.next_batch_available ||
        customQty.batchQuantity === customQty.maxDeclarableQuantity
      ) {
        if (!window.confirm(this.confirm_stop_session_message)) {
          return;
        }
        willStopSession = true;
      }

      await this.$store.dispatch('declareBatch', {
        batch_qt: customQty.batchQuantity,
      });
      if (willStopSession) {
        this.$router.push({ name: 'userJobs' });
      }
    },

    goToStep(step_key) {
      this.current_step_key = step_key;
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
          this.goToStep(step._key);
          return;
        }
      }

      const firstStep = this.job.step_sequence[0];
      if (firstStep) {
        this.goToStep(firstStep._key);
        return;
      }

      console.warn('No steps found, cannot go to any step');
      this.goToStep(undefined);
    },
  },
};
</script>
