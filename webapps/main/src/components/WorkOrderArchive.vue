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
      hide-bottom
      dense
      separator="none"
      table-class="text-high"
      card-class="background no-shadow q-mt-sm"
      :rows-per-page-options="[0]"
      @row-dblclick="showWorkOrderScreen">

      <template #loading>
        <div class="absolute-center">
          <q-spinner indeterminate />
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
import { mapState } from 'vuex'
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
      this.loading = true
      console.log('Fetching...')
      setTimeout(() => {
        this.$api.get('work-order-archive', {
          params: {
            search: this.filters.search_string
          }
        }).then(resp => {
          this.wo_list = resp.data
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
</style>
