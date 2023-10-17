<template>
  <div class="column full-height">
    <template v-if="operation">
      <div class="row q-pa-lg q-ma-md">
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

      <q-separator />

      <div class="col scroll">
        <ProcessParameters
          :edit_mode="edit_mode"
          :params="temp_params"
          @update="updateParam">
        </ProcessParameters>
      </div>
    </template>

    <NoDataAlert v-else />
  </div>
</template>

<script>
import NoDataAlert from '@/components/NoDataAlert.vue'
import ProcessParameters from '@/components/ProcessParameters.vue'
import BaseTooltipIcon from '@/components/BaseTooltipIcon.vue'

export default {

  name: 'OperationDetail',

  components: {
    BaseTooltipIcon,
    NoDataAlert,
    ProcessParameters
  },

  props: {
    operation: {
      type: Object,
      required: true
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
        allow_unsupervised_work: false
      }
    }
  },

  computed: {
    products_using_operation() {
      return this.operation.used_for
    },
  },  


  methods: {
    setTempData(){
      // At first render, sometimes the function runs before the prop has been passed, resulting in error
      if (this.operation) {
        Object.keys(this.temp_metadata).forEach( key => {
          this.temp_metadata[key] = this.operation[key]
        })

        const saved_params = this.operation.default_phase_parameters
        Object.keys(this.temp_params).forEach( key => {
          this.temp_params[key] = saved_params[key]
        })
      }
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
          default_phase_parameters: this.temp_params
        }
      }
      await this.$store.dispatch('updateOperation', data)
      this.saving = false
      this.edit_mode = false
    },

    showDelete() {
      if (this.products_using_operation.length) {
        const product_codes = this.products_using_operation.map( o => o.code )
        window.alert(this.$capitalize(this.$t('operation.alerts.op_in_use') + ": " +  product_codes))
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
    edit_mode: 'setTempData',
    operation: 'setTempData'
  }
}
</script>

<style lang="css" scoped>
</style>
