<template>
  <q-card square class="surface1 q-pa-md" style="min-width: 600px; max-width: 1200px;">
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
        @select="(value) => issue_type = value"
        :value="issue_type">
      </BaseAutocompleteIssueType>

      <div class="row q-gutter-md q-mt-lg">
        <q-btn color="theme-orange" :label="$t('save')" @click="save" :loading="saving"/>
        <q-btn color="theme-red" @click="() => {critical = true; save()}">
          {{ $t('save') }} {{ $t('critical') }}
        </q-btn>
        <q-space />
        <q-btn
          color="theme-grey"
          :label="$t('cancel')"
          @click="$emit('close')">
        </q-btn>
      </div>


      <!-- <div v-else class="column full-width flex-center">
        <q-icon
          name="mdi-check-circle"
          color="theme-green"
          size="xl">
        </q-icon>
        <div class="q-mt-sm">{{ $t('issue_new_success') }}</div>
        <q-spinner class="q-mt-md"/>
      </div> -->
    </q-card-section>
  </q-card>
</template>

<script>
import BaseAutocompleteIssueType from '@/components/BaseAutocompleteIssueType.vue'
import { timestamp } from '@/lib/TimeHandling.js'

export default {

  name: 'WorkSessionIssueNew',

  components: {
    BaseAutocompleteIssueType
  },

  data () {
    return {
      current_issue_step: 1,
      saving: false,
      issue_type: null,
      title: '',
      description: '',
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
        linked_to: link_data
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
  }
}
</script>

<style lang="sass" scoped>
.q-stepper
  background-color: var(--surface-1)
  border-radius: 0px

  .q-stepper__dot
    color: white
</style>
