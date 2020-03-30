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
      <v-container v-for="o in assignments" :key="o.operator._id">
        <v-row justify="start" align="center" no-gutters class="mt-2">
          <v-col cols="12">
          
          <v-avatar size="36">
            <v-img :src="getPicPath(o.operator)">
              <template v-slot:placeholder>
                <v-icon x-large>mdi-account-circle</v-icon>
              </template>
            </v-img>
          </v-avatar>
          <span class="ml-4 solid-white weight-medium medium">
            {{ o.operator.name + ' ' + o.operator.surname }}
          </span>
          </v-col>
        </v-row>        

        <v-data-table 
          :items="o.assigned_jobs"
          :headers="job_data"
          hide-default-footer
          dense
          no-data-text="Nessun lavoro assegnato"
          class="assignment-list mt-4 ml-n3"
          >  
          <template v-slot:item="{ item: job }">
            <tr v-if="matchJobToFilters(job)">
              <td 
                v-for="(header, index) in job_data" 
                :key="index"
                :class="header.value.includes('qt') ? 'text-right' : ''">
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

                <template v-else>{{ job[header.value] | capitalize_all }}</template>

              </td>
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
        "search_string":"",
        "started":true,
        "queued":true,
        "on_time":true,
        "late":true,
        "active":true,
        "idle":true,
        "critical":true,
        "not_critical":true
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
      ]
    }
  },

  computed: {
    // department_list() {
    //   return [
    //     { name: 'tutti'}, 
    //     ...this.$store.state.org.departments,
    //     { name: 'non assegnati'} 
    //   ]
    // },
    
    // active_dep: {
    //   get() {
    //     let dep = this.$store.state.job.nav_state.active_dep
    //     return dep ? dep : 0
    //   },
    //   set(dep_code) {
    //     this.$store.commit('UPDATE_JOB_DEP_NAV_STATE', dep_code)
    //   }
    // }
    // operator_list() {
    //   return this.$store.getters.operator_list()
    // },

    assignments() {
      return this.$store.state.job.assigned_job_list
    },

    unassigned_jobs() {
      return this.$store.state.job.unassigned_job_list
    },

    // job_list() {
    //   return this.$store.state.job.job_list
    // },

    // job_map() {
    //   return this.job_list.reduce((result, job) => {
    //     result[job._id] = job
    //     return result
    //   }, {})
    // },

    // job_list_by_operator() {
    //   return this.operator_list.reduce( (obj, operator) => {
    //     let operator_jobs = this.getOperatorJobs(operator._id)
    //     obj[operator._id] = operator_jobs
    //   }, {})
    // },

    // jobs_by_operator() {
    //   let map = {}

    //   for (const a of this.assignment_list) {
    //     const job_data = this.job_map[a._from]
    //     if (matchJobToFilters(job_data, this.filters, this.search_fields)) {
    //       if (a._to in map) map[a._to].push(job_data)
    //       else map[a._to] = [job_data]
    //     } 
    //     else {
    //       continue
    //     }
    //   }
    //   return map
    // }
  },

  methods: {
    // getOperatorJobs(operator_id) {
    //   return this.assignment_list
    //     .filter( a => a._to === operator_id )
    //     .map( a => this.filtered_job_list[a._from])
    // },

    matchJobToFilters(job) {
      return matchJobToFilters(job, this.filters, this.search_fields)
    },

    getPicPath(operator) {
      let user_pic_folder = '/media/user/'
      let filename = (operator.name + operator.surname).replace(/\s+/,'').toLowerCase()
      return user_pic_folder + filename + '.jpg'
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

</style>