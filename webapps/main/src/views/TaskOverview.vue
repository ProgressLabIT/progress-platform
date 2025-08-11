<template>
  <div ref="container" class="q-px-sm q-pt-sm full-height">
    <!-- EDIT BUTTON -->
    <q-btn
      v-if="!edit_mode && task_list.length > 0"
      round
      color="theme-blue"
      icon="mdi-pencil"
      class="absolute-bottom-left q-mb-sm q-ml-md"
      style="z-index: 999"
      @click="edit_mode = true"
    />

    <q-table
      id="task_list"
      v-model:pagination="pagination"
      :columns="taskColumns"
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
      :selection="edit_mode ? 'multiple' : 'none'"
      @virtual-scroll="(details) => $emit('onScroll', details)"
      @request="
        (props) => {
          onRequest(props);
          $emit('onRequest', props);
        }
      "
    >
      <template #header-selection>
        <q-checkbox
          v-if="edit_mode"
          dense
          :model-value="allTasksSelected"
          @update:model-value="toggleAllTasks"
        />
      </template>

      <template #body="props">
        <q-tr
          :id="props.row._key"
          :key="props.row._key"
          :props="props"
          :style="props.row.status === 'completed' ? 'opacity: .5' : ''"
          @click="edit_mode ? toggleTask(props.row._key) : null"
          @dblclick="!edit_mode ? showTaskDetails(props.row._key) : null"
        >
          <!-- SELECTION CHECKBOX -->
          <q-td v-if="edit_mode">
            <q-checkbox
              dense
              :model-value="selected_tasks.has(props.row._key)"
              @update:model-value="toggleTask(props.row._key)"
            />
          </q-td>

          <!-- TASK CARD CONTEXT MENU -->
          <q-popup-proxy context-menu>
            <div class="q-pa-md column q-gutter-y-md" style="max-width: 300px">
              <!-- CODE AND STATUS -->
              <div class="row items-center justify-between">
                <div class="text-h5">
                  {{ props.row.task_type_name }} #{{ props.row.code || '-'}}
                </div>
                <div class="q-mx-md"></div>
                <q-chip
                  size="xs"
                  :color="taskStatusOptions[props.row.status]?.color || 'theme-grey'"
                  :label="taskStatusOptions[props.row.status]?.label"
                  :icon="taskStatusOptions[props.row.status]?.icon || 'mdi-circle-outline'"
                  class="text-uppercase highlight"
                />
              </div>

              <!-- TITLE -->
              <div class="text-h4 highlight">
                {{ props.row.title }}
              </div>

              <!-- DESCRIPTION -->
              <div class="q-mt-md" v-if="props.row.description">
                {{ props.row.description }}
              </div>

              <template v-if="props.row.assigned_to && props.row.assigned_to.length > 0">

                <q-separator />

                <!-- ASSIGNED TO -->
                <div class="text-h5 uppercase text-low">{{ $t('assigned_to') }}</div>
                <q-list dense>
                  <q-item v-for="userKey in props.row.assigned_to" :key="userKey" style="padding-left: 0px; padding-right: 0px;">
                    <BaseUserAvatar
                    :user="getUserByKey(userKey)"
                    :size="'24px'"
                    />
                  </q-item>
                </q-list>
              </template>

            </div>
          </q-popup-proxy>


          <!-- TASK COLUMNS -->

          <template v-for="column in taskColumns" :key="column.name">
            <q-td class="ellipsis" :props="props">
              <template v-if="column.name === 'type'">
                <q-icon :name="props.row.icon || 'mdi-check-circle-outline'" size="18px"/>
              </template>

              <template v-else-if="column.name === 'status'">
                <q-icon
                  size="16px"
                  :color="taskStatusOptions[props.row.status]?.color || 'grey'"
                  :name="taskStatusOptions[props.row.status]?.icon || 'mdi-circle-outline'"
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
                    :show_name="false"
                    dense
                  />
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

    <!-- Extra space to account for bottom toolbar -->
    <div v-if="edit_mode" class="q-my-xl" />

    <!-- ############### -->
    <!--   EDIT ACTIONS  -->
    <!-- ############### -->
    <div
      v-if="edit_mode"
      class="row full-width bg-theme-blue justify-between q-py-sm q-px-md items-center absolute-bottom"
    >
      <div class="col-auto">
        {{ $t('countInfo.selected', { count: selected_tasks.size }) }}
      </div>

      <div v-if="selected_tasks.size" class="col-auto row items-center q-gutter-md">
        <!-- START FROM DATE -->
        <q-input
          v-model="task_start_from"
          filled
          dense
          clearable
          mask="####-##-##"
          :label="$t('start_from')"
          placeholder="YYYY-MM-DD"
          :rules="[validateDate]"
          style="min-width: 150px"
          hide-bottom-space
        >
          <template #append>
            <q-icon name="mdi-calendar" class="cursor-pointer">
              <q-popup-proxy
                cover
                transition-show="scale"
                transition-hide="scale"
              >
                <q-date v-model="task_start_from" minimal mask="YYYY-MM-DD">
                  <div class="row items-center justify-end">
                    <q-btn v-close-popup :label="$t('close')" color="primary" flat />
                  </div>
                </q-date>
              </q-popup-proxy>
            </q-icon>
          </template>
        </q-input>

        <!-- DUE BY DATE -->
        <q-input
          v-model="task_due_by"
          filled
          dense
          clearable
          mask="####-##-##"
          :label="$t('due_by')"
          placeholder="YYYY-MM-DD"
          :rules="[validateDate]"
          class="text-white"
          style="min-width: 150px"
          hide-bottom-space
        >
          <template #append>
            <q-icon name="mdi-calendar" class="cursor-pointer">
              <q-popup-proxy
                cover
                transition-show="scale"
                transition-hide="scale"
              >
                <q-date v-model="task_due_by" minimal mask="YYYY-MM-DD">
                  <div class="row items-center justify-end">
                    <q-btn v-close-popup :label="$t('close')" color="primary" flat />
                  </div>
                </q-date>
              </q-popup-proxy>
            </q-icon>
          </template>
        </q-input>

        <!-- ASSIGNEES -->
        <q-select
          v-model="task_assigned_to"
          :options="user_options"
          option-label="label"
          option-value="value"
          multiple
          filled
          dense
          clearable
          emit-value
          map-options
          :label="$t('assigned_to')"
          :placeholder="task_assigned_to.length === 0 ? $t('operator_select_prompt') : ''"
          style="min-width: 200px"
          @filter="filterUsers"
        >
          <template #option="scope">
            <q-item v-bind="scope.itemProps">
              <q-item-section side>
                <q-checkbox
                  :model-value="scope.selected"
                  @update:model-value="scope.toggleOption"
                />
              </q-item-section>
              <q-item-section avatar>
                <BaseUserAvatar
                  :user="getUserByKey(scope.opt.value)"
                  :size="'32px'"
                  :show-name="false"
                />
              </q-item-section>
            </q-item>
          </template>

          <template #selected>
            <template v-if="task_assigned_to.length === 1">
              <BaseUserAvatar
                :user="getUserByKey(task_assigned_to[0])"
                :show-avatar="false"
                dense
                class="q-mr-xs"
              />
            </template>
            <template v-else-if="task_assigned_to.length > 1">
                {{ task_assigned_to.length }}x
            </template>
          </template>
        </q-select>

        <!-- STATUS -->
        <q-select
          v-model="task_status"
          :options="Object.values(taskStatusOptions)"
          option-label="label"
          option-value="value"
          filled
          dense
          clearable
          emit-value
          map-options
          :label="$t('status')"
          style="min-width: 150px"
        >
          <template #option="scope">
            <q-item v-bind="scope.itemProps">
              <q-item-section>
                <q-badge
                  :color="scope.opt.color"
                  :label="scope.opt.label"
                />
              </q-item-section>
            </q-item>
          </template>
        </q-select>
      </div>

      <div class="col-auto row">
        <q-btn
          v-if="selected_tasks.size && hasEditData"
          size="sm"
          color="theme-blue"
          class="q-mr-md"
          unelevated
          :label="$t('confirm')"
          :loading="saving"
          @click="updateTasks"
        />
        <q-btn
          size="sm"
          color="theme-grey"
          unelevated
          :label="$t('cancel_changes')"
          @click="exitEditMode"
        />
      </div>
    </div>

    <!-- TASK DETAIL -->
    <router-view />
  </div>
</template>

<script setup>
import { useQuasar, date } from 'quasar';
import { ref, computed, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter, useRoute } from 'vue-router';
import { useStore } from 'vuex';
import BaseUserAvatar from '@/components/BaseUserAvatar.vue';
import { sendEvent } from '@/composables/event.js';
import multiMatch from '@/lib/MultiFieldSearch.js';
import { useTaskStore } from '@/stores/task.js';
import { useTask } from '@/composables/task.js';


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
const $q = useQuasar();
const taskStore = useTaskStore();
const { taskColumns, taskStatusOptions } = useTask();

// Reactive state
const pagination = ref({
  rowsPerPage: 0,
  sortBy: 'created',
  descending: false,
  page: 1,
  rowsNumber: 1000,
});

// Edit mode state
const edit_mode = ref(false);
const selected_tasks = ref(new Set());
const saving = ref(false);

// task edit fields
const task_start_from = ref(null);
const task_due_by = ref(null);
const task_assigned_to = ref([]);
const task_status = ref(null);

// User selection state
const user_options = ref([]);
const all_users = ref([]);

// Computed properties
const task_list = computed(() => taskStore.tasks);

// Edit mode computed properties
const allTasksSelected = computed(() => {
  if (task_list.value.length === 0) {
    return false;
  }
  return task_list.value.every(task => selected_tasks.value.has(task._key));
});

const hasEditData = computed(() => {
  return task_start_from.value || task_due_by.value || task_assigned_to.value.length > 0 || task_status.value;
});

// Methods
function onRequest(requestProps) {
  const { page, rowsPerPage, sortBy, descending } = requestProps.pagination;
  pagination.value.sortBy = sortBy;
  pagination.value.descending = descending;
  pagination.value.page = page;
  pagination.value.rowsPerPage = rowsPerPage;
}


function getUserByKey(userKey) {
  return store.getters.getUserByKey(userKey);
}

function showTaskDetails(taskKey) {
  const to_route = {
    name: 'taskScreen',
    params: { taskKey },
    query: {
      back_to: route.name,
      ...route.query,
    },
  };
  router.push(to_route);
}

// Edit mode methods
function toggleTask(taskKey) {
  if (selected_tasks.value.has(taskKey)) {
    selected_tasks.value.delete(taskKey);
  } else {
    selected_tasks.value.add(taskKey);
  }
}

function toggleAllTasks(value) {
  if (value) {
    task_list.value.forEach(task => {
      selected_tasks.value.add(task._key);
    });
  } else {
    selected_tasks.value.clear();
  }
}

function exitEditMode() {
  edit_mode.value = false;
  selected_tasks.value.clear();
  task_start_from.value = null;
  task_due_by.value = null;
  task_assigned_to.value = [];
  task_status.value = null;
}

function initUserOptions() {
  const users = store.state.user?.user_list || [];
  all_users.value = users;
  user_options.value = users.map(user => ({
    label: `${user.name} ${user.surname}`,
    value: user._key
  }));
}

function filterUsers(value, update) {
  if (value === '') {
    update(() => {
      user_options.value = all_users.value.map(user => ({
        label: `${user.name} ${user.surname}`,
        value: user._key
      }));
    });
    return;
  }

  update(() => {
    const needle = value.toLowerCase();
    user_options.value = all_users.value
      .filter(user => multiMatch(needle, user, ['name', 'surname']))
      .map(user => ({
        label: `${user.name} ${user.surname}`,
        value: user._key
      }));
  });
}

async function updateTasks() {
  if (!hasEditData.value) {
    return;
  }

  saving.value = true;
  try {
    const updatePromises = Array.from(selected_tasks.value).map(taskKey => {
      const eventData = {
        task_key: taskKey
      };

      if (task_start_from.value) {
        eventData.start_from = task_start_from.value;
      }
      if (task_due_by.value) {
        eventData.due_by = task_due_by.value;
      }
      if (task_assigned_to.value.length > 0) {
        eventData.assigned_to = task_assigned_to.value;
      }
      if (task_status.value) {
        eventData.status = task_status.value;
      }

      return sendEvent({
        event_type: 'TASK_UPDATED',
        event_data: eventData
      });
    });

    await Promise.all(updatePromises);

    $q.notify({
      message: `${selected_tasks.value.size} ${t('task', selected_tasks.value.size)} updated successfully`,
      color: 'theme-green',
      timeout: 2000,
      position: 'top',
    });

    // Refresh the task list
    await taskStore.fetchTasks();
    exitEditMode();
  } catch (error) {
    console.error('Error updating tasks:', error);
    $q.notify({
      message: t('errors.save_err'),
      color: 'theme-red',
      timeout: 3000,
      position: 'top',
    });
  } finally {
    saving.value = false;
  }
}

// Date validation function
function validateDate(value) {
  if (!value) {
    return true; // Allow empty values
  }

  return date.isValid(value) || 'Please enter a valid date';
}

// Lifecycle
onMounted(async () => {
  await Promise.all([
    taskStore.fetchTasks(),
    store.dispatch('loadUsers')
  ]);
  initUserOptions();
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
