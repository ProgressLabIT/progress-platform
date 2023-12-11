<template>
  <q-btn
    square
    :style="`background-color: ${progress_button_color}`"
    :disable="!progress_button_active"
    class="fit"
    v-touch-hold.mouse="progress_button.altAction"
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
import QuantityPickerDialog from './QuantityPickerDialog.vue';
import { api } from 'boot/axios';

export default {
  name: 'ProgressBtn',

  data() {
    return {
      clickTimer: null,
    };
  },

  computed: {
    ...mapState({
      j: (state) => state.traceability.working_job_data,
      batch_data: (state) => state.traceability.current_batch_data.step_data,
    }),

    progress_button_active() {
      return this.j.active && !this.current_step_done;
    },

    progress_button_color() {
      return this.progress_button_active
        ? (this.j.critical ? this.$theme.red : this.$theme.green) + 'aa'
        : this.$theme.surface2;
    },

    progress_button() {
      const complete_step = {
        icon: 'mdi-check',
        text: this.$t('job.complete_step'),
        action: this.completeStep,
        altAction: undefined,
      };

      const declare_batch = {
        icon: 'mdi-plus',
        text:
          this.j.parameters.production_batch_qt == 1
            ? this.$t('job.complete_piece')
            : this.$t('job.complete_batch'),
        action: this.declareBatch,
        altAction: this.declareCustomBatch,
      };

      if ('parameters' in this.j) {
        return this.j.parameters.step_check ? complete_step : declare_batch;
      } else return declare_batch;
    },

    current_step_done() {
      const current_step = this.batch_data
        ? this.batch_data[this.current_step_index]
        : null;
      return current_step ? current_step.done : null;
    },

    completed_steps_count() {
      return this.batch_data
        ? this.batch_data.reduce((total, current) => total + current.done, 0)
        : 0;
    },

    current_step_is_last() {
      return this.completed_steps_count === this.j.step_sequence.length - 1;
    },

    current_batch_is_last() {
      const remaining_qt = this.j.qt_planned - this.j.qt_completed;
      return this.j.active_batch_qt === remaining_qt;
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

    current_step_index: {
      get() {
        return this.$store.state.traceability.current_step_index ?? 0;
      },
      set(index) {
        this.$store.state.traceability.current_step_index = index;
      },
    },
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

    async completeStep() {
      let can_proceed = true;

      // Values will change after committing mutation save to use for navigation later on
      const current_step_was_last = this.current_step_is_last;
      const current_batch_was_last = this.current_batch_is_last;

      if (current_step_was_last) {
        can_proceed = window.confirm(this.confirm_batch_done_message);

        if (can_proceed && !this.j.next_batch_available) {
          if (current_batch_was_last) {
            can_proceed = window.confirm(this.confirm_job_done_message);
          } else {
            can_proceed = window.confirm(this.confirm_stop_session_message);
          }
        }
      }

      if (can_proceed) {
        await this.$store.dispatch('completeStep', {
          step_index: this.current_step_index,
          batch_qt: this.j.active_batch_qt,
        });

        if (current_step_was_last && current_batch_was_last) {
          this.$router.push({ name: 'userJobs' });
        } else if (current_step_was_last) {
          this.goToStep(0);
        } else if (this.j.parameters.step_check) {
          // Go to first step that is not done.
          // This works with both force_order mode active or not
          this.goToNextUndoneStep();
        }
      }
    },

    async declareBatch() {
      let can_proceed = true;
      const current_batch_was_last = this.current_batch_is_last;

      if (current_batch_was_last) {
        can_proceed = window.confirm(this.confirm_job_done_message);
      } else if (!this.j.next_batch_available) {
        can_proceed = window.confirm(this.confirm_stop_session_message);
      }

      if (can_proceed) {
        await this.$store.dispatch('declareBatch', {
          batch_qt: this.j.active_batch_qt,
        });
        if (
          current_batch_was_last ||
          (!this.j.next_batch_available && !this.j.active_batch_qt)
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
    async declareCustomBatch() {
      const remainingTotalQuantity = this.j.qt_planned - this.j.qt_completed;

      Loading.show();
      const { data } = await api.get('/wip', {
        params: { job_key: this.j._key },
      });
      Loading.hide();
      const maxDeclarableQuantity = this.j.first_phase
        ? remainingTotalQuantity
        : data.free_wip_qt_upstream + this.j.active_batch_qt;

      const batchQuantity = await this.getCustomBatchInput({
        initialValue: this.j.active_batch_qt,
        max: maxDeclarableQuantity,
      });
      if (batchQuantity === 0) {
        return;
      }

      let willStopSession = false;
      const isCompletingJob = batchQuantity === remainingTotalQuantity;
      if (isCompletingJob) {
        if (!window.confirm(this.confirm_job_done_message)) {
          return;
        }
        willStopSession = true;
      } else if (
        !this.j.next_batch_available ||
        batchQuantity === maxDeclarableQuantity
      ) {
        if (!window.confirm(this.confirm_stop_session_message)) {
          return;
        }
        willStopSession = true;
      }

      await this.$store.dispatch('declareBatch', {
        batch_qt: batchQuantity,
      });
      if (willStopSession) {
        this.$router.push({ name: 'userJobs' });
      }
    },

    goToStep(step_index) {
      this.current_step_index = step_index;
    },

    goToNextUndoneStep() {
      if (this.batch_data?.length) {
        const procedure_length = this.j.step_sequence.length;
        for (let i = this.current_step_index; i < procedure_length; i++) {
          if (!this.batch_data[i].done) {
            this.goToStep(i);
            return;
          }
        }
        const next_step_index = this.batch_data.findIndex((step) => !step.done);
        this.goToStep(next_step_index);
      }
    },
  },

  mounted() {
    this.goToNextUndoneStep();
  },
};
</script>

<style lang="css" scoped></style>
