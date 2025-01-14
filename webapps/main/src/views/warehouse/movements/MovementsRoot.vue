<template>
  <div ref="container" class="q-px-sm q-pt-sm full-height">
    <q-table
      id="movement_list"
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
      @virtual-scroll="addMovements"
      @request="reloadMovements"
    >
      <template #body="props">
        <q-tr
          :id="props.row._key"
          :key="props.row._key"
          :props="props"
          :style="props.row.closed ? 'opacity: .5' : ''"
          @dblclick="showMovementDetails(props.row._key)"
        >
          <template v-for="column in columns" :key="column.name">
            <q-td class="ellipsis" :props="props">
              <template
                v-if="['created', 'start', 'end'].includes(column.name)"
              >
                {{
                  props.row[column.name] === null
                    ? '-'
                    : $shortDateString(props.row[column.name], $i18n.locale)
                }}
              </template>

              <template v-else-if="column.name === 'type'">
                <q-icon :name="typeIconMap[props.row.type]" size="xs"/>
              </template>

              <template v-else-if="column.name === 'status'">
                <q-icon :name="statusIconMap[props.row.status]" size="15px"/>
              </template>

              <template v-else-if="column.name === 'quantity'">
                {{ props.row.qt_confirmed }} / {{ props.row.qt_planned }}
              </template>

              <template v-else>
                {{ $capitalizeAll(props.row[column.field] || '-') }}
              </template>
            </q-td>
          </template>
        </q-tr>
      </template>
    </q-table>

  </div>
</template>

<script>
import { ref } from 'vue';
import queryModel from '@/lib/queryModelFactory.js';
import { useMovementColumns } from 'app/src/composables/warehouse';

export default {
  name: 'MovementsRoot',

  setup() {
    const pagination = ref({
      rowsPerPage: 0,
      sortBy: 'created',
      descending: false,
      page: 1,
      rowsNumber: 1000,
    });

    const typeIconMap = {
      'receipt': 'mdi-import',
      'transfer': 'mdi-swap-horizontal',
      'shipment': 'mdi-export',
      'adjustment': 'mdi-plus-minus-variant',
      'production': 'mdi-package-variant-closed-plus',
      'consumption': 'mdi-package-variant-closed-minus'
    }

    const statusIconMap = {
      'completed': 'mdi-check-circle-outline',
      'started': 'mdi-progress-helper',
      'planned': 'mdi-calendar-clock-outline'
    }

    const movementColumns = useMovementColumns();

    return {
      pagination,
      movementColumns,
      typeIconMap,
      statusIconMap
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
        'position_from',
        'position_to',

        'position_filter_operator',

        'movement_type',
        'movement_status',

        'start_from',
        'start_to',
        'end_from',
        'end_to',
      ],
      bool_filters: [],
    };
  },

  computed: {
    product_code: queryModel(String, 'product_code', null),
    position_from: queryModel(String, 'position_from', null),
    position_to: queryModel(String, 'position_to', null),

    positionFilterOperator: queryModel(
      String,
      'position_filter_operator',
      'AND',
    ),

    movement_type: queryModel(String, 'movement_type', null),
    movement_status: queryModel(String, 'movement_status', null),

    start_from: queryModel(String, 'start_from', null),
    start_to: queryModel(String, 'start_to', null),
    end_from: queryModel(String, 'end_from', null),
    end_to: queryModel(String, 'end_to', null),

    filters() {
      return {
        product_code: this.product_code,
        position_from: this.position_from,
        position_to: this.position_to,
        position_filter_operator: this.positionFilterOperator,

        movement_type: this.movement_type,
        movement_status: this.movement_status,
        start_from: this.start_from,
        start_to: this.start_to,
        end_from: this.end_from,
        end_to: this.end_to,
      };
    },

    movement_list() {
      return this.$store.state.warehouse.movements;
    },

    columns() {
      return this.movementColumns;
    },
  },

  watch: {
    filters: {
      deep: true,
      handler: 'getMovements',
    },
  },

  created() {
    this.getMovements();
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
      this.refreshMovements();
      let event = JSON.parse(message.data);
      if (event.notification === 'ERROR') {
        this.$q.notify({
          message: this.getErrorMessage(event.error_code, event.error),
          color: 'theme-red',
          timeout: 1500,
          movement: 'top',
        });
      }
    },

    refreshMovements() {
      this.getMovements();
    },

    getMovements() {
      this.reloadMovements({ pagination: this.pagination });
    },

    showMovementDetails(movementKey) {
      const to_route = {
        name: 'movementDetail',
        params: { movementKey },
        query: {
          back_to: this.$route.name,
          ...this.$route.query,
        },
      };
      this.$router.push(to_route);
    },

    reloadMovements(data) {
      const { sortBy, descending } = data.pagination ?? {};

      this.sort_by = sortBy;
      this.sorting_order = descending ? 'desc' : 'asc';
      this.loading = true;
      this.$store
        .dispatch('getMovements', {
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
      return this.limit + this.offset <= this.$store.getters.getMovementCount();
    },

    addMovements(data) {
      const lastIndex = this.$store.getters.getMovementCount() - 1;

      if (this.loading !== true && data.to === lastIndex && this.hasMore()) {
        this.offset += this.limit;
        this.loading = true;
        this.$store
          .dispatch('appendMovements', {
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
#movement_list
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
    movement: sticky
    z-index: 1
    top: 0
</style>
