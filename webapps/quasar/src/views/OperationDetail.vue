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
              :tooltip="$tc('edit') | capitalize"
              :color="$theme.blue"
              @iconClick="edit_mode=true">
            </BaseTooltipIcon>

            <BaseTooltipIcon
              icon="mdi-delete"
              :tooltip="$tc('archive') | capitalize"
              :color="$theme.red"
              @iconClick="showDelete">
            </BaseTooltipIcon>            
          
          </template>

          <template v-else>
            <v-col cols="4" class="px-0">
              <h5 class="mb-2">{{ $tc('name') }}</h5>        
              <v-text-field 
                single-line
                hide-details 
                v-model="temp_metadata.name"
                class="pt-0">
              </v-text-field>
            </v-col>

            <v-spacer></v-spacer>
            
            <v-btn small :color="$theme.blue" @click="save" :loading="saving">
              {{ $tc('save') }}
            </v-btn>
            <v-btn small :color="$theme.grey" @click="cancel" class="ml-2">
              {{ $tc('cancel') }}
            </v-btn>
            
          </template>
        </v-row>
        
        <v-row class="flex-grow-1 mt-12 mx-0" align="start">
          <v-col cols="4" class="d-flex flex-column px-0">

            <!-- OPERATION CODE -->
            <h5 class="mb-2 text-uppercase">{{ $tc('code') }}</h5>        
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
            <h5 class="mt-8 mb-2 text-uppercase">{{ $tc('description') }}</h5>
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


            <!-- PRODUCTS USING OPERATION -->
            <!-- <h5 class="mt-8 mb-2">ESEGUITA PER</h5>
            <router-link 
              v-for="product in products_using_operation" 
              :key="product.code" 
              :to="goToProductProcess(product._key)"
              class="body-2">
              {{ product.code }}
            </router-link> -->
          </v-col>  

          <v-col class="d-flex flex-column flex-grow-1 pl-12 pr-0">
            
            <h5 class="text-uppercase">
              {{ $tc('operation.default_params_title') }}
            </h5>
            
            <p class='medium mt-2'>
              {{ $tc('operation.default_params_explainer') }}
            </p>

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
                          <h5 class="text-uppercase mb-3" :color="$theme.text_low">
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
          
          </v-col>
        </v-row>
      

      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import {capitalize as c} from '@/lib/filters.js'
import params_map from '@/lib/PhaseParams.js'
import BaseTooltipIcon from '@/components/BaseTooltipIcon'
import NonExistentOperationGuard from '@/mixins/NonExistentOperationGuard'

export default {

  name: 'OperationDetail',

  components: { BaseTooltipIcon },

  mixins: [NonExistentOperationGuard],

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
        max_offline: 60,
        parallel_job_allowed: true,
        step_check: 'none',
        step_check_force_order: false,
        production_batch_qt: 1,
      }
    }
  },

  computed: {
    products_using_operation() {
      return this.operation.used_for
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

    goToProductProcess(product_key) {
      return {
        name: 'productionProcess',
        params: { product_key },
        query: {
          back_to: this.$route.name, 
          param: `operation_key:${this.operation._key}`
        }
      }
    },

    paramHumanName(param_key) {
      return this.$tc(`phase.params.${param_key}.title`)
    },

    paramType(param_key) {
      return params_map[param_key].type
    },

    paramHumanValue(param_key, value_key) {
      if (this.paramType(param_key) == 'int') {
        return this.temp_params[param_key]
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
      if (this.products_using_operation.length) {
        const product_codes = this.products_using_operation.map( o => o.code )
        window.alert(c(this.$tc('operation.alerts.op_in_use') + ": " +  product_codes))
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
    edit_mode() {
      this.setTempData()
    }
  }
}
</script>

<style lang="css" scoped>
</style>
