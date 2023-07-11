<template>
  <div class="full-height q-mx-xs q-px-sm q-py-lg scroll" id="job-list">
    <NoDataAlert v-if="!jobs_view.length" />

    <template
      v-else
      v-for="(o, index) in jobs_view"
      :key="index">
      <div class="row items-center q-pl-sm">
        <BaseUserAvatar
          :user="o.operator"
          name_class="medium weight-medium"
          size="36px">
        </BaseUserAvatar>
        <q-btn
          v-if="o.operator._key == 'unassigned'"
          size="sm"
          color="theme-blue"
          :label="$t('assign')"
          class="q-ml-lg"
          @click="show_assignment_dialog = true">
        </q-btn>
        <q-space />
        <q-chip :ripple="false" class="col-auto text-body2" color="theme-grey" size="sm">
          <strong>
            {{ o.filtered_jobs.length }}
          </strong>
          <span class="q-mx-xs">
            {{ $t('of') }}
          </span>
          <strong>
            {{ o.assigned_jobs_count }}
          </strong>
        </q-chip>
      </div>

      <q-table
        :columns="job_data"
        :rows="o.filtered_jobs"
        row-key="_key"
        hide-bottom
        virtual-scroll
        dense
        separator="none"
        table-class="text-high assignment-list"
        card-class="background no-shadow q-mt-md"
        :rows-per-page-options="[0]">

        <template #header-cell-issue_count="props">
          <q-th :props="props">
            <q-icon name="mdi-flag" size="14px"/>
          </q-th>
        </template>

        <template #body="props">
          <q-tr :props="props" @dblclick="showWorkOrderScreen(props.row.wo_key)">
            <template v-for="field in job_data" :key="field.name">
              <q-td
                :props="props"
                :class="{ 'filter-field': search_fields.includes(field.name) }">

                <!-- PROGRESS -->
                <template v-if="field.name==='progress'">
                  <div class="row items-center q-col-gutter-sm">
                    <div class="col-9">
                      <BaseProgressBar :data="props.row" />
                    </div>
                    <span class="col-2 text-right">{{ props.row[field.name] }} %</span>
                  </div>
                </template>

                <template v-else-if="field.name.includes('qt')">
                  {{ props.row[field.name] }}
                </template>

                <template v-else-if="field.name == 'issue_count'">
                  {{ (props.row.issues_open ?? 0) + '/' + (props.row.issues_total ?? 0) }}
                </template>

                <template v-else-if="field.name == 'ready'">
                  <q-icon
                    :name="jobIcon(props.row).name"
                    :color="jobIcon(props.row).color"
                    size="xs">
                    <!-- calendar-clock check-circle cube-off/toybrick-remove-->
                  </q-icon>
                </template>

                <div class="row items-center justify-end q-gutter-xs" v-else-if="field.name == 'due_by'">
                  <q-icon v-if="props.row.due_by < now" color="theme-red" name="mdi-alert-octagon"/>
                  <div>{{ props.row.due_by == null ? '-' : $shortDateString(props.row.due_by, $i18n.locale) }}</div>
                </div>

                <template v-else>

                  <span @click="setSearch(field.name, props.row[field.name])">
                    {{ $capitalizeAll(props.row[field.name] || '' ) }}
                  </span>
                </template>

              </q-td>
            </template>
          </q-tr>
        </template>
      </q-table>

      <q-separator class="q-my-lg q-mr-xs q-ml-sm" v-if="index < jobs_view.length - 1"/>

    </template>

    <BaseDialog
      :show="show_assignment_dialog"
      @close="show_assignment_dialog = false"
      maximized
      background="#0004">
      <q-card
        style="width: 60vw; height: 90vh;" class="q-pa-lg q-px-md background">
        <div class="column fit">
          <div class="row justify-between">
            <div>
              <div class="display text-h3">ASSEGNA LAVORI IN BLOCCO</div>
              <div class="q-mt-sm">
                {{ $t('job.shown_jobs_message', {shown: batch_assignment_view.length, total: unassigned_jobs.length}) }}
              </div>
            </div>
            <q-input
              filled
              clearable
              :placeholder="$t('search').toUpperCase()"
              dense
              v-model="assign_search_string">
              <template #append>
                <q-icon name="mdi-magnify" size="xs"/>
              </template>
            </q-input>
          </div>

          <q-table
            square
            :columns="batch_assignment_cols"
            :rows="batch_assignment_view"
            row-key="_key"
            hide-bottom
            color="theme-blue"
            dense flat bordered
            class="my-sticky-header-table col q-my-lg"
            separator="none"
            card-class="text-high full-height background"
            table-class="q-px-none"
            table-header-class="surface1"
            :pagination="{ rowsPerPage: 0 }"
            :rows-per-page-options="[0]"
            v-model:selected="jobs_to_assign"
            selection="multiple">
            <template #body-cell="props">
              <q-td
                :props="props"
                v-if="search_fields.includes(props.col.name)"
                class="filter-field"
                @click="assign_search_string = props.value">
                {{ props.value }}
              </q-td>
              <q-td v-else :props="props">
                {{ props.value }}
              </q-td>
            </template>
          </q-table>

          <div class="row text-h5 text-uppercase q-mb-sm" v-show="jobs_to_assign.length">
            {{ $t('assign') + ' ' + jobs_to_assign.length + ' ' + $t('job.label', 2) }}
          </div>
          <div class="row q-gutter-md items-center">
            <div class="col-6">
              <BaseAutocompleteOperator
                :placeholder="$t('operator_select_prompt')"
                v-show="jobs_to_assign.length"
                :value="batch_assign_to"
                @select="(selection) => batch_assign_to = selection">
              </BaseAutocompleteOperator>
            </div>
            <q-space />
            <div class="col-auto">
            <q-btn
              v-if="batch_assign_to && jobs_to_assign.length"
              color="theme-blue"
              :label="$t('save')"
              :loading="saving"
              @click="assign_jobs">
            </q-btn>
            </div>
            <div class="col-auto">
            <q-btn
              color="theme-grey"
              :label="$t('close')"
              @click="() => {show_assignment_dialog = false; batch_assign_to = null}">
            </q-btn>
            </div>
          </div>
        </div>
      </q-card>
    </BaseDialog>

  </div>
</template>

<script>
import BaseAutocompleteOperator from '@/components/BaseAutocompleteOperator.vue'
import BaseProgressBar from '@/components/BaseProgressBar.vue'
import BaseUserAvatar from '@/components/BaseUserAvatar.vue'
import BaseDialog from '@/components/BaseDialog.vue'
import BaseActionCard from '@/components/BaseActionCard.vue'
import multiMatch from '@/lib/MultiFieldSearch.js'
import NoDataAlert from '@/components/NoDataAlert.vue'
export default {

  name: 'JobList',

  components: {
    BaseAutocompleteOperator,
    BaseProgressBar,
    BaseUserAvatar,
    BaseActionCard,
    BaseDialog,
    NoDataAlert
  },

  props: {
    filters: {
      type: Object,
      required: true,
      default: () => { return {
        search_string:"",
        started:true,
        queued:true,
        on_time:true,
        late:true,
        active:true,
        idle:true,
        critical:true,
        not_critical:true,
        assigned: true,
        unassigned: true,
        department_key: undefined,
        operator_key: undefined
      }}
    }
  },

  data () {
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
      jobs_to_assign: [],
      now: new Date().toISOString(),
      saving: false
    }
  },

  computed: {
    wo_map() {
      return this.$store.state.workorder.wo_map
    },

    job_data() {
      return [
        {
          field: 'wo_sequence',
          name: 'wo_sequence',
          sortable: true,
          label: this.$t('work_order.list_headers.sequence').toUpperCase(),
          align: 'left'
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
          style: 'max-width: 10vw'
        },
        { 
          label: this.$t('phase.short').toUpperCase(),
          field: 'phase_alias',
          name: 'phase_alias',
          sortable: true,
          classes: 'ellipsis',
          align: 'left',
          style: 'max-width: 10vw'
        },
        { 
          label: this.$t('progress').toUpperCase(),
          sortable: true,
          field: 'progress',
          name: 'progress',
          style: 'min-width: 15vw',
          align: 'left'
        },
        {
          field: 'issue_count',
          name: 'issue_count',
          sortable: true,
          align: 'right'
        },
        { 
          label: this.$t('quantity.completed.short').toUpperCase(),
          sortable: true,
          field: 'qt_completed',
          name: 'qt_completed',
          align: 'right'
        },
        {
          label: this.$t('quantity.planned.short').toUpperCase(),
          field: 'qt_planned',
          name: 'qt_planned',
          sortable: true,
          align: 'right'
        },
        {
          label: this.$t('production.filters.ready').toUpperCase(),
          field: 'ready',
          name: 'ready',
          align: 'right'
        },
        {
          field: 'due_by',
          sortable: true,
          name: 'due_by',
          align: 'right',
          label: this.$t('work_order.list_headers.due_by').toUpperCase(),
        }
      ]
    },

    assignments() {
      return this.$store.state.job.assigned_job_list
    },

    filtered_assignments() {

      let list = []
      for (let i = 0; i < this.assignments.length; i++) {
        let a = this.assignments[i]
        const department_match = [a.operator.department_key, undefined].includes(this.filters.department_key)
        const operator_match = [a.operator._key, undefined].includes(this.filters.operator_key)
        // Check if operator is in department selected or no department filter is set
        if (operator_match && department_match) {

          const filtered_jobs = a.assigned_jobs ? a.assigned_jobs.filter(this.matchJobToFilters) : []
          
          if (filtered_jobs.length) {
            const active_jobs = []
            const queued_jobs = []
            filtered_jobs.forEach( j => {
              const data = {
                ...j,
                wo_sequence: this.wo_map[j.wo_key].sequence
              }
              j.active ? active_jobs.push(data) : queued_jobs.push(data)
            })

            const operator_filtered_assignments = {
              operator: a.operator,
              assigned_jobs_count: a.assigned_jobs.length,
              filtered_jobs: [...active_jobs, ...queued_jobs]
            }
            list.push(operator_filtered_assignments)
          }
        }
      }

      return list
    },

    unassigned_jobs() {
      return this.$store.state.job.unassigned_job_list
    },

    jobs_view() {
      const result = this.filters.assigned ? [...this.filtered_assignments] : []

      if (this.filters.unassigned && this.filters.operator_key === undefined) {
        const filtered_unassigned_jobs = this.unassigned_jobs.filter(this.matchJobToFilters).map(j => {
          return {
            ...j,
            ready: this.isReleased(j) && j.next_batch_available,
            wo_sequence: this.wo_map[j.wo_key].sequence
          }
        })
        if (filtered_unassigned_jobs.length) {
          result.push({
            operator: {
              _key: 'unassigned',
              name: this.$t("job.unassigned_jobs"),
              surname: ''
            },
            assigned_jobs_count: this.unassigned_jobs.length,
            filtered_jobs: filtered_unassigned_jobs
          })
        }
      }

      return result
    },

    batch_assignment_cols() {
      const cols = ['wo_code', 'project_code', 'product_code', 'phase_alias', 'qt_planned']
      return this.job_data.filter(col => cols.includes(col.name))
    },

    batch_assignment_view() {
      return this.unassigned_jobs.filter(j => {
        return multiMatch(this.assign_search_string, j, this.search_fields)
      })
    }
  },

  methods: {
    isReleased(item) {
      return item.start_from <= this.now
    },

    jobIcon(job) {
      return !this.isReleased(job)
        ? { name: 'mdi-calendar-clock', color: 'grey-backdrop' }
        : job.next_batch_available
        ? { name: 'mdi-check-circle', color: 'theme-blue' }
        : { name: 'mdi-cube-off', color: 'orange-backdrop' }
    },

    matchJobToFilters(job) {
      /*
      Initialize filter results.
      If any false will be found in this array the filter function will return false
      */
      let filter_match_map = []

      for (const [filter, value] of Object.entries(this.filters)) {
        // by default show item in the list
        let match = true

        switch (filter) {

          // Perform text search in the defined fields
          case 'search_string':
            match = multiMatch(this.filters.search_string, job, this.search_fields)
            break

          case 'started':
            if (!value && job.stage === 'started') match = false
            break

          case 'queued':
            if (!value && ['created', 'planned'].includes(job.stage)) match = false
            break

          case 'on_time':
            if (!value && job.due_by > this.now) match = false
            break

          case 'late':
            if (!value && !job.due_by <= this.now) match = false
            break

          case 'critical':
            if (!value && job.critical) match = false
            break

          case 'not_critical':
            if (!value && !job.critical) match = false
            break

          case 'active':
            // Do not show if control is false and job is active
            if (!value && job.active) match = false
            break

          case 'idle':
            // Do not show if control is false and job is not active
            if (!value && !job.active) match = false
            break

          case 'ready':
            if (!value && (this.isReleased(job) && job.next_batch_available)) match = false
            break

          case 'not_ready':
            if (!value && (!this.isReleased(job) || !job.next_batch_available)) match = false
            break
        }

        // add result of the specific filter to the map
        filter_match_map.push(match)
      }

      // Return false and exclude job from list if any filter returned false
      return !filter_match_map.some( i => i === false )
    },

    getPicPath(operator) {
      let user_pic_folder = '/media/user/'
      let filename = (operator.name + operator.surname).replace(/\s+/,'').toLowerCase()
      return user_pic_folder + filename + '.jpg'
    },

    progressColor(job) {
      return job.active
        ? 'theme-blue'
        : 'theme-grey'
    },

    setSearch(field, text) {
      if (this.search_fields.includes(field)) {
        this.$emit('setSearch', text)
      }
    },

    showWorkOrderScreen(wo_key) {
      let data_to_emit = {
        wo_key,
        back_to_route_name: this.$route.name
      }
      this.$emit('itemDblClick', data_to_emit)
    },

    async assign_jobs() {
      const job_updates = this.jobs_to_assign.map(job => ({
        action: 'update',
        data: { _key: job._key, assigned_to: this.batch_assign_to._key }
      }))
      this.saving = true
      await this.$api.post('job/update', job_updates)
      setTimeout(() => {
        this.$store.dispatch('loadJobAssignments')
        this.saving = false
        this.jobs_to_assign = []
        this.batch_assign_to = null
        this.$q.notify({
          message: this.$t('assignment_success'),
          color: 'theme-green',
          timeout: 2000,
          position: 'top'
        })
      }, 500)
    },

    sortDate(a,b) {
      // equal items sort equally
      if (a === b) {
          return 0
      }
      // nulls sort after anything else
      else if (a === null) {
          return 1
      }
      else if (b === null) {
          return -1
      }
      // standard sorting
      else {
          return a < b ? 1 : -1
      }
    },
  },

  watch: {
    assign_search_string() {
      this.jobs_to_assign = []
    },
    jobs_to_assign(val) {
      if (!val.length) {
        this.batch_assign_to = null
      }
    }
  }
}
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
