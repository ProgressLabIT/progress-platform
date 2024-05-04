<template>
  <div ref="container" class="q-px-sm q-pt-sm full-height">
    <q-table
      id="serial_list"
      :columns="columns"
      :rows="serial_list"
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
      :rows-per-page-options="[0]"
    >
      <template #body="props">
        <q-tr
          :id="props.row._key"
          :key="props.row._key"
          :props="props"
          :style="props.row.closed ? 'opacity: .5' : ''"
          @dblclick="showSerialDetails(props.row._key)"
        >
          <template v-for="column in columns" :key="column.name">
            <q-td class="ellipsis" :props="props">
              <template v-if="['created', 'closed'].includes(column.name)">
                {{
                  props.row[column.name] === null
                    ? '-'
                    : $shortDateString(props.row[column.name], $i18n.locale)
                }}
              </template>

              <template
                v-else-if="
                  ['product_code', 'work_order_code', 'project_code'].includes(
                    column.name,
                  )
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

    <!-- SERIAL DETAIL -->
    <router-view />
  </div>
</template>

<script>
import enrichSerial from '@/mixins/serials.js';

export default {
  name: 'SerialsOverview',

  mixins: [enrichSerial],

  props: {
    loading: {
      type: Boolean,
      default: false,
    },
  },

  data() {
    return {
      table_height: '80vh',
    };
  },

  computed: {
    serial_list() {
      return this.$store.state.traceability.serials.map((i) =>
        this.enrichSerial(i),
      );
    },

    columns() {
      return [
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
          sort: this.sortDate,
          style: 'max-width: 5vw',
        },
        {
          name: 'closed',
          field: 'closed',
          sortable: true,
          align: 'right',
          label: this.$t('closed_date').toUpperCase(),
          sort: this.sortDate,
        },
      ];
    },
  },

  methods: {
    sortDate(a, b) {
      // equal items sort equally
      if (a === b) {
        return 0;
      }
      // nulls sort after anything else
      else if (a === null) {
        return 1;
      } else if (b === null) {
        return -1;
      }
      // standard sorting
      else {
        return a < b ? 1 : -1;
      }
    },

    showSerialDetails(serialKey) {
      const to_route = {
        name: 'serialDetail',
        params: { serialKey },
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
#serial_list
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
