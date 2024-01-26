<template>
  <div class="column full-height">
    <template v-if="operation">
      <div class="row q-px-lg q-pt-lg q-mx-md q-mt-md">
        <template v-if="!editMode">
          <div v-if="!editMode" class="col">
            <div class="text-h2 uppercase display highlight">
              {{ operation.name }}
              {{ operation.code ? '(' + operation.code + ')' : '' }}
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
            @icon-click="editMode = true"
          >
          </BaseTooltipIcon>

          <BaseTooltipIcon
            icon="mdi-delete"
            :tooltip="$capitalize($t('archive'))"
            :color="$theme.red"
            @icon-click="showDelete"
          >
          </BaseTooltipIcon>
        </template>
        <template v-else>
          <div class="column justify-between col-4">
            <q-input
              v-model="temp_metadata.name"
              filled
              stack-label
              hide-bottom-space
              :label="$capitalize($t('name'))"
            >
            </q-input>
            <q-input
              v-model="temp_metadata.code"
              filled
              stack-label
              hide-bottom-space
              :label="$capitalize($t('code'))"
              class="q-mt-md"
            >
            </q-input>
          </div>
          <div class="col-5 q-ml-xl">
            <q-input
              v-model="temp_metadata.description"
              filled
              stack-label
              autogrow
              hide-bottom-space
              :label="$capitalize($t('description'))"
            >
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
              :loading="saving"
              :label="$t('save')"
              @click="save"
            >
            </q-btn>
            <q-btn
              size="12px"
              color="theme-grey"
              :label="$t('cancel')"
              @click="cancel"
            >
            </q-btn>
          </div>
        </template>
      </div>

      <q-tabs
        v-model="activeTab"
        class="transparent text-low display q-mx-md"
        active-class="highlight"
        align="right"
        shrink
        dense
        indicator-color="theme-blue"
      >
        <q-tab name="steps">
          {{ $t('views.PhaseSteps') }}
        </q-tab>

        <q-tab name="parameters">
          {{ $t('views.PhaseParameters') }}
        </q-tab>

        <q-tab name="notes">
          {{ $t('views.PhaseNotes') }}
        </q-tab>
      </q-tabs>

      <q-card square class="col scroll q-mx-md q-mb-md">
        <q-tab-panels v-model="activeTab" class="fit surface2">
          <q-tab-panel name="steps">
            <ProcessSteps v-model="temp_steps" :edit-mode="editMode" />
          </q-tab-panel>

          <q-tab-panel name="parameters">
            <ProcessParameters
              v-model="temp_params"
              :process-has-steps="false"
              :edit-mode="editMode"
            />
          </q-tab-panel>

          <q-tab-panel name="notes">
            <ProductionNotes
              v-model="temp_notes"
              :edit-mode="editMode"
              class="q-pa-lg"
            />
          </q-tab-panel>
        </q-tab-panels>
      </q-card>
    </template>
    <NoDataAlert v-else />
  </div>
</template>

<script>
import { cloneDeep } from 'lodash'; // TODO: replace with lodash-es
import { ref } from 'vue';

import BaseTooltipIcon from '@/components/BaseTooltipIcon.vue';
import NoDataAlert from '@/components/NoDataAlert.vue';
import ProcessParameters from '@/components/ProcessParameters.vue';
import ProductionNotes from '@/components/ProductionNotes.vue';
import ProcessSteps from '@/components/process-steps/ProcessSteps.vue';

export default {
  name: 'OperationDetail',

  components: {
    BaseTooltipIcon,
    NoDataAlert,
    ProcessParameters,
    ProductionNotes,
    ProcessSteps,
  },

  props: {
    operation: {
      type: Object,
      required: true,
    },
  },

  setup() {
    const tab = ref('parameters');

    return {
      activeTab: tab,
    };
  },

  data() {
    return {
      editMode: false,
      saving: false,
      temp_metadata: {
        name: '',
        code: '',
        description: '',
      },
      temp_params: {
        max_offline: 60,
        parallel_job_allowed: true,
        step_check: false,
        step_check_force_order: false,
        production_batch_qt: 1,
        auto_new_batch: true,
        unsupervised_work_allowed: false,
      },
      temp_notes: '',
      temp_steps: [],
    };
  },

  computed: {
    products_using_operation() {
      return this.operation.used_for ?? [];
    },
  },

  watch: {
    operation: {
      handler: 'setTempData',
      immediate: true,
    },
    editMode: 'setTempData',
  },

  methods: {
    setTempData() {
      // At first render, sometimes the function runs before the prop has been passed, resulting in error
      if (!this.operation) {
        return;
      }

      this.temp_notes = this.operation.default_phase_notes ?? '';

      this.temp_steps = cloneDeep(this.operation.default_phase_steps ?? []);

      Object.keys(this.temp_metadata).forEach((key) => {
        this.temp_metadata[key] = this.operation[key];
      });

      const saved_params = this.operation.default_phase_parameters;
      Object.keys(this.temp_params).forEach((key) => {
        const value = saved_params[key];
        // If the value is undefined, then the parameter is not present in the saved data
        // and we should not overwrite the default value
        if (value !== undefined) {
          this.temp_params[key] = value;
        }
      });
    },

    cancel() {
      this.saving = false;
      this.editMode = false;
    },

    async save() {
      this.saving = true;
      const data = {
        key: this.operation._key,
        update: {
          ...this.temp_metadata,
          default_phase_parameters: this.temp_params,
          default_phase_notes: this.temp_notes,
          default_phase_steps: this.temp_steps,
        },
      };
      await this.$store.dispatch('updateOperation', data);
      this.saving = false;
      this.editMode = false;
    },

    showDelete() {
      if (this.products_using_operation.length) {
        const product_codes = this.products_using_operation.map(
          ({ code }) => code,
        );
        window.alert(
          this.$capitalize(
            this.$t('operation.alerts.op_in_use') + ': ' + product_codes,
          ),
        );
      } else {
        this.$router.push({
          name: 'operationDelete',
          params: { operation_key: this.operation._key },
        });
      }
    },
  },
};
</script>
