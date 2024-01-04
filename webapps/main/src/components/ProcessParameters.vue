<template>
  <NoDataAlert v-if="Object.keys(paramsModel) === 0" />
  <q-list v-else>
    <template
      v-for="(paramValue, paramKey, index) in paramsModel"
      :key="paramKey"
    >
      <q-expansion-item
        :expand-icon="params_map[paramKey].type === 'int' || !editMode ? 'none' : ''"
        :model-value="expandedParamKey === paramKey"
        @update:model-value="(isExpanded) => {
          expandedParamKey = isExpanded ? paramKey : null
        }"
      >
        <!-- SELECTED OPTION -->
        <template #header>
          <div class="full-width q-pa-lg">
            <div class="text-h5 uppercase q-mb-sm low-text">
              {{ $t(`phase.params.${paramKey}.title`) }}
            </div>
            <div
              v-if="!editMode || params_map[paramKey].type !== 'int'"
              class="text-h3 highlight"
            >
              {{ getParamHumanValue(paramKey, paramValue) }}
            </div>
            <q-input
              v-else
              :model-value="getParamHumanValue(paramKey)"
              type="number"
              min="0"
              :readonly="!editMode"
              @update:model-value="(value) => updateParam(paramKey, value)"
            />
            <div class="q-mt-sm">
              {{ getParamValueDesc(paramKey, paramValue) }}
            </div>
          </div>
        </template>

        <!-- OTHER OPTIONS -->
        <template v-if="params_map[paramKey].type !== 'int' && editMode">
          <q-list>
            <q-item
              v-for="(value, index) in getParamOtherValues(paramKey, paramValue)"
              v-ripple
              :key="index"
              clickable
              @click="updateParam(paramKey, value)"
            >
              <q-item-label class="q-pa-lg">
                <div class="text-h5 highlight q-mb-sm">
                  {{ getParamHumanValue(paramKey, value) }}
                </div>
                <div>
                  {{ getParamValueDesc(paramKey, value) }}
                </div>
              </q-item-label>
            </q-item>
          </q-list>
        </template>
      </q-expansion-item>

      <q-separator v-if="index < Object.keys(paramsModel).length - 1" />
    </template>
  </q-list>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import NoDataAlert from '@/components/NoDataAlert.vue'
import params_map from '@/lib/PhaseParams.js'
import { capitalize } from '../boot/filters'

const props = defineProps({
  processHasSteps: {
    type: Boolean,
    required: true
  },
  editMode: {
    type: Boolean,
    required: true
  }
})

const paramsModel = defineModel({ type: Object })

const expandedParamKey = ref()

watch(() => props.editMode, (newValue, oldValue) => {
  // If edit mode got disabled, close the expanded param
  if (newValue === false && oldValue === true) {
    expandedParamKey.value = null
  }
})

const { t } = useI18n()

function getParamHumanValue(key, value) {
  if (params_map[key].type === 'int') {
    // Show "JOB" label if zero. See parameter explanation for details
    if (key === 'production_batch_qt' && paramsModel.value[key] === 0) {
      return props.editMode ? 0 : t('job.label').toUpperCase()
    }

    return paramsModel.value[key]
  }

  return t(`phase.params.${key}.${value}.title`)
}

function getParamValueDesc(key, value) {
  if (params_map[key].type === 'int') {
    return t(`phase.params.${key}.desc`)
  }

  return t(`phase.params.${key}.${value}.desc`)
}

function getParamOtherValues(key, value) {
  const paramAllValues = params_map[key].values
  return paramAllValues.filter(v => v !== value)
}

function updateParam(key, value) {
  if (key === 'step_check' && !props.processHasSteps && value === true) {
    window.alert(
      capitalize(t('phase.alerts.add_steps_first'))
    )
    expandedParamKey.value = null
    return
  }

  paramsModel.value[key] = value
}
</script>
