<template>
  <!-- TODO: This component is not used anywhere -->
  TEST
</template>

<script>
import { cloneDeep as _cloneDeep } from 'lodash';
export default {
  name: 'ProductParamsCard',

  props: {
    product: {
      type: Object,
      required: true,
    },
    // eslint-disable-next-line vue/no-unused-properties
    editMode: {
      type: Boolean,
      default: false,
    },
  },

  data() {
    return {
      // Map performances for temporary population in created hook
      time_perfs: ['processing_time', 'throughput_time'],

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

      //   cost: {
      //     name: 'Costo',
      //     target: 58000,
      //     average: 58780,
      //   }
      // }
    };
  },

  computed: {
    params() {
      return {
        active: this.$t('status'),
        technical_batch_qt: this.$t('product.technical_batch'),
        minimum_order_qt: this.$t('product.minimum_order'),
        processing_time: this.$t('performance.processing_time.medium'),
        throughput_time: this.$t('performance.throughput_time.medium'),
        cost: this.$t('cost.label'),
      };
    },

    perfs() {
      return [...this.time_perfs, 'cost'];
    },

    temp_params() {
      let temp = _cloneDeep(this.product);

      let temp_params = Object.fromEntries(
        Object.entries(temp)
          // keep only keys included in the param object
          .filter((e) => e[0] in this.params)

          .map(([k, v]) => {
            // add the translated name
            let new_value = {
              name: this.params[k],
              value: v,
            };

            // if time related param, populate hour and minute fields
            const is_time_perf = this.time_perfs.includes(k);
            if (is_time_perf) {
              let target = this.$options.filters.duration(temp[k].target, {
                returnValue: 'object',
              });
              new_value.value.hours = target.h;
              new_value.value.minutes = target.m;
            }
            return [k, new_value];
          }),
      );
      return temp_params;
    },

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
    getTargetTime(event) {
      const msPerMinute = 1000 * 60;
      const msPerHour = msPerMinute * 60;

      // $refs returns an array
      const [param, hm] = event.target.id.split('/');

      let hours = null;
      let minutes = null;

      switch (hm) {
        case 'hours':
          hours = event.target.value;
          minutes = this.$refs[`${param}/minutes`][0].value;
          break;

        case 'minutes':
          hours = this.$refs[`${param}/hours`][0].value;
          minutes = event.target.value;
          break;
      }

      const new_target = hours * msPerHour + minutes * msPerMinute;
      return new_target;
    },

    updateTarget(param, event) {
      if (this.time_perfs.includes(param)) {
        const target = this.getTargetTime(event);
        this.$store.commit('UPDATE_TEMP_TARGET', { param, new_target: target });
      } else if (param == 'cost') {
        this.$store.commit('UPDATE_TEMP_TARGET', {
          param,
          new_target: event.target.value,
        });
      }
    },

    updateParam(param, new_value) {
      this.$store.commit('UPDATE_TEMP_PARAMETER', { param, new_value });
    },

    // updateTempHoursMinutes(param) {
    //   let target = this.duration( param.target, { returnValue: 'object' })
    //   param.temp_hours = target.h
    //   param.temp_minutes = target.m
    // }
  },
};
</script>
