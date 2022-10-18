<template>
  <v-container class="px-5 py-4 fill"> 
    <h5 class="display medium highlight mb-6">Parametri</h5>          

    <v-row v-for="(p, key) in params" :key="key">
      
      <!-- PARAM NAME -->
      <v-col cols="auto" class="body-2">
        {{ perfs.includes(key) ? $tc('product_params.target') : '' | capitalize }} {{ p }}
      </v-col>
      
      <v-spacer></v-spacer>

      <!-- PARAM VALUE -->
      <template v-if="key == 'active_state'">
        <v-col cols="auto" v-if="edit_mode">
          <v-switch 
            hide-details flat
            :color="$theme.blue"
            :input-value="temp_params[key].value"
            @change="updateParam('active', $event)"
            class="ma-0 pa-0">
          </v-switch>   
        </v-col>
        <v-col cols="4" class="body-2 highlight text-right" :style="`color: ${$theme.text_high}`">
          <div v-if="temp_params[key].value">
            {{ $tc('active') | capitalize }}
          </div>
          <div v-else>
            {{ $tc('inactive') | capitalize }}
          </div>
        </v-col>
      </template>

      <v-col v-else cols="5" class="text-right body-2 highlight">
        <template v-if="time_perfs.includes(key)">
          <template v-if="!edit_mode">
            {{ temp_params[key].value.target | duration({ precision:'m' }) }}
          </template>
          <template v-else>
            <v-row no-gutters>
              <v-col>
                <v-text-field 
                  :ref="`${key}/hours`"
                  :id="`${key}/hours`"
                  type="number" min="0"
                  hide-details reverse dense
                  prefix="h"
                  :value="temp_params[key].value.hours"
                  class="my-0 py-0"
                  @blur="updateTarget(key, $event)">
                </v-text-field>  
              </v-col>
              <v-col >
                <v-text-field 
                  :ref="`${key}/minutes`"
                  :id="`${key}/minutes`"
                  type="number" min="0"
                  hide-details reverse dense
                  :value="temp_params[key].value.minutes"
                  prefix="m"
                  class="my-0 py-0"
                  @blur="updateTarget(key, $event)">
                </v-text-field>
              </v-col>
            </v-row>            
          </template>
        </template>

        <template v-else-if="key == 'cost'">
          <template v-if="!edit_mode">
            € {{ temp_params[key].value.target }}
          </template>
          <v-text-field v-else 
            type="number" min="0"
            hide-details reverse dense
            :value="temp_params[key].value.target"
            prefix="€"
            class="my-0 py-0"
            @blur="updateTarget(key, $event)">
          </v-text-field>
        </template>

        <template v-else>
          <span v-if="!edit_mode">
            {{ temp_params[key].value }}
          </span>
          <v-text-field v-else 
            type="number" min="0"
            hide-details reverse dense
            :value="temp_params[key].value"
            class="my-0 py-0"
            @blur="updateParam(key, $event.target.value)">
          </v-text-field>
        </template>
      </v-col>

      <v-col cols="auto">
        <v-icon x-small :color="$theme.text_low">info</v-icon>
      </v-col>
    </v-row>                    

  </v-container>
</template>

<script>
import { cloneDeep as _cloneDeep } from 'lodash'
export default {

  name: 'ProductParamsCard',

  props: ['product', 'edit_mode'],

  data () {
    return {

      // Map performances for temporary population in created hook
      time_perfs: ['processing_time', 'throughput_time', 'lead_time'],

      /**
       * PRODUCT PERFORMANCE ARE TEMPORARY HIDDEN UNTIL A PROPER CALCULATION IS
       * DEVELOPED IN THE BACKEND
       */

      // temp_params: { 
      //   active: {
      //       name: 'Stato',
      //       value: true,
      //   },

      //   technical_batch: {
      //     name: 'Lotto tecnico',
      //     value: 1
      //   },
        
      //   min_order: {
      //     name: 'Ordine minimo',
      //     value: 1
      //   },
        
      //   processing_time: {
      //     name: 'TP',
      //     target: 0,
      //     average: 0,
      //     temp_hours: 0,
      //     temp_minutes: 0,
      //   },
        
      //   throughput_time: {
      //     name: 'TA',
      //     target: 0,
      //     average: 0,
      //     temp_hours: 0,
      //     temp_minutes: 0,
      //   },
        
      //   lead_time: {
      //     name: 'TE',
      //     target: 0,
      //     average: 0,
      //     temp_hours: 0,
      //     temp_minutes: 0,
      //   },
        
      //   cost: {
      //     name: 'Costo',
      //     target: 58000,
      //     average: 58780,
      //   }
      // }
    }
  },

  computed: {

    params() {
      return {
        active: this.$tc('status'),
        technical_batch_qt: this.$tc('product.technical_batch'),
        minimum_order_qt: this.$tc('product.minimum_order'),
        processing_time: this.$tc('performance.processing_time.medium'),
        throughput_time: this.$tc('performance.throughput_time.medium'),
        lead_time: this.$tc('performance.lead_time.medium'),
        cost: this.$tc('cost.label')
      }
    },

    perfs() { return [...this.time_perfs, 'cost'] },
      
    temp_params() {
      let temp = _cloneDeep(this.product)

      let temp_params = Object.fromEntries(
        Object.entries(temp)
          // keep only keys included in the param object
          .filter( e => e[0] in this.params )

          .map( ([k,v]) => {
            // add the translated name
            let new_value = {
              name: this.params[k],     
              value: v
            }

            // if time related param, populate hour and minute fields
            const is_time_perf = this.time_perfs.includes(k)
            if (is_time_perf) {
              let target = this.$options.filters.duration( temp[k].target, { returnValue: 'object' })
              new_value.value.hours = target.h
              new_value.value.minutes = target.m
            }
            return [ k, new_value ]
          })
      )
      return temp_params
    }
    
    


    // perf_list() {
    //   return Object.fromEntries(
    //     Object.entries(this.temp_params).map(([k, v]) => {
          
    //       if ( this.perfs.includes(k) ) {
    //         let delta_abs = 
    //           k == 'cost' 
    //           ? v.average-v.target // cost delta
    //           : Math.ceil((v.average-v.target)/60000)*60000 // time deltas

    //         return [k, {
    //           ...v,
    //           delta_pc: (100*(v.average/v.target-1)).toFixed(2),
    //           delta_abs: delta_abs
    //         }]
    //       }

    //       else return          
    //   }))
    // },
  },

  methods: {

    capitalize(string) {
      return this.$options.filters.capitalize(string)
    },

    getTargetTime(event) {
      const msPerMinute = 1000 * 60
      const msPerHour = msPerMinute * 60

      // $refs returns an array
      const [param, hm] = event.target.id.split('/')

      let hours = null
      let minutes = null

      switch (hm) {
        case 'hours':
          hours = event.target.value
          minutes = this.$refs[`${param}/minutes`][0].value
          break

        case 'minutes':
          hours = this.$refs[`${param}/hours`][0].value
          minutes = event.target.value
          break
      }

      const new_target = hours * msPerHour + minutes * msPerMinute
      return new_target
    },

    updateTarget(param, event) {
      if (this.time_perfs.includes(param)) {
        const target = this.getTargetTime(event)
        this.$store.commit('UPDATE_TEMP_TARGET', { param, new_target: target })  
      }
      else if (param == 'cost') {
        this.$store.commit('UPDATE_TEMP_TARGET', { param, new_target: event.target.value })
      }
    },

    updateParam(param, new_value) {
      this.$store.commit('UPDATE_TEMP_PARAMETER', { param, new_value })
    },

   

    // updateTempHoursMinutes(param) {
    //   let target = this.duration( param.target, { returnValue: 'object' })
    //   param.temp_hours = target.h
    //   param.temp_minutes = target.m
    // } 
  },
}
</script>

<style lang="css" scoped>
</style>
