<template>
  <BaseDialog :show="show">
    <q-card class="q-pa-md surface2 column" style="width: 600px; height: 80vh">
      <q-card-section class="text-h3 col-auto">
        {{ $capitalize($t('work_order.qt_rebalance_title')) }}
      </q-card-section>

      <q-card-section class="scroll col">
        <div
          v-for="(phase, index) in phase_data"
          :key="phase.phase_key">
          <q-separator v-if="index != 0" class="q-my-md"/>

          <!-- PHASE HEADER -->
          <div class="row items-center justify-between">
            <div class="display highlight weight medium">
              {{ phase.phase_alias }}
            </div>
            <q-chip
              :color="phases_delta[phase.phase_key] ? 'theme-orange' : 'theme-green'">
              <span v-if="phases_delta[phase.phase_key]"
                class="solid-white weight-medium text-uppercase">
                {{ phases_delta[phase.phase_key] > 0 ? $t('increase') + ' +' : $t('decrease') }}   {{ phases_delta[phase.phase_key] }}
              </span>
              <q-icon v-else name="mdi-check" class="solid-white weight-bold" />
            </q-chip>
          </div>

          <!-- PHASE JOBS -->
          <div
            class="row items-center q-py-sm"
            v-for="job in phase.jobs"
            :key="job._key">
            <div class="col-3">
              {{ job._key }}
            </div>
            <BaseUserAvatar
              v-if="job.assigned_to"
              class="col-4"
              :user="job.assigned_to">
            </BaseUserAvatar>
            <q-space />
            <div class="col-1 text-uppercase q-mr-md">
              {{ $t('quantity.remaining.short') }}
            </div>
            <q-input
              class="col-2"
              :key="index"
              dense
              input-class="text-right"
              hide-bottom-space
              type="number"
              v-model.number="job_updates[job._key].new_remaining"
              min="0"
              :max="new_wo_qt">
            </q-input>

          </div>
        </div>
      </q-card-section>

      <q-card-actions align="between" class="col-auto">
        <q-btn color="theme-grey" @click="$emit('close')">
          {{ $t('cancel') }}
        </q-btn>
        <q-btn color="theme-blue" :loading="saving" @click="save" v-if="can_save">
          {{ $t('save') }}
        </q-btn>
      </q-card-actions>
    </q-card>
  </BaseDialog>
</template>

<script>
import BaseDialog from '@/components/BaseDialog.vue'
import BaseUserAvatar from '@/components/BaseUserAvatar.vue'

export default {

  name: 'WorkOrderJobQtRebalance',

  components: {
    BaseDialog,
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
    },
    show: {
      type: Boolean,
      default: true
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
          obj[phase.phase_key] = self.new_wo_qt - (phase.qt_completed + phase.active_batch_qt + phase_temp_remaining)
          return obj
        }, {})
        return delta_map
      }
      else return {}
    },

    can_save() {
      // Check if any delta is not zero
      return Object.values(this.phases_delta).every( delta => delta === 0 )
    }
  },

  methods: {

    save() {
      if (this.can_save) {
        this.saving = true
        const updates = Object.entries(this.job_updates).map( ([job_key, data]) => {
          const job_update =  {
            action: 'update',
            data: {
              _key: job_key,
              qt_planned: data.completed + data.active + data.new_remaining
            }
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
          new_remaining: j.qt_planned - j.qt_completed - j.active_batch_qt,
          completed: j.qt_completed,
          active: j.active_batch_qt
        }
      })
      return obj
    }, {})
  }
}
</script>

<style lang="css" scoped>
</style>
