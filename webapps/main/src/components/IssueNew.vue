<template>
  <BaseDialog :show="show">
    <q-card square class="surface1 q-pa-md" style="min-width: 600px; max-width: 1200px;">
      <q-form>
        <q-card-section>
          <div class="row justify-between items-center">
            <div class="text-h2 display highlight text-center">
              {{ $t('issue_new_title') }}
            </div>
            <q-btn
              round
              flat
              padding="sm sm"
              icon="mdi-close"
              @click="$emit('close')">
            </q-btn>
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
              v-for="field in issue_type.form_template"
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
              @click="save"
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

  name: 'IssueNew',

  components: {
    BaseAutocompleteIssueType,
    BaseDialog,
    FormField
  },

  props: {
    show: {
      type: Boolean,
      default: true
    }
  },

  data () {
    return {
      critical_only: false,
      saving: false,
      issue_type: null,
      form_data: {},
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
    setIssueType(value) {
      this.issue_type = value
      if (value.critical) {
        this.critical_only = true
      }
      else {
        this.critical_only = false
      }
    },

    cancel() {
      this.issue_type = null
      this.form_data = {}
      this.$emit('close')
    },

    save() {
      // if link is active send data in the form e.g. { type: product, key: whatever }
      const link_data = this.links.map(l => ({ type: l.type, key: l.value }))

      const user = this.session_data.user._key

      this.saving = true
      const issue_data = {
        issue_type: this.issue_type ? this.issue_type._key : null,
        created_by: `User/${user}`, // temporarily hardcoding DB id
        critical: this.critical,
        close_within: this.issue_type ? this.issue_type.close_within : 0,
        // Map links to list of objects, including only populated properties
        linked_to: link_data,
        data: this.issue_type ? this.issue_type.form_template.map(f => {
          return { _key: f._key, value: f.value }
        }) : null
      }
      const event = {
        event_type: 'ISSUE_CREATED',
        user_key: user,
        user_session_key: this.session_data.session_key,
        timestamp: timestamp(),
        issue_data
      }
      this.$api.post('event', event)
      .then(() => {
        this.saving = false
        this.$store.dispatch('getIssues', { job_key: this.job_data._key })
        this.$emit('close')
        this.$q.notify({
          message: this.$t('issue_new_success'),
          color: this.critical ? 'theme-red' : 'theme-orange',
          timeout: 1500,
          position: 'top'
        })
      })
    }
  },

  mounted() {
    this.links.forEach(l => {
      l.value = (
        l.type == 'product' ? this.job_data.product_key
        : l.type == 'operation' ? this.job_data.operation_key
        : l.type == 'phase' ? this.job_data.phase_key
        : l.type == 'work_order' ? this.job_data.wo_key
        : l.type == 'user' ? this.session_data.user._key
        : l.type == 'job' ? this.job_data._key
        : null
      )
    })
  },
}
</script>

<style lang="sass" scoped>
.q-stepper
  background-color: var(--surface-1)
  border-radius: 0px

  .q-stepper__dot
    color: white
</style>
