<template>
  <BaseDialog :show="show">
    <q-card
      class="q-pa-md surface2 column"
      style="min-width: 600px; height: 80vh"
    >
      <q-card-section class="text-h3 col-auto">
        {{ $capitalize($t('work_order.qt_rebalance_title')) }}
      </q-card-section>

      <q-card-section class="scroll col">
        <div v-for="(phase, index) in effectivePhaseData" :key="phase.phase_key">
          <q-separator v-if="index !== 0" class="q-my-md" />

          <!-- PHASE HEADER -->
          <div class="row items-center justify-between">
            <div class="display highlight weight medium">
              {{ phase.phase_alias }}
            </div>
            <q-chip
              :color="
                phases_delta[phase.phase_key] ? 'theme-orange' : 'theme-green'
              "
            >
              <span
                v-if="phases_delta[phase.phase_key]"
                class="solid-white weight-medium text-uppercase"
              >
                {{
                  phases_delta[phase.phase_key] > 0
                    ? $t('increase') + ' +'
                    : $t('decrease')
                }}
                {{ phases_delta[phase.phase_key] }}
              </span>
              <q-icon v-else name="mdi-check" class="solid-white weight-bold" />
            </q-chip>
          </div>

          <!-- PHASE JOBS -->
          <div
            v-for="job_update in job_updates[phase.phase_key]"
            :key="job_update._key"
            class="row items-center q-py-sm"
          >
            <div class="col-3">
              {{ job_update._key }}
            </div>
            <div class="col-auto">
              <BaseUserAvatar
                v-if="job_update.assigned_to"
                :user="job_update.assigned_to"
              >
              </BaseUserAvatar>
            </div>
            <q-space />
            <template
              v-if="job_update._key !== 'NA' && job_update.new_remaining"
            >
              <div class="col-auto text-uppercase q-mr-md">
                {{ $t('quantity.remaining.short') }}
              </div>
              <q-input
                v-if="job_update.new_remaining"
                :key="index"
                v-model.number="job_update.new_remaining"
                class="col-2"
                dense
                input-class="text-right"
                hide-bottom-space
                type="number"
                min="0"
                :max="new_wo_qt"
              />
            </template>
            <q-chip
              v-else-if="job_update._key !== 'NA'"
              square
              class="text-uppercase highlight q-ml-lg"
              color="theme-grey"
              size="md"
              :removable="phase.qt_completed < new_wo_qt"
              :label="$t('closed')"
              @remove="job_update.new_remaining = 1"
            />
          </div>
        </div>
      </q-card-section>

      <q-card-actions align="between">
        <q-btn color="theme-grey" :label="$t('cancel')" @click="$emit('close')">
        </q-btn>
        <q-btn
          color="theme-orange"
          :label="$t('job.rebalance.spread')"
          @click="spreadRemaining"
        >
        </q-btn>
        <q-space />
        <q-btn
          v-if="can_save"
          color="theme-blue"
          :loading="saving"
          :label="$t('save')"
          @click="save"
        >
        </q-btn>
      </q-card-actions>
    </q-card>
  </BaseDialog>
</template>

<script>
import BaseDialog from '@/components/BaseDialog.vue';
import BaseUserAvatar from '@/components/BaseUserAvatar.vue';
import { computePhaseData } from '@/composables/productionAdminActions';

export default {
  name: 'WorkOrderJobQtRebalance',

  components: {
    BaseDialog,
    BaseUserAvatar,
  },

  props: {
    phase_data: {
      type: Array,
      required: false,
      default: () => [],
    },
    new_wo_qt: {
      type: Number,
      required: true,
    },
    wo_key: {
      type: String,
      required: true,
    },
    show: {
      type: Boolean,
      default: true,
    },
  },

  emits: ['close'],

  data() {
    return {
      job_updates: {}, // job_key => qt
      saving: false,
      effectivePhaseData: [],
    };
  },

  computed: {
    phases_delta() {
      const deltas = {};
      this.effectivePhaseData.forEach((phase) => {
        // Guard: job_updates might not be initialized yet during async created()
        if (!this.job_updates[phase.phase_key]) {
          deltas[phase.phase_key] = 0;
          return;
        }

        if (phase.qt_completed >= this.new_wo_qt) {
          deltas[phase.phase_key] = 0;
        } else {
          const phase_new_remaining =
            this.new_wo_qt - phase.qt_completed - phase.active_batch_qt;
          const current_remaining = this.job_updates[phase.phase_key].reduce(
            (sum, job) => sum + job.new_remaining,
            0,
          );
          deltas[phase.phase_key] = phase_new_remaining - current_remaining;
        }
      });
      return deltas;
    },

    can_save() {
      // Check if any delta is not zero
      return Object.values(this.phases_delta).every((delta) => delta === 0);
    },
  },

  async created() {
    await this.initPhaseData();
    this.buildJobUpdates();
  },

  methods: {
    async initPhaseData() {
      // Check if phase_data is incomplete or missing jobs
      const needsFetch = !this.phase_data ||
                         this.phase_data.length === 0 ||
                         this.phase_data.some(p => !Array.isArray(p.jobs) || p.jobs.length === 0);

      if (needsFetch) {
        // Fetch full work order data and store it in Vuex
        await this.$store.dispatch('loadWorkOrderData', this.wo_key);
        // Compute phase data from the store state
        this.effectivePhaseData = computePhaseData(this.$store.state.workorder.wo_data);
      } else {
        this.effectivePhaseData = this.phase_data;
      }
    },

    buildJobUpdates() {
      /*
      for each phase
        check remaining quantity
        if any
          get open jobs
        else (if increase)
          add new job
      */
      this.job_updates = this.effectivePhaseData.reduce((obj, phase) => {
        obj[phase.phase_key] = [];
        const delta = this.new_wo_qt - (phase.qt_completed + phase.qt_remaining);

        if (phase.qt_completed >= this.new_wo_qt) {
          phase.jobs.forEach((j) => {
            const update =
              j.stage != 'closed'
                ? { ...j, new_remaining: 0 }
                : { _key: 'NA', new_remaining: 0 };

            obj[phase.phase_key].push(update);
          });
        } else if (phase.qt_remaining) {
          const open_jobs = phase.jobs.filter((j) => j.stage != 'closed');
          open_jobs.forEach((j) => {
            obj[phase.phase_key].push({
              ...j,
              new_remaining: j.qt_planned - j.qt_completed - j.active_batch_qt,
            });
          });
        } else {
          const job_data =
            delta > 0
              ? {
                  _key: 'NEW',
                  phase_key: phase.phase_key,
                  qt_completed: 0,
                  active_batch_qt: 0,
                  new_remaining: delta,
                }
              : { _key: 'NA', new_remaining: 0 };

          obj[phase.phase_key].push(job_data);
        }

        return obj;
      }, {});
    },

    spreadRemaining() {
      Object.entries(this.job_updates).forEach(([phase_key, phase_jobs]) => {
        const delta = this.phases_delta[phase_key];
        let remainder = delta % phase_jobs.length;
        const base_job_variation = (delta - remainder) / phase_jobs.length;

        phase_jobs.forEach((j) => {
          const current_remaining = j.new_remaining;
          let new_remaining = current_remaining + base_job_variation;
          if (remainder) {
            new_remaining += Math.sign(delta); // handle both increase and decrease of quantity
            remainder -= Math.sign(remainder);
          }
          j.new_remaining = new_remaining;
        });
      });
    },

    async save() {
      if (!this.can_save) {
        window.alert(this.$t('work_order.alerts.assign_workload_first'));
        return;
      }

      this.saving = true;

      // Job update data is in an object divided by phase. First get a full, flat list
      const flat_list = Object.values(this.job_updates).flat();

      // Then build the data to be sent to the backend
      const job_updates = [];
      flat_list.forEach((data) => {
        if (data._key == 'NA') {
          return;
        }

        if (data._key == 'NEW') {
          job_updates.push({
            action: 'insert',
            data: {
              phase_key: data.phase_key,
              qt_planned: data.new_remaining,
            },
          });
        } else {
          // In case a new completed is greater or equal than the new planned the job will be closed
          job_updates.push({
            action: 'update',
            data: {
              _key: data._key,
              qt_planned:
                data.qt_completed + data.active_batch_qt + data.new_remaining,
            },
          });
        }
      });

      try {
        await this.$store.dispatch('updateWorkOrderQuantities', {
          wo_key: this.wo_key,
          new_quantity: this.new_wo_qt,
          job_updates,
        });
        await this.$store.dispatch('loadWorkOrderData', this.wo_key);
        this.saving = false;
        this.$q.notify({
          message: this.$capitalize(this.$t('quantity.update_success')),
          color: 'theme-green',
          timeout: 1500,
          position: 'top',
        });
        this.$emit('close');
      } catch (error) {
        console.error(error);
        // TODO: Add better error handling
        window.alert(error);
      }
    },
  },
};
</script>
