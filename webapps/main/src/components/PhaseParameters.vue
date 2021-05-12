<template>
  <v-container fluid>
      <v-expansion-panels flat hover tile accordion :disabled="!edit_mode" v-model="expansion_map">

        <v-expansion-panel
          v-for="(p_value, p_key) in phase_params" :key="p_key"
          :readonly="paramType(p_key) == 'int'">

          <v-expansion-panel-header :hide-actions="paramType(p_key) == 'int'">
            <template v-slot:default="{ open }">
              <v-container>
                <v-row>
                  <v-col cols="auto">
                    <h5 class="text-uppercase mb-3" :color="$theme.white_low">{{ paramHumanName(p_key, p_value) }}</h5>

                    <h3 v-if="!edit_mode || paramType(p_key) != 'int'" class="highlight mb-6">{{ paramHumanValue(p_key, p_value) }}</h3>
                    <v-text-field v-else
                      type="number" min="0"
                      :value="paramHumanValue(p_key)"
                      @blur="updateParam(p_key, $event.target.value)">
                    </v-text-field>

                    <p>{{ paramValueDesc(p_key, p_value) }}</p>
                  </v-col>
                </v-row>
              </v-container>
            </template>
          </v-expansion-panel-header>

          <v-expansion-panel-content v-if="paramType(p_key) != 'int'">
            <v-container>
              <v-hover v-slot:default="{ hover }"
                v-for="(value, index) in paramOtherValues(p_key, p_value)" :key="index">
                <v-row
                  :class="hover && edit_mode ? 'hover-highlight' : ''"
                  :style="edit_mode ? 'cursor:pointer' : '' "
                  @click="edit_mode ? updateParam(p_key, value) : null">
                  <v-col cols="auto" >
                    <h5 class="highlight mb-1">{{ paramHumanValue(p_key, value) }}</h5>
                    <p class="body-2">{{ paramValueDesc(p_key, value) }}</p>
                  </v-col>
                </v-row>
              </v-hover>
            </v-container>
          </v-expansion-panel-content>

          <v-divider></v-divider>

        </v-expansion-panel>

      </v-expansion-panels>

   </v-container>
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
      return this.$tc(`phase.params.${param_key}.title`)
    },

    paramType(param_key) {
      return params_map[param_key].type
    },

    paramHumanValue(param_key, value_key) {
      if (this.paramType(param_key) == 'int') {
        return this.phase_params[param_key]
      }
      return this.$tc(`phase.params.${param_key}.${value_key}.title`)
    },

    paramValueDesc(param_key, value_key) {
      // const param_value = this.phase_params[param_key]
      if (this.paramType(param_key) == 'int') {
        return this.$tc(`phase.params.${param_key}.desc`)
      }
      else return this.$tc(`phase.params.${param_key}.${value_key}.desc`)
    },

    paramOtherValues(param_key, param_value) {
      const param_all_values = params_map[param_key].values
      return param_all_values.filter(v => v != param_value)
    },

    updateParam(param_key, value) {
      if (param_key === 'step_check') {
        if (!this.phase_data.steps.length && value != 'none') {
          window.alert(this.$options.filters.capitalize(
            this.$tc('phase.alerts.add_steps_first')
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
</style>
