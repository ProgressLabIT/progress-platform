<template>
  <v-container fluid ref="container" class="pa-0 fill-height" id="table_container">
    <v-data-table
      id="wo-list"
      dense
      :headers="table_headers"
      :items="filtered_wo_list"
      loading-text="Recupero dati in corso..."
      fixed-header  
      :height="table_height"
      disable-pagination
      hide-default-footer
      class="fill">

      <template v-slot:item="{ item }">
        <!-- <tr @dblclick="$emit('showDetails', item.wo_code)"> -->
        <tr @dblclick="showWorkOrderScreen(item.wo_code)">
          <td v-for="(header, index) in table_headers" :key="index"
            :class="header.value.includes('qt') ? 'text-right' : '' ">
            
            <template v-if="header.value === 'progress'">
              <v-row no-gutters align="center" >
                <v-col>
                  <v-progress-linear 
                    dense 
                    :value="item.progress"
                    :color="woBarColor(item)">
                  </v-progress-linear>
                </v-col>
                <v-col cols="auto" class="ml-4">
                  {{ item.progress }}%
                </v-col>
              </v-row>
            </template>
            
            <template v-else-if="header.value === 'active_phases'">
              
              <v-tooltip bottom v-if="typeof item.active_phases === 'object'">
                <template v-slot:activator="{on}">
                  <span class="font-italic" v-on="on">Multiple</span>
                </template>
                <div v-for="(phase, phase_index) in item.active_phases" :key="phase_index">
                  {{ phase }}
                </div>
              </v-tooltip>

              <span v-else>{{ item.active_phases }}</span>
            </template>

            <template v-else>{{ item[header.value] }}</template>
          </td>
        </tr>
      </template>

    </v-data-table>
  </v-container>
</template>

<script>
import multiMatch from '@/lib/MultiFieldSearch.js'
import wo_list from '@/dummy_data/WorkOrders.json'

export default {

  name: 'WorkOrderList',

  props: ['filters'],

  data () {
    return {
      table_headers: [
        { value: 'wo_code', text: 'OP'},
        { value: 'wo_line', text: 'RIGA', },
        { value: 'product_code', text: 'PRODOTTO'},
        { value: 'progress', text: 'AVANZAMENTO', width: '30%' },
        { value: 'completed_qt', text: 'QC', align: 'end'},
        { value: 'total_qt', text: 'QT', align: 'end'},
        { value: 'remaining_qt', text: 'QR', align: 'end'},
        { value: 'active_phases', text: 'FASE'},
      ],
      table_height: '85vh',
      wo_list: wo_list,
    }
  },

  computed: {
    filtered_wo_list() {
      return this.wo_list.filter( wo => {
        
        // Define wo fields to use with the text search
        const search_fields = ['wo_code', 'wo_line', 'product_code', 'active_phases']
        
        /* 
        Initialize filter results. 
        If any false will be found in this array the filter function will return false
        */
        const filter_match_map = []

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
            case 'not_started':
            case 'on_tme':
            case 'late':
            case 'critical':
            case 'queued':
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
      // const this_route = this.$route
      const to_route = {
        name: 'workOrderHome',
        params: {
          wo_key: wo_key,
        },
        query: {
          back_to: this.$route.name
        }
      }
      // console.log({this_route}, {to_route})
      this.$router.push(to_route)
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