<template>
  <div ref="container" class="q-px-sm q-pt-sm full-height">
    <q-table
      id="position_list"
      v-model:pagination="pagination"
      :columns="columns"
      :rows="position_list"
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
          :style="props.row.closed ? 'opacity: .5' : ''"
          @dblclick="showPositionDetails(props.row._key)"
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

              <template v-else>
                {{ $capitalizeAll(props.row[column.name] || '-') }}
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
import { usePositionColumns } from 'app/src/composables/warehouse';

export default {
  name: 'PositionsRoot',

  setup() {
    const pagination = ref({
      rowsPerPage: 0,
      sortBy: 'created',
      descending: false,
      page: 1,
      rowsNumber: 1000,
    });

    const positionColumns = usePositionColumns();

    return {
      pagination,
      positionColumns,
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
        'is_in_position',
        'contains_position',
        'created_min',
        'created_max',
      ],
      bool_filters: [],
    };
  },

  computed: {
    search_string: queryModel(String, 'search', null),
    is_in_position: queryModel(String, 'is_in_position', null),
    contains_position: queryModel(String, 'contains_position', null),

    created_min: queryModel(String, 'created_min', null),
    created_max: queryModel(String, 'created_max', null),

    filters() {
      return {
        search: this.search_string,
        is_in_position: this.is_in_position,
        contains_position: this.contains_position,
        created_min: this.created_min,
        created_max: this.created_max,
      };
    },

    position_list() {
      return this.$store.state.warehouse.positions;
    },

    columns() {
      return this.positionColumns;
    },
  },

  watch: {
    filters: {
      deep: true,
      handler: 'getPositions',
    },
  },

  created() {
    this.getPositions();
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
      this.refreshPositions();
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

    refreshPositions() {
      this.getPositions();
    },

    getPositions() {
      this.reloadPositions({ pagination: this.pagination });
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

    reloadPositions(data) {
      const { sortBy, descending } = data.pagination ?? {};

      this.sort_by = sortBy;
      this.sorting_order = descending ? 'desc' : 'asc';
      this.loading = true;
      this.$store
        .dispatch('getPositions', {
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
#position_list
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
