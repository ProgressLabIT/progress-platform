<template>
  <div ref="container" class="q-px-sm q-pt-sm full-height">
    <q-table
      id="issue_list"
      :columns="columns"
      :rows="issue_list"
      row-key="_key"
      :loading="loading"
      color="primary"
      hide-bottom
      class="full-height"
      dense
      separator="none"
      table-class="text-high"
      card-class="background no-shadow"
      virtual-scroll
      :virtual-scroll-item-size="48"
      :virtual-scroll-sticky-size-start="48"
      :pagination="pagination"
      :rows-per-page-options="[0]"
      @virtual-scroll="(details) => $emit('onScroll', details)"
      @request="
        (props) => {
          onRequest(props);
          $emit('onRequest', props);
        }
      "
    >
      <template #body="props">
        <q-tr
          :id="props.row._key"
          :key="props.row._key"
          :props="props"
          :style="props.row.closed ? 'opacity: .5' : ''"
          @dblclick="showIssueDetails(props.row._key)"
        >
          <template v-for="column in columns" :key="column.name">
            <q-td class="ellipsis" :props="props">
              <template v-if="column.name === 'issue_type'">
                <q-icon :name="props.row.icon || 'mdi-help'" />
              </template>

              <template v-else-if="['created', 'closed'].includes(column.name)">
                {{
                  props.row[column.name] === null
                    ? '-'
                    : $shortDateString(props.row[column.name], $i18n.locale)
                }}
              </template>

              <template v-else-if="column.name === 'critical'">
                <q-avatar
                  v-if="props.row.critical"
                  :color="props.row.closed ? 'theme-grey' : 'theme-red'"
                  size="6px"
                >
                </q-avatar>
              </template>

              <template v-else-if="column.name === 'open'">
                <q-icon
                  v-if="!props.row.open"
                  name="mdi-check-circle"
                  size="14px"
                  color="theme-grey"
                >
                </q-icon>
              </template>

              <template
                v-else-if="
                  [
                    'product_code',
                    'work_order_code',
                    'project_code',
                    'serial_code',
                  ].includes(column.name)
                "
              >
                {{ $capitalizeAll(column.field(props.row) || '-') }}
              </template>

              <template v-else>
                {{ $capitalizeAll(props.row[column.name] || '-') }}
              </template>
            </q-td>
          </template>
        </q-tr>
      </template>
    </q-table>

    <!-- ISSUE DETAIL -->
    <router-view />
  </div>
</template>

<script>
import enrichIssue from '@/mixins/issues.js';

export default {
  name: 'IssueOverview',

  mixins: [enrichIssue],

  props: {
    loading: {
      type: Boolean,
      default: false,
    },
  },

  emits: ['onScroll', 'onRequest'],

  setup() {
    const pagination = {
      rowsPerPage: 0,
      sortBy: 'created',
      descending: false,
      page: 1,
      rowsNumber: 1000,
    };

    function onRequest(props) {
      const { page, rowsPerPage, sortBy, descending } = props.pagination;
      pagination.sortBy = sortBy;
      pagination.descending = descending;
      pagination.page = page;
      pagination.rowsPerPage = rowsPerPage;
    }

    return {
      pagination,
      onRequest,
    };
  },

  data() {
    return {
      table_height: '80vh',
    };
  },

  computed: {
    issue_list() {
      return this.$store.state.quality.issues.map((i) => this.enrichIssue(i));
    },

    columns() {
      return [
        {
          name: 'issue_type',
          sortable: true,
          label: this.$t('type').toUpperCase(),
          align: 'left',
          classes: 'q-pr-none',
        },
        {
          name: '_key',
          field: '_key',
          sortable: true,
          label: 'ID',
          align: 'left',
          style: 'max-width: 10vw',
        },
        {
          name: 'product_code',
          field: (row) => row.links?.product?.code,
          sortable: true,
          align: 'left',
          label: this.$t('product.label').toUpperCase(),
          style: 'max-width: 10vw',
        },
        {
          name: 'work_order_code',
          field: (row) => row.links?.work_order?.wo_code,
          sortable: true,
          label: this.$t('work_order.list_headers.wo_code').toUpperCase(),
          align: 'left',
          style: 'max-width: 10vw',
        },
        {
          name: 'serial_code',
          field: (row) => row.links?.serial?.code,
          sortable: true,
          label: this.$t('serial').toUpperCase(),
          align: 'left',
          style: 'max-width: 10vw',
        },
        {
          name: 'project_code',
          field: (row) => row.links?.work_order?.project_code,
          sortable: true,
          label: this.$t('project').toUpperCase(),
          align: 'left',
          style: 'max-width: 10vw',
        },
        {
          name: 'phase_alias',
          field: 'phase_alias',
          sortable: true,
          label: this.$t('phase.short').toUpperCase(),
          align: 'left',
        },
        {
          name: 'critical',
          field: 'critical',
          sortable: true,
          label: this.$t('issue_critical').toUpperCase(),
          align: 'center',
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
          style: 'max-width: 5vw',
        },
        {
          name: 'closed',
          field: 'closed',
          sortable: true,
          align: 'right',
          label: this.$t('closed_date').toUpperCase(),
        },
      ];
    },
  },

  methods: {
    showIssueDetails(issueKey) {
      const to_route = {
        name: 'issueDetail',
        params: { issueKey },
        query: {
          back_to: this.$route.name,
          ...this.$route.query,
        },
      };
      this.$router.push(to_route);
    },
  },
};
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
