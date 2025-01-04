<template>
  <div ref="container" class="q-px-sm q-pt-sm full-height">
    <q-table
      id="movement_list_table"
      v-model:pagination="pagination"
      :columns="columns"
      :rows="movement_list"
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
      @virtual-scroll="addPositions"
      @request="reloadPositions"
    >
      <template #body="props">
        <q-tr
          :id="props.row._key"
          :key="props.row._key"
          :props="props"
          :style="props.row.status === 'COMPLETED' ? 'opacity: .5' : ''"
        >
          <template v-for="column in columns" :key="column.name">
            <q-td class="ellipsis" :props="props">
              <template v-if="column.name === 'type'">
                <q-icon :name="typeIconMap[props.row[column.field]]" />
              </template>

              <template v-else-if="column.format">
                {{ column.format(props.row[column.field]) }}
              </template>

              <template v-else>
                {{ $capitalizeAll(props.row[column.field] || '-') }}
              </template>
            </q-td>
          </template>
        </q-tr>
      </template>
    </q-table>

    <!-- POSITION DETAIL -->
    <router-view />
  </div>
</template>

<script>
import { ref } from 'vue';
import queryModel from '@/lib/queryModelFactory.js';
import { useMovementListColumns } from 'app/src/composables/warehouse';

export default {
  setup() {
    const pagination = ref({
      rowsPerPage: 0,
      sortBy: 'created',
      descending: false,
      page: 1,
      rowsNumber: 1000,
    });

    const movementListColumns = useMovementListColumns();

    const typeIconMap = {
      'receipt': 'mdi-import',
      'transfer': 'mdi-swap-horizontal',
      'shipment': 'mdi-export',
      'adjustment': 'mdi-plus-minus-variant'
    }

    return {
      pagination,
      movementListColumns,
      typeIconMap,
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
        'search',
        'due_by_min',
        'due_by_max',
        'status',
        'type',
      ],
      bool_filters: [],
    };
  },

  computed: {
    search_string: queryModel(String, 'search', null),
    due_by_min: queryModel(String, 'due_by_min', null),
    due_by_max: queryModel(String, 'due_by_max', null),
    status: queryModel(String, 'status', null),
    type: queryModel(String, 'type', null),

    filters() {
      return {
        search: this.search_string,
        due_by_min: this.due_by_min,
        due_by_max: this.due_by_max,
        status: this.status,
        type: this.type,
      };
    },

    movement_list() {
      return this.$store.state.warehouse.movement_lists;
    },

    columns() {
      return this.movementListColumns;
    },
  },

  watch: {
    filters: {
      deep: true,
      handler: 'getMovementLists',
    },
  },

  created() {
    this.getMovementLists();
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
      this.reloadMovementLists();
      let event = JSON.parse(message.data);
      if (event.notification === 'ERROR') {
        this.$q.notify({
          message: this.getErrorMessage(event.error_code, event.error),
          color: 'theme-red',
          timeout: 1500,
          position: 'top',
        });
      }
    },

    refreshMovementLists() {
      this.getMovementLists();
    },

    getMovementLists() {
      this.reloadMovementLists({ pagination: this.pagination });
    },

    showPositionDetails(positionKey) {
      const to_route = {
        name: 'positionDetail',
        params: { positionKey },
        query: {
          back_to: this.$route.name,
          ...this.$route.query,
        },
      };
      this.$router.push(to_route);
    },

    reloadMovementLists(data) {
      const { sortBy, descending } = data.pagination ?? {};

      this.sort_by = sortBy;
      this.sorting_order = descending ? 'desc' : 'asc';
      this.loading = true;
      this.$store
        .dispatch('getMovementLists', {
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
      return this.limit + this.offset <= this.$store.getters.getPositionCount();
    },

    addPositions(data) {
      const lastIndex = this.$store.getters.getPositionCount() - 1;

      if (this.loading !== true && data.to === lastIndex && this.hasMore()) {
        this.offset += this.limit;
        this.loading = true;
        this.$store
          .dispatch('appendPositions', {
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
#movement_list_table
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
