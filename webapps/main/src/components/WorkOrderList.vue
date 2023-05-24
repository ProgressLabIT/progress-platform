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

      <template #header-cell-issue_count="props">
        <q-th :props="props">
          <q-icon name="mdi-flag" size="14px"/>
        </q-th>
      </template>

      <template #body="props">
        <q-tr
          :id="props.row._key"
          :key="props.row._key"
          :props="props"
          @dblclick="showWorkOrderScreen(props.row._key)">
          <template v-for="c in columns" :key="c.name">
            <q-td
              :props="props"
              class="ellipsis"
              :class="{ 'filter-field': search_fields.includes(c.name) }">

              <!-- PROGRESS BAR -->
              <template v-if="c.name==='progress'">
                <div class="row items-center">
                  <div class="col q-pr-sm">
                    <BaseProgressBar :data="props.row" />
                  </div>
                  <q-space></q-space>
                  <span class="col-2 text-right">{{ props.row.progress }} %</span>
                </div>
              </template>
              <!-- ADD ALERT ICONS HERE -->

              <template v-else-if="c.name==='due_by'">
                <div class="pointer" @click="showDatePicker({ field: 'due_by', wo_data: props.row })">
                  <q-icon v-if="isLate(props.row.due_by)" color="theme-red" name="mdi-alert-octagon" />
                  {{ props.row.due_by == null ? '-' : $shortDateString(props.row.due_by, $i18n.locale) }}
                </div>
              </template>

              <template v-else-if="c.name==='start_from'">
                <div class="pointer" @click="showDatePicker({ field: 'start_from', wo_data: props.row })">
                  {{ props.row.start_from == null ? '-' : $shortDateString(props.row.start_from, $i18n.locale) }}
                </div>
              </template>

              <template v-else-if="c.name==='issue_count'">
                {{ props.row.issue_count }}
              </template>

              <template v-else-if="c.name.includes('qt')">
                <span>{{ props.row[c.name] || 0 }}</span>
              </template>

              <template v-else>
                <span
                  class="table-data"
                  @click="setSearch(c.name, props.row[c.name])">
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

    <router-view />
  </div>
</template>

<script>
import BaseProgressBar from '@/components/BaseProgressBar.vue'
import Sortable from 'sortablejs'
import multiMatch from '@/lib/MultiFieldSearch.js'
import { mapState } from 'vuex'
import { throttle as _throttle } from 'lodash'
import { DateTime as DT } from 'luxon'
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
        "not_critical":true,
        "ready":true,
        "not_ready":true
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
      temp_date: null,
      now: new Date().getTime()
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
          align: 'left',
          style: 'max-width: 10vw'
        },
        {
          field: 'project_code',
          name: 'project_code',
          label: this.$t('project').toUpperCase(),
          align: 'left',
          style: 'max-width: 10vw'
        },
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
          style: 'min-width: 15vw'
        },
        {
          field: 'issue_count',
          name: 'issue_count',
        },
        { 
          field: 'qt_completed',
          name: 'qt_completed',
          label: this.$t('work_order.list_headers.qt_completed').toUpperCase(),
          align: 'right'
        },
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
          field: 'start_from',
          name: 'start_from',
          align: 'right',
          label: this.$t('work_order.list_headers.start_from').toUpperCase()
        },
        { 
          field: 'due_by',
          name: 'due_by',
          align: 'right',
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
              if (!value && !this.isLate(wo.due_by)) match = false
              break 

            case 'late':
              if (!value && this.isLate(wo.due_by)) match = false
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

            case 'ready':
              if (!value && this.isReleased(wo)) match = false
              break

            case 'not_ready':
              if (!value && !this.isReleased(wo)) match = false
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
      return new Date(wo.start_from).getTime() <= this.now
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
    },

    isLate(due_by_date) {
      return DT.fromISO(due_by_date).toMillis() < this.now
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
      onEnd: (evt) => {
        /*
        the sortable DOM list is shorter than the actual work order list due to the virtual scroll (only part of the list is actually rendered).

        Sortable can only see the rendered list so the old and new index will not be referred to the actual work order queue, but to the position in the rendered list and are not useful as such.

        For this reason each table row has been tagged with its key as the dom element id, so that it can be retrieved after dragging and retrieve the index based on the original position of the key in the queue.

        The new index will be calculated using the difference between the indexes detected by Sortable.
        */
        const moved_item = evt.item
        const old_queue_index = this.temp_queue.findIndex(i => i == moved_item.id)
        const delta = evt.newIndex - evt.oldIndex
        const new_queue_index = old_queue_index + delta
        _self.$emit('editing')
        _self.$store.commit('UPDATE_TEMP_QUEUE', { new_queue_index, old_queue_index })
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
