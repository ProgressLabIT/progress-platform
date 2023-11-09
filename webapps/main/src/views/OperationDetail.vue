<template>
  <div class="column full-height">
    <template v-if="operation">
      <div class="row q-px-lg q-pt-lg q-mx-md q-mt-md">
        <template v-if="!edit_mode">
          <div class="col" v-if="!edit_mode">
            <div class="text-h2 uppercase display highlight">
              {{ operation.name }} {{ operation.code ? '(' + operation.code + ')' : ''}}
            </div>
            <div style="width: 50%">
              {{ operation.description || '— No Description —' }}
            </div>
          </div>

          <q-space />

          <BaseTooltipIcon
            icon="mdi-pencil"
            :tooltip="$capitalize($t('edit'))"
            :color="$theme.blue"
            @iconClick="edit_mode=true">
          </BaseTooltipIcon>

          <BaseTooltipIcon
            icon="mdi-delete"
            :tooltip="$capitalize($t('archive'))"
            :color="$theme.red"
            @iconClick="showDelete">
          </BaseTooltipIcon>
        </template>
        <template v-else>
          <div class="column justify-between col-4">
            <q-input
              filled
              stack-label
              hide-bottom-space
              :label="$capitalize($t('name'))"
              v-model="temp_metadata.name">
            </q-input>
            <q-input
              filled
              stack-label
              hide-bottom-space
              :label="$capitalize($t('code'))"
              v-model="temp_metadata.code"
              class="q-mt-md">
            </q-input>
          </div>
          <div class="col-5 q-ml-xl">
            <q-input
              filled
              stack-label
              autogrow
              hide-bottom-space
              :label="$capitalize($t('description'))"
              v-model="temp_metadata.description">
            </q-input>
          </div>

          <div class="col column q-pl-xl q-gutter-md">
            <!-- <q-btn
              size="12px"
              color="theme-orange"
              @click="setDefault"
              :loading="saving">
              Imposta come default
              <q-icon name="mdi-information-outline">
                <q-tooltip>
                  I nuovi prodotti verranno creati con questa fase
                </q-tooltip>
              </q-icon>
            </q-btn> -->
            <q-btn
              size="12px"
              color="theme-blue"
              @click="save"
              :loading="saving"
              :label="$t('save')">
            </q-btn>
            <q-btn
              size="12px"
              color="theme-grey"
              @click="cancel"
              :label="$t('cancel')">
            </q-btn>
          </div>
        </template>
      </div>

      <q-tabs
        v-model="activeTab"
        class="transparent text-low display"
        active-class="highlight"
        align="right"
        shrink
        dense
        indicator-color="theme-blue"
      >
        <!-- TODO: #326 - Add default steps -->
        <!-- <q-tab name="procedure">
          {{ $t('views.PhaseSteps') }}
        </q-tab> -->

        <q-tab name="parameters">
          {{ $t('views.PhaseParameters') }}
        </q-tab>

        <q-tab name="notes">
          {{ $t('views.PhaseNotes') }}
        </q-tab>
      </q-tabs>

      <q-separator />

      <q-tab-panels v-model="activeTab" class="col scroll">
        <!-- <q-tab-panel name="procedure" /> -->

        <q-tab-panel name="parameters">
          <ProcessParameters
            :edit_mode="edit_mode"
            :params="temp_params"
            @update="updateParam"
          />
        </q-tab-panel>

        <q-tab-panel name="notes">
          <ProductionNotes
            v-model="temp_notes"
            :edit-mode="edit_mode"
            class="q-pa-lg"
          />
        </q-tab-panel>
      </q-tab-panels>
    </template>
    <NoDataAlert v-else />
  </div>
</template>

<script>
import { ref } from 'vue'

import NoDataAlert from '@/components/NoDataAlert.vue'
import ProcessParameters from '@/components/ProcessParameters.vue'
import BaseTooltipIcon from '@/components/BaseTooltipIcon.vue'
import ProductionNotes from '../components/ProductionNotes.vue'

export default {
  name: 'OperationDetail',

  components: {
    BaseTooltipIcon,
    NoDataAlert,
    ProcessParameters,
    ProductionNotes
  },

  props: {
    operation: {
      type: Object,
      required: true
    }
  },

  setup() {
    const tab = ref('parameters')

    return {
      activeTab: tab
    }
  },

  data () {
    return {
      edit_mode: false,
      saving: false,
      temp_metadata: {
        name: '',
        code: '',
        description: ''
      },
      temp_params: {
        max_offline: 60,
        parallel_job_allowed: true,
        step_check: false,
        step_check_force_order: false,
        production_batch_qt: 1,
        auto_new_batch: true,
        unsupervised_work_allowed: false
      },
      temp_notes: ''
    }
  },

  computed: {
    products_using_operation() {
      return this.operation.used_for
    },
  },

  methods: {
    setTempData() {
      // At first render, sometimes the function runs before the prop has been passed, resulting in error
      if (!this.operation) {
        return
      }

      this.temp_notes = this.operation.default_phase_notes ?? ''

      Object.keys(this.temp_metadata).forEach(key => {
        this.temp_metadata[key] = this.operation[key]
      })

      const saved_params = this.operation.default_phase_parameters
      Object.keys(this.temp_params).forEach(key => {
        const value = saved_params[key]
        // If the value is undefined, then the parameter is not present in the saved data
        // and we should not overwrite the default value
        if (value !== undefined) {
          this.temp_params[key] = value
        }
      })
    },

    updateParam({ param, value }) {
      this.temp_params[param] = value
    },

    cancel() {
      this.saving = false
      this.edit_mode = false
    },

    async save() {
      this.saving = true
      const data = {
        key: this.operation._key,
        update: {
          ...this.temp_metadata,
          default_phase_parameters: this.temp_params,
          default_phase_notes: this.temp_notes
        }
      }
      await this.$store.dispatch('updateOperation', data)
      this.saving = false
      this.edit_mode = false
    },

    showDelete() {
      if (this.products_using_operation.length) {
        const product_codes = this.products_using_operation.map(({ code }) => code)
        window.alert(this.$capitalize(this.$t('operation.alerts.op_in_use') + ": " + product_codes))
      }
      else {
        this.$router.push({
          name: 'operationDelete',
          params: { operation_key: this.operation._key }
        })
      }
    },
  },

  watch: {
    operation: {
      handler: 'setTempData',
      immediate: true
    },
    edit_mode: 'setTempData'
  }
}
</script>

<style lang="css" scoped>
</style>
