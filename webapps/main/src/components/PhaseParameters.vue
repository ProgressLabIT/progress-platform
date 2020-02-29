<template>
  <v-container fluid>
      <v-expansion-panels flat hover tile accordion>
        
        <v-expansion-panel 
          v-for="(p_value, p_key) in phase_params" :key="p_key"
          :readonly="paramType(p_key) == 'int'">
          
          <v-expansion-panel-header :hide-actions="paramType(p_key) == 'int'">
            <template v-slot:default="{ open }">
              <v-container>
                <v-row>
                  <v-col cols="auto">
                    <h5 class="text-uppercase mb-3">{{ paramHumanName(p_key, p_value) }}</h5>
                    
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
                v-for="[v_key, value] in paramOtherValues(p_key, p_value)" :key="v_key">  
                <v-row 
                  :class="hover && edit_mode ? 'hover-highlight' : ''"
                  :style="edit_mode ? 'cursor:pointer' : '' "
                  @click="edit_mode ? updateParam(p_key, v_key) : null">
                  <v-col cols="auto" >
                    <h5 class="highlight mb-1">{{ value.name }}</h5>
                    <p class="body-2">{{ value.description }}</p>
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

  props: ['edit_mode'],

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
  },

  methods: {
    paramHumanName(param_key) {
      return params_map[param_key].title
    },

    paramType(param_key) {
      return params_map[param_key].type
    },

    paramHumanValue(param_key, value_key) {
      // const param_value = this.phase_params[param_key]
      if (this.paramType(param_key) == 'int') {
        return this.phase_params[param_key]
      }
      return params_map[param_key].values.get(value_key).name
    },

    paramValueDesc(param_key, value_key) {
      // const param_value = this.phase_params[param_key]
      if (this.paramType(param_key) == 'int') {
        return params_map[param_key].description
      }
      else return params_map[param_key].values.get(value_key).description
    },

    paramOtherValues(param_key, param_value) {
      /* must update to keep map structure so that keys can be used when 
         updating param */
      // const param_current_value = this.phase_params[param_key]
      const param_all_values = params_map[param_key].values
      const param_alternative_values = new Map(
        [...param_all_values.keys()]
          .filter( k => k != param_value )
          .map( k => [k, param_all_values.get(k)] )
      )
      return param_alternative_values
    },

    updateParam(param_key, value) {
      this.$store.commit('UPDATE_PHASE_PARAMS', {
        phase_no: this.current_phase,
        param: param_key,
        value: value,
      })
    }

  }
};
</script>

<style lang="css" scoped>
</style>
