<template>
  <v-container>
    <v-row dense justify="space-between" class="text-uppercase mx-0">
      <h5>{{ $tc('work_order.wo_code') }}</h5>
      <h5>{{ $tc('work_order.wo_line.line_only', 1) }}</h5>
    </v-row>
    <v-row dense justify="space-between" class="display highlight weight-bold mx-0">
      <h3>{{ wo_data.wo_code }}</h3>
      <h3>{{ wo_data.wo_line }}</h3>
    </v-row>
    <v-row dense justify="space-between" class="text-uppercase mx-0 mt-6">
      <h5>{{ $tc('product.label') }}</h5>
      <h5>{{ $tc('quantity.short') }}</h5>
    </v-row>
    <v-row dense justify="space-between">
      <v-col cols="9">
        <h3 class="text-truncate display highlight">{{ wo_data.product_code }}</h3>
        <p class="medium mt-1">{{ wo_data.product_description }}</p>
      </v-col>
      <v-col cols="auto">
        <h3 class="highlight display">{{ wo_data.qt_planned }}</h3>
      </v-col>
    </v-row>

    <v-row dense justify="space-between" align="end" class="mt-4 mx-0 mb-2">
      <h5 class="weight-bold text-uppercase">{{ $tc('progress') }}</h5>
      <h3 class="weight-bold text-uppercase highlight">{{ wo_data.progress}}%</h3>
    </v-row>

    <v-progress-linear
      :value="wo_data.progress"
      :color="wo_data.active ? $theme.blue : $theme.grey">
    </v-progress-linear>

    <v-row dense class="ml-0 mb-6 mt-4" justify="space-between">
      <div 
        v-for="(tab, index) in views" 
        :key="index">
        <v-hover v-slot:default="{ hover }">
          <span     
            @click="current_view = index"
            class="text-uppercase font-weight-medium caption"
            style="cursor: pointer"
            :style="hover ? 'text-decoration: underline' : ''"
            :class="current_view === index ? 'font-weight-black highlight' : ''">
              {{ tabever.text }}
          </span>
        </v-hover>
      </div>
    </v-row>
    
    <v-card class="scroll" :height="panelHeight()" flat color="transparent">
      <v-tabs-items 
        v-model="current_view" style="background:transparent;">
        <v-tab-item key="info">
          <v-row 
            v-for="i in wo_info" 
            :key="i.name" 
            justify="space-between"
            align="end"
            class="mx-0 mb-2">
            <span class="text-uppercase caption">
              {{ i.text }}
            </span>
            <span class="highlight weight-medium">
              {{ woInfoValue(i.name) | capitalize }}
            </span>
          </v-row>
        </v-tab-item>
        <v-tab-item key="people" class="ml-n2">
          <BaseAvatarListElement 
            v-for="operator in assignments"
            :key="operator._key"
            :src="getPicPath(operator)"
            :title="operator.name + ' ' + operator.surname"
            :subtitle="getAssignedPhases(operator) | capitalize_all">
          </BaseAvatarListElement>
        </v-tab-item>
      </v-tabs-items>
    </v-card>
  </v-container>
</template>

<script>
import { getPicPath } from '@/lib/media.js'
import { durationFromMillisec } from '@/lib/duration.js'
import { DateTime as DT } from 'luxon'

import BaseAvatarListElement from '@/components/BaseAvatarListElement.vue'
import { roundFloat } from '@/lib/filters.js'

export default {

  name: 'WorkOrderDataColumn',

  components: {
    BaseAvatarListElement
  },

  props: {
    wo_data: {
      type: Object,
      required: true,
    },
  },

  data () {
    return {
      current_view: 0,
    }
  },

  computed: {

    views() {
      return [
        { 
          name: 'info', 
          text: this.$tc('info'), 
          align: 'start' 
        },
        { 
          name: 'people', 
          text: this.$tc('people'), 
          align: 'start' 
        },
        // { name: 'equipment', text: 'MACCHINARI', align: 'end' },
      ]
    },

    wo_info() {
      return [
        { 
          name: 'due_by', 
          text: this.$tc('due_by') 
        },
        { 
          name: 'status', 
          text: this.$tc('status')
        },
        { 
          name: 'created', 
          text: this.$tc('creation_date'), 
          value: '' 
        },
        { 
          name: 'start', 
          text: this.$tc('start_date')
        },
        // { name: 'queueing_time', text: 'T. coda' },
        { 
          name: 'end', 
          text: this.$tc('end_date') 
        },
        { 
          name: 'processing_time', 
          text: this.$tc('processing_time')
        },
        { 
          name: 'lead_time', 
          text: this.$tc('lead_time')
        },
        { 
          name: 'processing_cost', 
          text: this.$tc('processing_cost') 
        },
        { 
          name: 'material_cost', 
          text: this.$tc('material_cost')
        },
        { 
          name: 'total_cost', 
          text: this.$tc('total_cost')
        },
      ]
    },

    assignments() {
      if (typeof this.wo_data != 'undefined') {
        let assignments = {}
        this.wo_data.jobs.forEach( j => {
          if (j.assigned_to == null) {
            if ('unassigned' in assignments) assignments.unassigned.jobs.push(j)
            else assignments.unassigned = { jobs: [j] }
          }

          else {
            const key = j.assigned_to._key
            if (key in assignments) assignments[key].jobs.push(j)
            else {
              assignments[key] = this.$store.getters.user_data(key)
              assignments[key].jobs = [j]
            }
          }
        })
        return assignments
      }
      else return {}
    }
  },

  methods: {

    woInfoValue(info_name) {
      function formatDate(timestamp) {
        if (timestamp) {
          return DT.fromISO(timestamp)
                  .setLocale('it').toLocaleString({ 
                    weekday: 'short', 
                    month: 'short', 
                    day: 'numeric'
                  })
        }
        else return '-'
      }

      switch (info_name) {
        case 'status': {
          let active_text = this.$tc('active')
          let inactive_text = this.$tc('waiting')
          let on_time_text = this.$tc('on_time')
          let late_text = this.$tc('late')
          let critical_text = this.$tc('critical')
          let active = this.wo_data.active ? active_text : inactive_text

          let state = ''
         
          if (this.wo_data.critical) state = critical_text
          else if (!this.wo_data.on_time) state = late_text
          else state = on_time_text

          return active + ' - ' + state
        }

        case 'created':
        case 'start':
        case 'end':
        case 'due_by':
          return formatDate(this.wo_data[info_name])
               

        case 'processing_time': {
          const processing_time = this.wo_data.processing_time
          return processing_time ? durationFromMillisec(processing_time, { precision: 's'}) : '-'
        }

        case 'queueing_time': {
          const created = DT.fromISO(this.wo_data.created)
          const start = DT.fromISO(this.wo_data.start)
          const benchmark = start ? start : DT.utc()
          return this.wo_data.start 
            ? durationFromMillisec(benchmark - created, {precision: 'h'})
            : '-'
        }

        case 'lead_time': {
          const created = DT.fromISO(this.wo_data.created)
          const end = DT.fromISO(this.wo_data.end)
          return this.wo_data.end 
            ? durationFromMillisec(end - created, {precision: 'h'}) 
            : '-'
        }

        case 'processing_cost': {
          return roundFloat(this.wo_data.processing_cost || 0, 1) || '-'
        }

        case 'material_cost': {
          return roundFloat(this.wo_data.material_cost || 0, 1) || '-'
        }

        case 'total_cost': {
          return roundFloat(this.wo_data.total_cost || 0, 1) || '-'
        }

      }
    },

    getPicPath(operator) {
      return getPicPath(operator)
    },

    getAssignedPhases(operator) {
      let phase_list = operator.jobs.map( j => j.phase_alias)
      return phase_list.join(' / ')
    },

    panelHeight() {
      let height = document.body.clientHeight - 360
      return height + 'px'
    }
  }
}
</script>

<style lang="css" scoped>
</style>