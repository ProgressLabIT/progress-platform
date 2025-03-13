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
        >
          <template v-for="column in columns" :key="column.name">
            <q-td class="ellipsis" :props="props" :style="column.style">
              <template v-if="column.format">
                {{
                  column.format(
                    (val = props.row[column.name]),
                    (row = props.row),
                  )
                }}
              </template>

              <template v-else-if="column.name === 'position'">
                {{ props.row.path.map(p => p.position_code).join(' > ') }}
              </template>

              <template v-else>
                {{ $capitalizeAll(props.row[column.field] || '-') }}
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
import {
  useInventoryColumns,
  useInventoryFilters,
} from 'app/src/composables/warehouse';

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

    const inventoryColumns = useInventoryColumns();
    const { filters } = useInventoryFilters();

    return {
      pagination,
      inventoryColumns,
      filters,
    };
  },

  data() {
    return {
      loading: false,
      loading_fields: false,
      events: NaN,
      limit: 200,
      offset: 0,

      filter_list: ['product_code', 'position', 'serial'],
      bool_filters: [],
    };
  },

  computed: {
    inventory_list() {
      return this.$store.state.warehouse.inventory;
    },

    columns() {
      return this.inventoryColumns;
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

    // routeToMovemets(row) {
    //   const to_route = {
    //     name: 'movements',
    //     params: { row },
    //     query: {
    //       back_to: this.$route.name,
    //       position_from: row.position_key,
    //       position_to: row.position_key,
    //       position_filter_operator: 'OR',
    //     },
    //   };
    //   this.$router.push(to_route);
    // },

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
