<template>
  <v-container fluid>
      <v-expansion-panels flat hover multiple tile accordion>
        
        <v-expansion-panel 
          v-for="(p_value, p_key) in phase_params" :key="p_key"
          :readonly="paramType(p_key) == 'int'">
          
          <v-expansion-panel-header :hide-actions="paramType(p_key) == 'int'">
            <template v-slot:default="{ open }">
              <v-container>
                <v-row>
                  <v-col cols="auto">
                    <h5 class="text-uppercase mb-3">{{ paramHumanName(p_key) }}</h5>
                    <h3 class="highlight mb-6">{{ paramHumanValue(p_key) }}</h3>
                    <p>{{ paramValueDesc(p_key) }}</p>  
                  </v-col>
                </v-row>
              </v-container>
            </template> 
          </v-expansion-panel-header>
          
          <v-expansion-panel-content v-if="paramType(p_key) != 'int'">
            <v-container>
            <v-row v-for="(value, index) in paramOtherValues(p_key)" :key="index">
              <v-col cols="auto">
                <h5 class="highlight mb-1">{{ value.value_name }}</h5>
                <p class="body-2">{{ value.value_desc }}</p>
              </v-col>
            </v-row>
            </v-container>
          </v-expansion-panel-content>
  
          <v-divider></v-divider>
        
        </v-expansion-panel>

      </v-expansion-panels>

   </v-container> 
</template>

<script>
import phase_params_map from '@/lib/PhaseParams.js'
export default {

  name: 'PhaseParameters',

  data() {
    return {
      expansion_map: []
    }
  },

  computed: {
    
    product_key() {
      return this.$route.params.item_key
    },

    product_data() {
      return this.$store.getters.productData(this.product_key)
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

    params_map() {
      return phase_params_map
    }

    // params() {
    //   let phase_params = {}
    //   const param_values = this.phase_data.params
    //   console.log(phase_params_map)
    //   // Remap param values with human readable version and additional description
    //   Object.keys(param_values).forEach(p => {

    //     if (phase_params_map[p].type == 'int') {
    //       const param_4_humans = phase_params_map[p].values.get(param_values[p])
    //     }
    //     phase_params[p] = {
    //       title: phase_params_map[p].title,
    //       type: phase_params_map[p].type,
    //       value: param_4_humans.value_name
    //     }
    //   })
    //   return phase_params
    // }
  },

  methods: {
    paramHumanName(param_key) {
      return phase_params_map[param_key].title
    },

    paramType(param_key) {
      return phase_params_map[param_key].type
    },

    paramHumanValue(param_key) {
      const param_value = this.phase_params[param_key]
      if (this.paramType(param_key) == 'int') {
        return this.phase_params[param_key]
      }
      return phase_params_map[param_key].values.get(param_value).value_name
    },

    paramValueDesc(param_key) {
      const param_value = this.phase_params[param_key]
      if (this.paramType(param_key) == 'int') {
        return phase_params_map[param_key].description
      }
      else return phase_params_map[param_key].values.get(param_value).value_desc
    },

    paramOtherValues(param_key) {
      const param_value = this.phase_params[param_key]
      const other_values_map = phase_params_map[param_key].values
      const other_values_array = []
      other_values_map.forEach( (v, k) => {
        if (k != param_value) {
          other_values_array.push(v)
        }
      })
      return other_values_array
    }

  }
};
</script>

<style lang="css" scoped>
</style>
