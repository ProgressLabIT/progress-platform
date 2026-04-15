<template>
  <div
    id="table_container"
    ref="container"
    class="q-px-sm q-pt-sm col full-height"
  >
    <q-table
      id="wo_list"
      :columns="columns"
      :rows="filtered_wo_list"
      row-key="_key"
      virtual-scroll
      hide-bottom
      dense
      class="full-height"
      separator="none"
      table-class="text-high"
      card-class="background no-shadow"
      :rows-per-page-options="[0]"
    >
      <template #header-cell-issue_count="props">
        <q-th :props="props">
          <q-icon name="mdi-flag" size="14px" />
        </q-th>
      </template>

      <template #body="props">
        <q-tr
          :id="props.row._key"
          :key="props.row._key"
          :props="props"
          @dblclick="showWorkOrderScreen(props.row._key)"
          @contextmenu.prevent="showProductionAdminMenu($event, props.row)"
        >

          <template v-for="column in columns" :key="column.name">
            <q-td
              :props="props"
              class="ellipsis"
              :class="{ 'filter-field': search_fields.includes(column.name) }"
            >
              <!-- SEQUENCE -->
              <div
                v-if="column.name === 'sequence'"
                class="pointer"
                @click="change_sequence_for_wo = props.row"
              >
                {{ props.row.sequence }}
              </div>

              <!-- PROGRESS BAR -->
              <template v-else-if="column.name === 'progress'">
                <div class="row items-center">
                  <div class="col-2 col-md q-pr-sm">
                    <q-avatar
                      v-if="$q.screen.lt.md"
                      size="10px"
                      :color="
                        props.row.critical
                          ? 'theme-red'
                          : props.row.active
                            ? 'theme-blue'
                            : 'theme-grey'
                      "
                      class="q-pr-sm"
                      style="opacity: 0.6"
                    />
                    <BaseProgressBar v-else :data="props.row" />
                  </div>
                  <div class="col-2 text-right">{{ props.row.progress }} %</div>
                </div>
              </template>
              <!-- ADD ALERT ICONS HERE -->

              <template v-else-if="column.name === 'due_by'">
                <div
                  class="pointer"
                  @click="
                    showDatePicker({ field: 'due_by', wo_data: props.row })
                  "
                >
                  <q-icon
                    v-if="isLate(props.row.due_by)"
                    color="theme-red"
                    name="mdi-alert-octagon"
                  />
                  {{
                    props.row.due_by === null
                      ? '-'
                      : $shortDateString(props.row.due_by, $i18n.locale)
                  }}
                </div>
              </template>

              <template v-else-if="column.name === 'start_from'">
                <div
                  class="pointer"
                  @click="
                    showDatePicker({ field: 'start_from', wo_data: props.row })
                  "
                >
                  {{
                    props.row.start_from === null
                      ? '-'
                      : $shortDateString(props.row.start_from, $i18n.locale)
                  }}
                </div>
              </template>

              <template v-else-if="column.name === 'issue_count'">
                {{ props.row.issue_count }}
              </template>

              <template v-else-if="column.name.includes('qt')">
                <span>{{ props.row[column.name] || 0 }}</span>
              </template>

              <template v-else>
                <span @click="setSearch(column.name, props.row[column.name])">
                  {{ props.row[column.name] }}
                  <q-tooltip
                    :delay="500"
                    anchor="top left"
                    self="bottom left"
                    :offset="[8, 6]"
                    transition-show="fade"
                    transition-hide="fade"
                  >
                    <template v-if="column.name === 'product_code'">
                      <div class="highlight">
                        {{ props.row.product_code }}
                      </div>
                      <div>
                        {{ props.row.product_description }}
                      </div>
                    </template>
                    <template v-else>
                      {{ $capitalizeAll(props.row[column.name] || '') }}
                    </template>
                  </q-tooltip>
                </span>
              </template>
            </q-td>
          </template>
        </q-tr>
      </template>
    </q-table>

    <BaseDialog
      :show="temp_date !== null"
      :no-backdrop-dismiss="false"
      no-refocus
      @close="temp_date = null"
    >
      <q-date
        v-if="temp_date"
        minimal
        mask="YYYY-MM-DD"
        :model-value="temp_date.value"
        @update:model-value="(val) => updateWorkOrder(val)"
      >
      </q-date>
    </BaseDialog>

    <BasePrompt
      :prompt="
        $t('work_order.move_title', {
          wo_code: change_sequence_for_wo?.wo_code,
        })
      "
      :show="change_sequence_for_wo !== null"
      :initial_value="
        change_sequence_for_wo ? change_sequence_for_wo.sequence : ''
      "
      input_type="number"
      :min="1"
      :max="wo_list.length"
      @close="change_sequence_for_wo = null"
      @update="updateSequence"
    />

    <ProductionAdminMenu
      v-if="show_production_admin_menu"
      :wo="show_production_admin_menu"
      show-work-order-actions
      show-headers
      context-menu
      @ok="() => {
        store.dispatch('updateWorkOrderList')
      }"
    />

    <router-view />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { DateTime as DT } from 'luxon';
import Sortable from 'sortablejs';
import { useStore } from 'vuex';
import { useQuasar } from 'quasar';
import { useRoute } from 'vue-router';
import { useI18n } from 'vue-i18n';
import BaseDialog from '@/components/BaseDialog.vue';
import BaseProgressBar from '@/components/BaseProgressBar.vue';
import BasePrompt from '@/components/BasePrompt.vue';
import multiMatch from '@/lib/MultiFieldSearch.js';
import ProductionAdminMenu from '@/components/ProductionAdminMenu.vue';

// Props
const props = defineProps({
  filters: {
    type: Object,
    required: true,
    default: () => {
      return {
        search_string: '',
        started: true,
        queued: true,
        on_time: true,
        late: true,
        active: true,
        idle: true,
        critical: true,
        not_critical: true,
        ready: true,
        not_ready: true,
        start_from_min: null,
        start_from_max: null,
        due_by_min: null,
        due_by_max: null,
      };
    },
  },
});

// Emits
const emit = defineEmits(['editing', 'setSearch', 'itemDblClick']);

// Composables
const store = useStore();
const route = useRoute();
const $q = useQuasar();
const { t: $t } = useI18n();

// Reactive data
const container = ref(null);
const search_fields = ref([
  'wo_code',
  'product_code',
  'project_code',
  'product_description',
]);
const temp_date = ref(null);
const change_sequence_for_wo = ref(null);
const now = ref(new Date());
const show_production_admin_menu = ref(null);

// Computed properties
const columns = computed(() => [
  {
    field: 'sequence',
    name: 'sequence',
    sortable: true,
    label: $t('work_order.list_headers.sequence').toUpperCase(),
    align: 'left',
  },
  {
    field: 'wo_code',
    name: 'wo_code',
    sortable: true,
    label: $t('work_order.list_headers.wo_code').toUpperCase(),
    align: 'left',
    style: 'max-width: 10vw',
  },
  {
    field: 'project_code',
    name: 'project_code',
    sortable: true,
    label: $t('project').toUpperCase(),
    align: 'left',
    style: 'max-width: 10vw',
  },
  {
    field: 'product_code',
    name: 'product_code',
    sortable: true,
    label: $t('work_order.list_headers.product_code').toUpperCase(),
    style: 'max-width: 10vw',
    align: 'left',
  },
  {
    field: 'progress',
    name: 'progress',
    sortable: true,
    label: $t('work_order.list_headers.progress').toUpperCase(),
    align: 'left',
    style: () => ($q.screen.lt.md ? undefined : 'min-width: 15vw'),
  },
  {
    field: 'issue_count',
    sortable: true,
    name: 'issue_count',
  },
  {
    field: 'qt_completed',
    name: 'qt_completed',
    sortable: true,
    label: $t('work_order.list_headers.qt_completed').toUpperCase(),
    align: 'right',
  },
  {
    field: 'qt_planned',
    name: 'qt_planned',
    sortable: true,
    label: $t('work_order.list_headers.qt_planned').toUpperCase(),
    align: 'right',
  },
  {
    field: 'qt_remaining',
    name: 'qt_remaining',
    sortable: true,
    label: $t('work_order.list_headers.qt_remaining').toUpperCase(),
    align: 'right',
  },
  {
    field: 'start_from',
    sortable: true,
    name: 'start_from',
    align: 'right',
    label: $t('work_order.list_headers.start_from').toUpperCase(),
    sort: sortDate,
  },
  {
    field: 'due_by',
    sortable: true,
    name: 'due_by',
    align: 'right',
    label: $t('work_order.list_headers.due_by').toUpperCase(),
    sort: sortDate,
  },
]);

const temp_queue = computed(() => store.state.workorder.temp_queue);
const wo_data_map = computed(() => store.state.workorder.wo_map);

const wo_list = computed(() => {
  return temp_queue.value.map((wo_key) => wo_data_map.value[wo_key]);
});

const filtered_wo_list = computed(() => {
  return wo_list.value.filter((wo) => {
    /*
    Initialize filter results.
    If any false will be found in this array the filter function will return false
    */
    let filter_match_map = [];

    for (const [filter, value] of Object.entries(props.filters)) {
      // by default show wo in the list
      let match = true;

      switch (filter) {
        // Perform text search in the defined fields
        case 'search_string':
          match = multiMatch(
            props.filters.search_string,
            wo,
            search_fields.value,
          );
          break;

        case 'started':
          if (!value && wo.status === 'started') {
            match = false;
          }
          break;

        case 'queued':
          if (!value && ['created', 'planned'].includes(wo.status)) {
            match = false;
          }
          break;

        case 'on_time':
          if (!value && !isLate(wo.due_by)) {
            match = false;
          }
          break;

        case 'late':
          if (!value && isLate(wo.due_by)) {
            match = false;
          }
          break;

        case 'critical':
          if (!value && wo.critical) {
            match = false;
          }
          break;

        case 'not_critical':
          if (!value && !wo.critical) {
            match = false;
          }
          break;

        case 'active':
          // Do not show if control is false and wo is active
          if (!value && wo.active) {
            match = false;
          }
          break;

        case 'idle':
          // Do not show if control is false and wo is not active
          if (!value && !wo.active) {
            match = false;
          }
          break;

        case 'ready':
          if (!value && isReleased(wo)) {
            match = false;
          }
          break;

        case 'not_ready':
          if (!value && !isReleased(wo)) {
            match = false;
          }
          break;

        case 'start_from_min':
          if (!!value && new Date(value) > new Date(wo.start_from)) {
            match = false;
          }
          break;

        case 'start_from_max':
          if (
            !!value &&
            new Date(value).setHours(23, 59, 59, 999) <=
              new Date(wo.start_from)
          ) {
            match = false;
          }
          break;

        case 'due_by_min':
          if (!!value && new Date(value) > new Date(wo.due_by)) {
            match = false;
          }
          break;

        case 'due_by_max':
          if (
            !!value &&
            new Date(value).setHours(23, 59, 59, 999) < new Date(wo.due_by)
          ) {
            match = false;
          }
          break;
      }

      // add result of the specific filter to the map
      filter_match_map.push(match);
    }

    // Return false and exclude wo from list if any filter returned false
    return filter_match_map.every((i) => i === true);
  });
});

// Methods
const setSearch = (field, text) => {
  if (search_fields.value.includes(field)) {
    emit('setSearch', text);
  }
};

const showWorkOrderScreen = (wo_key) => {
  emit('itemDblClick', {
    wo_key: wo_key,
    back_to_route_name: route.name,
  });
};

const updateSequence = (new_sequence) => {
  emit('editing');
  store.commit('UPDATE_TEMP_QUEUE', {
    new_queue_index: new_sequence - 1,
    old_queue_index: change_sequence_for_wo.value.sequence - 1,
  });
  change_sequence_for_wo.value = null;
};

const isReleased = (wo) => {
  // Set start_from as beginning of day in case there's an hour set
  return new Date(wo.start_from).setHours(0, 0, 0) <= now.value;
};

const sortDate = (a, b) => {
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
};

const showDatePicker = ({ field, wo_data }) => {
  const update_field = field == 'due_by' ? 'new_due_date' : 'new_from_date';
  temp_date.value = {
    update_field,
    value: wo_data[field],
    wo_key: wo_data._key,
  };
};

const updateWorkOrder = async (new_date_value) => {
  let wo_update = {};

  wo_update[temp_date.value.update_field] = new_date_value;
  wo_update.wo_key = temp_date.value.wo_key;

  await store.dispatch('updateWorkOrder', wo_update);
  await store.dispatch('updateWorkOrderList');
  temp_date.value = null;
};

const isLate = (due_by_date) => {
  return DT.fromISO(due_by_date).toMillis() < now.value;
};

const showProductionAdminMenu = (event, wo) => {
  show_production_admin_menu.value = wo;
};

// Lifecycle
onMounted(() => {
  // make the table rows draggable
  let table = document.querySelector('.q-virtual-scroll__content');
  Sortable.create(table, {
    ...store.state.drag_options,
    // use onEnd event provided by SortableJs library
    onEnd: (evt) => {
      /*
      the sortable DOM list is shorter than the actual work order list due to the virtual scroll (only part of the list is actually rendered).

      Sortable can only see the rendered list so the old and new index will not be referred to the actual work order queue, but to the position in the rendered list and are not useful as such.

      For this reason each table row has been tagged with its key as the dom element id, so that it can be retrieved after dragging and retrieve the index based on the sequence number  position of the key in the queue.

      The new index will be calculated using the difference between the indexes detected by Sortable.
      */
      const moved_item = evt.item;
      const old_queue_index = temp_queue.value.findIndex(
        (wo) => wo == moved_item.id,
      );
      const moving_down = evt.newIndex > evt.oldIndex;
      const reference_item = moving_down
        ? moved_item.previousSibling
        : moved_item.nextSibling;
      const reference_index = temp_queue.value.findIndex(
        (wo) => wo == reference_item.id,
      );
      const new_queue_index = reference_index;

      emit('editing');
      store.commit('UPDATE_TEMP_QUEUE', {
        new_queue_index,
        old_queue_index,
      });
    },
  });
});
</script>

<style lang="sass">
#wo_list
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
  thead tr:last-child th
    /* height of all previous header rows */
    top: 48px
  thead tr:first-child th
    top: 0
</style>
