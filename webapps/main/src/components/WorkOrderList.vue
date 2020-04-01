<template>
  <v-container fluid ref="container" class="pa-0 fill-height" id="table_container">
    <v-data-table
      id="wo-list"
      dense
      :headers="table_headers"
      :items="filtered_wo_list"
      :options="{sortBy: ['due_by', 'wo_code']}"
      loading-text="Recupero dati in corso..."
      fixed-header  
      :height="table_height"
      disable-pagination
      hide-default-footer
      class="fill">

      <template v-slot:item="{ item }">
        <!-- <tr @dblclick="$emit('showDetails', item.wo_code)"> -->
        <tr 
          @dblclick="showWorkOrderScreen(item._key)">
          <td 
            v-for="(header, index) in table_headers" :key="index"
            :class="header.value.includes('qt') ? 'text-right' : '' ">
            
            <template v-if="header.value === 'progress'">
              <v-row no-gutters align="center" >
                <v-col cols="9">
                  <v-progress-linear 
                    dense 
                    :value="item.progress"
                    :color="woBarColor(item)">
                  </v-progress-linear>
                </v-col>
                <v-col cols="2" class="pl-4 text-right">
                  {{ item.progress }}%
                </v-col>
                <v-col cols="1" class="text-right pl-2">
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
            
            <!-- <template v-else-if="header.value === 'active_phases'">
              
              <v-tooltip bottom v-if="item.active_phases.length > 1">
                <template v-slot:activator="{on}">
                  <span class="font-italic" v-on="on">Multiple</span>
                </template>
                <div v-for="(phase, phase_index) in item.active_phases" :key="phase_index">
                  {{ phase | capitalize_all }}
                </div>
              </v-tooltip>

              <span v-else class="text-truncate">
                {{ item.active_phases[0] | capitalize_all }}
              </span>
            </template>
 -->
            <!-- DUE BY - with date formatting -->
            <template v-else-if="header.value==='due_by'">
              {{ item[header.value] | shortDateString('it') }}
            </template>

            <!-- OTHER FIELDS -->
            <template v-else>{{ item[header.value] }}</template>
          </td>
        </tr>
      </template>

    </v-data-table>
  </v-container>
</template>

<script>
import multiMatch from '@/lib/MultiFieldSearch.js'
// import wo_list from '@/dummy_data/WorkOrders.json'

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
      table_headers: [
        { value: 'wo_code', text: 'CODICE'},
        { value: 'wo_line_no', text: 'RIGA', },
        { value: 'product_code', text: 'PRODOTTO'},
        { value: 'progress', text: 'AVANZAMENTO', width: '30%' },
        { value: 'qt_completed', text: 'QC', align: 'end'},
        { value: 'qt_planned', text: 'QP', align: 'end'},
        { value: 'qt_remaining', text: 'QR', align: 'end'},
        // { value: 'active_phases', text: 'FASE'},
        { value: 'due_by', text: 'ENTRO', }
      ],
      table_height: '85vh',
      // wo_list: wo_list,
    }
  },

  computed: {

    wo_list() {
      return this.$store.state.workorder.wo_list
    },

    // filter_match_map() {
    //   let filter_match_map
    // },

    filtered_wo_list() {
      return this.wo_list.filter( wo => {
        
        // Define wo fields to use with the text search
        const search_fields = ['wo_code', 'wo_line_no', 'product_code']
        
        /* 
        Initialize filter results. 
        If any false will be found in this array the filter function will return false
        */
        let filter_match_map = []

        for (const [filter, value] of Object.entries(this.filters)) {
        // for (const filter of Object.keys(this.filters)) {
          
          // by default show wo in the list
          let match = true
          
          switch (filter) {

            // Perform text search in the defined fields
            case 'search_string':
              match = multiMatch(this.filters.search_string, wo, search_fields)
              // console.log({wo}, "Search string: ", this.filters.search_string, {match})
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
    // Temporarily unused, until on_time data will be available
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
  },

  mounted() {
    // set table height explicitly and resize with window
    const resizeTable = () => this.table_height = this.$refs.container.clientHeight
    resizeTable()
    window.onresize = resizeTable
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