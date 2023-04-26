<template>
  <div ref="container" id="table_container" class="q-px-sm">
    <q-table
      id="wo_list"
      :columns="columns"
      :rows="wo_list"
      row-key="_key"
      :style="`height: ${table_height}`"
      virtual-scroll
      :loading="loading"
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

      <template #loading>
        <div class="absolute-center">
          <q-spinner indeterminate />
        </div>
      </template>

      <template #bottom>
        <div class="row full-width justify-end text-low">
          <div>{{ wo_list.length }} Record (Max 100)</div>
        </div>
      </template>

      <template #body="props">
        <q-tr
          :key="props.row._key"
          :props="props"
          @dblclick="showWorkOrderScreen(props.row._key)">
          <template v-for="c in columns" :key="c.name">
            <q-td :props="props">
              <template v-if="['start', 'end'].includes(c.name)">
                <div>
                  {{ props.row.due_by == null ? '-' : $capitalize(getHumanDate(props.row[c.name])) }}
                </div>
              </template>

              <template v-else-if="c.name.includes('qt') || c.name == 'issue_count'">
                <span>{{ props.row[c.name] || 0 }}</span>
              </template>

              <!--<template v-else-if="c.name == 'processing_time'">
                <span>{{ props.row.processing_time }} / {{ props.row.unit_processing_time }}</span>
              </template>

              <template v-else-if="c.name == 'processing_cost'">
                <span>{{ props.row.processing_cost }} / {{ props.row.unit_processing_cost }}</span>
              </template>-->

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

    <q-btn
      class="absolute"
      style="top: 15px; right: 20px"
      color="theme-blue"
      :label="$t('export')"
      @click="export_csv">
    </q-btn>
  </div>
</template>

<script>
import { DateTime as DT } from 'luxon'
import { mapState } from 'vuex'
import { durationFromMillisec as duration } from '@/lib/duration.js'
import NoDataAlert from '@/components/NoDataAlert.vue'

export default {

  name: 'WorkOrderArchive',

  components: {
    NoDataAlert
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
      loading: true,
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
          field: 'issue_count',
          name: 'issue_count',
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
          field: 'processing_time',
          name: 'processing_time',
          align: 'right',
          label: this.$t('performance.processing_time.medium').toUpperCase() + ' (TOT)'
        },
        {
          field: 'unit_processing_time',
          name: 'unit_processing_time',
          csv_only: true,
          label: this.$t('performance.processing_time.medium').toUpperCase() + ' (UN)'
        },
        {
          field: 'processing_cost',
          name: 'processing_cost',
          align: 'right',
          label: this.$t('performance.processing_cost.medium').toUpperCase() + ' (TOT)'
        },
        {
          field: 'unit_processing_cost',
          name: 'unit_processing_cost',
          csv_only: true,
          label: this.$t('performance.processing_cost.medium').toUpperCase() + ' (UN)'
        },
      ]
    }
  },

  methods: {

    fetchData() {
      this.loading = true
      setTimeout(() => {
        this.$api.get('work-order-archive', {
          params: {
            search: this.filters.search_string
          }
        }).then(resp => {
          this.wo_list = resp.data.map(wo => {
            return {
              ...wo,
              processing_time: this.getHumanDuration(wo.processing_time),
              unit_processing_time: this.getHumanDuration(wo.processing_time / wo.qt_completed),
              processing_cost: wo.processing_cost.toFixed(2),
              unit_processing_cost: (wo.processing_cost / wo.qt_completed).toFixed(2)
            }
          })
          this.loading = false
        })
      }, 1000)
    },

    showWorkOrderScreen(wo_key) {
      this.$emit('itemDblClick', {
        wo_key: wo_key,
        back_to_route_name: this.$route.name
      })
    },

    getHumanDate(iso_string) {
      return DT.fromISO(iso_string).setLocale(this.$i18n.locale).toLocaleString(DT.DATE_MED_WITH_WEEKDAY)
    },

    getHumanDuration(millisecs) {
      return duration(millisecs)
    },

    export_csv() {
      const file_heading = 'data:text/csv;charset=utf-8,'
      const header_row = this.columns.map(c => c.label).join(';') + '\n'
      const data = this.wo_list.map(wo => {
        return this.columns.map(c => wo[c.field]).join(';')
      }).join('\n')
      const csv_url = encodeURI(file_heading + header_row + data)
      const link = document.createElement('a')
      link.setAttribute('href', csv_url)
      link.setAttribute('download', 'archivio.csv')
      document.body.appendChild(link)
      link.click()
      link.remove()
    }
  },

  created() {
    this.fetchData()
  },

  watch: {
    'filters.search_string'() {
      this.fetchData()
    }
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

  .q-table__bottom
    border-top: 1px solid #fff2

</style>
