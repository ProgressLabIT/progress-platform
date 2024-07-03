<template>
  <q-btn
    class="fit"
    :style="`background-color: ${color}`"
    square
    @click="startPauseResumeJob().action()"
  >
    <div class="row items-center absolute-full">
      <div class="col-1 offset-2">
        <q-icon size="lg" :name="j.active ? 'mdi-pause' : 'mdi-play'" />
      </div>
      <div class="display medium offset-1">
        {{ startPauseResumeJob().text }}
      </div>
    </div>
  </q-btn>
</template>

<script>
import { Dialog } from 'quasar';
import { mapState } from 'vuex';
import SerialBatchSelectionDialog from '../components/job/SerialBatchSelectionDialog.vue';
export default {
  name: 'StartPauseResumeBtn',

  computed: {
    j() {
      return this.$store.state.traceability.working_job_data;
    },

    color() {
      return this.j.active
        ? this.$theme.grey + 'aa'
        : (this.j.critical ? this.$theme.red : this.$theme.blue) + 'aa';
    },

    ...mapState({
      step_serials: (state) => state.traceability.current_step_serials,
    }),
  },

  methods: {
    startPauseResumeJob() {
      const result = {
        text: null,
        action: null,
      };

      if (this.j.active) {
        result.text = this.$t('job.pause').toUpperCase();
        result.action = () => this.$store.dispatch('pauseJob');
        return result;
      } else {
        // Check if progress has already been made or user has already started
        if (this.j.stage == 'started' || this.j.stage == 'serial_selected') {
          result.text = this.$t('job.resume').toUpperCase();
          result.action = () => this.$store.dispatch('resumeJob');
          return result;
        } else if (this.step_serials && this.step_serials.length > 0) {
          result.text = this.$t('job.link_serials');
          result.action = this.linkSerials;
          return result;
        } else {
          result.text = this.$t('job.start').toUpperCase();
          result.action = () =>
            this.$store.dispatch('startJob', { batch_serials: [] });
          return result;
        }
      }
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

    optionsToSerial(step_serials, options) {
      let serials = [];

      for (const serial of step_serials) {
        serials.push({
          serial_key: serial.serial_key,
          serial_code: serial.serial_code,
          active: options.includes(serial.serial_key),
        });
      }

      return serials;
    },

    serialsInitialSelection(serials) {
      let options = [];

      for (const serial of serials) {
        options.push(serial.serial_key);
      }

      return options;
    },

    async linkSerials() {
      let selected_serials = [];
      if (this.step_serials && this.step_serials.length > 0) {
        selected_serials = await this.selectSerialBatch(
          this.serialsToOptions(this.step_serials),
          this.serialsInitialSelection(this.step_serials),
        );
        if (selected_serials.length <= 0) {
          return;
        }

        this.$store.dispatch('startJob', {
          batch_serials: this.optionsToSerial(
            this.step_serials,
            selected_serials,
          ),
        });
        //await this.$store.dispatch('linkBatchSerial', {
        //  stepKey: this.current_step_key,
        //  batch_serials: selected_serials,
        //});
        //await this.$store.commit('UPDATE_step_serials', selected_serials);
      }
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
  },
};
</script>
