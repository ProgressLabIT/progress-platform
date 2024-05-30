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
                    v-if="link.route_name === 'jobIssues'"
                    size="9px"
                    :color="getItemCountColor(link)"
                    class="q-ml-sm weight-bold text-body2"
                  >
                    {{ link.item_count }}
                  </q-chip>
                  <q-avatar
                    v-else
                    size="xs"
                    :color="getItemCountColor(link)"
                    class="q-ml-sm weight-bold text-body2"
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
                <div class="col-7">
                  <span>{{ $capitalizeAll(j[field.name]) }}</span>
                </div>
              </div>
            </template>

            <!-- JOB PROGRESS / STATUS -->
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
                  color="theme-grey"
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
                  color="theme-grey"
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
        auto_link_mode="work_session"
        :auto_links="issue_links"
        @close="show_issue_form = false"
      />
    </q-page>
  </q-page-container>
</template>

<script>
import { until } from '@vueuse/core';

import Sortable from 'sortablejs';
import { mapState } from 'vuex';

import BaseProgressBar from '@/components/BaseProgressBar.vue';
import IssueForm from '@/components/IssueForm.vue';
import ProgressBtn from '@/components/ProgressBtn.vue';
import StartPauseResumeBtn from '@/components/StartPauseResumeBtn.vue';

export default {
  name: 'WorkSessionScreen',

  components: {
    BaseProgressBar,
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
    };
  },

  computed: {
    ...mapState({
      j: (state) => state.traceability.working_job_data,
      ws_list: (state) => state.traceability.work_session_list,
      batch_data: (state) => state.traceability.current_batch_data.step_data,
      wo_data: (state) => state.workorder.wo_data,
      batch_serials: (state) => state.batch_serials,
    }),

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
          item_count: this.j.job_bom.length,
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

    serial_selected() {
      return this.j.stage == 'serial_selected';
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

  created() {
    // Load job data
    this.loadJob();
    this.polling_instance = setInterval(this.updateJobData, 10000);
  },

  async mounted() {
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
  },

  beforeUnmount() {
    window.removeEventListener('beforeunload', this.beforeUnloadAlert);
    clearInterval(this.polling_instance);
    this.$store.state.traceability.current_step_key = undefined;
    this.$store.commit('UPDATE_BATCH_SERIALS', []);
  },

  methods: {
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

    getItemCountColor(link) {
      return this.$route.name == link.route_name
        ? this.j.critical
          ? 'theme-red'
          : 'theme-blue'
        : 'theme-grey';
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
        this.$api.get(`product-steps/${this.jobKey}`),
        this.$store.dispatch('loadWorkOrderData', this.j.wo_key),
      ]).then(([jobResponse]) => {
        this.$store.commit('UPDATE_JOB', jobResponse.data.detail);
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
