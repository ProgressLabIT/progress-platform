<template>
  <div class="q-px-lg q-py-md full-height column">

    <!-- COLUMN HEADER -->
    <div class="text-uppercase low-text text-h5 q-mb-xs">{{ $t('work_order.wo_code') }}</div>
    <div class="full-width display weight-bold text-h3 ellipsis">{{ wo_data.wo_code }}</div>

    <div class="text-uppercase low-text text-h5 q-mb-xs q-mt-lg">{{ $t('project') }}</div>
    <div class="full-width display weight-bold text-h3 ellipsis">{{ wo_data.project_code }}</div>

    <div class="row justify-between text-uppercase low-text q-mt-lg text-h5">
      <div>{{ $t('product.label') }}</div>
      <div>{{ $t('quantity.short') }}</div>
    </div>

    <div class="row justify-between q-mt-xs">
      <div class="col-9">
        <div class="text-truncate display text-h3">
          {{ wo_data.product_code}}
        </div>
        <div class="medium q-mt-xs">
          {{ wo_data.product_description }}
        </div>
      </div>
      <div class="col-auto display text-h3">
        {{ wo_data.qt_planned }}
      </div>
    </div>

    <div class="row justify-between items-end weight-bold text-uppercase q-mt-md q-mb-xs">
      <div class="low-text text-h5">
        {{ $t('progress') }}
      </div>
      <div class="text-h3">
        {{ wo_data.progress }}%
      </div>
    </div>

    <BaseProgressBar :data="wo_data" class="q-mt-sm"/>


    <!-- INFO PANELS -->
    <div id="panels" class="row q-mt-lg justify-between text-h6 text-uppercase">
      <div
        v-for="tab in views"
        @click="current_view = tab.name"
        style="cursor: pointer"
        :key="tab.name"
        :class="current_view === tab.name ? 'weight-bold' : 'low-text'">
        {{ tab.text }}
      </div>
    </div>

    <q-tab-panels v-model="current_view" animated class="transparent q-mt-lg col column">

      <!-- WORK ORDER DETAILS -->
      <q-tab-panel name="info" class="q-pa-none col">
        <div
          v-for="i in wo_info"
          :key="i.name"
          class="row justify-between items-end q-mb-sm text-high">
          <div class="text-uppercase text-caption">
            {{ i.text }}
          </div>
          <div class="weight-medium text-body1 relative-position">
            <q-icon
              v-if="isLate(wo_data.due_by) && i.name == 'due_by' && wo_data.status != 'closed'"
              class="q-mb-xs q-mr-xs"
              name="mdi-alert-octagon"
              color="theme-red">
            </q-icon>
            {{ $capitalize(woInfoValue(i.name)) }}
          </div>
        </div>
      </q-tab-panel>

      <!-- ASSIGNMENTS -->
      <q-tab-panel name="people" class="q-pa-none column col">
        <div class="col-11 scroll">
          <BaseUserAvatar
            v-for="operator in assignments"
            :key="operator._key"
            :user="operator"
            name_class="highlight text-body1"
            subtitle_class="low-text"
            class="q-mb-md q-py-xs"
            size="40px">
            <template #subtitle>
              <div class="text-low">
                {{ $capitalizeAll(getAssignedPhases(operator)) }}
              </div>
            </template>
          </BaseUserAvatar>
        </div>

        <q-space />

        <div class="col-auto text-uppercase text-caption">
          {{ $t('job.unassigned_jobs') }}: {{ unassigned_jobs.length }}
        </div>
      </q-tab-panel>

    </q-tab-panels>

    <!-- ACTIONS -->
    <q-btn
      v-if="wo_data.status != 'closed'"
      outline square
      class="full-width q-mt-md"
      color="theme-blue"
      :loading="saving"
      :label="$t('update')">
      <q-menu fit :style="`background-color: ${$theme.surface2}`">
        <q-list class="text-uppercase capitalize text-body2">
          <q-item
            clickable
            v-close-popup
            v-if="!wo_data.active"
            @click="edit_project = true">
            <q-item-section>
              {{ $t('project_update') }}
            </q-item-section>
          </q-item>
          <q-item clickable v-close-popup @click="edit_qt = true">
            <q-item-section>
              {{ $t('quantity.update') }}
            </q-item-section>
          </q-item>
          <q-item clickable v-close-popup @click="editDate('start_from')">
            <q-item-section>
              {{ $t('work_order.update_from_date') }}
            </q-item-section>
          </q-item>
          <q-item clickable v-close-popup @click="editDate('due_by')">
            <q-item-section>
              {{ $t('work_order.update_due_date') }}
            </q-item-section>
          </q-item>
          <q-item
            clickable
            v-close-popup
            class="text-theme-red"
            v-if="wo_data.status == 'created'"
            @click="delete_stage = 'confirm'">
            <q-item-section>
              {{ $t('work_order.delete_action') }}
            </q-item-section>
          </q-item>
        </q-list>
      </q-menu>
    </q-btn>

    <!-- EDIT PROJECT DIALOG -->
    <BaseDialog :show="edit_project" @close="closeEditDialogs">
      <q-card class="surface2 q-pa-md" style="width: 500px">
        <q-card-section>
          <div class="text-h4 display highlight text-uppercase">
            {{ $t('project') }}
          </div>
          <q-input
            autofocus
            class="q-mt-md"
            input-class="text-body1 text-uppercase"
            hide-bottom-space
            v-model="temp_project_code">
          </q-input>
        </q-card-section>
        <q-card-actions align="between">
          <q-btn
            size="12px"
            flat
            color="theme-grey"
            @click="closeEditDialogs">
            {{ $t('cancel') }}
          </q-btn>
          <q-btn
            size="12px"
            flat
            v-if="temp_project_code != wo_data.project_code"
            color="theme-blue"
            @click="saveWorkOrderUpdate">
            {{ $t('save') }}
          </q-btn>
        </q-card-actions>
      </q-card>
    </BaseDialog>

    <!-- EDIT QUANTITY DIALOG -->
    <BaseDialog :show="edit_qt" @close="closeEditDialogs">
      <q-card class="surface2 q-pa-md" style="width: 300px">
        <q-card-section>
          <div class="text-h4 display highlight text-uppercase">
            {{ $t('work_order.new_quantity') }}
          </div>
          <q-input
            autofocus
            class="q-mt-md"
            input-class="text-body1"
            hide-bottom-space
            type="number"
            :min="min_allowable_wo_qt"
            v-model.number="new_qt">
          </q-input>
        </q-card-section>
        <q-card-actions align="between">
          <q-btn
            size="12px"
            flat
            color="theme-grey"
            @click="closeEditDialogs">
            {{ $t('cancel') }}
          </q-btn>
          <q-btn
            size="12px"
            flat
            v-if="new_qt != wo_data.qt_planned"
            color="theme-blue"
            @click="show_job_qt_rebalance = true">
            {{ $t('save') }}
          </q-btn>
        </q-card-actions>
      </q-card>
    </BaseDialog>

    <WorkOrderJobQtRebalance
      v-if="show_job_qt_rebalance"
      :new_wo_qt="new_qt"
      :phase_data="phase_data"
      :wo_key="wo_data._key"
      @close="closeEditDialogs">
    </WorkOrderJobQtRebalance>

    <!-- EDIT DATES DIALOG -->
    <BaseDialog
      :show="edit_date != null"
      @close="closeEditDialogs">
      <q-card class="surface2">
        <q-date
          minimal
          v-model="temp_date"
          mask="YYYY-MM-DD">
        </q-date>
        <div class="row justify-between q-pa-sm">
          <q-btn flat
            size="12px"
            color="theme-grey"
            @click="closeEditDialogs">
            {{ $t('cancel') }}
          </q-btn>
          <q-btn
            flat
            size="12px"
            color="theme-blue"
            @click="saveWorkOrderUpdate">
            {{ $t('save') }}
          </q-btn>
        </div>
      </q-card>
    </BaseDialog>

    <BaseDialog :show="!!delete_stage" @close="closeEditDialogs">
      <q-card class="surface2 q-pa-md" style="width: 300px">
        <transition name="slide-fade" mode="out-in">
          <q-card-section
            v-if="delete_stage==='confirm'"
            key="confirm"
            align="between">
            <div class="text-h4 q-mb-lg">
              {{ $t('work_order.delete_question') }}
            </div>
            <div class="row justify-between">
              <q-btn
                color="theme-red"
                :label="$t('delete')"
                @click="deleteWorkOrder">
              </q-btn>
              <q-btn
                color="theme-grey"
                :label="$t('cancel')"
                @click="closeEditDialogs">
              </q-btn>
            </div>
          </q-card-section>

          <q-card-section
            v-else-if="delete_stage==='success'"
            key="success">
            <div class="text-h4 q-mb-md">
              {{ $t('work_order.delete_success') }}
            </div>
            <q-btn
              class="full-width"
              color="theme-grey"
              :label="$t('close')"
              @click="$router.back()">
            </q-btn>
          </q-card-section>
        </transition>
      </q-card>
    </BaseDialog>

  </div>
</template>

<script>
import { getPicPath } from '@/lib/media.js'
import { durationFromMillisec } from '@/lib/duration.js'
import { DateTime as DT } from 'luxon'
import BaseDialog from '@/components/BaseDialog.vue'
import WorkOrderJobQtRebalance from '@/components/WorkOrderJobQtRebalance.vue'
import BaseProgressBar from '@/components/BaseProgressBar.vue'
import BaseUserAvatar from '@/components/BaseUserAvatar.vue'
import { formatDateTime } from '../lib/TimeHandling'

export default {

  name: 'WorkOrderDataColumn',

  components: {
    BaseDialog,
    BaseProgressBar,
    BaseUserAvatar,
    WorkOrderJobQtRebalance // Balance wo quantity changes among jobs
  },

  props: {
    wo_data: {
      type: Object,
      required: true,
    },
  },

  data () {
    return {
      current_view: 'info',
      edit_project: false,
      temp_project_code: null,
      edit_qt: false,
      new_qt: null,
      edit_date: null,
      temp_date: null,
      show_job_qt_rebalance: false,
      delete_stage: null,
      saving: false
    }
  },

  computed: {

    views() {
      return [
        {
          name: 'info',
          text: this.$t('info'),
          class: 'justify-start'
        },
        {
          name: 'people',
          text: this.$t('people') + ' (' + this.people_count + ')',
          class: 'justify-end'
        },
        // { name: 'equipment', text: 'MACCHINARI', align: 'end' },
      ]
    },

    wo_info() {
      return [
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
          name: 'start_from',
          text: this.$t('start_from_date'),
        },
        {
          name: 'start',
          text: this.$t('start_date')
        },
        {
          name: 'due_by',
          text: this.$t('due_by')
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
          name: 'processing_cost',
          text: this.$t('processing_cost')
        },
        // {
        //   name: 'material_cost',
        //   text: this.$t('material_cost')
        // },
        // {
        //   name: 'total_cost',
        //   text: this.$t('total_cost')
        // },
      ]
    },

    assignments() {
      // handle missing data gracefully
      if (typeof this.wo_data != 'undefined') {

        const assignments = {}

        this.wo_data.jobs.forEach( j => {
          if (j.assigned_to != null) {
            const key = j.assigned_to._key
            if (key in assignments) {
              assignments[key].jobs.push(j)
            }
            else {
              const data = {
                ...this.$store.getters.user_data(key),
                jobs: [j]
              }
              assignments[key] = data
            }
          }
        })
        return assignments
      }

      else return {}
    },

    people_count() {
      return  Object.keys(this.assignments).length
    },

    unassigned_jobs() {
      let unassigned_jobs = []
      if (typeof this.wo_data != 'undefined') {
        unassigned_jobs = this.wo_data.jobs.filter(j => j.assigned_to == null)
      }
      return unassigned_jobs
    },

    min_allowable_wo_qt() {
      return Math.max(this.wo_data.jobs.map(j => j.qt_completed + j.active_batch_qt))
    },

    phase_data() {
      return this.wo_data.phase_sequence.map( phase_key => {
        const jobs = this.wo_data.jobs.filter( j => j.phase_key === phase_key )
        const params = jobs[0].parameters
        const phase_alias = jobs[0].phase_alias
        const total_completed = jobs.reduce( (sum, job) => sum + job.qt_completed, 0)
        const total_active = jobs.reduce( (sum, job) => sum + job.active_batch_qt, 0)
        // const total_released = jobs.reduce( (sum, job) => sum + job.qt_released, 0 )
        const total_remaining = jobs.reduce( (sum, job) => {
          return sum + job.qt_planned - job.qt_completed - job.active_batch_qt
        }, 0)
        const total_progress = Math.floor(
          jobs.reduce( (sum, job) => sum + job.progress * job.qt_planned, 0) / this.wo_data.qt_planned
        )
        const active = jobs.reduce( (count, job) => count + job.active, 0)

        // const assignments = jobs.map( job => job.assigned_to )

        return {
          jobs,
          phase_key,
          phase_alias,
          active,
          ...params,
          // qt_released: total_released,
          qt_completed: total_completed,
          qt_remaining: total_remaining,
          active_batch_qt: total_active,
          progress: total_progress,
        }
      })
    }
  },

  methods: {
    woInfoValue(info_name) {
      switch (info_name) {
        case 'status': {
          if (this.wo_data.status == 'closed') {
            return this.$t('closed')
          }
          else {
            let active_text = this.$t('active')
            let inactive_text = ['created', 'planned'].includes(this.wo_data.status)
              ? this.$t('production.filters.queued')
              : this.$t('waiting')
            // let on_time_text = this.$t('on_time')
            // let late_text = this.$t('late')
            // let critical_text = this.$t('critical')
            let active = this.wo_data.active ? active_text : inactive_text

            /*
            let state = ''

            if (this.wo_data.critical) state = critical_text
            else if (!this.wo_data.on_time) state = late_text
            else state = on_time_text
            */
            return active  //+ ' - ' + state
          }
        }

        case 'created':
        case 'start_from':
        case 'due_by': {
          const value = this.wo_data[info_name]
          if (!value) {
            return '-'
          }

          return formatDateTime(value, this.$i18n.locale, {
            weekday: 'short',
            month: 'short',
            day: 'numeric',
            year: '2-digit'
          })
        }

        case 'start':
        case 'end': {
          const value = this.wo_data[info_name]
          if (!value) {
            return '-'
          }

          return formatDateTime(value, this.$i18n.locale, {
            weekday: 'short',
            month: 'short',
            day: 'numeric',
            year: '2-digit',
            hour: 'numeric',
            minute: 'numeric',
          })
        }

        case 'processing_time': {
          const processing_time = this.wo_data.processing_time
          return processing_time ? durationFromMillisec(processing_time, { precision: 's'}) : '-'
        }

        case 'queueing_time': {
          const created = DT.fromISO(this.wo_data.created)
          const start = DT.fromISO(this.wo_data.start)
          const benchmark = start ? start : DT.utc()
          return this.wo_data.start
            ? durationFromMillisec(benchmark - created, { precision: 'h'})
            : '-'
        }

        case 'processing_cost': {
          return (this.wo_data.processing_cost || 0).toFixed(2) || '-'
        }

        case 'material_cost': {
          return (this.wo_data.material_cost || 0).toFixed(2) || '-'
        }

        case 'total_cost': {
          return (this.wo_data.total_cost || 0).toFixed(2) || '-'
        }

      }
    },

    isLate(due_by_date) {
      return DT.fromISO(due_by_date) < DT.now()
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
    },

    editDate(date_field) {
      this.edit_date = date_field
      this.temp_date = this.wo_data[date_field]
    },

    closeEditDialogs() {
      this.edit_date = null
      this.edit_qt = false
      this.temp_date = null
      this.new_qt = this.wo_data.qt_planned
      this.temp_project_code = this.wo_data.project_code
      this.edit_project = false
      this.show_job_qt_rebalance = false
      this.delete_stage = null
    },

    async saveWorkOrderUpdate() {
      this.saving = true

      const wo_update = {
        wo_key: this.wo_data._key,
        new_qt: this.new_qt,
        new_project_code: this.temp_project_code,
      }

      switch (this.edit_date) {
        case 'due_by':
          wo_update.new_due_date = this.temp_date
          break
        case 'start_from':
          wo_update.new_from_date = this.temp_date
          break
      }

      await this.$store.dispatch('updateWorkOrder', wo_update)
      await this.$store.dispatch('loadWorkOrderData', wo_update.wo_key)
      this.closeEditDialogs()
      this.saving = false
    },

    deleteWorkOrder() {
      this.loading = true
      this.$api.delete(`work-order/${this.wo_data._key}`).then(() => {
        this.$store.dispatch('loadWorkOrders')
        this.delete_stage = 'success'
      })
    }
  },

  created() {
    this.temp_project_code = this.wo_data.project_code
    this.temp_due_date = this.wo_data.due_by
    this.new_qt = this.wo_data.qt_planned
  }
}
</script>

<style lang="scss">
#panels div:hover {
  text-decoration: underline;
}
</style>
