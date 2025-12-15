<template>
  <div ref="container" class="column full-height">
    <q-table
      id="count_session_list"
      v-model:pagination="pagination"
      :columns="columns"
      :rows="count_session_list"
      row-key="_key"
      :loading="loading"
      color="primary"
      hide-bottom
      class="col full-height"
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
          @dblclick="onRowDoubleClick(props.row)"
          style="cursor: pointer"
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
                {{ capitalizeAll(props.row[column.field] || '-') }}
              </template>

              <template v-else-if="column.name === 'status'">
                {{ capitalizeAll(props.row[column.field] || '-') }}
              </template>

              <template v-else>
                {{ capitalizeAll(props.row[column.field] || '-') }}
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

<script setup>
import { computed, onMounted, ref, watch } from 'vue';
import { useStore } from 'vuex';
import { useRouter } from 'vue-router';
import { capitalizeAll } from '@/boot/filters';
import {
  useCountSessionColumns,
  useCountSessionFilters,
} from 'app/src/composables/warehouse';

const store = useStore();
const router = useRouter();

const pagination = ref({
  rowsPerPage: 0,
  sortBy: 'created',
  descending: false,
  page: 1,
  rowsNumber: 1000,
});

const countSessionColumns = useCountSessionColumns();
const { filters } = useCountSessionFilters();

const loading = ref(false);
const limit = ref(200);
const offset = ref(0);
const sort_by = ref(null);
const sorting_order = ref('asc');

const count_session_list = computed(() => {
  return store.state.warehouse.count_sessions;
});

const columns = computed(() => {
  return countSessionColumns;
});

function getCountSessions() {
  reloadCountSessions({ pagination: pagination.value });
}

function reloadCountSessions(data) {
  const { sortBy, descending } = data.pagination ?? {};

  sort_by.value = sortBy;
  sorting_order.value = descending ? 'desc' : 'asc';
  loading.value = true;
  store
    .dispatch('getCountSessions', {
      ...filters.value,
      limit: offset.value + limit.value,
      offset: 0,
      sort_by: sort_by.value,
      sorting_order: sorting_order.value,
    })
    .then(() =>
      setTimeout(() => {
        loading.value = false;
      }, 1000),
    );
}

function hasMore() {
  return (
    limit.value + offset.value <= store.getters.getCountSessionCount()
  );
}

function addCountSessions(data) {
  const lastIndex = store.getters.getCountSessionCount() - 1;

  if (loading.value !== true && data.to === lastIndex && hasMore()) {
    offset.value += limit.value;
    loading.value = true;
    store
      .dispatch('appendCountSessions', {
        ...filters.value,
        offset: offset.value,
        sort_by: sort_by.value,
        sorting_order: sorting_order.value,
      })
      .then(() =>
        setTimeout(() => {
          loading.value = false;
        }, 1000),
      );
  }
}

function onRowDoubleClick(row) {
  router.push({
    name: 'countSessionDetail',
    params: { countSessionKey: row._key },
  });
}

watch(
  filters,
  () => {
    getCountSessions();
  },
  { deep: true },
);

onMounted(() => {
  getCountSessions();
});
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

