<template>
  <v-container class="fill pa-0 ">  

    <div class="flex-grow-1 scroll">
      <v-container 
        v-for="(o, index) in jobs_view" 
        :key="index">
          <v-row 
            justify="start" 
            align="center" 
            no-gutters 
            class="mt-2">
            <v-col cols="auto">
              <v-avatar size="36">
                <v-img eager :src="getPicPath(o.operator)">
                  <template v-slot:placeholder>
                    <v-icon x-large>mdi-account-circle</v-icon>
                  </template>
                </v-img>
              </v-avatar>
              <span class="ml-4 solid-white weight-medium medium">
                {{ o.operator.name + ' ' + o.operator.surname | capitalize_all }}
              </span>
            </v-col>
            <v-spacer></v-spacer>
            <v-col cols="auto">
              <v-chip small>
                <span class="weight-medium solid-white mr-1">{{ o.filtered_jobs.length }}</span>
                di 
                <span class="weight-medium solid-white ml-1">{{ o.assigned_jobs_count }}</span>
              </v-chip>
            </v-col>
          </v-row>        

          <v-data-table 
            :items="o.filtered_jobs"
            :headers="job_data"
            hide-default-footer
            dense
            disable-pagination
            :no-data-text="$tc('job.no_job_assigned') | capitalize"
            class="assignment-list mt-4 ml-n3"
            >  
            <template v-slot:item="{ item: job }">
              <tr @dblclick="showWorkOrderScreen(job.wo_key)">
                <!-- <v-hover v-slot:default="{ hover }"> -->
                  <td 
                    v-for="(header, index) in job_data" 
                    :key="index"
                    :class="header.value.includes('qt') ? 'text-right' : ''"
                    class="text-uppercase"
                    @click="setSearch(header.value, job[header.value])">
                    <template v-if="header.value ==='progress'">
                      <v-row no-gutters align="center">
                        <v-col cols="9">
                          <v-progress-linear 
                            dense 
                            :value="job.progress"
                            :color="job.active ? $theme.blue : $theme.grey">
                          </v-progress-linear>
                        </v-col>
                        <v-col cols="2" class="pl-4 text-right">
                          {{ job.progress }}%
                        </v-col>
                        <v-col cols="1" class="text-right pl-2">
                          <v-icon small 
                            v-if="job.critical" 
                            :color="$theme.red"
                            @click="$emit('criticalOnly')">
                            mdi-alert-octagon
                          </v-icon>
                          <v-icon small 
                            v-else-if="!job.on_time" 
                            :color="$theme.orange"
                            @click="$emit('lateOnly')">
                            mdi-alert
                          </v-icon>
                        </v-col>
                      </v-row>
                    </template>

                    <template v-else>
                      <v-hover v-slot:default="{ hover }">
                      <div 
                        :class="filter_fields.includes(header.value) ? 'filter-field' : ''"
                        :style="filter_fields.includes(header.value) && hover ? 'text-decoration: underline' : ''"
                        >
                        {{ job[header.value] | capitalize_all }}
                      </div>
                      </v-hover>
                    </template>

                  </td>
                <!-- </v-hover> -->
              </tr>
            </template>
          </v-data-table>
          <v-divider class="mt-4"></v-divider>
      </v-container>
    </div>
  </v-container>

</template>

<script>
// import filterJobs from '@/lib/ProductionFilters.js'
import matchJobToFilters from '@/lib/ProductionFilters.js'

export default {

  name: 'JobList',

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
        department: undefined 
      }}
    }
  },

  data () {
    return {
      search_fields: [
        'wo_code', 
        'wo_line', 
        'product_code',
        'product_description',
        'phase_alias',
      ],
      filter_fields: ['wo_code', 'product_code', 'phase_alias']
    }
  },

  computed: {

    job_data() {
      return [
        { 
          text: this.$tc('work_order.wo_code').toUpperCase(), 
          value: 'wo_code', 
        },
        { 
          text: this.$tc('work_order.wo_line.line_only', 1).toUpperCase(), 
          value: 'wo_line', 
        },
        { 
          text: this.$tc('product.label', 1).toUpperCase(), 
          value: 'product_code', 
        },
        { 
          text: this.$tc('phase.short').toUpperCase(), 
          value: 'phase_alias', 
        },
        { 
          text: this.$tc('progress').toUpperCase(), 
          value: 'progress', 
          width: '30%'
        },
        { 
          text: this.$tc('quantity.completed.short').toUpperCase(), 
          value: 'qt_completed', 
          align: 'end'
        },
        // { text: this.$tc('job_list.job_data.qt_released'), value: 'qt_released', align: 'end' },
        { 
          text: this.$tc('quantity.planned.short').toUpperCase(), 
          value: 'qt_planned', 
          align: 'end' 
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
        // Check if operator is in department selected or no department filter is set
        if ([a.operator.department_key, undefined].includes(this.filters.department)) {

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
      const filtered_unassigned_jobs = this.unassigned_jobs.filter(this.matchJobToFilters)

      if (filtered_unassigned_jobs.length) {
        result.push({
          operator: {
            _key: 'unassigned',
            name: this.$tc("job.unassigned_jobs"),
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

    matchJobToFilters(job) {
      return matchJobToFilters(job, this.filters, this.search_fields)
    },

    getPicPath(operator) {
      let user_pic_folder = '/media/user/'
      let filename = (operator.name + operator.surname).replace(/\s+/,'').toLowerCase()
      return user_pic_folder + filename + '.jpg'
    },

    setSearch(field, text) {
      if (this.filter_fields.includes(field)) {
        this.$emit('setSearch', text)
      }
    },

    showWorkOrderScreen(wo_key) {
      let data_to_emit = {
        wo_key,
        back_to_route_name: this.$route.name
      }
      this.$emit('itemDblClick', data_to_emit)
    }
  }
}
</script>

<style lang="css" scoped>
.assignment-list {
  background-color: transparent !important;
}

.assignment-list >>> td {
  border: none !important;
  padding: 8px 16px;
}

.assignment-list >>> th {
  border: none !important;
}

.filter-field {
  cursor: pointer;
}

</style>