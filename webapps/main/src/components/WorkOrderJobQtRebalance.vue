<template>
  <BaseDialog :show="show">
    <q-card class="q-pa-md surface2 column" style="min-width: 600px; height: 80vh">
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
            v-for="job_update in job_updates[phase.phase_key]"
            :key="job_update._key">
            <div class="col-3">
              {{ job_update._key }}
            </div>
            <div class="col-auto">
              <BaseUserAvatar
                v-if="job_update.assigned_to"
                :user="job_update.assigned_to">
              </BaseUserAvatar>
            </div>
            <q-space />
            <template v-if="job_update._key != 'NA'">
              <div class="col-auto text-uppercase q-mr-md">
                {{ $t('quantity.remaining.short') }}
              </div>
              <q-input
                class="col-2"
                :key="index"
                dense
                input-class="text-right"
                hide-bottom-space
                type="number"
                v-model.number="job_update.new_remaining"
                min="0"
                :max="new_wo_qt">
              </q-input>
            </template>

          </div>
        </div>
      </q-card-section>

      <q-card-actions align="between">
        <q-btn
          color="theme-grey"
          @click="$emit('close')"
          :label="$t('cancel')">
        </q-btn>
        <q-btn
          color="theme-orange"
          @click="spreadRemaining"
          :label="$t('job.rebalance.spread')">
        </q-btn>
        <q-space />
        <q-btn
          v-if="can_save"
          color="theme-blue"
          :loading="saving"
          @click="save"
          :label="$t('save')">
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
      job_updates: {}, // job_key => qt
      saving: false
    }
  },

  computed: {
    phases_delta() {
      const deltas = {}
      this.phase_data.forEach(phase => {
        const phase_new_remaining = this.new_wo_qt - phase.qt_completed - phase.active_batch_qt
        const current_remaining = this.job_updates[phase.phase_key].reduce((sum, job) => sum + job.new_remaining, 0)
        deltas[phase.phase_key] = phase_new_remaining - current_remaining
      })
      return deltas
    },

    can_save() {
      // Check if any delta is not zero
      return Object.values(this.phases_delta).every(delta => delta === 0)
    }
  },

  methods: {
    spreadRemaining() {
      Object.entries(this.job_updates).forEach(([phase_key, phase_jobs]) => {
        const delta = this.phases_delta[phase_key]
        let remainder = delta % phase_jobs.length
        const base_job_variation = (delta - remainder) / phase_jobs.length

        phase_jobs.forEach(j => {
          const current_remaining = j.new_remaining
          let new_remaining = current_remaining + base_job_variation
          if (remainder) {
            new_remaining += Math.sign(delta) // handle both increase and decrease of quantity
            remainder -= Math.sign(remainder)
          }
          j.new_remaining = new_remaining
        })
      })
    },

    async save() {
      if (!this.can_save) {
        window.alert(this.$t('work_order.alerts.assign_workload_first'))
        return
      }

      this.saving = true

      // Job update data is in an object divided by phase. First get a full, flat list
      const flat_list = Object.values(this.job_updates).flat()

      // Then build the data to be sent to the backend
      const job_updates = []
      flat_list.forEach(data => {
        if (data._key == 'NA') {
          return
        }

        if (data._key == 'NEW') {
          job_updates.push({
            action: 'insert',
            data: {
              phase_key: data.phase_key,
              qt_planned: data.new_remaining
            }
          })
        } else {
          job_updates.push({
            action: 'update',
            data: {
              _key: data._key,
              qt_planned: data.qt_completed + data.active_batch_qt + data.new_remaining
            }
          })
        }
      })

      try {
        await this.$store.dispatch('updateWorkOrderQuantities', {
          wo_key: this.wo_key,
          new_quantity: this.new_wo_qt,
          job_updates
        })
        await this.$store.dispatch('loadWorkOrderData', this.wo_key)
        this.saving = false
        this.$emit('close')
      } catch (error) {
        console.error(error)
        // TODO: Add better error handling
        window.alert(error)
      }
    }
  },

  created() {
    /*
    for each phase
      check remaining quantity
      if any
        get open jobs
      else (if increase)
        add new job
    */
    this.job_updates = this.phase_data.reduce((obj, phase) => {
      obj[phase.phase_key] = []
      const delta = this.new_wo_qt - (phase.qt_completed + phase.qt_remaining)

      if (phase.qt_remaining) {
        const open_jobs = phase.jobs.filter(j => j.stage != 'closed')
        open_jobs.forEach(j => {
          obj[phase.phase_key].push({ ...j, new_remaining: j.qt_planned - j.qt_completed - j.active_batch_qt })
        })
      }

      else {
        const job_data = (delta > 0
          ? { _key: 'NEW', phase_key: phase.phase_key, qt_completed: 0, active_batch_qt: 0, new_remaining: delta }
          : { _key: 'NA', new_remaining: 0 }
        )

        obj[phase.phase_key].push(job_data)
      }

      return obj
    }, {})
  }
}
</script>

<style lang="css" scoped>
</style>
