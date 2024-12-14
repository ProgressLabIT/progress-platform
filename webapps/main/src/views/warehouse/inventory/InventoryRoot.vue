<template>
  <div ref="container" class="q-px-sm q-pt-sm full-height">
    <q-table
      id="inventory_list"
      v-model:pagination="pagination"
      :columns="columns"
      :rows="inventory_list"
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
      binary-state-sort
      :virtual-scroll-item-size="48"
      :virtual-scroll-sticky-size-start="48"
      :rows-per-page-options="[0]"
      @virtual-scroll="addInventory"
      @request="reloadInventory"
    >
      <template #body="props">
        <q-tr
          :id="props.row._key"
          :key="props.row._key"
          :props="props"
          :style="props.row.closed ? 'opacity: .5' : ''"
          @dblclick="showInventoryDetails(props.row._key)"
        >
          <template v-for="column in columns" :key="column.name">
            <q-td class="ellipsis" :props="props">
              <template
                v-if="
                  ['expiration_date', 'date_received'].includes(column.name)
                "
              >
                {{
                  props.row[column.name] === null
                    ? '-'
                    : $shortDateString(props.row[column.name], $i18n.locale)
                }}
              </template>

              <template v-else>
                {{ $capitalizeAll(props.row[column.name] || '-') }}
              </template>
            </q-td>
          </template>
        </q-tr>
      </template>
    </q-table>

    <!-- INVENTORY DETAIL -->
    <router-view />
  </div>
</template>

<script>
import { ref } from 'vue';
import queryModel from '@/lib/queryModelFactory.js';

export default {
  name: 'InventoryRoot',

  setup() {
    const pagination = ref({
      rowsPerPage: 0,
      sortBy: 'created',
      descending: false,
      page: 1,
      rowsNumber: 1000,
    });

    return {
      pagination,
    };
  },

  data() {
    return {
      loading: false,
      loading_fields: false,
      events: NaN,
      limit: 200,
      offset: 0,

      filter_list: [
        'product_code',
        'position',

        'start_from',
        'start_to',
        'end_from',
        'end_to',
      ],
      bool_filters: [],
    };
  },

  computed: {
    product: queryModel(String, 'product', null),
    position: queryModel(String, 'position', null),

    start_from: queryModel(String, 'start_from', null),
    start_to: queryModel(String, 'start_to', null),
    end_from: queryModel(String, 'end_from', null),
    end_to: queryModel(String, 'end_to', null),

    filters() {
      return {
        product_key: this.product,
        position_key: this.position,

        start_from: this.start_from,
        start_to: this.start_to,
        end_from: this.end_from,
        end_to: this.end_to,
      };
    },

    inventory_list() {
      return this.$store.state.warehouse.inventory;
    },

    columns() {
      return [
        {
          name: 'position_code',
          field: 'position_code',
          sortable: true,
          label: this.$t('warehouse.inventory.position').toUpperCase(),
          align: 'left',
          style: 'max-width: 10vw',
        },

        {
          name: 'product_code',
          field: 'product_code',
          sortable: true,
          label: this.$t('warehouse.inventory.product_code').toUpperCase(),
          align: 'left',
          style: 'max-width: 10vw',
        },
        {
          name: 'serial',
          field: 'serial_key',
          sortable: true,
          label: this.$t('warehouse.inventory.serial').toUpperCase(),
          align: 'left',
          style: 'max-width: 10vw',
        },
        {
          name: 'quantity',
          field: 'quantity',
          sortable: true,
          label: this.$t('warehouse.inventory.quantity').toUpperCase(),
          align: 'left',
          style: 'max-width: 10vw',
        },

        {
          name: 'owned',
          field: 'owned',
          sortable: true,
          label: this.$t('warehouse.inventory.owned').toUpperCase(),
          align: 'left',
          style: 'max-width: 10vw',
        },
        {
          name: 'date_received',
          field: 'date_received',
          sortable: true,
          align: 'right',
          label: this.$t('warehouse.inventory.date_received').toUpperCase(),
          style: 'max-width: 5vw',
        },

        {
          name: 'expiration_date',
          field: 'expiration_date',
          sortable: true,
          align: 'right',
          label: this.$t('warehouse.inventory.expiration_date').toUpperCase(),
          style: 'max-width: 5vw',
        },
      ];
    },
  },

  watch: {
    filters: {
      deep: true,
      handler: 'getInventory',
    },
  },

  created() {
    this.getInventory();
    let eventURL =
      this.$api.defaults.baseURL + '/notification/inventory-notification';
    this.events = new EventSource(eventURL, {
      withCredentials: false,
    });
    this.events.addEventListener('inventory-notification', (event) => {
      this.handleMessage(event);
    });
  },

  beforeUnmount() {
    if (this.events) {
      this.events.close();
    }
  },

  methods: {
    handleMessage(message) {
      this.refreshInventory();
      let event = JSON.parse(message.data);
      if (event.notification === 'ERROR') {
        this.$q.notify({
          message: this.getErrorMessage(event.error_code, event.error),
          color: 'theme-red',
          timeout: 1500,
          inventory: 'top',
        });
      }
    },

    refreshInventory() {
      this.getInventory();
    },

    getInventory() {
      this.reloadInventory({ pagination: this.pagination });
    },

    showInventoryDetails(inventoryKey) {
      const to_route = {
        name: 'inventoryDetail',
        params: { inventoryKey },
        query: {
          back_to: this.$route.name,
          ...this.$route.query,
        },
      };
      this.$router.push(to_route);
    },

    reloadInventory(data) {
      const { sortBy, descending } = data.pagination ?? {};

      this.sort_by = sortBy;
      this.sorting_order = descending ? 'desc' : 'asc';
      this.loading = true;
      this.$store
        .dispatch('getInventory', {
          ...this.filters,
          limit: this.offset + this.limit,
          offset: 0,
          sort_by: this.sort_by,
          sorting_order: this.sorting_order,
        })
        .then(() =>
          setTimeout(() => {
            this.loading = false;
          }, 1000),
        );
    },

    hasMore() {
      return (
        this.limit + this.offset <= this.$store.getters.getInventoryCount()
      );
    },

    addInventory(data) {
      const lastIndex = this.$store.getters.getInventoryCount() - 1;

      if (this.loading !== true && data.to === lastIndex && this.hasMore()) {
        this.offset += this.limit;
        this.loading = true;
        this.$store
          .dispatch('appendInventory', {
            ...this.filters,
            filter_unreleased: true,
            offset: this.offset,
            sort_by: this.sort_by,
            sorting_order: this.sorting_order,
          })
          .then(() =>
            setTimeout(() => {
              this.loading = false;
            }, 1000),
          );
      }
    },
  },
};
</script>

<style lang="sass">
#inventory_list
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
    inventory: sticky
    z-index: 1
    top: 0
</style>
