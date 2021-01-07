<template>
  <v-dialog 
    value="true"
    max-width="600px"
    persistent no-click-animation>
    <v-card scrollable>

      <v-card-title>
        {{ $tc('work_order.qt_rebalance_title') | capitalize }}
      </v-card-title>

      <v-card-text class="mt-6">
        <div v-for="(phase, index) in phase_data" :key="phase.phase_key">
          <v-divider v-if="index != 0"></v-divider>

          <!-- Phase header -->
          <v-row class="mx-0" justify="space-between" align="center">
            <span class="display highlight font-weight-medium text-uppercase">{{phase.phase_alias}}</span>
            <v-chip small :color="phases_delta[phase.phase_key] ? $theme.orange :  $theme.green">
              <!-- delta to allocate in orange or check in green if delta == 0 -->
              <span 
                v-if="phases_delta[phase.phase_key]"
                class="solid-white font-weight-medium text-uppercase">
                {{ phases_delta[phase.phase_key] > 0 ? $tc('increase') + "  +" : $tc('decrease') }}  {{ phases_delta[phase.phase_key] }}
              </span>
              <v-icon class="solid-white weight-bold" v-else>mdi-check</v-icon>
            </v-chip>
          </v-row>

          <!-- Phase jobs -->
          <v-row v-for="job in phase.jobs" :key="job._key">
            <v-col cols="3">
              {{ job._key }}
            </v-col>
            <v-col cols="4" offset="1">
              <BaseUserAvatar :user="job.assigned_to"/>
            </v-col>
            <v-col cols="3" offset="1">
              <v-text-field
                class="ma-0 pa-0"
                :key="index"
                reverse
                single-line
                hide-details
                type="number"
                v-model.number="job_updates[job._key].new_remaining"
                min="0"
                :max="new_wo_qt">
              </v-text-field>
            </v-col>


          </v-row>


        </div>
      </v-card-text>

      <v-card-actions>
        <v-btn 
          :color="$theme.grey" 
          @click="$emit('close')">
          {{ $tc('cancel') }}
        </v-btn>
        <v-btn 
          :color="$theme.blue" 
          :loading="saving"
          @click="save">
          {{ $tc('save') }}
        </v-btn>
      </v-card-actions>

    </v-card>
  </v-dialog>
</template>

<script>
import BaseUserAvatar from '@/components/BaseUserAvatar'

export default {

  name: 'WorkOrderJobQtRebalance',

  components: {
    BaseUserAvatar
  },

  props: {
    phase_data: {
      type: Array,
      required: true
    },
    new_wo_qt: {
      type: Number,
      required: true
    },
    wo_key: {
      type: String,
      required: true
    }
  },

  data () {
    return {
      phase_index: 0,
      job_updates: {}, // job_key => qt
      saving: false
    }
  },

  computed: {
    // phases_to_rebalance() {
    //   return this.phase_data.filter( p => p.jobs.length > 1 )
    // },

    phases_delta() {
      if (this.job_updates != {}) {
        const self = this
        const delta_map = this.phase_data.reduce( (obj, phase) => {
          const phase_temp_remaining = phase.jobs.reduce( (sum, job) => sum + self.job_updates[job._key].new_remaining, 0)
          obj[phase.phase_key] = self.new_wo_qt - (phase.qt_completed + phase_temp_remaining)
          return obj
        }, {})
        return delta_map
      }
      else return {}
    },

    can_save() {
      // Check if any delta is not zero
      const any_phase_has_delta = Object.entries(this.phases_delta).some( (phase_entry) => phase_entry.delta )
      return !any_phase_has_delta
    }
  },

  methods: {

    save() {
      if (this.can_save) {
        this.saving = true
        const updates = Object.entries(this.job_updates).map( ([job_key, data]) => {
          const job_update =  {
            action: 'update',
            data: { _key: job_key, qt_planned: data.completed + data.new_remaining }
          }
          return job_update
        })
        // dispatch wo and job updates
        this.$store.dispatch('updateWorkOrder', {
          wo_key: this.wo_key,
          new_qt: this.new_wo_qt,
          job_updates: updates
        })
        .then(() => {
          this.saving = false
          this.$emit('close')
        })
        .catch( err => window.alert(err) )
      }
      else window.alert(this.$tc('work_order.alerts.assign_workload_first'))
    }
  },

  created() {
    this.job_updates = this.phase_data.reduce( (obj, phase) => {
      phase.jobs.forEach( j => {
        obj[j._key] = {
          new_remaining: j.qt_planned - j.qt_completed,
          completed: j.qt_completed
        }
      })
      return obj
    }, {})
  }
}
</script>

<style lang="css" scoped>
</style>