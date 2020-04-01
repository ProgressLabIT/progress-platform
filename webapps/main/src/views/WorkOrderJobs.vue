<template>
  <v-container class="fill pa-0">
    <v-data-table
      :headers="headers"
      :items="phase_data"
      hide-default-footer
      disable-pagination
      class="job-list">
      <template v-slot:item="{ item }">
        <tr>
          <td 
            v-for="(header, index) in headers" :key="index"
            :class="header.value.includes('qt') ? 'text-right' : '' ">

            <template v-if="header.value === 'progress'">
              <v-row no-gutters align="center" >
                <v-col cols="9">
                  <v-progress-linear 
                    dense 
                    :value="item.progress"
                    :color="item.active ? $theme.blue : $theme.grey">
                  </v-progress-linear>
                </v-col>
                <v-col class="pl-4 text-right">
                  {{ item.progress }}%
                </v-col>
                <!-- <v-col cols="1" class="text-right pl-2">
                  <v-icon small 
                    v-if="item.critical" 
                    :color="$theme.red"
                    @click="$emit('criticalOnly')">
                    mdi-alert-octagon
                  </v-icon>
                  <v-icon small 
                    v-else-if="!item.on_time" 
                    :color="$theme.orange"
                    @click="$emit('lateOnly')">
                    mdi-alert
                  </v-icon>
                </v-col> -->
              </v-row>
            </template>

            <template v-else>
              {{ item[header.value] | capitalize_all }}
            </template>
            
          </td>
        </tr>
        
      </template>
    </v-data-table>
  </v-container>
</template>

<script>
export default {

  name: 'WorkOrderJobs',

  props: {
    wo_data: {
      type: Object,
      required: true,
    }
  },

  data () {
    return {
      headers: [
        { value: 'phase_alias', text: 'FASE'},
        { value: 'progress', text: 'AVANZAMENTO', width: '30%'},
        { value: 'qt_completed', text: 'QComp', align: 'end'},
        { value: 'qt_released', text: 'QRil', align: 'end'},
        { value: 'assigned_to', text: 'ASSEGNATO A', align: 'end'},
      ]
    }
  },

  computed: {
    phase_data() {
      return this.wo_data.phase_sequence.map( phase_id => {
        let phase_data = this.wo_data.phase_jobs[phase_id]
        let jobs = phase_data.jobs
        const total_completed = jobs.reduce( (sum, job) => sum + job.qt_completed, 0)
        const total_released = jobs.reduce( (sum, job) => sum + job.qt_released, 0 )
        const total_progress = Math.floor(
          jobs.reduce( (sum, job) => sum + job.progress, 0) / jobs.length
        )
        return {
          ...phase_data,
          phase_id,
          qt_released: total_released,
          qt_completed: total_completed,
          progress: total_progress
        }
      })
    }
  }
}
</script>

<style lang="css" scoped>
.job-list {
  background-color: transparent !important;
}

.job-list >>> td {
  border: none !important;
  /*padding: 8px 16px;*/
}

.job-list >>> th {
  border: none !important;
}

.filter-field {
  cursor: pointer;
}
</style>