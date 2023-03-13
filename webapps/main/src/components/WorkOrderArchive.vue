<template>
  <div ref="container" id="table_container" class="q-px-sm">
    <q-table
      id="wo_list"
      :columns="columns"
      :rows="wo_list"
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
            <q-td :props="props">
              <template v-if="['start', 'end', 'due_by'].includes(c.name)">
                <div>
                  {{ props.row.due_by == null ? '-' : getHumanDate(props.row.due_by) }}
                </div>
              </template>

              <template v-else-if="c.name.includes('qt')">
                <span>{{ props.row[c.name] || 0 }}</span>
              </template>

              <template v-else>
                <span class="table-data">
                  {{ $capitalizeAll(props.row[c.name] || '') }}
                </span>
              </template>
            </q-td>
          </template>
        </q-tr>
      </template>
    </q-table>
  </div>
</template>

<script>
import { DateTime as DT } from 'luxon'
import BaseProgressBar from '@/components/BaseProgressBar.vue'
import Sortable from 'sortablejs'
import multiMatch from '@/lib/MultiFieldSearch.js'
import { mapState } from 'vuex'
import { throttle as _throttle, debounce as _debounce } from 'lodash'
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
      wo_list: []
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
        }
      ]
    }
  },

  methods: {

    fetchData() {
      this.$api.get('work-order-archive', {
        params: {
          search: this.search_string
        }
      }).then(resp => this.wo_list = resp.data)
    },

    showWorkOrderScreen(wo_key) {
      this.$emit('itemDblClick', {
        wo_key: wo_key,
        back_to_route_name: this.$route.name
      })
    },

    getHumanDate(iso_string) {
      return DT.fromISO(iso_string).setLocale(this.$i18n.locale).toLocaleString(DT.DATE_MED_WITH_WEEKDAY)
    }
  },

  created() {
    console.log('Created')
    this.fetchData()
    this.$watch('search_string', _debounce(this.fetchData, 500))
  },
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
