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
        <q-card-section>
          <BaseAutocompleteIssueType
            @select="(value) => setIssueType(value)"
            :value="issue_type">
          </BaseAutocompleteIssueType>
        </q-card-section>

        <q-card-section>
          <template v-if="issue_type">
            <FormField
              v-for="field in form_data"
              :key="field._key"
              :field_data="field"
              @update="val => field.value = val">
            </FormField>
          </template>
        </q-card-section>

        <!-- ACTIONS -->
        <q-card-section>
          <div class="row q-gutter-md">
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
import BaseDialog from '@/components/BaseDialog.vue'
import FormField from '@/components/FormField.vue'
import { timestamp } from '@/lib/TimeHandling.js'

export default {

  name: 'IssueForm',

  components: {
    BaseAutocompleteIssueType,
    BaseDialog,
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
    }
  },

  data () {
    return {
      critical_only: false,
      saving: false,
      issue_type: null,
      form_data: [],
      confirmed: false,
      critical: false,
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
    initFormData() {
      // Show empty form fields if it's a new issue or the issue type is being changed
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

    cancel() {
      this.initIssueType()
      this.form_data = []
      this.critical_only = false
      this.$emit('close')
    },

    save() {
      this.saving = true

      const issue_data = {
        issue_type_key: this.issue_type?._key || null,
        critical: this.critical,
        data: this.form_data
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
      .then(() => {
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
    }
  },

  mounted() {
    // Currently for use only from WorkSessionScreen
  },

  watch: {
    issue_type: {
      deep: true,
      handler: 'initFormData'
    }
  }
}
</script>

<style lang="sass" scoped>
</style>
