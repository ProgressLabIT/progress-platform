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
import { Dialog, Loading } from 'quasar';
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
      j: (state) => state.traceability.working_job_data,
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
        if (
          this.j.traceability_level &&
          !this.j.first_phase &&
          !this.j.active_batch_key
        ) {
          result.text = this.$t('job.link_serials');
          result.action = this.selectSerialWipAndStartSession;
          return result;
        } else if (this.j.stage == 'started') {
          result.text = this.$t('job.resume').toUpperCase();
          result.action = () =>
            this.$store.dispatch('resumeJob', { batch_serials: null });
          return result;
        } else {
          result.text = this.$t('job.start').toUpperCase();
          result.action = () =>
            this.$store.dispatch('startJob', { batch_serials: [] });
          return result;
        }
      }
    },

    async selectSerialWipAndStartSession() {
      Loading.show();
      const params = {
        wo_key: this.j.wo_key,
        phase_key: this.j.phase_key,
      };
      const { data: available_serials } = await this.$api.get('wip-serial', {
        params,
      });
      Loading.hide();
      let selected_serials = await new Promise((resolve) => {
        Dialog.create({
          component: SerialBatchSelectionDialog,
          componentProps: {
            available_serials: available_serials.map((s) => ({
              label: s.serial_code,
              value: s.serial_key,
            })),
            selected_serials: [],
            max_quantity: this.j.qt_planned - this.j.qt_completed,
          },
        })
          .onOk((selected_serials) => resolve(selected_serials))
          .onCancel(() => resolve(false));
      });
      if (selected_serials) {
        const action = this.j.stage == 'created' ? 'startJob' : 'resumeJob';
        this.$store.dispatch(action, {
          batch_serials: selected_serials,
        });
      }
    },
  },
};
</script>
