<template>
  <div ref="container" class="q-px-sm q-pt-sm full-height">
    <q-table
      id="issue_list"
      :columns="columns"
      :rows="issue_list"
      row-key="_key"
      :loading="loading"
      color="primary"
      virtual-scroll
      hide-bottom
      class="full-height"
      dense
      separator="none"
      table-class="text-high"
      card-class="background no-shadow"
      :rows-per-page-options="[0]">

      <template #body="props">
        <q-tr
          :id="props.row._key"
          :key="props.row._key"
          :props="props"
          :style="props.row.closed ? 'opacity: .5' : ''"
          @dblclick="showIssueDetails(props.row._key)">

          <template v-for="c in columns" :key="c.name">
            <q-td class="ellipsis" :props="props">

              <template v-if="c.name == 'issue_type'">
                <q-icon :name="props.row.icon || 'mdi-help'" />
              </template>

              <template v-else-if="['created', 'closed'].includes(c.name)">
                {{ props.row[c.name] == null ? '-' : $shortDateString(props.row[c.name], $i18n.locale) }}
              </template>

              <template v-else-if="c.name == 'critical'">
                <q-avatar
                  v-if="props.row.critical"
                  :color="props.row.closed ? 'theme-grey' : 'theme-red'"
                  size="6px">
                </q-avatar>
              </template>

              <template v-else-if="c.name == 'open'">
                <q-icon
                  v-if="!props.row.open"
                  name="mdi-check-circle"
                  size="14px"
                  color="theme-grey">
                </q-icon>
              </template>

              <template v-else-if="['product_code', 'work_order_code', 'project_code'].includes(c.name)">
                {{ $capitalizeAll(c.field(props.row) || '-') }}
              </template>

              <template v-else>
                {{ $capitalizeAll(props.row[c.name] || '-') }}
              </template>
            </q-td>
          </template>
        </q-tr>
      </template>

    </q-table>
  </div>
</template>

<script>
import { mapState } from 'vuex'
import { throttle as _throttle } from 'lodash'
import enrichIssue from '@/mixins/issues.js'
import NoDataAlert from '@/components/NoDataAlert.vue'
import LoadingSignal from '@/components/LoadingSignal.vue'
import queryModel from '@/lib/queryModelFactory.js'

export default {

  name: 'IssueOverview',

  components: {
    LoadingSignal,
    NoDataAlert,
  },

  mixins: [enrichIssue],

  props: {
    loading: {
      type: Boolean,
      default: false
    }
  },

  data () {
    return {
      table_height: '80vh'
    }
  },

  computed: {

    issue_list() {
      return this.$store.state.quality.issues.map(i => this.enrichIssue(i))
    },

    columns() {
      return [
        {
          name: 'issue_type',
          sortable: true,
          label: this.$t('type').toUpperCase(),
          align: 'left',
          classes: 'q-pr-none'
        },
        {
          name: '_key',
          field: '_key',
          sortable: true,
          label: 'ID',
          align: 'left',
          style: 'max-width: 10vw'
        },
        {
          name: 'product_code',
          field: row => row.links.product?.code,
          sortable: true,
          align: 'left',
          label: this.$t('product.label').toUpperCase(),
          style: 'max-width: 10vw',
        },
        {
          name: 'work_order_code',
          field: row => row.links.work_order?.wo_code,
          sortable: true,
          label: this.$t('work_order.list_headers.wo_code').toUpperCase(),
          align: 'left',
          style: 'max-width: 10vw'
        },
        {
          name: 'project_code',
          field: row => row.links.work_order?.project_code,
          sortable: true,
          label: this.$t('project').toUpperCase(),
          align: 'left',
          style: 'max-width: 10vw'
        },
        {
          name: 'phase_alias',
          field: 'phase_alias',
          sortable: true,
          label: this.$t('phase.short').toUpperCase(),
          align: 'left'
        },
        {
          name: 'critical',
          field: 'critical',
          sortable: true,
          label: this.$t('issue_critical').toUpperCase(),
          align: 'center'
        },
        // {
        //   name: 'open',
        //   field: 'open',
        //   sortable: true,
        //   label: this.$t('issue_closed').toUpperCase(),
        //   align: 'center'
        // },
        {
          name: 'created',
          field: 'created',
          sortable: true,
          align: 'right',
          label: this.$t('opened_date').toUpperCase(),
          sort: this.sortDate,
          style: "max-width: 5vw"
        },
        {
          name: 'closed',
          field: 'closed',
          sortable: true,
          align: 'right',
          label: this.$t('closed_date').toUpperCase(),
          sort: this.sortDate
        }
      ]
    }
  },

  methods: {
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

    showIssueDetails(issue_key) {
      const to_route = {
        name: "issueDetail",
        params: { issue_key },
        query: {
          back_to: this.$route.name,
          ...this.$route.query
        }
      }
      this.$router.push(to_route)
    },
  }
}
</script>

<style lang="sass">
#issue_list
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
