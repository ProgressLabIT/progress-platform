<template>
  <v-container class="fill pa-0 ">
    
    <!-- DEPARTMENT TABS -->
<!--     <v-row class="flex-grow-0">
      <v-tabs
        background-color="transparent"
        v-model="active_dep"
        :color="$theme.whitehigh"
        hide-slider
        class="flex-shrink-1 flex-grow-0 pl-2">
        <v-tab 
          v-for="dep in department_list"
          :key="dep.code"
          class="display">
          <span v-if="dep.code">{{ dep.code + ':' }}</span>
          {{ dep.name }}
        </v-tab>
      </v-tabs>
    </v-row> -->    

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
                {{ o.operator.name + ' ' + o.operator.surname }}
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
            no-data-text="Nessun lavoro assegnato"
            class="assignment-list mt-4 ml-n3"
            >  
            <template v-slot:item="{ item: job }">
              <tr @dblclick="showWorkOrderScreen(job.wo_id)">
                <!-- <v-hover v-slot:default="{ hover }"> -->
                  <td 
                    v-for="(header, index) in job_data" 
                    :key="index"
                    :class="header.value.includes('qt') ? 'text-right' : ''"
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
        department: '' 
      }}
    }
  },

  data () {
    return {
      job_data: [
        { text: 'OP', value: 'wo_code', },
        { text: 'RIGA', value: 'wo_line_no', },
        { text: 'PRODOTTO', value: 'product_code', },
        { text: 'FASE', value: 'phase_alias', },
        { text: 'PROGRESSO', value: 'progress', width: '30%'},
        { text: 'QComp', value: 'qt_completed', align: 'end'},
        { text: 'QRil', value: 'qt_released', align: 'end' },
        { text: 'QTot', value: 'qt_planned', align: 'end' },
      ],
      search_fields: [
        'wo_code', 
        'wo_line_no', 
        'product_code',
        'product_description',
        'phase_alias',
      ],
      filter_fields: ['wo_code', 'product_code', 'phase_alias']
    }
  },

  computed: {

    assignments() {
      return this.$store.state.job.assigned_job_list
    },

    filtered_assignments() {

      let list = []
      // return this.assignments.map( a => {
      for (let i = 0; i < this.assignments.length; i++) {
        let a = this.assignments[i]
        // Check if operator is in department selected or no department filter is set
        if ([a.operator.department_id, ''].includes(this.filters.department)) {

          const filtered_jobs = a.assigned_jobs.filter(this.matchJobToFilters)
          
          if (filtered_jobs.length) {
            const operator_filtered_assignments = {
              operator: a.operator,
              assigned_jobs_count: a.assigned_jobs.length,
              filtered_jobs: filtered_jobs.sort(this.sortActiveJobFirst)
            }
            list.push(operator_filtered_assignments)
          }
        }
      }

      return list
    },

    // operators_to_show() {
    //   return this.filtered_assignments
    //     .filter( operator => operator.filtered_jobs.length > 0 )
    // },

    // operators_to_hide() {
    //   return this.filtered_assignments
    //     .filter( operator => operator.filtered_jobs.length == 0 )
    //     .map( o => o.operator._id )
    // },

    unassigned_jobs() {
      return this.$store.state.job.unassigned_job_list
    },

    jobs_view() {
      return [
        ...this.filtered_assignments, 
        {
          operator: {
            _id: 'unassigned',
            name: 'Lavori',
            surname: 'non assegnati'
          },
          assigned_jobs: this.unassigned_jobs,
          filtered_jobs: this.unassigned_jobs.filter(this.matchJobToFilters)
        }
      ]
    }
  },

  methods: {

    // checkDepartment(dep_id) {
    //   // Return true if filter is not set or equal to the department checked
    //   return [dep_id, ''].includes(this.filters.department_id)
    //     ? true
    //     : false
    // },

    matchJobToFilters(job) {
      return matchJobToFilters(job, this.filters, this.search_fields)
    },

    sortActiveJobFirst(job1, job2) {
      if (!job1.active && job2.active) return 1
      else return -1
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

    showWorkOrderScreen(wo_id) {
      let data_to_emit = {
        wo_key: wo_id.split('/')[1],
        back_to_route_name: this.$route.name
      }
      console.log({data_to_emit})
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