<template>
  <div ref="container" class="q-px-sm q-pt-sm full-height">
    <q-table
      id="count_session_list"
      v-model:pagination="pagination"
      :columns="columns"
      :rows="count_session_list"
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
      @virtual-scroll="addCountSessions"
      @request="reloadCountSessions"
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

              <template v-else-if="column.name === 'type'">
                {{ $capitalizeAll(props.row[column.field] || '-') }}
              </template>

              <template v-else-if="column.name === 'status'">
                {{ $capitalizeAll(props.row[column.field] || '-') }}
              </template>

              <template v-else>
                {{ $capitalizeAll(props.row[column.field] || '-') }}
              </template>
            </q-td>
          </template>
        </q-tr>
      </template>
    </q-table>

    <!-- COUNT SESSION DETAIL -->
    <router-view />
  </div>
</template>

<script>
import { ref } from 'vue';
import {
  useCountSessionColumns,
  useCountSessionFilters,
} from 'app/src/composables/warehouse';

export default {
  name: 'CountingRoot',

  setup() {
    const pagination = ref({
      rowsPerPage: 0,
      sortBy: 'created',
      descending: false,
      page: 1,
      rowsNumber: 1000,
    });

    const countSessionColumns = useCountSessionColumns();
    const { filters } = useCountSessionFilters();

    return {
      pagination,
      countSessionColumns,
      filters,
    };
  },

  data() {
    return {
      loading: false,
      limit: 200,
      offset: 0,
    };
  },

  computed: {
    count_session_list() {
      return this.$store.state.warehouse.count_sessions;
    },

    columns() {
      return this.countSessionColumns;
    },
  },

  watch: {
    filters: {
      deep: true,
      handler: 'getCountSessions',
    },
  },

  created() {
    this.getCountSessions();
  },

  methods: {
    getCountSessions() {
      this.reloadCountSessions({ pagination: this.pagination });
    },

    reloadCountSessions(data) {
      const { sortBy, descending } = data.pagination ?? {};

      this.sort_by = sortBy;
      this.sorting_order = descending ? 'desc' : 'asc';
      this.loading = true;
      this.$store
        .dispatch('getCountSessions', {
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
        this.limit + this.offset <= this.$store.getters.getCountSessionCount()
      );
    },

    addCountSessions(data) {
      const lastIndex = this.$store.getters.getCountSessionCount() - 1;

      if (this.loading !== true && data.to === lastIndex && this.hasMore()) {
        this.offset += this.limit;
        this.loading = true;
        this.$store
          .dispatch('appendCountSessions', {
            ...this.filters,
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
#count_session_list
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
  thead tr:first-child th
    top: 0
</style>

