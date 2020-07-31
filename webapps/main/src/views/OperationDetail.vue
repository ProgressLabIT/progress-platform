<template>
  <v-container fill-height class="px-12 py-8">
    <v-row class="fill-height">
      <v-col >
      
    
        <!-- OPERATION NAME & ACTION BUTTONS -->
        <v-row class="flex-grow-0 mx-0" align="center">
          <template v-if="!edit_mode">
            <h2 class="text-uppercase display highlight mr-6">
              {{ operation.name }}
            </h2>
            
            <v-spacer></v-spacer>

            <BaseTooltipIcon
              icon="mdi-pencil"
              tooltip="Modifica"
              :color="$theme.blue"
              @iconClick="edit_mode=true">
            </BaseTooltipIcon>

            <BaseTooltipIcon
              icon="mdi-delete"
              tooltip="Archivia"
              :color="$theme.red"
              @iconClick="showDelete">
            </BaseTooltipIcon>            
          
          </template>

          <template v-else>
            <v-col cols="4" class="px-0">
              <h5 class="mb-2">NOME</h5>        
              <v-text-field 
                single-line
                hide-details 
                v-model="temp_metadata.name"
                class="pt-0">
              </v-text-field>
            </v-col>

            <v-spacer></v-spacer>
            
            <v-btn small :color="$theme.blue" @click="save" :loading="saving">
              SALVA
            </v-btn>
            <v-btn small :color="$theme.grey" @click="cancel" class="ml-2">
              ANNULLA
            </v-btn>
            
          </template>
        </v-row>
        
        <v-row class="flex-grow-1 mt-12 mx-0" align="start">
          <v-col cols="4" class="d-flex flex-column px-0">

            <!-- OPERATION CODE -->
            <h5 class="mb-2">CODICE</h5>        
            <span v-if="!edit_mode" class="mt-2 body-2">
              {{ operation.code || '-' }}
            </span>
            <v-text-field
              v-else
              single-line
              hide-details
              v-model="temp_metadata.code"
              class="pt-0">
            </v-text-field>


            <!-- DESCRIPTION -->
            <h5 class="mt-8 mb-2">DESCRIZIONE</h5>
            <span v-if="!edit_mode" class="mt-2 body-2">
              {{ operation.description || '-' }}
            </span>
            <v-textarea
              v-else
              auto-grow
              single-line
              hide-details
              v-model="temp_metadata.description"
              class="pt-0">
            </v-textarea>

          </v-col>  

          <v-col class="d-flex flex-column flex-grow-1 pl-12 pr-0">
            <h5>PARAMETRI DI DEFAULT</h5>
            <p class='medium mt-2'>Le nuove fasi associate a questa operazione verranno create con i parametri indicati qui. I parametri specifici della fase potranno essere modificati in maniera indipendente dopo la creazione.</p>
              <v-expansion-panels flat hover tile accordion 
                :disabled="!edit_mode" 
                v-model="expansion_map">
                
                <v-expansion-panel 
                  v-for="(p_value, p_key) in temp_params" :key="p_key"
                  :readonly="paramType(p_key) == 'int'">
                  
                  <v-expansion-panel-header 
                    :hide-actions="paramType(p_key) == 'int'"
                    class="px-0 mx-n3">
                    <template v-slot:default="{ open }">
                      <v-container>
                        <v-row>
                          <v-col cols="auto">
                            <h5 class="text-uppercase mb-3" :color="$theme.white_low">
                              {{ paramHumanName(p_key, p_value) }}
                            </h5>
                            
                            <h3 
                              v-if="!edit_mode || paramType(p_key) != 'int'" 
                              class="highlight mb-6">
                              {{ paramHumanValue(p_key, p_value) }}
                            </h3>
                            <v-text-field v-else 
                              type="number" min="1"
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
          
          </v-col>
        </v-row>
      

      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import params_map from '@/lib/PhaseParams.js'
import BaseTooltipIcon from '@/components/BaseTooltipIcon'

export default {

  name: 'OperationDetail',

  components: { BaseTooltipIcon },

  props: {
    operation: {
      type: Object
    }
  },

  data () {
    return {
      expansion_map: undefined,
      edit_mode: false,
      saving: false,
      temp_metadata: {
        name: '',
        code: '',
        description: ''
      },
      temp_params: {
        parallel_job_allowed: true,
        step_check: 'none',
        step_check_force_order: false,
        production_batch_qt: 1,
      }
    }
  },


  methods: {
    setTempData(){
      Object.keys(this.temp_metadata).forEach( key => {
        if (key in this.operation) {
          this.$set(this.temp_metadata, key, this.operation[key])
        }
      })
      Object.keys(this.temp_params).forEach( key => {
        const saved_params = this.operation.default_phase_parameters
        if (key in saved_params) {
          this.$set(this.temp_params, key, saved_params[key])
        }
      })
    },

    paramHumanName(param_key) {
      return params_map[param_key].title
    },

    paramType(param_key) {
      return params_map[param_key].type
    },

    paramHumanValue(param_key, value_key) {
      if (this.paramType(param_key) == 'int') {
        return this.temp_params[param_key]
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
      const param_all_values = params_map[param_key].values
      const param_alternative_values = new Map(
        [...param_all_values.keys()]
          .filter( k => k != param_value )
          .map( k => [k, param_all_values.get(k)] )
      )
      return param_alternative_values
    },

    updateParam(param_key, new_value) {
      this.temp_params[param_key] = new_value
    },

    cancel() {
      this.saving = true
      // this.setTempData()
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
      this.$router.push({
        name: 'operationDelete',
        params: { user_key: this.user._key }
      })
    },
  },

  watch: {
    edit_mode() {
      this.setTempData()
    }
  }
}
</script>

<style lang="css" scoped>
</style>