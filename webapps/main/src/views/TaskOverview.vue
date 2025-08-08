<template>
  <div ref="container" class="q-px-sm q-pt-sm full-height">
    <q-table
      id="task_list"
      v-model:pagination="pagination"
      :columns="columns"
      :rows="task_list"
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
          :style="props.row.status === 'completed' ? 'opacity: .5' : ''"
          @dblclick="showTaskDetails(props.row._key)"
        >
          <template v-for="column in columns" :key="column.name">
            <q-td class="ellipsis" :props="props">
              <template v-if="column.name === 'type'">
                <q-icon :name="props.row.icon || 'mdi-check-circle-outline'" />
              </template>

              <template v-else-if="column.name === 'status'">
                <q-badge
                  :color="getStatusColor(props.row.status)"
                  :label="$capitalizeAll(props.row.status || '')"
                />
              </template>

              <template v-else-if="['created', 'start_from', 'due_by', 'closed'].includes(column.name)">
                {{
                  props.row[column.name] === null
                    ? '-'
                    : $shortDateString(props.row[column.name], $i18n.locale)
                }}
              </template>

              <template v-else-if="column.name === 'assigned_to'">
                <div v-if="props.row.assigned_to && props.row.assigned_to.length > 0" class="row q-gutter-xs">
                  <BaseUserAvatar
                    v-for="userKey in props.row.assigned_to"
                    :key="userKey"
                    :user="getUserByKey(userKey)"
                    :size="'24px'"
                    :show-name="false"
                    dense
                  />
                  <q-tooltip class="bg-white text-dark shadow-2" style="max-width: 250px;">
                    <div class="column q-gutter-xs q-pa-xs">
                      <BaseUserAvatar
                        v-for="userKey in props.row.assigned_to"
                        :key="userKey"
                        :user="getUserByKey(userKey)"
                        :size="'32px'"
                        :show-name="true"
                        dense
                      />
                    </div>
                  </q-tooltip>
                </div>
                <span v-else>-</span>
              </template>

              <template v-else>
                {{ $capitalizeAll(props.row[column.name] || '-') }}
              </template>
            </q-td>
          </template>
        </q-tr>
      </template>
    </q-table>

    <!-- TASK DETAIL -->
    <router-view />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter, useRoute } from 'vue-router';
import { useStore } from 'vuex';
import BaseUserAvatar from '@/components/BaseUserAvatar.vue';
import { useTaskStore } from '@/stores/task.js';

// Props and emits
defineProps({
  loading: {
    type: Boolean,
    default: false,
  },
});

defineEmits(['onScroll', 'onRequest']);

// Composables
const router = useRouter();
const route = useRoute();
const store = useStore();
const { t } = useI18n();
const taskStore = useTaskStore();

// Reactive state
const pagination = ref({
  rowsPerPage: 0,
  sortBy: 'created',
  descending: false,
  page: 1,
  rowsNumber: 1000,
});

// Computed properties
const task_list = computed(() => taskStore.tasks);

const columns = computed(() => [
  {
    name: 'type',
    field: 'type',
    sortable: true,
    label: t('type').toUpperCase(),
    align: 'left',
  },
  {
    name: 'code',
    field: 'code',
    sortable: true,
    label: t('code').toUpperCase(),
    align: 'left',
    style: 'max-width: 10vw',
  },
  {
    name: 'title',
    field: 'title',
    sortable: true,
    label: t('title').toUpperCase(),
    align: 'left',
  },
  {
    name: 'status',
    field: 'status',
    sortable: true,
    label: t('status').toUpperCase(),
    align: 'center',
  },
  {
    name: 'assigned_to',
    field: 'assigned_to',
    sortable: false,
    label: t('assigned_to').toUpperCase(),
    align: 'left',
  },
  {
    name: 'start_from',
    field: 'start_from',
    sortable: true,
    align: 'right',
    label: t('start_from').toUpperCase(),
    style: 'max-width: 10vw',
  },
  {
    name: 'due_by',
    field: 'due_by',
    sortable: true,
    align: 'right',
    label: t('due_by').toUpperCase(),
    style: 'max-width: 10vw',
  },
  {
    name: 'created',
    field: 'created',
    sortable: true,
    align: 'right',
    label: t('created_date').toUpperCase(),
    style: 'max-width: 10vw',
  },
  {
    name: 'closed',
    field: 'closed',
    sortable: true,
    align: 'right',
    label: t('closed_date').toUpperCase(),
  },
]);

// Methods
function onRequest(requestProps) {
  const { page, rowsPerPage, sortBy, descending } = requestProps.pagination;
  pagination.value.sortBy = sortBy;
  pagination.value.descending = descending;
  pagination.value.page = page;
  pagination.value.rowsPerPage = rowsPerPage;
}

function getStatusColor(status) {
  switch (status) {
    case 'pending':
      return 'orange';
    case 'completed':
      return 'green';
    case 'canceled':
      return 'red';
    default:
      return 'grey';
  }
}

function getUserByKey(userKey) {
  return store.getters.getUserByKey(userKey);
}

function showTaskDetails(taskKey) {
  const to_route = {
    name: 'taskDetail',
    params: { taskKey },
    query: {
      back_to: route.name,
      ...route.query,
    },
  };
  router.push(to_route);
}

// Lifecycle
onMounted(async () => {
  await Promise.all([
    taskStore.fetchTasks(),
    store.dispatch('loadUsers')
  ]);
});
</script>

<style lang="sass">
#task_list
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
