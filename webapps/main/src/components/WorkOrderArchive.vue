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
      :rows-per-page-options="[0]"
      @row-dblclick="showWorkOrderScreen">

      <template #body="props">
        <q-tr
          :key="props.row._key"
          :props="props"
          @dblclick="showWorkOrderScreen(props.row._key)">
          <template v-for="c in columns" :key="c.name">
            <q-td :props="props" :class="{ 'filter-field': search_fields.includes(c.name)}">

              <!-- PROGRESS BAR -->
              <template v-if="c.name==='progress'">
                <div class="row items-center q-col-gutter-sm">
                  <div class="col-9">
                    <BaseProgressBar v-if="isReleased(props.row)" :data="props.row" />
                  </div>
                  <span class="col-2 text-right">{{ props.row.progress }} %</span>
                </div>
              </template>
              <!-- ADD ALERT ICONS HERE -->

              <template v-else-if="c.name==='due_by'">
                <div class="pointer" @click="showDatePicker({ field: 'due_by', wo_data: props.row })">
                  {{ props.row.due_by == null ? '-' : $shortDateString(props.row.due_by, $i18n.locale) }}
                </div>
              </template>

              <template v-else-if="c.name==='start_from'">
                <div class="pointer" @click="showDatePicker({ field: 'start_from', wo_data: props.row })">
                  {{ props.row.start_from == null ? '-' : $shortDateString(props.row.start_from, $i18n.locale) }}
                </div>
              </template>

              <template v-else-if="c.name.includes('qt')">
                <span>{{ props.row[c.name] || 0 }}</span>
              </template>

              <template v-else>
                <span class="table-data" @click="setSearch(c.name, props.row[c.name])">
                  {{ $capitalizeAll(props.row[c.name] || '') }}
                </span>
              </template>
            </q-td>
          </template>
        </q-tr>
      </template>
    </q-table>

    <BaseDialog :show="temp_date != null" @close="temp_date = null">
      <q-date
        v-if="temp_date"
        minimal
        mask="YYYY-MM-DDTHH:mm:ss"
        :model-value="temp_date.value"
        @update:model-value="val => updateWorkOrder(val)">
      </q-date>
    </BaseDialog>
  </div>
</template>

<script>
import BaseProgressBar from '@/components/BaseProgressBar.vue'
import Sortable from 'sortablejs'
import multiMatch from '@/lib/MultiFieldSearch.js'
import { mapState } from 'vuex'
import { throttle as _throttle } from 'lodash'
import BaseDialog from '@/components/BaseDialog.vue'

export default {

  name: 'WorkOrderList',

  components: {
    BaseProgressBar,
    BaseDialog
  },

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
      },
      search_fields: ['wo_code', 'product_code', 'project_code', 'product_description'],
      temp_date: null
    }
  },

  computed: {

    columns() {
      return [
        {
          field: 'wo_code',
          name: 'wo_code',
          label: this.$t('work_order.list_headers.wo_code').toUpperCase(),
          align: 'left'
        },
        {
          field: 'project_code',
          name: 'project_code',
          label: this.$t('project').toUpperCase(),
          align: 'left'
        },
        {
          field: 'product_code',
          name: 'product_code',
          label: this.$t('work_order.list_headers.product_code').toUpperCase(),
          align: 'left'
        },
        {
          field: 'qt_completed',
          name: 'qt_completed',
          label: this.$t('work_order.list_headers.qt_completed').toUpperCase(),
          align: 'right'
        },
        {
          field: 'start',
          name: 'start',
          align: 'right',
          label: this.$t('start_date').toUpperCase()
        },
        {
          field: 'end',
          name: 'end',
          align: 'right',
          label: this.$t('end_date').toUpperCase()
        },
        {
          field: 'due_by',
          name: 'due_by',
          align: 'right',
          label: this.$t('work_order.list_headers.due_by').toUpperCase()
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
              match = multiMatch(this.filters.search_string, wo, this.search_fields)
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

    setSearch(field, text) {
      if (this.search_fields.includes(field)) {
        this.$emit('setSearch', text)
      }
    },

    showWorkOrderScreen(wo_key) {
      this.$emit('itemDblClick', {
        wo_key: wo_key,
        back_to_route_name: this.$route.name
      })
    },

    isReleased(wo) {
      return new Date(wo.start_from).getTime() <= new Date().getTime()
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
    },

    showDatePicker({ field, wo_data }) {
      const update_field = field == 'due_by' ? 'new_due_date' : 'new_from_date'
      this.temp_date = { update_field, value: wo_data[field], wo_key: wo_data._key }
    },

    async updateWorkOrder(new_date_value) {
      let wo_update = {}

      wo_update[this.temp_date.update_field] = new_date_value
      wo_update.wo_key = this.temp_date.wo_key

      await this.$store.dispatch('updateWorkOrder', wo_update)
      await this.$store.dispatch('updateWorkOrderList')
      this.temp_date = null
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
        _self.$store.commit('UPDATE_TEMP_QUEUE', { newIndex, oldIndex })
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
