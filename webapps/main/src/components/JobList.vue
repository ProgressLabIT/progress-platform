<template>
  <div id="job-list" class="full-height q-mx-xs q-px-sm q-py-lg scroll">
    <NoDataAlert v-if="operator_assignments.length === 0" />

    <template v-else>
      <!-- EDIT BUTTON -->
      <q-btn
        v-if="!edit_mode"
        round
        color="theme-blue"
        icon="mdi-pencil"
        class="absolute-bottom-right q-mb-md q-mr-md"
        style="z-index: 999"
        @click="edit_mode = true"
      />

      <!-- MAIN CONTENT -->
      <template
        v-for="(assignment, index) in operator_assignments"
        :key="index"
      >
        <!-- ############### -->
        <!-- OPERATOR HEADER -->
        <!-- ############### -->
        <div class="row items-center q-pl-sm">
          <BaseUserAvatar
            :user="assignment.operator"
            name_class="medium weight-medium"
            size="36px"
          />

          <q-space />

          <template v-if="config.allowIndependentReorderingOfJobQueues">
            <q-btn
              v-if="
                assignment.independent && assignment.assigned_jobs_count > 1
              "
              size="sm"
              color="theme-blue"
              :label="$t('independentOrdering.reorder')"
              class="q-mr-sm"
              @click="openReorderDialog(assignment)"
            />

            <q-checkbox
              v-if="assignment.operator._key !== 'unassigned'"
              :model-value="assignment.independent"
              :label="$t('independentOrdering.switch.label')"
              class="q-mr-sm"
              color="theme-blue"
              size="sm"
              @update:model-value="updateAssignmentDependency(assignment)"
            >
              <q-tooltip>
                {{ $t('independentOrdering.switch.hint') }}
              </q-tooltip>
            </q-checkbox>
          </template>

          <q-chip
            :ripple="false"
            class="col-auto text-body2"
            color="theme-blue"
            size="sm"
          >
            <q-icon name="mdi-timer-sand" class="q-mr-sm" size="14px" />
            <strong>
              {{ calculateWorkloadHours(assignment.filtered_jobs) }}
            </strong>
            <span class="q-mx-xs">
              {{ $t('of') }}
            </span>
            <strong>
              {{ assignment.total_workload_hours }}
            </strong>
            <q-tooltip
              :delay="200"
              anchor="top middle"
              self="center middle"
              transition-show="fade"
              transition-hide="fade"
              class="transparent text-low"
            >
              {{ $capitalize($t('workload_hours')) }}
            </q-tooltip>
          </q-chip>

          <q-chip
            :ripple="false"
            class="col-auto text-body2"
            color="theme-grey"
            size="sm"
          >
            <q-icon name="mdi-eye-outline" class="q-mr-sm" size="14px" />
            <strong>
              {{ assignment.filtered_jobs.length }}
            </strong>
            <span class="q-mx-xs">
              {{ $t('of') }}
            </span>
            <strong>
              {{ assignment.assigned_jobs_count }}
            </strong>
            <q-tooltip
              :delay="200"
              anchor="top middle"
              self="center middle"
              transition-show="fade"
              transition-hide="fade"
              class="transparent text-low"
            >
              {{ $capitalize($t('shown', 2)) }}
            </q-tooltip>
          </q-chip>
        </div>

        <!-- ############### -->
        <!-- OPERATOR JOBS -->
        <!-- ############### -->
        <q-table
          :columns="job_data"
          :rows="assignment.filtered_jobs"
          row-key="_key"
          hide-bottom
          virtual-scroll
          dense
          separator="none"
          table-class="text-high assignment-list"
          card-class="background no-shadow q-mt-md"
          :rows-per-page-options="[0]"
          :selection="edit_mode ? 'multiple' : false"
        >
          <template v-if="edit_mode" #header-selection>
            <q-checkbox
              dense
              :model-value="userJobsModel(assignment.filtered_jobs)"
              @update:model-value="
                (value) =>
                  toggleJobs({
                    added: value,
                    keys: assignment.filtered_jobs
                      .filter((j) => !j.active)
                      .map((j) => j._key),
                  })
              "
            />
          </template>

          <template #header-cell-issue_count="props">
            <q-th :props="props">
              <q-icon name="mdi-flag" size="14px" />
            </q-th>
          </template>

          <template #body="props">
            <q-tr
              :props="props"
              @click="
                toggleJobs({
                  added: !selected_jobs.has(props.row._key),
                  keys: [props.row._key],
                })
              "
              @dblclick="showWorkOrderScreen(props.row.wo_key)"
            >
              <q-td v-if="edit_mode">
                <q-checkbox
                  v-show="!props.row.active"
                  dense
                  :model-value="selected_jobs.has(props.row._key)"
                  @update:model-value="
                    (value) =>
                      toggleJobs({
                        added: value,
                        keys: [props.row._key],
                      })
                  "
                />
              </q-td>
              <template v-for="field in job_data" :key="field.name">
                <q-td
                  :props="props"
                  :class="{
                    'filter-field': search_fields.includes(field.name),
                  }"
                >
                  <!-- PROGRESS -->
                  <template v-if="field.name === 'progress'">
                    <div class="row items-center q-col-gutter-sm">
                      <div class="col">
                        <BaseProgressBar :data="props.row" />
                      </div>
                      <span class="col-2 text-right"
                        >{{ props.row[field.name] }} %</span
                      >
                    </div>
                  </template>

                  <template v-else-if="field.name.includes('qt')">
                    {{ props.row[field.name] }}
                  </template>

                  <template v-else-if="field.name === 'issue_count'">
                    {{
                      (props.row.issues_open ?? 0) +
                      '/' +
                      (props.row.issues_total ?? 0)
                    }}
                  </template>

                  <template v-else-if="field.name === 'ready'">
                    <q-icon
                      :name="jobIcon(props.row).name"
                      :color="jobIcon(props.row).color"
                      size="xs"
                    >
                      <!-- calendar-clock check-circle cube-off/toybrick-remove-->
                    </q-icon>
                  </template>

                  <div
                    v-else-if="field.name === 'due_by'"
                    class="row items-center justify-end q-gutter-xs"
                  >
                    <q-icon
                      v-if="props.row.due_by < now.toISOString()"
                      color="theme-red"
                      name="mdi-alert-octagon"
                    />
                    <div>
                      {{
                        props.row.due_by === null
                          ? '-'
                          : $shortDateString(props.row.due_by, $i18n.locale)
                      }}
                    </div>
                  </div>

                  <template v-else>
                    <span
                      @click.stop="setSearch(field.name, props.row[field.name])"
                    >
                      {{ $capitalizeAll(props.row[field.name] || '') }}
                      <q-tooltip
                        :delay="500"
                        anchor="top left"
                        self="bottom left"
                        :offset="[8, 6]"
                        transition-show="fade"
                        transition-hide="fade"
                      >
                        <template v-if="field.name === 'product_code'">
                          <div class="highlight">
                            {{ props.row.product_code }}
                          </div>
                          <div>
                            {{ props.row.product_description }}
                          </div>
                        </template>
                        <template v-else>
                          {{ $capitalizeAll(props.row[field.name] || '') }}
                        </template>
                      </q-tooltip>
                    </span>
                  </template>
                </q-td>
              </template>
            </q-tr>
          </template>
        </q-table>

        <q-separator
          v-if="index < operator_assignments.length - 1"
          class="q-my-lg q-mr-xs q-ml-sm"
        />
      </template>

      <!-- Extra space to account for bottom toolbar -->
      <div v-if="edit_mode" class="q-my-xl" />
    </template>

    <!-- ############### -->
    <!--     ACTIONS     -->
    <!-- ############### -->
    <div
      v-if="edit_mode"
      class="row full-width bg-theme-blue justify-between q-py-sm q-px-md items-center absolute-bottom"
    >
      <div class="col-auto">
        {{ $t('job.selected_count', selected_jobs.size) }}
      </div>
      <div v-if="selected_jobs.size" class="col-auto row items-center">
        <div class="q-mr-md text-uppercase">
          {{ $t('job.assign_to') }}
        </div>
        <BaseAutocompleteUser
          dense
          :placeholder="$t('operator_select_prompt')"
          :value="batch_assign_to"
          @select="(selection) => (batch_assign_to = selection)"
        />
      </div>
      <div class="col-auto row">
        <q-btn
          v-if="batch_assign_to && selected_jobs.size"
          size="sm"
          color="theme-blue"
          class="q-mr-md"
          unelevated
          :label="$t('save')"
          :loading="saving"
          @click="assignJobs"
        />
        <q-btn
          size="sm"
          color="theme-grey"
          unelevated
          :label="$t('cancel')"
          @click="exitEditMode"
        />
      </div>
    </div>
  </div>
</template>

<script>
import { storeToRefs } from 'pinia';
import { Dialog } from 'quasar';
import { useI18n } from 'vue-i18n';
import { useStore } from 'vuex';
import BaseAutocompleteUser from '@/components/BaseAutocompleteUser.vue';
import BaseProgressBar from '@/components/BaseProgressBar.vue';
import BaseUserAvatar from '@/components/BaseUserAvatar.vue';
import NoDataAlert from '@/components/NoDataAlert.vue';
import multiMatch from '@/lib/MultiFieldSearch.js';
import { useConfigStore } from '../stores/config';
import OperatorJobsReorderDialog from './OperatorJobsReorderDialog.vue';

export default {
  name: 'JobList',

  components: {
    BaseAutocompleteUser,
    BaseProgressBar,
    BaseUserAvatar,
    NoDataAlert,
  },

  props: {
    filters: {
      type: Object,
      required: true,
      default: () => {
        return {
          search_string: '',
          started: true,
          queued: true,
          on_time: true,
          late: true,
          active: true,
          idle: true,
          critical: true,
          not_critical: true,
          assigned: true,
          unassigned: true,
          department_key: undefined,
          operator_key: undefined,
          start_from_min: null,
          start_from_max: null,
          due_by_min: null,
          due_by_max: null,
        };
      },
    },
  },

  emits: ['setSearch', 'itemDblClick'],

  setup() {
    const { t } = useI18n();
    const { config } = storeToRefs(useConfigStore());
    const store = useStore();

    async function updateAssignmentDependency({ operator, independent }) {
      if (independent === false) {
        await store.dispatch('updateJobAssignment', {
          operator_key: operator._key,
          independent: true,
        });
        return;
      }

      Dialog.create({
        title: t('independentOrdering.switch.label'),
        message: t('independentOrdering.turnOffConfirm'),
        ok: t('yes'),
        cancel: t('no'),
      }).onOk(async () => {
        await store.dispatch('updateJobAssignment', {
          operator_key: operator._key,
          independent: false,
        });

        // Re-fetch data after the triggered reordering
        await store.dispatch('updateWorkOrderList');
        await store.dispatch('loadJobAssignments');
      });
    }

    /*
      We use a separate dialog instead of in-place reordering because:
      - when data is re-fetched, the table gets re-rendered even if the data was not changed, and the order is lost
      - when there are filters and sorting, the ordered items will only be a subset of the whole list, making the UX&logic confusing
      - it's really hard/annoying to make grouped reordering work (jobs within same work order should stay together)
      - UX is not ideal with grouped reordering with the potential solutions (they don't look like a group, only one item is draggable, etc.)
    */
    function openReorderDialog({ operator }) {
      Dialog.create({
        component: OperatorJobsReorderDialog,
        componentProps: {
          operator,
        },
      }).onOk(async (newJobsOrder) => {
        await store.dispatch('updateJobAssignment', {
          operator_key: operator._key,
          jobs: newJobsOrder,
        });

        // Re-fetch data after submitting the new ordering
        await store.dispatch('updateWorkOrderList');
        await store.dispatch('loadJobAssignments');
      });
    }

    return {
      config,
      updateAssignmentDependency,
      openReorderDialog,
    };
  },

  data() {
    return {
      search_fields: [
        'wo_code',
        'product_code',
        'project_code',
        'product_description',
        'phase_alias',
      ],
      assign_search_string: null,
      show_assignment_dialog: false,
      batch_assign_to: null,
      selected_jobs: new Set(),
      jobs_to_assign: [],
      now: new Date(),
      saving: false,
      edit_mode: false,
    };
  },

  computed: {
    wo_map() {
      return this.$store.state.workorder.wo_map;
    },

    job_data() {
      return [
        {
          field: 'wo_sequence',
          name: 'wo_sequence',
          sortable: true,
          label: this.$t('work_order.list_headers.sequence').toUpperCase(),
          align: 'left',
        },
        {
          label: this.$t('work_order.wo_code').toUpperCase(),
          field: 'wo_code',
          name: 'wo_code',
          sortable: true,
          style: 'max-width: 10vw',
          classes: 'ellipsis',
          align: 'left',
        },
        {
          label: this.$t('project').toUpperCase(),
          field: 'project_code',
          name: 'project_code',
          sortable: true,
          classes: 'ellipsis',
          style: 'max-width: 10vw',
          align: 'left',
        },
        {
          label: this.$t('product.label', 1).toUpperCase(),
          field: 'product_code',
          name: 'product_code',
          sortable: true,
          classes: 'ellipsis',
          align: 'left',
          style: 'max-width: 10vw',
        },
        {
          label: this.$t('phase.short').toUpperCase(),
          field: 'phase_alias',
          name: 'phase_alias',
          sortable: true,
          classes: 'ellipsis',
          align: 'left',
          style: 'max-width: 10vw',
        },
        {
          label: this.$t('progress').toUpperCase(),
          sortable: true,
          field: 'progress',
          name: 'progress',
          style: 'min-width: 15vw',
          align: 'left',
        },
        {
          field: 'issue_count',
          name: 'issue_count',
          sortable: true,
          align: 'right',
        },
        {
          label: this.$t('quantity.completed.short').toUpperCase(),
          sortable: true,
          field: 'qt_completed',
          name: 'qt_completed',
          align: 'right',
        },
        {
          label: this.$t('quantity.planned.short').toUpperCase(),
          field: 'qt_planned',
          name: 'qt_planned',
          sortable: true,
          align: 'right',
        },
        {
          label: this.$t('production.filters.ready').toUpperCase(),
          field: 'ready',
          name: 'ready',
          align: 'right',
        },
        {
          field: 'due_by',
          sortable: true,
          name: 'due_by',
          align: 'right',
          label: this.$t('work_order.list_headers.due_by').toUpperCase(),
        },
      ];
    },

    assignments() {
      return this.$store.state.job.assigned_job_list;
    },

    filtered_assignments() {
      const list = [];
      for (let i = 0; i < this.assignments.length; i++) {
        const assignment = this.assignments[i];

        const total_workload_hours = this.calculateWorkloadHours(
          assignment.assigned_jobs,
        );

        // Match department filter (filter = undefined means no filter)
        const department_match = [
          assignment.operator.department_key,
          undefined,
        ].includes(this.filters.department_key);

        // Match operator filter (filter = undefined means no filter)
        const operator_match = [assignment.operator._key, undefined].includes(
          this.filters.operator_key,
        );

        if (operator_match && department_match) {
          const filtered_jobs = assignment.assigned_jobs
            ? assignment.assigned_jobs.filter(this.matchJobToFilters)
            : [];

          if (filtered_jobs.length) {
            const active_jobs = [];
            const queued_jobs = [];
            filtered_jobs.forEach((j) => {
              const data = {
                ...j,
                wo_sequence: this.wo_map[j.wo_key]?.sequence,
              };
              j.active ? active_jobs.push(data) : queued_jobs.push(data);
            });

            list.push({
              operator: assignment.operator,
              assigned_jobs_count: assignment.assigned_jobs.length,
              total_workload_hours,
              filtered_jobs: [...active_jobs, ...queued_jobs],
              independent: assignment.independent,
            });
          }
        }
      }

      return list;
    },

    unassigned_jobs() {
      return this.$store.state.job.unassigned_job_list;
    },

    operator_assignments() {
      const result = this.filters.assigned
        ? [...this.filtered_assignments]
        : [];

      if (this.filters.unassigned && this.filters.operator_key === undefined) {
        const filtered_unassigned_jobs = this.unassigned_jobs
          .filter(this.matchJobToFilters)
          .map((job) => {
            return {
              ...job,
              ready: this.isReleased(job) && job.next_batch_available,
              wo_sequence: this.wo_map[job.wo_key].sequence,
            };
          });
        if (filtered_unassigned_jobs.length > 0) {
          result.push({
            operator: {
              _key: 'unassigned',
              name: this.$t('job.unassigned_jobs'),
              surname: '',
            },
            total_workload_hours: this.calculateWorkloadHours(
              this.unassigned_jobs,
            ),
            assigned_jobs_count: this.unassigned_jobs.length,
            filtered_jobs: filtered_unassigned_jobs,
          });
        }
      }

      return result;
    },

    batch_assignment_cols() {
      const cols = [
        'wo_code',
        'project_code',
        'product_code',
        'phase_alias',
        'qt_planned',
      ];
      return this.job_data.filter((col) => cols.includes(col.name));
    },

    batch_assignment_view() {
      return this.unassigned_jobs.filter((j) => {
        return multiMatch(this.assign_search_string, j, this.search_fields);
      });
    },
  },

  watch: {
    assign_search_string() {
      this.jobs_to_assign = [];
    },
    jobs_to_assign(val) {
      if (!val.length) {
        this.batch_assign_to = null;
      }
    },
  },

  methods: {
    isReleased(item) {
      // Set start_from as beginning of day in case there's an hour set
      return new Date(item.start_from).setHours(0, 0, 0) <= this.now;
    },

    jobIcon(job) {
      return !this.isReleased(job)
        ? { name: 'mdi-calendar-clock', color: 'grey-backdrop' }
        : job.next_batch_available
          ? { name: 'mdi-check-circle', color: 'theme-blue' }
          : { name: 'mdi-cube-off', color: 'orange-backdrop' };
    },

    userJobsModel(filtered_jobs) {
      const user_selected_jobs = filtered_jobs.filter((j) =>
        this.selected_jobs.has(j._key),
      );
      if (user_selected_jobs.length) {
        return user_selected_jobs.length ===
          filtered_jobs.filter((j) => !j.active).length
          ? true
          : undefined;
      } else {
        return false;
      }
    },

    toggleJobs({ added, keys }) {
      added
        ? keys.map((k) => this.selected_jobs.add(k))
        : keys.map((k) => this.selected_jobs.delete(k));
    },

    matchJobToFilters(job) {
      /*
      Initialize filter results.
      If any false will be found in this array the filter function will return false
      */
      let filter_match_map = [];

      for (const [filter, value] of Object.entries(this.filters)) {
        // by default show item in the list
        let match = true;

        switch (filter) {
          // Perform text search in the defined fields
          case 'search_string':
            match = multiMatch(
              this.filters.search_string,
              job,
              this.search_fields,
            );
            break;

          case 'started':
            if (!value && job.stage === 'started') {
              match = false;
            }
            break;

          case 'queued':
            if (!value && ['created', 'planned'].includes(job.stage)) {
              match = false;
            }
            break;

          case 'on_time':
            if (!value && job.due_by > this.now) {
              match = false;
            }
            break;

          case 'late':
            if (!value && !job.due_by <= this.now) {
              match = false;
            }
            break;

          case 'critical':
            if (!value && job.critical) {
              match = false;
            }
            break;

          case 'not_critical':
            if (!value && !job.critical) {
              match = false;
            }
            break;

          case 'active':
            // Do not show if control is false and job is active
            if (!value && job.active) {
              match = false;
            }
            break;

          case 'idle':
            // Do not show if control is false and job is not active
            if (!value && !job.active) {
              match = false;
            }
            break;

          case 'ready':
            if (!value && this.isReleased(job) && job.next_batch_available) {
              match = false;
            }
            break;

          case 'not_ready':
            if (
              !value &&
              (!this.isReleased(job) || !job.next_batch_available)
            ) {
              match = false;
            }
            break;

          case 'start_from_min':
            if (!!value && new Date(value) > new Date(job.start_from)) {
              match = false;
            }
            break;

          case 'start_from_max':
            if (!!value && new Date(value) < new Date(job.start_from)) {
              match = false;
            }
            break;

          case 'due_by_min':
            if (!!value && new Date(value) > new Date(job.due_by)) {
              match = false;
            }
            break;

          case 'due_by_max':
            if (!!value && new Date(value) < new Date(job.due_by)) {
              match = false;
            }
            break;
        }

        // add result of the specific filter to the map
        filter_match_map.push(match);
      }

      // Return false and exclude job from list if any filter returned false
      return !filter_match_map.some((i) => i === false);
    },

    getPicPath(operator) {
      let user_pic_folder = '/media/user/';
      let filename = (operator.name + operator.surname)
        .replace(/\s+/, '')
        .toLowerCase();
      return user_pic_folder + filename + '.jpg';
    },

    progressColor(job) {
      return job.active ? 'theme-blue' : 'theme-grey';
    },

    setSearch(field, text) {
      if (this.search_fields.includes(field)) {
        this.$emit('setSearch', text);
      }
    },

    showWorkOrderScreen(wo_key) {
      let data_to_emit = {
        wo_key,
        back_to_route_name: this.$route.name,
      };
      this.$emit('itemDblClick', data_to_emit);
    },

    exitEditMode() {
      this.selected_jobs = new Set();
      this.batch_assign_to = null;
      this.edit_mode = false;
    },

    async assignJobs() {
      const job_updates = Array.from(this.selected_jobs).map((_key) => ({
        action: 'update',
        data: { _key, assigned_to: this.batch_assign_to._key },
      }));
      this.saving = true;
      await this.$api.post('job/update', job_updates);
      setTimeout(() => {
        this.$store.dispatch('loadJobAssignments');
        this.saving = false;
        this.selected_jobs = new Set();
        this.batch_assign_to = null;
        this.$q.notify({
          message: this.$t('assignment_success'),
          color: 'theme-green',
          timeout: 2000,
          position: 'top',
        });
      }, 500);
    },

    sortDate(a, b) {
      // equal items sort equally
      if (a === b) {
        return 0;
      }
      // nulls sort after anything else
      else if (a === null) {
        return 1;
      } else if (b === null) {
        return -1;
      }
      // standard sorting
      else {
        return a < b ? 1 : -1;
      }
    },

    calculateWorkloadHours(job_list) {
      const total_workload_seconds = job_list.reduce((sum, job) => {
        // Prevent negative workload when completed qt is higher than planned due to work order qt updates
        return (sum +=
          job.parameters.std_processing_time *
          Math.max(0, job.qt_planned - job.qt_completed));
      }, 0);

      return Math.ceil(total_workload_seconds / 360) / 10; // round up to first decimal
    },
  },
};
</script>

<style lang="sass">
#job-list
  .q-table--dense .q-table th:first-child,
  .q-table--dense .q-table td:first-child
    padding-left: 12px

  .q-table--dense .q-table th:last-child,
  .q-table--dense .q-table td:last-child
    padding-right: 10px
</style>
