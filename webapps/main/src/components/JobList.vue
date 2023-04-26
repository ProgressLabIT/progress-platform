<template>
  <q-scroll-area class="col q-mx-xs q-px-sm q-pt-lg" :visible="false">
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
              <q-td :props="props" :class="{ 'filter-field': search_fields.includes(field.name)}">

                <!-- PROGRESS -->
                <template v-if="field.name==='progress'">
                  <div class="row items-center q-col-gutter-sm">
                    <div class="col-9">
                      <BaseProgressBar :data="props.row" />
                    </div>
                    <span class="col-2 text-right">{{ props.row[field.name] }} %</span>
                  </div>
                </template>

                <template v-else-if="field.name.includes('qt') || field.name == 'issue_count'">
                  {{ props.row[field.name] }}
                </template>

                <template v-else-if="field.name == 'ready'">
                  <q-icon
                    :name="jobIcon(props.row).name"
                    :color="jobIcon(props.row).color"
                    size="xs">
                    <!-- calendar-clock check-circle cube-off/toybrick-remove-->
                  </q-icon>
                </template>

                <template v-else>
                  <span class="table-data" @click="setSearch(field.name, props.row[field.name])">
                    {{ $capitalizeAll(props.row[field.name] || '' ) }}
                  </span>
                </template>

              </q-td>
            </template>
          </q-tr>
        </template>
      </q-table>

      <q-separator class="q-my-lg q-mx-sm"/>

    </template>
  </q-scroll-area>
</template>

<script>
import BaseProgressBar from '@/components/BaseProgressBar.vue'
import BaseUserAvatar from '@/components/BaseUserAvatar.vue'
import multiMatch from '@/lib/MultiFieldSearch.js'
import NoDataAlert from '@/components/NoDataAlert.vue'
export default {

  name: 'JobList',

  components: {
    BaseProgressBar,
    BaseUserAvatar,
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
      now: new Date().getTime()
    }
  },

  computed: {

    job_data() {
      return [
        { 
          label: this.$t('work_order.wo_code').toUpperCase(),
          field: 'wo_code',
          name: 'wo_code',
          align: 'left',
          style: 'width: 10%'
        },
        {
          label: this.$t('project').toUpperCase(),
          field: 'project_code',
          name: 'project_code',
          align: 'left',
          style: 'width: 10%'
        },
        { 
          label: this.$t('product.label', 1).toUpperCase(),
          field: 'product_code',
          name: 'product_code',
          align: 'left',
          style: 'width: 15%'
        },
        { 
          label: this.$t('phase.short').toUpperCase(),
          field: 'phase_alias',
          name: 'phase_alias',
          style: 'width: 15%',
          align: 'left'
        },
        { 
          label: this.$t('progress').toUpperCase(),
          field: 'progress',
          name: 'progress',
          style: 'width: 25%',
          align: 'left'
        },
        {
          field: 'issue_count',
          name: 'issue_count',
          style: 'width: 5%',
          align: 'right'
        },
        { 
          label: this.$t('quantity.completed.short').toUpperCase(),
          field: 'qt_completed',
          name: 'qt_completed',
          style: 'width: 5%',
          align: 'right'
        },
        {
          label: this.$t('quantity.planned.short').toUpperCase(),
          field: 'qt_planned',
          name: 'qt_planned',
          style: 'width: 5%',
          align: 'right'
        },
        {
          label: this.$t('production.filters.ready').toUpperCase(),
          field: 'ready',
          name: 'ready',
          style: 'width: 5%',
          align: 'right'
        },
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
        if (department_match && operator_match) {

          const filtered_jobs = a.assigned_jobs ? a.assigned_jobs.filter(this.matchJobToFilters) : []
          
          if (filtered_jobs.length) {
            const active_jobs = []
            const queued_jobs = []
            filtered_jobs.forEach( j => {
              j.active ? active_jobs.push(j) : queued_jobs.push(j)
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
      const result = [...this.filtered_assignments]
      const filtered_unassigned_jobs = this.unassigned_jobs.filter(this.matchJobToFilters).map(j => {
        return {
          ...j,
          ready: this.isReleased(j) && j.next_batch_available
        }
      })

      if (filtered_unassigned_jobs.length && this.filters.operator_key === undefined) {
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

      return result
    }
  },

  methods: {
    isReleased(item) {
      return new Date(item.start_from).getTime() <= this.now
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
            if (!value && job.on_time) match = false
            break

          case 'late':
            if (!value && !job.on_time) match = false
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
  }
}
</script>

<style lang="sass">
</style>
