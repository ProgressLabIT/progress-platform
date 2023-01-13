<template>
  <v-container fluid ref="container" class="pa-0 fill-height" id="table_container">
    <v-data-table
      id="wo-list"
      dense
      :headers="table_headers"
      :items="filtered_wo_list"
      :options="{sortBy: ['priority']}"
      :loading-text="$tc('loading_text') | capitalize"
      fixed-header  
      :height="table_height"
      disable-pagination
      hide-default-footer
      class="fill">

      <template v-slot:item="{ item }">
        <!-- <tr @dblclick="$emit('showDetails', item.wo_code)"> -->
        <tr 
          @dblclick="showWorkOrderScreen(item._key)" :key="item._key">
          <td 
            v-for="(header, index) in table_headers" :key="index"
            :class="header.value.includes('qt') ? 'text-right' : '' ">
            
            <template v-if="header.value === 'progress'">
              <v-row no-gutters align="center" >
                <v-col cols="8">
                  <v-progress-linear 
                    dense 
                    :value="item.progress"
                    :color="woBarColor(item)">
                  </v-progress-linear>
                </v-col>
                <v-col cols="2" class="pl-4 text-right">
                  {{ item.progress }}%
                </v-col>
                <v-col cols="2" class="text-right pl-2 pointer">
                  <v-icon small 
                    v-if="item.critical" 
                    :color="$theme.red"
                    @click="$emit('criticalOnly')">
                    mdi-alert-octagon
                  </v-icon>
                  <v-icon small 
                    v-else-if="!item.on_time" 
                    :color="$theme.orange"
                    @click="$emit('lateOnly')">
                    mdi-alert
                  </v-icon>
                </v-col>
              </v-row>
            </template>
            
            <!-- DUE BY - with date formatting -->
            <template v-else-if="header.value==='due_by'">
              {{ item[header.value] | shortDateString('it') }}
            </template>

            <!-- OTHER FIELDS -->
            <template v-else>{{ item[header.value] || '' }}</template>
          </td>
        </tr>
      </template>

    </v-data-table>
  </v-container>
</template>

<script>
import Sortable from 'sortablejs'
import multiMatch from '@/lib/MultiFieldSearch.js'
import { throttle as _throttle } from 'lodash'

export default {

  name: 'WorkOrderList',

  props: {
    filters: {
      type: Object,
      required: true,
      default: () => { return {
        "search_string":"",
        "started":true,
        "queued":true,
        "on_time":true,
        "late":true,
        "active":true,
        "idle":true,
        "critical":true,
        "not_critical":true
      }}
    }
  },

  data () {
    return {
      table_height: '85vh',
    }
  },

  computed: {

    table_headers() {
      return [
        { 
          value: 'sequence', 
          text: this.$tc('work_order.list_headers.sequence').toUpperCase()},
        { 
          value: 'wo_code', 
          text: this.$tc('work_order.wo_code').toUpperCase()},
        {
          value: 'project_code',
          text: this.$tc('project').toUpperCase()
        },
        { 
          value: 'product_code', 
          text: this.$tc('work_order.list_headers.product_code').toUpperCase()},
        { 
          value: 'progress', 
          text: this.$tc('work_order.list_headers.progress').toUpperCase(), 
          width: '40%' },
        { 
          value: 'qt_completed', 
          text: this.$tc('work_order.list_headers.qt_completed').toUpperCase(), 
          align: 'end'},
        { 
          value: 'qt_planned', 
          text: this.$tc('work_order.list_headers.qt_planned').toUpperCase(), 
          align: 'end'},
        { 
          value: 'qt_remaining', 
          text: this.$tc('work_order.list_headers.qt_remaining').toUpperCase(), 
          align: 'end'},
        { 
          value: 'due_by', 
          text: this.$tc('work_order.list_headers.due_by').toUpperCase(), 
          sort: this.sortDate
        }
      ]
    },

    temp_queue() {
      return this.$store.state.workorder.temp_queue
    },

    wo_data_map() {
      return this.$store.state.workorder.wo_map
    },

    wo_list() {
      return this.temp_queue.map( wo_key => this.wo_data_map[wo_key])
    },

    filtered_wo_list() {
      return this.wo_list.filter( wo => {
        
        // Define wo fields to use with the text search
        const search_fields = ['wo_code', 'product_code', 'project_code']
        
        /* 
        Initialize filter results. 
        If any false will be found in this array the filter function will return false
        */
        let filter_match_map = []

        for (const [filter, value] of Object.entries(this.filters)) {          
          // by default show wo in the list
          let match = true
          
          switch (filter) {
            // Perform text search in the defined fields
            case 'search_string':
              match = multiMatch(this.filters.search_string, wo, search_fields)
              break

            case 'started':
              if (!value && wo.status === 'started') match = false
              break

            case 'queued':
              if (!value && ['created', 'planned'].includes(wo.status)) match = false
              break

            case 'on_time':
              if (!value && wo.on_time) match = false
              break 

            case 'late':
              if (!value && !wo.on_time) match = false
              break

            case 'critical':
              if (!value && wo.critical) match = false
              break

            case 'not_critical':
              if (!value && !wo.critical) match = false
              break

            case 'active':
              // Do not show if control is false and wo is active
              if (!value && wo.active) match = false
              break

            case 'idle':
              // Do not show if control is false and wo is not active
              if (!value && !wo.active) match = false
              break
          }

          // add result of the specific filter to the map
          filter_match_map.push(match)
        }

        // Return false and exclude wo from list if any filter returned false
        return !filter_match_map.some( i => i === false )
      })
    }
  },

  methods: {
    woBarColor(wo) {
      if (wo.active === false) return this.$theme.grey
      else return this.$theme.blue
    },

    showWorkOrderScreen(wo_key) {
      this.$emit('itemDblClick', {
        wo_key,
        back_to_route_name: this.$route.name
      })
    },

    sortDate(a,b) {
      // equal items sort equally
      if (a === b) {
          return 0
      }
      // nulls sort after anything else
      else if (a === null) {
          return 1
      }
      else if (b === null) {
          return -1
      }
      // standard sorting
      else { 
          return a < b ? 1 : -1
      }

    }
  },

  mounted() {
    // set table height explicitly and resize with window
    const resizeTable = () => this.table_height = this.$refs.container.clientHeight
    resizeTable()
    window.onresize = _throttle(resizeTable, 100)

    // make the table rows draggable
    let table = document.querySelector(".v-data-table tbody")
    const _self = this
    Sortable.create(table, {
      ..._self.$store.state.drag_options,
      // use onEnd event provided by SortableJs library
      onEnd: ({ newIndex, oldIndex }) => {
        _self.$emit('editing')
        _self.$store.commit('UPDATE_TEMP_QUEUE', { newIndex, oldIndex })
      }
    })
  },
}
</script>

<style lang="css" scoped>
#wo-list {
  background-color: transparent !important;
}

#wo-list >>> th {
  background-color: var(--bg-color) !important;
}

#wo-list >>> tr:not(:last-child) {
  border: none !important;
}

#wo-list >>> table {
  border-color: transparent !important;
}

#wo-list >>> td {
  border: none;
}

#wo-list >>> td {
  padding: 8px 16px;
}
</style>
