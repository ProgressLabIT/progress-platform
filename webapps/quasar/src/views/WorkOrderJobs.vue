<template>
  <div class="q-px-md q-py-md full-height column">

    <!-- HEADERS -->
    <div class="row low-text items-center q-px-md">
      <div
        v-for="header in headers" :key="header.value"
        class="text-h5 text-uppercase"
        :class="getColClass(header)">
        {{ header.text }}
      </div>
    </div>

    <!-- CONTENT -->
    <div class="scroll">
      <q-expansion-item
        v-for="(phase, index) in phase_data"
        :key="phase.phase_key"
        expand-separator
        :model-value="expanded_phase === phase.phase_key"
        @click="togglePhase(phase.phase_key)"
        :header-class="getHeaderClass(phase.phase_key)"
        hide-expand-icon>

        <!-- PHASE SUMMARY DATA -->
        <template #header>
          <div
            v-for="header in headers"
            :class="getColClass(header)"
            :key="header.value">

            <!-- PHASE PROGRESS -->
            <template v-if="header.value === 'progress'">
              <div class="col-12 row items-center">
                <div class="col-9">
                  <BaseProgressBar :data="phase" />
                </div>
                <div class="col q-ml-md text-right">
                  {{ phase.progress }}%
                </div>
              </div>
            </template>

            <!-- OTHER PHASE DATA -->
            <template v-else-if="header.value != 'assigned_to'">
              {{ $capitalizeAll(phase[header.value]) }}
            </template>

          </div>
        </template>
        <!-- END OF HEADER -->

        <!-- JOB DATA & PHASE/JOB ACTIONS -->
        <div
          v-for="job in phase.jobs"
          :id="job._key"
          class="row items-center q-pa-md">

          <!-- JOB DATA -->
          <div
            v-for="header in headers"
            :key="header.value"
            :class="getColClass(header)">

            <!-- SELECT CHECKBOX -->
            <template v-if="header.value === 'phase_alias'">
              <q-checkbox
                color="theme-blue"
                :disable="job.active || job.stage === 'closed'"
                :val="job._key"
                v-model="selected_jobs">
              </q-checkbox>
            </template>

            <!-- JOB PROGRESS BAR -->
            <template v-else-if="header.value === 'progress'">
              <div class="row items-center">
                <div class="col-9">
                  <BaseProgressBar :data="job" />
                </div>
                <div class="col q-ml-md text-right">
                  {{ job.progress }}%
                </div>
              </div>
            </template>

            <!-- ASSIGNED OPERATOR -->
            <template v-else-if="header.value === 'assigned_to'">
              <BaseUserAvatar
                v-if="job.assigned_to"
                :user="job.assigned_to">
              </BaseUserAvatar>
              <q-btn
                v-else-if="selected_jobs.length === 0"
                size="sm"
                color="theme-blue"
                @click="updateSelectedJobData(job, true); edit_mode = 'modify'">
                {{ $t('assign') }}
              </q-btn>
            </template>

            <!-- REMAINING QUANTITY (CALCULATED) -->
            <template v-else-if="header.value === 'qt_remaining'">
              {{ job.qt_planned - job.qt_completed - job.active_batch_qt }}
            </template>

            <!-- OTHER FIELDS -->
            <template v-else>
              {{ $capitalizeAll(job[header.value]) }}
            </template>
          </div>
          <!-- END OF JOB DATA -->

        </div>

        <!-- JOB ACTIONS -->
        <div class="row items-center q-px-lg q-py-md">

          <!-- STARTING ACTION BUTTONS -->
          <template v-if="edit_mode=='actions'">

            <!-- SELECT ALL -->
            <q-btn
              size="12px"
              v-if="phase.jobs.length > 1"
              color="theme-grey"
              @click="toggleAll(phase)">
              {{ selected_jobs.length == 0
                  ? $t('select_all')
                  : $t('deselect_all')  }}
            </q-btn>

            <template v-if="phase.editing">
              <q-space />
              <q-btn
                size="12px"
                color="theme-blue"
                @click="edit_mode = 'modify'">
                {{ $t('edit') }}
              </q-btn>
            </template>
          </template>
          <!-- END OF STARTING ACTION BUTTONS -->

          <!-- REBALANCE ACTION CARD -->
          <template v-if="edit_mode == 'modify' ">
            <JobRebalanceActionCard
              :jobs="selected_jobs_data"
              @changeEditMode="edit_mode = $event">
            </JobRebalanceActionCard>
          </template>
        </div>
        <!-- END OF JOB ACTIONS -->

      </q-expansion-item>

    </div>
    <!-- END OF PHASE DETAILS -->

    <q-space />

    <!-- WORK ORDER ACTIONS -->
    <div class="row justify-between q-pb-sm q-gutter-md">
      <q-btn
        color="theme-blue"
        @click="edit_qt = true">
        {{ $t('quantity.update') }}
      </q-btn>
      <q-btn
        color="theme-blue"
        :loading="saving"
        @click="edit_due_date = true">
        {{ $t('work_order.update_due_date') }}
      </q-btn>
      <q-btn color="theme-red">
        {{ $t('work_order.close') }}
      </q-btn>
    </div>

    <!-- EDIT DUE-DATE DIALOG -->
    <BaseDialog
      :show="edit_due_date"
      @close="closeEditDialogs">
      <q-card class="surface2">
        <q-date
          minimal
          v-model="temp_due_date"
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

    <!-- EDIT QUANTITY DIALOG -->
    <BaseDialog :show="edit_qt" @close="closeEditDialogs">
      <q-card class="surface2 q-pa-md" style="width: 300px">
        <q-card-section>
          <div class="text-h4 display highlight text-uppercase">
            {{ $t('work_order.new_quantity') }}
          </div>
          <q-input
            class="q-mt-md"
            input-class="text-body1"
            hide-bottom-space
            type="number"
            :min="min_allowable_wo_qt"
            :model-value="wo_data.qt_planned"
            @update:model-value="val => new_qt = val">
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
      :new_wo_qt="parseInt(new_qt)"
      :phase_data="phase_data"
      :wo_key="wo_data._key"
      @close="closeEditDialogs">
    </WorkOrderJobQtRebalance>

  </div>
</template>

<script>
import BaseDialog from '@/components/BaseDialog.vue'
import BaseProgressBar from '@/components/BaseProgressBar.vue'
import BaseUserAvatar from '@/components/BaseUserAvatar.vue'
import JobRebalanceActionCard from '@/components/JobRebalanceActionCard.vue'
import WorkOrderJobQtRebalance from '@/components/WorkOrderJobQtRebalance.vue'

export default {

  name: 'WorkOrderJobs',

  components: {
    BaseDialog,
    BaseProgressBar,
    BaseUserAvatar,
    JobRebalanceActionCard, // Make changes to phase jobs
    WorkOrderJobQtRebalance // Balance wo quantity changes among jobs
  },

  props: {
    wo_data: {
      type: Object,
      required: true,
      default: function() {
        return { phase_sequence: [] }
      }
    },
  },

  data () {
    return {
      saving: false,
      expanded_phase: null,
      selected_jobs: [],
      jobs_temp_data: {},
      edit_mode: 'actions',
      edit_qt: false,
      new_qt: null,
      edit_due_date: false,
      temp_due_date: null,
      show_job_qt_rebalance: false
      // selected_jobs: []
    }
  },

  computed: {

    headers() {
      return [
        {
          value: 'phase_alias',
          text: this.$t('phase.short'),
          cols: 2,
          width: '20%'
        },
        {
          value: 'progress',
          text: this.$t('progress'),
          cols: 4,
        },
        {
          value: 'qt_completed',
          text: this.$t('quantity.completed.short'),
          align: 'end',
          cols: false,
        },
        // { value: 'qt_released', text: 'QRil', align: 'end', cols: false, width: 'auto'},
        {
          value: 'active_batch_qt',
          text: this.$t('quantity.active.short'),
          align: 'end',
          cols: false,
        },
        {
          value: 'qt_remaining',
          text: this.$t('quantity.remaining.short'),
          align: 'end',
          cols: false,
        },
        {
          value: 'assigned_to',
          text: this.$t('job.assigned_to'),
          align: 'end',
          cols: '3',
        },
      ]
    },

    selected_jobs_data() {
      return this.wo_data.jobs.filter(j => this.selected_jobs.includes(j._key))
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
        const editing = jobs.some( j => this.selected_jobs.includes(j._key) )

        // const assignments = jobs.map( job => job.assigned_to )

        return {
          jobs,
          phase_key,
          phase_alias,
          editing,
          active,
          ...params,
          // qt_released: total_released,
          qt_completed: total_completed,
          qt_remaining: total_remaining,
          active_batch_qt: total_active,
          progress: total_progress,
        }
      })
    },

    min_allowable_wo_qt() {
      return Math.max(this.wo_data.jobs.map(j => j.qt_completed))
    }
  },

  methods: {

    getHeaderClass(phase_key) {
      const base_classes = 'row items-center q-py-lg'
      const highlight = this.expanded_phase === phase_key ? ' highlight' : ''
      return base_classes + highlight
    },

    getColClass(header) {
      const alignment_class = header.value.includes('qt')
        ? 'text-right'
        : ''

      const cols = header.cols ? 'col-' + header.cols : 'col'
      return cols + ' ' + alignment_class + ' q-px-md'
    },

    togglePhase(phase_key) {
      if (this.expanded_phase === phase_key) {
        this.expanded_phase = null
      }
      else {
        this.expanded_phase = phase_key
      }
    },

    toggleAll(phase) {
      if (this.selected_jobs.length) {
        this.selected_jobs = []
      }
      else {
        // Select jobs that are open and NOT active
        phase.jobs.filter(j => {
          const job_is_open = j.stage != 'closed'
          const job_not_active = !j.active
          return job_is_open && job_not_active
        })
        .forEach( j => {
          this.selected_jobs.push(j._key)
        })
      }
    },

    updateSelectedJobData(job, selected) {
      if (selected) {
        this.job_select_model[job._key] = job
      }
      else delete this.job_select_model[job._key]
    },

    closeEditDialogs() {
      this.edit_due_date = false
      this.edit_qt = false
      this.temp_due_date = this.wo_data.due_by
      this.new_qt = null
      this.show_job_qt_rebalance = false
      this.new_qt = this.wo_data.qt_planned
    },

    async saveWorkOrderUpdate() {
      this.saving = true

      const wo_update = {
        wo_key: this.wo_data._key,
        new_qt: this.new_qt,
        new_due_date: this.temp_due_date
      }
      await this.$store.dispatch('updateWorkOrder', wo_update)
      this.closeEditDialogs()
      setTimeout(() => this.saving = false, 1000)
    }

  },

  created() {
    this.temp_due_date = this.wo_data.due_by
  },

  watch: {
    // Reset selection when toggling phases
    expanded_phase() {
      this.selected_jobs = []
    },

    // reset edit_mode after closing/switching phase details
    selected_jobs() {
      if (!this.selected_jobs.length) this.edit_mode = 'actions'
    },

    edit_mode() {
      if (this.edit_mode === 'actions') {
        this.selected_jobs = []
      }
    }
  },
}
</script>

<style lang="css" scoped>
</style>
