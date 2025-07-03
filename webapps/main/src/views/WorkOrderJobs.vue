<template>
  <div class="q-px-sm q-py-sm full-height column">
    <!-- HEADERS -->
    <div class="row low-text items-center q-py-sm q-pl-xs">
      <div
        v-for="header in headers"
        :key="header.value"
        class="text-h5 text-uppercase"
        :class="getColClass(header)"
      >
        <div v-if="header.value === 'issue_count'">
          <q-icon name="mdi-flag" size="14px" />
        </div>

        <div v-else-if="header.value !== 'assigned_to'">
          {{ header.text }}
        </div>

        <!-- ASSIGNED TO -->
        <div v-else class="row items-center">
          <div class="col-4 text-right q-pr-lg">
            {{ $t('performance.processing_time.short') }}
          </div>
          <div class="col">
            {{ $t('job.assigned_to') }}
          </div>
        </div>
      </div>
    </div>

    <!-- CONTENT -->
    <div class="scroll col">
      <q-expansion-item
        v-for="phase in phase_data"
        :key="phase.phase_key"
        expand-separator
        :model-value="expanded_phase === phase.phase_key"
        :header-class="getHeaderClass(phase.phase_key)"
        hide-expand-icon
        @click="togglePhase(phase.phase_key)"
      >
        <!-- PHASE SUMMARY DATA -->
        <template #header>
          <div
            v-for="header in headers"
            :key="header.value"
            :class="getColClass(header)"
          >
            <!-- PHASE PROGRESS -->
            <template v-if="header.value === 'phase_alias'">
              <span>{{ $capitalizeAll(phase[header.value]) }}</span>
              <span
                v-if="expanded_phase === phase.phase_key"
                class="q-ml-sm text-body2 smaller text-disabled"
                @click.stop="null"
              >
                ({{ phase.phase_key }})
              </span>
            </template>

            <template v-else-if="header.value === 'progress'">
              <div class="col-12 row items-center">
                <div class="col">
                  <BaseProgressBar :data="phase" />
                </div>
                <div class="col-2 text-right q-ml-sm">
                  {{ phase.progress }}%
                </div>
              </div>
            </template>

            <template v-else-if="header.value === 'issue_count'">
              {{ phase.issue_count }}
            </template>

            <template v-else-if="header.value === 'assigned_to'">
              <div class="row">
                <div class="col-3 text-right">
                  {{ phase.processing_time }}
                </div>
              </div>
            </template>

            <!-- OTHER PHASE DATA -->
            <template v-else>
              {{ $capitalizeAll(phase[header.value]) }}
            </template>
          </div>
        </template>
        <!-- END OF HEADER -->

        <!-- JOB DATA & PHASE/JOB ACTIONS -->
        <div
          v-for="job in phase.jobs"
          :id="job._key"
          :key="job._key"
          class="row items-center q-py-md q-pl-sm"
        >
          <!-- JOB DATA -->
          <div
            v-for="header in headers"
            :key="header.value"
            :class="getColClass(header)"
          >
            <!-- SELECT CHECKBOX -->
            <template v-if="header.value === 'phase_alias'">
              <div class="row items-center" style="margin-left: -12px">
                <q-checkbox
                  v-if="job.stage !== 'closed'"
                  v-model="selected_jobs"
                  color="theme-blue"
                  :disable="job.active"
                  :val="job._key"
                />
                <q-icon
                  v-else
                  color="theme-green"
                  name="mdi-check-circle-outline"
                  size="sm"
                  class="q-ma-sm"
                />

                <div class="smaller">
                  {{ job._key }}
                  <q-tooltip
                    :delay="Number(500)"
                    anchor="bottom left"
                    self="top left"
                    :offset="[10, 0]"
                    transition-show="fade"
                    transition-hide="fade"
                    class="surface1 text-high"
                  >
                    <div>
                      {{ $t('start_short') }}: {{ formatJobTimes(job.start) }}
                    </div>
                    <div>{{ $t('end') }}: {{ formatJobTimes(job.end) }}</div>
                  </q-tooltip>
                </div>

                <!-- JOB ACTIONS MENU -->
                <q-btn
                  round
                  flat
                  size="sm"
                  icon="mdi-dots-horizontal"
                  class="q-ml-sm"
                >
                  <ProductionAdminMenu :job="job" show-job-actions/>
                </q-btn>
              </div>
            </template>

            <!-- JOB PROGRESS BAR -->
            <template v-else-if="header.value === 'progress'">
              <div class="row items-center">
                <div class="col">
                  <BaseProgressBar :data="job" />
                </div>
                <div class="col-2 text-right q-ml-sm">{{ job.progress }}%</div>
              </div>
            </template>

            <!-- ASSIGNED OPERATOR -->
            <template v-else-if="header.value === 'assigned_to'">
              <div class="row items-center">
                <div class="text-right q-mr-lg col-3">
                  {{
                    job.stage !== 'created'
                      ? $durationFromMillisec(job.processing_time, {
                          precision: 'm',
                        }) || '< 1m'
                      : '-'
                  }}
                </div>
                <BaseUserAvatar v-if="job.assigned_to" :user="job.assigned_to">
                </BaseUserAvatar>
                <q-btn
                  v-else-if="selected_jobs.length === 0"
                  size="sm"
                  color="theme-blue"
                  icon="mdi-account-plus"
                  :label="$t('assign')"
                  @click="updateSelectedJobData(job)"
                >
                </q-btn>
              </div>
            </template>

            <!-- REMAINING QUANTITY (CALCULATED) -->
            <template v-else-if="header.value === 'qt_remaining'">
              {{ job.qt_planned - job.qt_completed - job.active_batch_qt }}
            </template>

            <!-- PROCESSING TIME -->
            <template v-else-if="header.value === 'processing_time'">
              {{
                $durationFromMillisec(job.processing_time, { precision: 'm' })
              }}
            </template>

            <!-- OTHER FIELDS -->
            <template v-else>
              {{ job[header.value] }}
            </template>
          </div>
          <!-- END OF JOB DATA -->
        </div>

        <!-- JOB ACTIONS -->
        <div class="row items-center q-pa-lg">
          <!-- STARTING ACTION BUTTONS -->
          <template v-if="editMode === 'actions'">
            <!-- SELECT ALL -->
            <q-btn
              v-if="phase.jobs.length > 1"
              size="12px"
              color="theme-grey"
              :label="
                selected_jobs.length === 0
                  ? $t('select_all')
                  : $t('deselect_all')
              "
              @click="toggleAll(phase)"
            >
            </q-btn>

            <template v-if="phase.editing">
              <q-space />
              <q-btn
                size="12px"
                color="theme-blue"
                @click="editMode = 'modify'"
              >
                {{ $t('edit') }}
              </q-btn>
            </template>
          </template>
          <!-- END OF STARTING ACTION BUTTONS -->

          <!-- REBALANCE ACTION CARD -->
          <template v-if="editMode === 'modify'">
            <JobRebalanceActionCard
              :jobs="selected_jobs_data"
              :qt-to-allocate="qtToAllocate"
              @change-edit-mode="editMode = $event"
            >
            </JobRebalanceActionCard>
          </template>
        </div>
        <!-- END OF JOB ACTIONS -->
      </q-expansion-item>
    </div>
  </div>
</template>

<script>
import BaseProgressBar from '@/components/BaseProgressBar.vue';
import BaseUserAvatar from '@/components/BaseUserAvatar.vue';
import JobRebalanceActionCard from '@/components/JobRebalanceActionCard.vue';
import { formatDateTime } from '@/lib/TimeHandling';
import sendEvent from '@/mixins/event.js';
import ProductionAdminMenu from '@/components/ProductionAdminMenu.vue';

export default {
  name: 'WorkOrderJobs',

  components: {
    BaseProgressBar,
    BaseUserAvatar,
    ProductionAdminMenu,
    JobRebalanceActionCard, // Make changes to phase jobs
  },

  mixins: [sendEvent],

  props: {
    wo_data: {
      type: Object,
      required: true,
      show_update: null,
      default: function () {
        return { phase_sequence: [] };
      },
    },
  },

  data() {
    return {
      saving: false,
      expanded_phase: null,
      selected_jobs: [],
      jobs_temp_data: undefined,
      editMode: 'actions',
      edit_job_time: null,
      edit_job_progress: null,
      confirm_cancel_batch: null,
      confirm_reset_job: null,
    };
  },

  computed: {
    headers() {
      return [
        {
          value: 'phase_alias',
          text: this.$t('phase.short') + ' / ID',
          cols: '2',
        },
        {
          value: 'progress',
          text: this.$t('progress'),
          cols: '3',
        },
        {
          value: 'issue_count',
          align: 'right',
        },
        {
          value: 'qt_completed',
          text: this.$t('quantity.completed.short'),
          align: 'end',
        },
        // { value: 'qt_released', text: 'QRil', align: 'end', cols: false, width: '1'},
        {
          value: 'active_batch_qt',
          text: this.$t('quantity.active.short'),
          align: 'end',
        },
        {
          value: 'qt_remaining',
          text: this.$t('quantity.remaining.short'),
          align: 'end',
        },
        {
          value: 'assigned_to',
          align: 'end',
          cols: '4',
        },
      ];
    },

    userCanStopJob() {
      return (
        this.$store.getters.hasPermission('production') ||
        this.$store.getters.hasPermission('admin')
      );
    },

    selected_jobs_data() {
      return this.wo_data.jobs.filter((job) =>
        this.selected_jobs.includes(job._key),
      );
    },

    qtToAllocate() {
      const selected_qt_remaining = Object.values(
        this.selected_jobs_data,
      ).reduce((sum, job) => {
        return sum + job.qt_planned - job.qt_completed - job.active_batch_qt;
      }, 0);
      const wo_qt_remaining =
        this.wo_data.qt_planned -
        Object.values(this.selected_jobs_data).reduce((sum, job) => {
          return sum + job.qt_completed + job.active_batch_qt;
        }, 0);
      return Math.min(selected_qt_remaining, wo_qt_remaining);
    },

    phase_data() {
      return this.wo_data.phase_sequence.map((phase_key) => {
        const jobs = this.wo_data.jobs
          .filter((job) => job.phase_key === phase_key)
          .sort((a, b) => (a._key > b._key ? -1 : a._key < b._key ? 1 : 0));
        const params = jobs[0].parameters;
        const phase_alias = jobs[0].phase_alias;
        const issue_count = jobs.reduce((sum, job) => sum + job.issue_count, 0);
        const total_completed = jobs.reduce(
          (sum, job) => sum + job.qt_completed,
          0,
        );
        const total_active = jobs.reduce(
          (sum, job) => sum + job.active_batch_qt,
          0,
        );
        // const total_released = jobs.reduce( (sum, job) => sum + job.qt_released, 0 )
        const total_remaining = jobs.reduce((sum, job) => {
          return sum + job.qt_planned - job.qt_completed - job.active_batch_qt;
        }, 0);
        const total_progress = Math.floor(
          jobs.reduce((sum, job) => sum + job.progress * job.qt_planned, 0) /
            this.wo_data.qt_planned,
        );
        const critical = jobs.some((job) => job.critical);

        const total_processing_time = jobs.reduce(
          (sum, job) => sum + job.processing_time,
          0,
        );
        const processing_time_string =
          total_processing_time == 0
            ? '-'
            : this.$durationFromMillisec(total_processing_time, {
                precision: 'm',
              }) || '< 1m';
        const active = !!jobs.reduce((count, job) => count + job.active, 0);
        const editing = jobs.some((job) =>
          this.selected_jobs.includes(job._key),
        );

        // const assignments = jobs.map( job => job.assigned_to )

        return {
          jobs,
          phase_key,
          phase_alias,
          editing,
          active,
          critical,
          issue_count,
          ...params,
          // qt_released: total_released,
          qt_completed: total_completed,
          qt_remaining: total_remaining,
          active_batch_qt: total_active,
          progress: total_progress,
          processing_time: processing_time_string,
        };
      });
    },
  },

  watch: {
    // Reset selection when toggling phases
    expanded_phase() {
      this.selected_jobs = [];
    },

    // reset editMode after closing/switching phase details
    selected_jobs() {
      if (!this.selected_jobs.length) {
        this.editMode = 'actions';
      }
    },

    editMode() {
      if (this.editMode === 'actions') {
        this.selected_jobs = [];
      }
    },
  },

  created() {
    this.temp_due_date = this.wo_data.due_by;
  },

  methods: {
    getHeaderClass(phase_key) {
      const base_classes = 'row items-center q-py-lg';
      const highlight = this.expanded_phase === phase_key ? ' highlight' : '';
      return base_classes + highlight + ' q-pl-xs q-pr-none';
    },

    getColClass(header) {
      const alignment_class =
        header.value.includes('qt') ||
        ['processing_time', 'issue_count'].includes(header.value)
          ? 'text-right'
          : '';

      const cols = header.cols ? 'col-' + header.cols : 'col';
      return cols + ' ' + alignment_class + ' q-pl-md';
    },

    togglePhase(phase_key) {
      if (this.expanded_phase === phase_key) {
        this.expanded_phase = null;
      } else {
        this.expanded_phase = phase_key;
      }
    },

    toggleAll(phase) {
      if (this.selected_jobs.length) {
        this.selected_jobs = [];
      } else {
        // Select jobs that are open and NOT active
        phase.jobs
          .filter((j) => {
            const job_is_open = j.stage != 'closed';
            const job_not_active = !j.active;
            return job_is_open && job_not_active;
          })
          .forEach((j) => {
            this.selected_jobs.push(j._key);
          });
      }
    },

    updateSelectedJobData(job) {
      this.selected_jobs.push(job._key);
      this.editMode = 'modify';
    },

    formatJobTimes(date) {
      return formatDateTime(date, this.$i18n.locale, {
        weekday: 'short',
        month: 'short',
        day: 'numeric',
      });
    },



    resetEditing() {
      this.jobs_temp_data = {};
    },
  },
};
</script>
