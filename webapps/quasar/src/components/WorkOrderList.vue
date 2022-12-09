<template>
  <div ref="container" id="table_container" class="q-px-sm">
    <q-table
      id="wo_list"
      :columns="columns"
      :rows="filtered_wo_list"
      row-key="_key"
      :style="`height: ${table_height}`"
      virtual-scroll
      hide-bottom
      dense
      separator="none"
      table-class="text-high"
      card-class="background no-shadow q-mt-sm"
      :rows-per-page-options="[0]">

      <!-- PROGRESS BAR -->
      <template #body-cell-progress="props">
        <q-td key="progress" :props="props">
          <div class="row items-center q-col-gutter-sm">
            <div class="col-9">
              <q-linear-progress
                :value="props.value / 100"
                :color="progressColor(props.row)"
                :buffer="1"
                size="4px">
              </q-linear-progress>
            </div>
            <span class="col-2 text-right">{{ props.value }} %</span>
          </div>
        </q-td>
        <!-- ADD ALERT ICONS HERE -->
      </template>

      <!-- ADD ONE-CLICK FILTERS HERE -->
    </q-table>
  </div>
</template>

<script>
import Sortable from 'sortablejs'
import multiMatch from '@/lib/MultiFieldSearch.js'
import { mapState } from 'vuex'
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
      table_height: '80vh',
      table_header_style: {
        borderBottom: '3px solid green',
        fontWeight: 'bold',
        borderCollapse: 'separate'
      }
    }
  },

  computed: {

    columns() {
      return [
        { 
          field: 'sequence',
          name: 'sequence',
          label: this.$t('work_order.list_headers.sequence').toUpperCase(),
          align: 'left'
        },
        { 
          field: 'wo_code',
          name: 'wo_code',
          label: this.$t('work_order.list_headers.wo_code').toUpperCase(),
          align: 'left'
        },
        // {
        //   field: 'wo_line',
        //   label: this.$t('work_order.list_headers.wo_line').toUpperCase() },
        {
          field: 'product_code',
          name: 'product_code',
          label: this.$t('work_order.list_headers.product_code').toUpperCase(),
          align: 'left'
        },
        { 
          field: 'progress',
          name: 'progress',
          label: this.$t('work_order.list_headers.progress').toUpperCase(),
          align: 'left',
          style: 'width: 25%'
        },
        { 
          field: 'qt_completed',
          name: 'qt_completed',
          label: this.$t('work_order.list_headers.qt_completed').toUpperCase(),
          align: 'right'},
        { 
          field: 'qt_planned',
          name: 'qt_planned',
          label: this.$t('work_order.list_headers.qt_planned').toUpperCase(),
          align: 'right'},
        { 
          field: 'qt_remaining',
          name: 'qt_remaining',
          label: this.$t('work_order.list_headers.qt_remaining').toUpperCase(),
          align: 'right'},
        { 
          field: 'due_by',
          name: 'due_by',
          label: this.$t('work_order.list_headers.due_by').toUpperCase(),
          sort: this.sortDate
        }
      ]
    },

    ...mapState({
      temp_queue: state => state.workorder.temp_queue,
      wo_data_map: state => state.workorder.wo_map
    }),

    wo_list() {
      return this.temp_queue.map( wo_key => this.wo_data_map[wo_key])
    },

    filtered_wo_list() {
      return this.wo_list.filter( wo => {
        
        // Define wo fields to use with the text search
        const search_fields = ['wo_code', 'wo_line', 'product_code']
        
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
        return filter_match_map.every( i => i === true )
      })
    }
  },

  methods: {
    progressColor(wo) {
      return wo.active
        ? 'theme-blue'
        : 'theme-grey'
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
    let table = document.querySelector(".q-virtual-scroll__content")
    const _self = this
    Sortable.create(table, {
      ..._self.$store.state.drag_options,
      // use onEnd event provided by SortableJs library
      onEnd: ({ newIndex, oldIndex }) => {
        _self.$emit('editing')
        console.log(this.filtered_wo_list.map(wo => {
          return { key: wo._key, seq: wo.sequence }
        }))
        console.log('Old: ', oldIndex, '\nNew:', newIndex)
        _self.$store.commit('UPDATE_TEMP_QUEUE', { newIndex, oldIndex })
        console.log(this.filtered_wo_list.map(wo => {
          return { key: wo._key, seq: wo.sequence }
        }))
      }
    })
  }
}
</script>

<style lang="sass">
#wo_list
  & th
    font-weight: bold
    color: var(--text-low)
    border-bottom: 1px solid #fff2
  & td
    font-size: 14px
    padding-top: 8px
    padding-bottom: 8px

  .q-table__top,
  .q-table__bottom,
  thead tr:first-child th /* bg color is important for th; just specify one */
    background-color: var(--bg-color)

  thead tr th
    position: sticky
    z-index: 1
  /* this will be the loading indicator */
  thead tr:last-child th
    /* height of all previous header rows */
    top: 48px
  thead tr:first-child th
    top: 0
</style>
