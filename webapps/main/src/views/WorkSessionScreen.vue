<template>
  <q-page-container>
    <q-page class="q-px-md q-pb-md column full-height">
      <q-circular-progress
        v-if="!vuex_ready"
        indeterminate
        color="theme-blue"
        class="q-mt-lg"
      >
      </q-circular-progress>

      <!-- JOB CLOSED NOTIFICATION -->
      <div
        v-else-if="job_closed || !has_material_to_proceed"
        class="row flex-center"
        style="height: 80vh"
      >
        <div class="col-6 text-center">
          <div v-if="job_closed" class="text-h3">
            {{ $t('job.alerts.job_closed') }}
          </div>
          <div v-else-if="!has_material_to_proceed" class="text-h3">
            {{ $t('job.alerts.input_not_available') }}
          </div>
          <q-circular-progress
            indeterminate
            color="theme-blue"
            class="q-mt-lg"
          />
        </div>
      </div>

      <div
        v-else-if="vuex_ready & !job_closed"
        class="row absolute-full q-pb-md q-px-xs"
      >
        <!-- ################################ -->
        <!--          JOB DETAILS             -->
        <!-- ################################ -->

        <div
          v-show="$q.screen.width > 800"
          id="job-info-section"
          class="column q-px-sm full-height col-8"
        >
          <!-- PANEL NAVIGATION -->
          <q-tabs
            class="transparent text-low"
            content-class="drag-container"
            active-class="text-high weight-bold"
            align="left"
            indicator-color="transparent"
          >
            <q-route-tab
              v-for="link in sorted_links"
              :key="link.route_name"
              :to="{ name: link.route_name }"
              :class="{ 'q-px-sm': link.item_count }"
            >
              <div class="row items-center justify-start display">
                <div
                  v-if="$q.screen.width > 1220"
                  :class="{ smaller: $q.screen.md }"
                >
                  {{ link.text }}
                </div>
                <q-icon v-else size="xs" :name="link.icon" class="q-mr-xs" />

                <template v-if="link.item_count">
                  <q-chip
                    v-if="['jobBom', 'jobIssues'].includes(link.route_name)"
                    size="9px"
                    :color="getItemCountColor(link)"
                    class="q-ml-xs weight-bold text-body2"
                  >
                    {{ link.item_count }}
                  </q-chip>
                  <q-avatar
                    v-else
                    size="xs"
                    :color="getItemCountColor(link)"
                    class="q-ml-xs weight-bold text-body2"
                  >
                    {{ link.item_count }}
                  </q-avatar>
                </template>
              </div>
            </q-route-tab>
          </q-tabs>

          <!-- PANEL CONTENT -->
          <q-card class="surface1 col" square>
            <router-view :job="j" />
          </q-card>
        </div>

        <!-- ################################ -->
        <!-- RIGHT COLUMN: JOB DATA & ACTIONS -->
        <!-- ################################ -->

        <div
          v-if="$route.name !== 'jobIssueDetail'"
          id="session-control-section"
          class="column col q-px-sm q-pt-xs"
          style="min-height: 600px"
        >
          <!-- JOB DATA -->
          <div id="job-data" class="col-auto">
            <!-- PRODUCT CODE & DESCRIPTION -->

            <div
              class="text-h2 display highlight row text-uppercase items-center"
              style="word-wrap: n"
            >
              <div class="nowrap q-mr-md">{{ j.phase_alias }}</div>
              <div class="nowrap q-mr-sm">{{ j.product_code }}</div>
              <q-btn class="" icon="mdi-information-outline" flat round />
            </div>
            <p class="q-mt-sm">
              {{ j.product_description }}
            </p>

            <!-- WORK ORDER DATA -->
            <template v-for="field in job_info">
              <div
                v-if="j[field.name] !== undefined"
                :key="field.name"
                class="row items-center q-py-xs"
              >
                <div class="col-5 text-h5 text-uppercase font-weight-medium">
                  {{ field.text }}
                </div>
                <div class="col-7 row q-gutter-md items-center justify-between">
                  <div>{{ $capitalizeAll(j[field.name]) }}</div>
                  <q-btn
                    v-if="field.name === 'active_batch_qt' && j.active"
                    icon-right="mdi-pencil"
                    color="theme-blue"
                    size="xs"
                    :label="$t('update')"
                    @click="editBatchQuantityOrSerials"
                  />
                </div>
              </div>
            </template>

            <!-- JOB PROGRESS / STATUS -->
            <template v-if="phase_progress">
              <PhaseProgressBar
                size="8px"
                :data="phase_progress"
                class="q-mt-lg q-mb-xs"
              >
              </PhaseProgressBar>
              <div class="row justify-between items-center q-pt-xs">
                <div class="text-h5 weight-bold text-uppercase">
                  {{ $t('processing_time') }}
                </div>
                <div>
                  {{ $durationFromMillisec(phase_progress.consumer_millis) }} /
                  {{ $durationFromMillisec(phase_progress.total * 1000) }}
                </div>
              </div>
            </template>

            <BaseProgressBar size="8px" :data="j" class="q-mt-lg q-mb-xs">
            </BaseProgressBar>

            <div class="row justify-between items-center q-pt-xs">
              <div class="text-h5 weight-bold text-uppercase">
                {{ $t('progress') }}
              </div>
              <div>{{ j.qt_completed }} / {{ j.qt_planned }}</div>
            </div>
          </div>

          <!-- ************************** -->
          <!-- JOB ACTIONS                -->
          <!-- ************************** -->
          <div id="job-actions" class="col column q-mt-lg q-col-gutter-y-sm">
            <!-- START/PAUSE BUTTOM -->
            <div class="col-4">
              <StartPauseResumeBtn />
            </div>

            <!-- PROGRESS BUTTON -->
            <div class="col-4">
              <ProgressBtn />
            </div>

            <!-- NEW ISSUE AND EXIT BUTTONS -->
            <div class="row col-4 q-col-gutter-x-sm">
              <div class="col">
                <q-btn
                  :style="`background-color: ${$theme.grey}aa`"
                  square
                  height="auto"
                  class="fit"
                  @click="show_issue_form = true"
                >
                  <q-icon color="text_high" size="lg" name="mdi-flag" />
                </q-btn>
              </div>

              <div class="col">
                <q-btn
                  :style="`background-color: ${$theme.grey}aa`"
                  square
                  height="auto"
                  class="fit"
                  @click="
                    () => {
                      exit_destination = { name: 'userJobs' };
                      if (j.active) {
                        show_exit_alert = true;
                      } else {
                        exitJob(false);
                      }
                    }
                  "
                >
                  <q-icon color="text-high" size="lg" name="mdi-close" />
                </q-btn>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- TODO: i18n -->
      <!-- Active session exit alert -->
      <q-dialog
        v-model="show_exit_alert"
        maximized
        transition-show="none"
        transition-hide="fade"
        style="z-index: 99999"
      >
        <div class="fixed-full glass" />
        <div class="row justify-between">
          <div v-if="j.parameters.unsupervised_work_allowed" class="col">
            <q-btn flat class="fit q-pa-lg" @click="exitJob(false)">
              <div class="column items-center">
                <q-icon name="mdi-play" size="100px" />
                <div>Esci e continua la sessione</div>
              </div>
            </q-btn>
          </div>
          <div class="col">
            <q-btn flat class="fit q-pa-lg" @click="exitJob(true)">
              <div class="column items-center">
                <q-icon name="mdi-pause" size="100px" />
                <div>Esci e ferma la sessione</div>
              </div>
            </q-btn>
          </div>
          <div class="col">
            <q-btn flat class="fit q-pa-lg" @click="show_exit_alert = false">
              <div class="column items-center">
                <q-icon name="mdi-close" size="100px" />
                <div>Annulla</div>
              </div>
            </q-btn>
          </div>
        </div>
      </q-dialog>

      <!-- NEW ISSUE -->
      <IssueForm
        :show="show_issue_form"
        mode="new"
        with_links
        auto_link_mode="work_session"
        :auto_links="issue_links"
        @close="show_issue_form = false"
      />
    </q-page>
  </q-page-container>
</template>

<script>
import { until } from '@vueuse/core';
import { Dialog, Loading } from 'quasar';
import Sortable from 'sortablejs';
import { mapState } from 'vuex';

import BaseProgressBar from '@/components/BaseProgressBar.vue';
import IssueForm from '@/components/IssueForm.vue';
import PhaseProgressBar from '@/components/PhaseProgressBar.vue';
import ProgressBtn from '@/components/ProgressBtn.vue';
import QuantityPickerDialog from '@/components/QuantityPickerDialog.vue';
import StartPauseResumeBtn from '@/components/StartPauseResumeBtn.vue';
import SerialBatchSelectionDialog from '@/components/job/SerialBatchSelectionDialog.vue';

export default {
  name: 'WorkSessionScreen',

  components: {
    BaseProgressBar,
    PhaseProgressBar,
    IssueForm,
    ProgressBtn,
    StartPauseResumeBtn,
  },

  beforeRouteLeave(to, _from, next) {
    if (this.j.active && !this.can_leave) {
      this.exit_destination = to;
      this.show_exit_alert = true;
      next(false);
    } else {
      next();
    }
  },

  props: {
    // from router
    jobKey: {
      type: String,
      required: true,
    },
  },

  data() {
    return {
      vuex_ready: false,
      show_exit_alert: false,
      exit_destination: { name: 'userJobs' },
      show_issue_form: false,
      alert_timeout: 4000,
      can_leave: false,
      events: undefined,
      show_progress: false,
      timer_count: 0,
      phase_progress: undefined,
    };
  },

  computed: {
    ...mapState({
      j: (state) => state.traceability.working_job_data,
      batch_data: (state) => state.traceability.current_batch_data.step_data,
      wo_data: (state) => state.workorder.wo_data,
    }),

    traceability_enabled() {
      return !!this.$store.state.traceability.working_job_data
        .traceability_level;
    },

    links() {
      return [
        {
          route_name: 'jobSteps',
          text: this.$t('procedure'),
          icon: 'mdi-order-bool-descending-variant',
          item_count: this.j.step_sequence.length,
        },
        {
          route_name: 'jobDocs',
          text: this.$t('document.label', 2),
          icon: 'mdi-file-document-multiple',
          item_count: this.j.job_docs.length,
        },
        {
          route_name: 'jobBom',
          text: this.$t('material', 2),
          icon: 'mdi-file-tree',
          item_count: this.j.job_bom.length + '/' + this.j.wo_bom.length,
        },
        {
          route_name: 'jobIssues',
          text: this.$t('issue', 2),
          icon: 'mdi-flag',
          item_count:
            this.$store.getters.getIssueCount(true) +
            '/' +
            this.$store.getters.getIssueCount(false),
        },
        {
          route_name: 'jobNotes',
          text: this.$t('notes', 2),
          icon: 'mdi-note-edit',
          item_count:
            !!this.j.order_notes +
            !!this.j.phase_notes +
            !!this.j.product_notes,
        },
        {
          route_name: 'jobMessages',
          text: this.$t('message', 2),
          icon: 'mdi-message-text-outline',
          item_count: this.j.message_count,
        },
        {
          route_name: 'jobProcessView',
          text: this.$t('process'),
          icon: 'mdi-chevron-triple-right',
          item_count: this.wo_data.phase_sequence?.length,
        },
      ];
    },

    sorted_links() {
      const links = [...this.links];
      return links.sort(
        (a, b) =>
          this.links_order.indexOf(a.route_name) -
          this.links_order.indexOf(b.route_name),
      );
    },

    job_info() {
      return [
        { name: 'wo_code', text: this.$t('work_order.list_headers.wo_code') },
        { name: 'project_code', text: this.$t('project') },
        { name: 'active_batch_qt', text: this.$t('quantity.active.medium') },
      ];
    },

    force_order() {
      return this.j.parameters.step_check_force_order;
    },

    job_color() {
      switch (true) {
        case this.j.critical:
          return 'theme-red';
        case !this.j.on_time:
          return 'theme-orange';
        case this.j.active:
          return 'theme-blue';
        default:
          return 'theme-grey';
      }
    },

    current_step_key: {
      get() {
        return this.$store.state.traceability.current_step_key;
      },
      set(key) {
        this.$store.dispatch('goToStep', key);
      },
    },

    current_step_done() {
      const currentStep = this.batch_data?.find(
        ({ _key }) => _key === this.current_step_key,
      );

      return currentStep?.done ?? false;
    },

    allow_step_forward() {
      let allow = true;
      if (this.force_order && !this.current_step_done) {
        allow = false;
      }
      return allow;
    },

    has_material_to_proceed() {
      return this.j.next_batch_available || this.j.active_batch_qt;
    },

    job_closed() {
      return this.j.stage == 'closed';
    },

    can_work() {
      return this.has_material_to_proceed && !this.job_closed;
    },

    issue_links() {
      return {
        product: this.j.product_key,
        operation: this.j.operation_key,
        phase: this.j.phase_key,
        work_order: this.j.wo_key,
        work_order_data: this.wo_data,
        job: this.j._key,
      };
    },

    links_order: {
      get() {
        return (
          this.$store.state.session.user.preferences.work_session_tabs_order ??
          this.links.map(({ route_name }) => route_name)
        );
      },
      set(order) {
        this.$store.dispatch('updatePreferences', {
          work_session_tabs_order: order,
        });
      },
    },
  },

  watch: {
    jobKey: {
      handler() {
        this.loadJob();
      },
    },

    timer_count: {
      handler() {
        if (this.show_progress && this.j.phase_key) {
          setTimeout(() => {
            this.refreshPhaseProgress();
          }, 5000);
        }
      },
      immediate: true, // This ensures the watcher is triggered upon creation
    },
  },

  created() {
    // Load job data
    this.loadJob();
    let eventURL =
      this.$api.defaults.baseURL + '/notification/global-notification';
    this.events = new EventSource(eventURL, {
      withCredentials: false,
    });
    this.events.addEventListener('global-notification', (event) => {
      this.handleMessage(event);
    });
  },

  async mounted() {
    // Go to first tab according to user preference if path doesn't specify one
    if (this.$route.name === 'workSession') {
      this.$router.push({ name: this.links_order[0] });
    }

    if (!this.traceability_enabled) {
      await this.fakeBatchSerials();
    }

    // Make sure an alert is raised if user tries to close the page
    window.addEventListener('beforeunload', this.beforeUnloadAlert);

    // Wait until the condition for the content to be rendered is met
    await until(() => this.vuex_ready & !this.job_closed).toBeTruthy();

    const container = document.querySelector('.drag-container');
    Sortable.create(container, {
      ...this.$store.state.drag_options,
      onEnd: ({ newIndex, oldIndex }) => {
        if (newIndex === oldIndex) {
          return;
        }

        // Use the sorted links as a reference since it's the source of truth.
        // Otherwise, the links_order might be missing some links, which would lead to an incorrect order or undefined values.
        const sortedLinkNames = this.sorted_links.map(
          ({ route_name }) => route_name,
        );
        const moved = sortedLinkNames.splice(oldIndex, 1)[0];

        this.links_order = [
          ...sortedLinkNames.slice(0, newIndex),
          moved,
          ...sortedLinkNames.slice(newIndex),
        ];
      },
    });

    this.refreshPhaseProgress();
  },

  beforeUnmount() {
    window.removeEventListener('beforeunload', this.beforeUnloadAlert);
    this.$store.state.traceability.current_step_key = undefined;
    this.$store.commit('UPDATE_BATCH_SERIALS', []);
    if (this.events) {
      this.events.close();
    }
  },

  methods: {
    handleMessage(message) {
      let event = JSON.parse(message.data);
      if (event.notification === 'REFRESH') {
        this.updateJobData();
      }
    },
    async loadJob() {
      this.$store.dispatch('loadWorkingJobData', this.jobKey).then(async () => {
        await this.$store.dispatch('loadWorkOrderData', this.j.wo_key);
        const data = this.$store.state.traceability;
        const job_data = data.working_job_data;

        // If job is closed, redirect to
        if (!this.can_work) {
          setTimeout(this.exitJob, this.alert_timeout);
        } else {
          this.vuex_ready = true;
          if (data.current_batch_data.step_data) {
            const next_step_index =
              this.batch_data.findIndex((step) => !step.done) || 0;
            // TODO: Utilize the query parameter or remove it
            this.$router.replace({ query: { step: next_step_index + 1 } });
          }
          // In case the job is already active, e.g. after accidentally closing and reopening the page, restart heartbeat
          if (job_data.active) {
            this.$store.commit('SET_HEARTBEAT', true);
          }
        }
      });
    },

    async fakeBatchSerials() {
      if (!this.traceability_enabled) {
        await this.$store.dispatch('fakeBatchSerials', {
          job_key: this.j._key,
        });
      }
    },

    getItemCountColor(link) {
      return this.$route.name == link.route_name
        ? this.j.critical
          ? 'theme-red'
          : 'theme-blue'
        : 'theme-grey';
    },

    async editBatchSerials() {
      Loading.show();
      const remainingTotalQuantity = this.j.qt_planned - this.j.qt_completed;
      const { data: available_serials } = await this.$api.get('/wip-serial', {
        params: {
          job_key: this.j._key,
          phase_key: this.j.phase_key,
          wo_key: this.j.wo_key,
        },
      });
      const initial_selection = available_serials
        .filter((s) => s.active)
        .map((s) => s.serial_key);
      Loading.hide();

      const selected_serials = await new Promise((resolve) => {
        Dialog.create({
          component: SerialBatchSelectionDialog,
          componentProps: {
            available_serials: available_serials.map((s) => ({
              label: s.serial_code,
              value: s.serial_key,
            })),
            selected_serials: initial_selection,
            max_quantity: remainingTotalQuantity,
          },
        })
          .onOk((selected_serials) => resolve(selected_serials))
          .onCancel(() => resolve(false));
      });

      if (selected_serials.length && selected_serials != initial_selection) {
        return {
          payload: {
            batchSerials: selected_serials,
            newBatchQuantity: selected_serials.length,
          },
          message: this.$capitalize('Seriali modificati correttamente'),
        };
      }
    },

    async editBatchQuantity() {
      Loading.show();
      const remainingTotalQuantity = this.j.qt_planned - this.j.qt_completed;
      const { data } = await this.$api.get('/wip', {
        params: { job_key: this.j._key },
      });
      const maxDeclarableQuantity = this.j.first_phase
        ? remainingTotalQuantity
        : Math.min(
            data.free_wip_qt_upstream + this.j.active_batch_qt,
            remainingTotalQuantity,
          );
      Loading.hide();

      let newBatchQuantity = await new Promise((resolve) => {
        Dialog.create({
          component: QuantityPickerDialog,
          componentProps: {
            initialValue: this.j.active_batch_qt,
            max: maxDeclarableQuantity,
          },
        })
          .onOk((quantity) => resolve(quantity))
          .onCancel(() => resolve(false));
      });

      if (newBatchQuantity) {
        if (!this.traceability_enabled) {
          this.fakeBatchSerials();
        }

        return {
          message: this.$capitalize('Quantità modificata correttamente'),
          payload: { newBatchQuantity },
        };
      }
    },

    async editBatchQuantityOrSerials() {
      const data = await (this.j.traceability_level && !this.j.first_phase
        ? this.editBatchSerials() // Show serial selection dialog
        : this.editBatchQuantity()); // Update quantity only (unconfirmed serials are handled in the backend if needed)

      if (data) {
        // Call new endpoint to update active batch quantity
        this.$store.dispatch('updateActiveBatch', data.payload).then(() => {
          this.$q.notify({
            message: data.message,
            color: 'theme-green',
            timeout: 1500,
            position: 'top',
          });
        });
      }
    },

    exitJob(stop_session) {
      if (stop_session) {
        this.$store
          .dispatch('pauseJob')
          .then(() => this.$router.push(this.exit_destination));
      } else {
        this.can_leave = true;
        this.$router.push(this.exit_destination);
      }
    },

    beforeUnloadAlert(event) {
      event.preventDefault();
      event.returnValue = '';
    },

    updateJobData() {
      Promise.all([
        this.$api.get(`job/${this.jobKey}`),
        this.$store.dispatch('loadWorkOrderData', this.j.wo_key),
      ]).then(([jobResponse]) => {
        this.$store.commit('UPDATE_JOB', jobResponse.data.detail);
      });
    },

    refreshPhaseProgress() {
      this.$api.get(`/progress/phase/${this.j.phase_key}`).then((resp) => {
        this.timer_count = resp?.data?.detail?.phase_processing_time;
        if (resp?.data?.detail?.params?.display_phase_progress) {
          this.show_progress = true;
          this.phase_progress = {
            consumed: resp?.data?.detail?.phase_processing_time_sec,
            consumer_millis: resp?.data?.detail?.phase_processing_time,
            total:
              resp?.data?.detail?.params?.std_processing_time *
              this.j.qt_planned,
            active: this.j.active,
          };
        } else {
          this.show_progress = false;
          this.phase_progress = undefined;
        }
      });
    },
  },
};
</script>

<style lang="sass" scoped>
.fixed-width-button
  width: 150px
  height: 200px
</style>
