<template>
  <v-container>
    <v-row dense justify="space-between" class="text-uppercase mx-0">
      <h5>codice op</h5>
      <h5>riga</h5>
    </v-row>
    <v-row dense justify="space-between" class="display highlight weight-bold mx-0">
      <h3>{{ wo_data.wo_code }}</h3>
      <h3>{{ wo_data.wo_line_no }}</h3>
    </v-row>
    <v-row dense justify="space-between" class="text-uppercase mx-0 mt-6">
      <h5>prodotto</h5>
      <h5>qt</h5>
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
      <h5 class="weight-bold text-uppercase">progresso</h5>
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
              {{ tab.text }}
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
            <span class="text-uppercase caption">{{ i.text }}</span>
            <span class="highlight weight-medium">{{ woInfoValue(i.name) }}</span>
          </v-row>
        </v-tab-item>
        <v-tab-item key="people" class="ml-n2">
          <BaseAvatarListElement 
            v-for="operator in assignments"
            :key="operator._id"
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
      views: [
        { name: 'info', text: 'INFO', align: 'start' },
        { name: 'people', text: 'PERSONE', align: 'start' },
        { name: 'equipment', text: 'MACCHINARI', align: 'end' },
      ],
      current_view: 0,
      wo_info: [
        { name: 'created', text: 'Data creazione', value: '' },
        { name: 'start', text: 'Data inizio' },
        { name: 'end', text: 'Data chiusura' },
        { name: 'due_by', text: 'Scadenza' },
        { name: 'status', text: 'Stato' },
        { name: 'processing_time', text: 'T. lavorazione' },
        { name: 'idle_time', text: 'T. attesa' },
        { name: 'queueing_time', text: 'T. coda' },
        { name: 'lead_time', text: 'T. evasione' },
      ]
    }
  },

  computed: {
    assignments() {
      let assignments = {}
      this.wo_data.jobs.forEach( j => {
        if (j.assigned_to == null) {
          if ('unassigned' in assignments) assignments.unassigned.jobs.push(j)
          else assignments.unassigned = { jobs: [j] }
        }

        else {
          const id = j.assigned_to._id
          if (id in assignments) assignments[id].jobs.push(j)
          else {
            assignments[id] = this.$store.getters.user_data(id)
            assignments[id].jobs = [j]
          }
        }
      })
      return assignments
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
          let active_text = 'Attivo'
          let inactive_text = 'In coda'
          let on_time_text = 'Puntuale'
          let late_text = 'In ritardo'
          let critical_text = 'Critico'
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
          const processing_time = this.wo_data.processing_time.actual
          return processing_time ? durationFromMillisec(processing_time, { precision: 'm'}) : '-'
        }

        case 'idle_time': {
          const processing_time = this.wo_data.processing_time.actual
          const start = DT.fromISO(this.wo_data.start)
          const end = DT.fromISO(this.wo_data.end)
          const benchmark = end ? end : DT.utc()
          return processing_time && start 
            ? durationFromMillisec(benchmark - start - processing_time
                                  , { precision: 'm' })
            : '-'
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