<template>
  <div>TEST</div>
</template>

<script>
import params_map from '@/lib/PhaseParams.js'
export default {

  name: 'PhaseParameters',

  props: ['edit_mode', 'phase', 'product_data'],

  data() {
    return {
      expansion_map: null
    }
  },

  computed: {

    product_key() {
      return this.$route.params.product_key
    },

    current_phase() {
      return this.product_data.last_phase
    },

    phase_data() {
       return this.$store.state.process.temp[this.current_phase]
    },

    phase_params() {
      return this.phase_data.params
    },
  },

  methods: {
    paramHumanName(param_key) {
      return this.$t(`phase.params.${param_key}.title`)
    },

    paramType(param_key) {
      return params_map[param_key].type
    },

    paramHumanValue(param_key, value_key) {
      if (this.paramType(param_key) == 'int') {
        return this.phase_params[param_key]
      }
      return this.$t(`phase.params.${param_key}.${value_key}.title`)
    },

    paramValueDesc(param_key, value_key) {
      // const param_value = this.phase_params[param_key]
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
      if (param_key === 'step_check') {
        if (!this.phase_data.steps.length && value != 'none') {
          window.alert(this.$options.filters.capitalize(
            this.$t('phase.alerts.add_steps_first')
          ))
          this.expansion_map = null
          return
        }
      }

      this.$store.commit('UPDATE_PHASE_PARAMS', {
        phase_index: this.current_phase,
        param: param_key,
        value: value,
      })
    },
  },

  watch: {
    edit_mode: function (newValue, oldValue) {
      if (newValue == false && oldValue == true)
      this.expansion_map = null
    }
  }
};
</script>

<style lang="css" scoped>
.theme--dark.v-expansion-panels .v-expansion-panel {
  background-color: var(--surface2);
}
</style>
