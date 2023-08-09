<template>
  <BaseDialog :show="show">
    <q-card square class="surface1 q-pa-md" style="min-width: 600px; max-width: 800px;">
      <q-form ref="issue-form">
        <q-card-section>
          <div class="row justify-between items-center">
            <div class="text-h2 display highlight text-center">
              <template v-if="mode=='new'">
                {{ $t('issue_new_title') }}
              </template>
              <template v-else>
                {{ $t('issue_update_title')}}
              </template>
            </div>
          </div>
        </q-card-section>

        <!-- FORM BODY -->

        <!-- ISSUE LINKS -->
        <q-card-section
          v-if="mode=='new' && with_links && form_step=='links'"
          key="issue_links"
          class="column q-gutter-md">
          <!-- "Path" selection (Order, Product, General) -->
          <q-select
            :options="['order', 'product', 'general']"
            filled
            v-model="link_form"
            :label="$t('issue_new_link_type_label')">
          </q-select>

          <!-- Link details (WO/Phase/Job, Product/Phase, Operation/User) -->
          <template v-if="link_form == 'order'">

            <!-- WORK ORDER -->
            <BaseAutocompleteWorkOrder
              :value="work_order"
              :label="$capitalize($t('work_order.long'))"
              @select="selection => loadWorkOrder(selection)">
            </BaseAutocompleteWorkOrder>

            <!-- PHASE -->
            <q-select
              v-if="work_order"
              v-model="phase"
              :label="$t('phase.short')"
              filled
              clearable
              :options="work_order_phase_data"
              option-label="alias">
            </q-select>

            <!-- JOB -->
            <q-select
              v-if="phase"
              v-model="job"
              :label="$capitalize($t('job.label'))"
              filled
              clearable
              :options="phase_jobs">
              <template #option="scope">
                <JobListItem
                  v-bind="scope.itemProps"
                  :job_data="scope.opt"
                  show_progress
                  show_assignee/>
              </template>
              <template #selected-item="scope">
                <JobListItem :job_data="scope.opt" />
              </template>
            </q-select>

          </template>

          <template v-else-if="link_form == 'product'">

          </template>


        </q-card-section>

        <!-- ISSUE DATA -->
        <div v-else key="issue_data">

          <!-- ISSUE TYPE SELECTION -->
          <q-card-section>
            <BaseAutocompleteIssueType
              @select="(value) => setIssueType(value)"
              :value="issue_type">
            </BaseAutocompleteIssueType>
          </q-card-section>

          <!-- FORM FIELDS -->
          <q-card-section>
            <template v-if="issue_type">
              <FormField
                v-for="field in form_data"
                :key="field._key"
                :field_data="field"
                :root_path="`/media/issue/${issue?._key}`"
                @update="val => field.value = val">
              </FormField>
            </template>
          </q-card-section>
        </div>


        <!-- FORM ACTIONS -->
        <q-card-section>
          <div class="row q-gutter-md">
            <q-btn
              v-if="mode == 'new' && with_links && form_step == 'links'"
              color="theme-blue"
              :label="$t('next')"
              @click="form_step = 'data'">
            </q-btn>
            <template v-else>
              <q-btn
                v-if="with_links"
                icon="mdi-arrow-left-bold"
                color="theme-blue"
                @click="form_step = 'links'">
              </q-btn>
              <q-btn
                v-if="!critical_only"
                color="theme-orange"
                :label="$t('save')"
                @click="() => { critical = false; save() }"
                :loading="saving">
              </q-btn>
              <q-btn
                color="theme-red"
                @click="() => {critical = true; save()}">
                {{ $t('save') }} {{ $t('critical') }}
              </q-btn>
            </template>

            <q-space />
            <q-btn
              color="theme-grey"
              :label="$t('cancel')"
              @click="cancel">
            </q-btn>
          </div>
        </q-card-section>

      </q-form>
    </q-card>
  </BaseDialog>
</template>

<script>
import BaseAutocompleteIssueType from '@/components/BaseAutocompleteIssueType.vue'
import BaseAutocompleteWorkOrder from '@/components/BaseAutocompleteWorkOrder.vue'
import BaseDialog from '@/components/BaseDialog.vue'
import FormField from '@/components/FormField.vue'
import JobListItem from '@/components/JobListItem.vue'
import { timestamp } from '@/lib/TimeHandling.js'

export default {

  name: 'IssueForm',

  components: {
    BaseAutocompleteIssueType,
    BaseAutocompleteWorkOrder,
    BaseDialog,
    JobListItem,
    FormField
  },

  props: {
    show: {
      type: Boolean,
      default: true
    },
    mode: {
      type: String,
      default: 'new'
    },
    issue: {
      type: Object,
      default: undefined
    },
    with_links: {
      type: Boolean,
      default: false
    }
  },

  data () {
    return {
      critical_only: false,
      saving: false,
      issue_type: null,
      form_step: 'data',
      form_data: [],
      confirmed: false,
      critical: false,
      link_form: null,
      work_order: null,
      work_order_phase_data: null,
      phase: null,
      phase_jobs: null,
      job: null,
      links: [
        {
          type: 'product',
          job_prop: 'product_code',
          label: this.$capitalize(this.$t('product.label')),
          active: true,
          value: null,
          visible: true
        },
        {
          type: 'operation',
          job_prop: 'phase_alias',
          label: this.$capitalize(this.$t('operation.issue_link_label')),
          active: true,
          value: null,
          visible: true
        },
        {
          type: 'phase',
          job_prop: 'phase_alias',
          label: this.$capitalize(this.$t('phase.issue_link_label')),
          active: true,
          value: null,
          visible: true
        },
        {
          type: 'work_order',
          job_prop: 'wo_code',
          label: this.$capitalize(this.$t('work_order.long')),
          active: true,
          value: null,
          visible: true
        },
        {
          type: 'user',
          active: true,
          value: null,
          visible: false
        },
        {
          type: 'job',
          active: true,
          value: null,
          visible: false
        }
      ]
    }
  },

  computed: {
    job_data() {
      return this.$store.state.traceability.working_job_data
    },

    session_data() {
      return this.$store.state.session
    }
  },

  methods: {
    initLinks() {
      // Show empty form fields if it's a new issue or the issue type is being changed
      if (this.with_links) {
        this.form_step = 'links'
        this.link_form = null
        this.work_order = null
        this.phase = null
        this.work_order_phase_data = null
      }
    },

    initFormData() {
      const use_clean_form = this.mode == 'new' || this.issue_type?._key != this.issue.issue_type_key

      if (use_clean_form) {
        // Use fields from issue type template adding empty value
        // If no template, force null, otherwise `undefiend` will not be included in the api body and the issue data will not be updated
        this.form_data = this.issue_type?.form_template.map(f => {
          return { ...f, value: null }
        }) ?? null
      }
      else this.form_data = [ ...this.issue.data ]
    },

    initIssueType() {
      // Fetch issue type data if editing an existing issue
      this.issue_type = this.issue?.issue_type_key != null
        ? this.$store.getters.getIssueType(this.issue.issue_type_key)
        : null
    },

    setIssueType(value) {
      this.issue_type = value
      if (value?.critical) {
        this.critical_only = true
      }
      else {
        this.critical_only = false
      }
    },

    loadWorkOrder(wo) {
      // Set work order data and initialize Phase options to select from
      this.work_order = wo
      let params = new URLSearchParams()
      this.work_order.phase_sequence.forEach(pk => params.append('phase_key', pk))
      this.$api.get('phase', { params }).then(
        resp => this.work_order_phase_data = resp.data
      )
    },

    loadPhase(phase_data) {
      this.phase = phase_data
      // Phase link exists for both order and product mode. Load jobs only in order mode
      if (this.link_form == 'order') {
        this.$api.get('job', { params: {
          work_order_key: this.work_order._key,
          phase_key: this.phase._key
        }}).then(resp => this.phase_jobs = resp.data.detail)
      }
    },

    cancel() {
      this.initIssueType()
      this.initFormData()
      this.initLinks()
      this.critical_only = false
      this.$emit('close')
    },

    saveFiles(issue_key) {
      this.form_data
      .filter(field => field.type == 'files')
      .forEach(async field => {


        const to_delete = []
        const to_add = []

        field.value.forEach(file => {
          if (file.temp) {
            to_add.push(file.content)
          }
          else if (file.delete) {
            to_delete.push(file.name)
          }
        })

        const target = {
          bucket: 'issue',
          object_key: issue_key,
          subfolder: field._key
        }

        // Upload new files
        if (to_add.length) {
          // Populate form data
          let add_body = new FormData()
          Object.entries(target).forEach(([k, v]) => add_body.append(k, v))
          to_add.forEach(file => add_body.append('contents', file))
          // Post files
          this.$api.post('/files',
            add_body, {
            headers: {'Content-Type': 'multipart/form-data'}
          }).catch( err => window.alert(err) )
        }

        // Delete files
        if (to_delete.length) {
          this.$api.delete('/files', { data: {
            ...target,
            filenames: to_delete
          }}).catch( err => window.alert(err))
        }
      })
    },

    async save() {
      this.saving = true

      const issue_data = {
        issue_type_key: this.issue_type?._key || null,
        critical: this.critical,
        data: this.form_data.map(field => {
          if (field.type == 'files') {
            return {
              ...field,
              value: field.value.filter(file => !file.delete).map(file => ({
                size: file.size,
                name: file.name
              }))
            }
          }
          else return field
        })
      }

      const user = this.session_data.user._key

      if (this.mode == 'new') {
        // if link is active send data in the form e.g. { type: product, key: whatever }
        issue_data.created_by = `User/${user}` // temporarily hardcoding DB id
        issue_data.close_within = this.issue_type ? this.issue_type.close_within : 0

        // Map links to list of objects, including only populated properties
        const link_data = this.links.map(l => {
          const value = (
            l.type == 'product' ? this.job_data.product_key
            : l.type == 'operation' ? this.job_data.operation_key
            : l.type == 'phase' ? this.job_data.phase_key
            : l.type == 'work_order' ? this.job_data.wo_key
            : l.type == 'user' ? this.session_data.user._key
            : l.type == 'job' ? this.job_data._key
            : null
          )
          return { type: l.type, key: value  }
        })
        issue_data.linked_to = link_data
      }

      // Add _key and data fields for ISSUE_UPDATED event
      else issue_data._key = this.issue._key

      const event = {
        event_type: this.mode == 'new' ? 'ISSUE_CREATED' : 'ISSUE_UPDATED',
        user_key: user,
        user_session_key: this.session_data.session_key,
        timestamp: timestamp(),
        issue_data
      }

      const message = this.mode == 'new' ? 'issue_new_success' : 'issue_update_success'
      this.$api.post('event', event)
      .then(async (resp) => {
        const issue_key = this.mode == 'new' ? resp.data.detail.issue_key : issue_data._key
        await this.saveFiles(issue_key)
        this.saving = false
        this.$store.dispatch('getIssues', { job_key: this.job_data._key })
        this.cancel()
        this.$q.notify({
          message: this.$t(message),
          color: this.critical ? 'theme-red' : 'theme-orange',
          timeout: 1500,
          position: 'top'
        })
      })
    },
  },

  created() {
    this.initIssueType()
    this.initFormData()

    // Inser links step if required
    if (this.mode == 'new' && this.with_links) this.form_step = 'links'
  },

  watch: {
    issue_type: {
      deep: true,
      handler: 'initFormData'
    },
    show: {
      handler: 'initFormData'
    },
    phase: {
      handler: 'loadPhase'
    }
  }
}
</script>

<style lang="sass" scoped>
</style>
