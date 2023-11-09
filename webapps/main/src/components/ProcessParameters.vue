<template>
  <q-list>
    <template
      v-for="(p_value, p_key, index) in params"
      :key="p_key"
    >
      <q-separator v-if="index > 0" />

      <q-expansion-item
        :expand-icon="paramType(p_key) == 'int' || !edit_mode ? 'none' : ''"
        :model-value="expansion_map == p_key"
        @update:model-value="(new_val) => updateExpansionMap(p_key, new_val)"
      >
        <!-- SELECTED OPTION -->
        <template #header>
          <div class="full-width q-pa-lg">
            <div class="text-h5 uppercase q-mb-sm low-text">
              {{ paramHumanName(p_key, p_value) }}
            </div>
            <div
              v-if="!edit_mode || paramType(p_key) != 'int'"
              class="text-h3 highlight">
              {{ paramHumanValue(p_key, p_value) }}
            </div>
            <q-input
              v-else
              type="number" min="0"
              :readonly="!edit_mode"
              :model-value="paramHumanValue(p_key)"
              @update:model-value="(value) => updateParam(p_key, value)">
            </q-input>
            <div class="q-mt-sm">
              {{ paramValueDesc(p_key, p_value) }}
            </div>
          </div>
        </template>

        <!-- OTHER OPTIONS -->
        <template v-if="paramType(p_key) != 'int' && edit_mode">
          <q-list>
            <q-item
              v-for="(value, index) in paramOtherValues(p_key, p_value)"
              :key="index"
              clickable
              v-ripple
              @click="updateParam(p_key, value)"
            >
              <q-item-label class="q-pa-lg">
                <div class="text-h5 highlight q-mb-sm">
                  {{ paramHumanValue(p_key, value) }}
                </div>
                <div>
                  {{ paramValueDesc(p_key, value) }}
                </div>
              </q-item-label>
            </q-item>
          </q-list>
        </template>
      </q-expansion-item>
    </template>
  </q-list>
</template>

<script>
import params_map from '@/lib/PhaseParams.js'

export default {

  name: 'ProcessParameters',

  props: {
    edit_mode: {
      type: Boolean,
      required: true
    },
    params: {
      type: Object,
      required: true
    }
  },

  data () {
    return {
      expansion_map: null
    }
  },

  methods: {
    paramHumanName(param_key) {
      return this.$t(`phase.params.${param_key}.title`)
    },

    paramType(param_key) {
      return params_map[param_key].type
    },

    updateExpansionMap(param_key, expanded) {
      if (expanded) {
        this.expansion_map = param_key
      }
      else {
        this.expansion_map = null
      }
    },

    paramHumanValue(param_key, value_key) {
      if (this.paramType(param_key) == 'int') {
        return this.params[param_key]
      }
      return this.$t(`phase.params.${param_key}.${value_key}.title`)
    },

    paramValueDesc(param_key, value_key) {
      if (this.paramType(param_key) == 'int') {
        return this.$t(`phase.params.${param_key}.desc`)
      }
      else return this.$t(`phase.params.${param_key}.${value_key}.desc`)
    },

    paramOtherValues(param_key, param_value) {
      const param_all_values = params_map[param_key].values
      return param_all_values.filter(v => v != param_value)
    },

    updateParam(param_key, value) {
      this.$emit('update', {
        param: param_key,
        value,
      })
      this.expansion_map = null
    },
  },

  watch: {
    edit_mode (newValue, oldValue) {
      if (newValue == false && oldValue == true) {
        this.expansion_map = null
      }
    }
  }
}
</script>

<style lang="css" scoped>
</style>
