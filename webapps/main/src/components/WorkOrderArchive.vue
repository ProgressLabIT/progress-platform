<template>
  <div ref="container" id="table_container" class="q-px-sm">
    <q-table
      id="wo_list"
      :columns="columns"
      :rows="wo_list"
      row-key="_key"
      :style="`height: ${table_height}`"
      virtual-scroll
      color="primary"
      :loading="loading"
      dense
      hide-bottom
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

      <template #top>
        <div class="row full-width justify-between text-low q-mb-md">
          <div class="row col-9 q-gutter-md">

            <!-- SEARCH BOX -->
            <q-input
              clearable
              filled
              dense
              hide-bottom-space
              autocomplete="off"
              name="search"
              debounce="300"
              :label="$capitalize($t('search'))"
              v-model="search"
              class="col-3">
              <template v-slot:append>
                <q-icon name="mdi-magnify" size="xs"/>
              </template>
            </q-input>

            <!-- START MIN -->
            <q-input
              filled
              dense
              clearable
              mask="date"
              v-model="time_start_from"
              debounce="1000"
              label="Start min"
              class="col">
              <template #append>
                <q-icon name="mdi-calendar" size="xs" class="cursor-pointer">
                  <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                    <q-date minimal v-model="time_start_from">
                      <div class="row items-center justify-end">
                        <q-btn v-close-popup label="Close" color="primary" flat />
                      </div>
                    </q-date>
                  </q-popup-proxy>
                </q-icon>
              </template>
            </q-input>

            <!-- START MAX -->
            <q-input
              filled
              dense
              clearable
              mask="date"
              v-model="time_start_to"
              debounce="1000"
              label="Start max"
              class="col">
              <template #append>
                <q-icon name="mdi-calendar" size="xs" class="cursor-pointer">
                  <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                    <q-date minimal v-model="time_start_to">
                      <div class="row items-center justify-end">
                        <q-btn v-close-popup label="Close" color="primary" flat />
                      </div>
                    </q-date>
                  </q-popup-proxy>
                </q-icon>
              </template>
            </q-input>

            <!-- END MIN -->
            <q-input
              filled
              dense
              clearable
              mask="date"
              v-model="time_end_from"
              debounce="1000"
              label="End min"
              class="col">
              <template #append>
                <q-icon name="mdi-calendar" size="xs" class="cursor-pointer">
                  <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                    <q-date minimal v-model="time_end_from">
                      <div class="row items-center justify-end">
                        <q-btn v-close-popup label="Close" color="primary" flat />
                      </div>
                    </q-date>
                  </q-popup-proxy>
                </q-icon>
              </template>
            </q-input>

            <!-- END MAX -->
            <q-input
              filled
              dense
              clearable
              mask="date"
              v-model="time_end_to"
              debounce="1000"
              label="End max"
              class="col">
              <template #append>
                <q-icon name="mdi-calendar" size="xs" class="cursor-pointer">
                  <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                    <q-date minimal v-model="time_end_to">
                      <div class="row items-center justify-end">
                        <q-btn v-close-popup label="Close" color="primary" flat />
                      </div>
                    </q-date>
                  </q-popup-proxy>
                </q-icon>
              </template>
            </q-input>
          </div>

          <!-- COUNT AND EXPORT -->
          <div class="row q-gutter-md items-center">
            <div class="smaller">
              {{ wo_list.length }} Record (Max 100)
            </div>
            <q-btn
              color="theme-blue"
              :label="$t('export')"
              @click="export_csv">
            </q-btn>
          </div>
        </div>
      </template>

      <!-- TABLE CONTENT -->
      <template #body="props">
        <q-tr
          :key="props.row._key"
          :props="props"
          @dblclick="showWorkOrderScreen(props.row._key)">
          <template v-for="c in columns" :key="c.name">
            <q-td :props="props" class="ellipsis">
              <template v-if="['start', 'end'].includes(c.name)">
                <div>
                  {{ getHumanDate(props.row[c.name]) }}
                </div>
              </template>

              <template v-else-if="c.name.includes('qt') || c.name == 'issue_count'">
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
import { durationFromMillisec as duration } from '@/lib/duration.js'
import queryModel from '@/lib/queryModelFactory.js'
import NoDataAlert from '@/components/NoDataAlert.vue'

export default {

  name: 'WorkOrderArchive',

  components: {
    NoDataAlert
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
      filter_list: ['search','time_start_from','time_start_to','time_end_from','time_end_to'],
      search_fields: ['wo_code', 'product_code', 'project_code', 'product_description'],
      wo_list: []
    }
  },

  computed: {

    search: queryModel(String, 'search', null),
    time_start_from: queryModel(String, 'date_start_from', null),
    time_start_to: queryModel(String, 'date_start_to', null),
    time_end_from: queryModel(String, 'date_end_from', null),
    time_end_to: queryModel(String, 'date_end_to', null),

    filters() {
      let filters_object = {}

      this.filter_list.forEach(f => {
        if (this[f]) {
          if (f.startsWith('time')) {
            const date = new Date(this[f])
            // The api handles full timestamps, thus to include issues created/closed during the day indicated we need to set the filter at the end of the same
            if (f.endsWith('_to')) {
              // Not using UTC time on purpose, to correctly represent the filter wanted by the user
              date.setHours(23,59,59,999)
            }
            filters_object[f] = date.toISOString()
          }
          else filters_object[f] = this[f]
        }
      })
      return filters_object
    },

    columns() {
      return [
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
          align: 'left',
          style: 'max-width: 10vw'
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
      this.$api.get('work-order', {
        params: { ...this.filters }
      }).then(resp => {
        setTimeout(() => {
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
        }, 1000)
      })
    },

    showWorkOrderScreen(wo_key) {
      this.$emit('itemDblClick', {
        wo_key: wo_key,
        back_to_route_name: this.$route.name
      })
    },

    getHumanDate(iso_string) {
      const config = { year: '2-digit', month: 'short', day: 'numeric' }
      return this.$capitalize(this.$formatDateTime(iso_string, this.$i18n.locale, config))
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
    filters: {
      deep: true,
      handler: 'fetchData'
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

  thead
    position: sticky
    z-index: 1
    top: 0

</style>
