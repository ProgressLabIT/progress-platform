<template>
  <q-card square class="surface1 q-pt-md" style="min-width: 600px; max-width: 1200px;">
    <q-card-section>
      <div class="row justify-between items-center q-px-lg">
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
      <q-stepper
        v-model="current_issue_step"
        animated
        vertical
        square
        flat
        header-class="full-width">

        <q-step
          :name="1"
          :title="$t('type').toUpperCase()"
          icon="mdi-tag"
          :done="!!issue_type">
          <BaseAutocompleteIssueType
            @select="(value) => issue_type = value"
            :value="issue_type">
          </BaseAutocompleteIssueType>
          <q-stepper-navigation class="row justify-between q-mt-md">
            <q-space />
            <q-btn
              v-if="issue_type"
              color="theme-blue"
              :label="$t('next')"
              @click="current_issue_step = 2">
            </q-btn>
          </q-stepper-navigation>
        </q-step>

        <q-step
          :name="2"
          :title="$t('title').toUpperCase()"
          icon="mdi-text-short"
          :done="!!title.length">
          <q-input filled v-model="title" autofocus/>
          <q-stepper-navigation class="row justify-between q-mt-md">
            <q-btn
              color="theme-grey"
              :label="$t('back')"
              @click="current_issue_step = 1">
            </q-btn>
            <q-btn
              v-if="title.length"
              color="theme-blue"
              :label="$t('next')"
              @click="current_issue_step = 3">
            </q-btn>
          </q-stepper-navigation>
        </q-step>

        <q-step
          :name="3"
          :title="$t('description').toUpperCase()"
          icon="mdi-text-long"
          :done="!!description.length">
          <q-input filled autogrow autofocus v-model="description" />
          <q-stepper-navigation class="row justify-between q-mt-md">
            <q-btn
              color="theme-grey"
              :label="$t('back')"
              @click="current_issue_step = 2">
            </q-btn>
            <q-btn
              v-if="description.length"
              color="theme-blue"
              :label="$t('next')"
              @click="current_issue_step = 4">
            </q-btn>
          </q-stepper-navigation>
        </q-step>

        <q-step
          :name="4"
          :title="$t('link', 2).toUpperCase()"
          icon="mdi-link-variant"
          :done="current_issue_step > 4">

          <div class="q-mb-lg">
            {{ $t('issue_new_link_step_helper') }}
          </div>

          <q-list style="max-width: 600px;">
            <q-item
              v-for="link in links.filter(l => l.visible)"
              :key="link.type">
              <q-item-section avatar>
                <q-checkbox v-model="link.active" />
              </q-item-section>
              <q-item-section>
                <q-item-label>
                  {{ link.label }}:
                </q-item-label>
              </q-item-section>
              <q-item-section>
                <q-item-label class="highlight">
                  {{ $capitalize(job_data[link.job_prop]) }}
                </q-item-label>
              </q-item-section>
            </q-item>
          </q-list>

          <q-stepper-navigation class="row justify-between q-mt-md">
            <q-btn
              color="theme-grey"
              :label="$t('back')"
              @click="current_issue_step = 3">
            </q-btn>
            <q-btn
              v-if="description.length"
              color="theme-blue"
              :label="$t('next')"
              @click="current_issue_step = 5">
            </q-btn>
          </q-stepper-navigation>
        </q-step>

        <q-step
          :name="5"
          :title="$t('summary').toUpperCase()"
          icon="mdi-file-check-outline"
          :done="confirmed">

          <div class="row">
            <div class="col-7">

              <div class="text-h5 text-low text-uppercase q-mt-lg q-mb-xs">
                {{ $t('type') }}
              </div>
              <div class="text-body1 text-high">
                {{ issue_type.name }}
                <span v-if="issue_type.code">
                  ({{ issue_type.code }})
                </span>
              </div>

              <div class="text-h5 text-low text-uppercase q-mt-lg q-mb-xs">
                {{ $t('title') }}
              </div>
              <div class="text-body1 text-high">
                {{ title }}
              </div>

              <div class="text-h5 text-low text-uppercase q-mt-lg q-mb-xs">
                {{ $t('description') }}
              </div>
              <div class="text-body1 text-high ellipsis-2-lines" style="max-width: 700px">
                {{ description }}
              </div>

              <q-toggle
                v-model="critical"
                color="theme-red"
                :label="$capitalize($t('critical'))"
                class="q-mt-lg">
              </q-toggle>

            </div>

            <div class="col-5">
              <div class="text-h5 text-low text-uppercase q-mt-lg q-mb-xs">
                {{ $t('link', 2) }}
              </div>

              <div
                  v-for="link in links.filter(l => l.visible && l.active)"
                  :key="link.type"
                  class="q-mt-md">
                  <div class="overline">{{ link.label }}</div>
                  <span class="weight-bold q-mt-xs">{{ $capitalize(job_data[link.job_prop]) }}</span>
                </div>

            </div>
          </div>


          <q-stepper-navigation class="row justify-between q-mt-md">
            <q-btn
              color="theme-grey"
              :label="$t('back')"
              @click="current_issue_step = 4">
            </q-btn>
            <q-btn
              :color="critical ? 'theme-red' : 'theme-orange'"
              class="q-ml-md"
              :label="$t('save')"
              @click="save">
            </q-btn>
          </q-stepper-navigation>
        </q-step>

        <q-step
          :name="6"
          :title="$t('end').toUpperCase()"
          icon="mdi-check"
          :done="false">
          <div class="column full-width flex-center">
            <q-icon
              name="mdi-check-circle"
              color="theme-green"
              size="xl">
            </q-icon>
            <div class="q-mt-sm">{{ $t('issue_new_success') }}</div>
            <q-spinner class="q-mt-md"/>
          </div>
        </q-step>

      </q-stepper>
    </q-card-section>
  </q-card>
</template>

<script>
import { api } from '@/boot/axios.js'
import BaseAutocompleteIssueType from '@/components/BaseAutocompleteIssueType.vue'

export default {

  name: 'IssueNew',

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
    }
  },

  methods: {
    save() {
      // if link is active send data in the form e.g. { type: product, key: whatever }
      const link_data = this.links.filter(l => !!l.active).map(l => ({ type: l.type, key: l.value }))

      const user = this.links.find(l => l.type == 'user').value

      this.saving = true
      const issue_data = {
        issue_type: this.issue_type._key,
        title: this.title,
        description: this.description,
        created_by: `User/${user}`, // temporarily hardcoding DB id
        critical: this.critical,
        close_within: this.issue_type.close_within,
        // Map links to list of objects, including only populated properties
        linked_to: link_data
      }
      api.post('issue', issue_data).then(() => {
        this.confirmed = true
        this.saving = false
        this.current_issue_step = 6
        setTimeout(() => this.$emit('close'), 3000)
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
        : l.type == 'user' ? this.$store.state.session.user._key
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
