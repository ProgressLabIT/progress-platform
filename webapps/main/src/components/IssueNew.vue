<template>
  <q-card square class="surface1" style="max-width: 1200px;">
    <q-card-section>
      <div class="text-h2 display highlight text-center q-mt-md">
        {{ $t('issue_new_title') }}
      </div>
    </q-card-section>
    <q-card-section>
      <q-stepper
        v-model="current_issue_step"
        animated
        square
        flat
        alternative-labels
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
          icon="mdi-link-variant">

          <div class="text-center text-body1 q-mb-lg">{{ $t('issue_new_link_step_helper') }}</div>

          <div class="row justify-center">
            <q-list style="max-width: 600px;">
              <q-item>
                <q-item-section avatar>
                  <q-checkbox v-model="links.product" />
                </q-item-section>
                <q-item-section>
                  <q-item-label>
                    {{ $capitalize($t('product.label'))}}:
                  </q-item-label>
                </q-item-section>
                <q-item-section>
                  <q-item-label class="highlight">
                    {{ job_data.product_code }}
                  </q-item-label>
                </q-item-section>
              </q-item>

              <q-item>
                <q-item-section avatar>
                  <q-checkbox v-model="links.operation" />
                </q-item-section>
                <q-item-section>
                  <q-item-label>
                  {{ $capitalize($t('operation.issue_link_label'))}}:
                  </q-item-label>
                </q-item-section>
                <q-item-section>
                  <q-item-label class="highlight">
                    {{ $capitalize(job_data.phase_alias) }}
                  </q-item-label>
                </q-item-section>
              </q-item>

              <q-item>
                <q-item-section avatar>
                  <q-checkbox v-model="links.phase" />
                </q-item-section>
                <q-item-section>
                  <q-item-label>
                  {{ $capitalize($t('phase.issue_link_label'))}}:
                  </q-item-label>
                </q-item-section>
                <q-item-section>
                  <q-item-label class="highlight">
                    {{ $capitalize(job_data.phase_alias) }}
                  </q-item-label>
                </q-item-section>
              </q-item>

              <q-item>
                <q-item-section avatar>
                  <q-checkbox v-model="links.work_order" />
                </q-item-section>
                <q-item-section>
                  <q-item-label>
                  {{ $capitalize($t('work_order.long'))}}:
                  </q-item-label>
                </q-item-section>
                <q-item-section>
                  <q-item-label class="highlight">
                    {{ job_data.wo_code }}
                  </q-item-label>
                </q-item-section>
              </q-item>

              <q-item v-if="job_data.project_code">
                <q-item-section>
                  <q-checkbox v-model="links.project" />
                </q-item-section>
                <q-item-section>
                  <q-item-label>
                    {{ $capitalize($t('project')) }}:
                  </q-item-label>
                </q-item-section>
                <q-item-section>
                  <q-item-label class="highlight">
                    {{ job_data.project_code }}
                  </q-item-label>
                </q-item-section>
              </q-item>
            </q-list>
          </div>


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
            <div class="col-8">

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

            <div class="col-4">
              <div class="text-h5 text-low text-uppercase q-mt-lg q-mb-xs">
                {{ $t('link', 2) }}
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
            <q-space />
            <q-btn
              color="theme-grey"
              :label="$t('cancel')"
              @click="$emit('hide')">
            </q-btn>
          </q-stepper-navigation>
        </q-step>

        <q-step
          :name="6"
          :title="$t('end').toUpperCase()"
          icon="mdi-check"
          :done="false">
          COMPLETED
          <q-stepper-navigation>
            <q-btn
              color="theme-grey"
              label="Back to previous page"
              @click="$emit('hide')">
            </q-btn>
          </q-stepper-navigation>
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
      product: null,
      operation: null,
      phase: null,
      work_order: null,
      project: null,
      user: null,
      job: null,
      links: {
        product: true,
        operation: true,
        phase: true,
        work_order: true,
        project: true,
        user: true,
        job: true
      }
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
      const active_links = Object.entries(this.links).filter(([k, v]) => !!v)
      const link_data = active_links.map(([k, v]) => ({ type: k, key: this[k] }))

      this.saving = true
      const issue_data = {
        issue_type: this.issue_type._key,
        title: this.title,
        description: this.description,
        created_by: `User/${this.user}`, // temporarily hardcoding DB id
        critical: this.critical,
        close_within: this.issue_type.close_within,
        // Map links to list of objects, including only populated properties
        linked_to: link_data
      }
      api.post('issue', issue_data).then(() => {
        this.saving = false
        this.current_issue_step = 6
      })
    }
  },

  mounted() {
    this.product = this.job_data.product_key
    this.operation = this.job_data.operation_key
    this.phase = this.job_data.phase_key
    this.work_order = this.job_data.wo_key
    this.project = this.job_data.project_code
    this.user = this.$store.state.session.user._key
    this.job = this.job_data._key
  }
}
</script>

<style lang="sass" scoped>
.q-stepper
  background-color: var(--surface-1)
  border-radius: 0px

</style>
