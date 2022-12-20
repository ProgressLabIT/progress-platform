<template>
  <div class="q-pa-lg">
    <div class="row justify-between text-uppercase low-text text-h5">
      <div>{{ $t('work_order.wo_code') }}</div>
      <div>{{ $t('work_order.wo_line.line_only') }}</div>
    </div>

    <div class="row justify-between display weight-bold text-h3">
      <div>{{ wo_data.wo_code }}</div>
      <div>{{ wo_data.wo_line }}</div>
    </div>

    <div class="row justify-between text-uppercase low-text q-mt-md text-h5">
      <div>{{ $t('product.label') }}</div>
      <div>{{ $t('quantity.short') }}</div>
    </div>

    <div class="row justify-between">
      <div class="col-9">
        <div class="text-truncate display text-h3">
          {{ wo_data.product_code}}
        </div>
        <div class="medium q-mt-xs">
          {{ wo_data.product_description }}
        </div>
        <div class="col-auto display text-h3">
          {{ wo_data.qt_planned }}
        </div>
      </div>
    </div>

    <div class="row justify-between items-end weight-bold text-uppercase q-mt-sm q-mb-xs">
      <div class="low-text text-h5">
        {{ $t('progress')}}
      </div>
      <div class="text-h3">
        {{ wo_data.progress }}%
      </div>
    </div>

    <BaseProgressBar :data="wo_data" />

  </div>
</template>

<script>
import { getPicPath } from '@/lib/media.js'
import { durationFromMillisec } from '@/lib/duration.js'
import { DateTime as DT } from 'luxon'
import BaseProgressBar from '@/components/BaseProgressBar.vue'
// import BaseAvatarListElement from '@/components/BaseAvatarListElement.vue'

export default {

  name: 'WorkOrderDataColumn',

  components: {
    BaseProgressBar
    // BaseAvatarListElement
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
          text: this.$t('info'),
          align: 'start' 
        },
        { 
          name: 'people', 
          text: this.$t('people'),
          align: 'start' 
        },
        // { name: 'equipment', text: 'MACCHINARI', align: 'end' },
      ]
    },

    wo_info() {
      return [
        { 
          name: 'due_by', 
          text: this.$t('due_by')
        },
        { 
          name: 'status', 
          text: this.$t('status')
        },
        { 
          name: 'created', 
          text: this.$t('creation_date'),
          value: '' 
        },
        { 
          name: 'start', 
          text: this.$t('start_date')
        },
        // { name: 'queueing_time', text: 'T. coda' },
        { 
          name: 'end', 
          text: this.$t('end_date')
        },
        { 
          name: 'processing_time', 
          text: this.$t('processing_time')
        },
        { 
          name: 'lead_time', 
          text: this.$t('lead_time')
        },
        { 
          name: 'processing_cost', 
          text: this.$t('processing_cost')
        },
        { 
          name: 'material_cost', 
          text: this.$t('material_cost')
        },
        { 
          name: 'total_cost', 
          text: this.$t('total_cost')
        },
      ]
    },

    assignments() {
      // handle missing data gracefully
      if (typeof this.wo_data != 'undefined') {

        let assignments = {}

        this.wo_data.jobs.forEach( j => {
          if (j.assigned_to != null) {
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
    },

    unassigned_jobs() {
      let unassigned_jobs = []
      if (typeof this.wo_data != 'undefined') {
        unassigned_jobs = this.wo_data.jobs.filter(j => j.assigned_to == null)
      }
      return unassigned_jobs
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
          let active_text = this.$t('active')
          let inactive_text = this.$t('waiting')
          let on_time_text = this.$t('on_time')
          let late_text = this.$t('late')
          let critical_text = this.$t('critical')
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
          return this.$roundFloat(this.wo_data.processing_cost || 0, 1) || '-'
        }

        case 'material_cost': {
          return this.$roundFloat(this.wo_data.material_cost || 0, 1) || '-'
        }

        case 'total_cost': {
          return this.$roundFloat(this.wo_data.total_cost || 0, 1) || '-'
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
