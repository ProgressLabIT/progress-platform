<template>
  <div ref="container" class="q-px-sm q-pt-sm full-height relative-position">
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
          @click.stop
        />
      </template>

      <template #body="props">
        <q-tr
          :id="props.row._key"
          :key="props.row._key"
          :props="props"
          @click="edit_mode ? toggleTask(props.row._key) : null"
          @dblclick="!edit_mode ? showTaskDetails(props.row._key) : null"
        >
          <!-- SELECTION CHECKBOX -->
          <q-td v-if="edit_mode">
            <q-checkbox
              dense
              :model-value="selected_tasks.has(props.row._key)"
              @update:model-value="toggleTask(props.row._key)"
              @click.stop
            />
          </q-td>

          <!-- TASK CARD CONTEXT MENU -->
          <q-popup-proxy context-menu>
            <div class="q-pa-md column q-gutter-y-md" style="min-width: 300px; max-width: 600px">
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
              <div v-if="props.row.description" class="q-mt-md">
                {{ props.row.description }}
              </div>

              <!-- OWNER -->
              <template v-if="props.row.owner_key">
                <div class="text-h5 uppercase text-low q-mt-lg">{{ $t('owner') }}</div>
                <BaseUserAvatar
                  :user="getUserByKey(props.row.owner_key)"
                  :size="'24px'"
                  :avatar-color-class="'bg-theme-blue'"
                />
              </template>

              <!-- PARTICIPANTS -->
              <template v-if="props.row.assigned_to?.length > 1">
                <div class="text-h5 uppercase text-low q-mb-xs q-mt-lg">{{ $t('participants') }}</div>
                <q-list dense class="q-mt-xs">
                  <q-item
                    v-for="user in props.row.assigned_to.filter(u => u.role === 'participant')"
                    :key="user.user_key"
                    style="padding-left: 0px; padding-right: 0px;"
                  >
                    <BaseUserAvatar
                      :user="getUserByKey(user.user_key)"
                      :size="'24px'"
                    />
                  </q-item>
                </q-list>
              </template>

              <!-- ACTIONS -->
              <div class="row q-gutter-sm q-mt-lg">
                <q-btn
                  color="theme-grey"
                  size="0.75rem"
                  :label="$t('go_to_task')"
                  @click="router.push({ name: 'taskScreen', params: { taskKey: props.row._key } })"
                />

                <template v-if="!['completed', 'canceled'].includes(props.row.status)">
                  <q-btn
                    v-if="!isTaskActive(props.row._key)"
                    color="theme-green"
                    size="0.75rem"
                    icon="mdi-play-circle-outline"
                    :label="$t('task_activate')"
                    @click="activateTask(props.row._key)"
                  />

                  <q-btn
                    v-else
                    color="orange"
                    size="0.75rem"
                    icon="mdi-stop-circle-outline"
                    :label="$t('task_deactivate')"
                    @click="deactivateTask()"
                  />
                </template>
              </div>

            </div>
          </q-popup-proxy>


          <!-- TASK COLUMNS -->

          <template v-for="column in taskColumns" :key="column.name">
            <q-td
              class="ellipsis"
              :style="['completed', 'canceled'].includes(props.row.status) ? 'opacity: .7' : ''"
              :props="props">
              <template v-if="column.name === 'type'">
                <q-icon
                  :name="props.row.icon || 'mdi-check-circle-outline'"
                  size="18px"
                  :class="{ 'active-task-icon': isTaskActive(props.row._key) }"
                />
              </template>

              <template v-else-if="column.name === 'status'">
                <q-icon
                  size="16px"
                  :color="taskStatusOptions[props.row.status]?.color || 'theme-grey'"
                  :name="taskStatusOptions[props.row.status]?.icon || 'mdi-circle-outline'"
                 />
                 <q-popup-proxy context-menu auto-close>
                    <q-list>
                      <q-item
                        v-for="status in Object.values(taskStatusOptions)"
                        clickable
                        :key="status.value"
                        @click="updateTaskStatus(props.row._key, status.value)"
                      >
                        <q-item-section side>
                          <q-icon :name="status.icon" :color="props.row.status === status.value ? status.color : 'theme-grey'" size="16px" />
                        </q-item-section>
                        <q-item-section>
                          <q-item-label class="uppercase smaller" :class="{ 'highlight': props.row.status === status.value }">{{ status.label }}</q-item-label>
                        </q-item-section>
                      </q-item>
                    </q-list>
                  </q-popup-proxy>
              </template>

              <template v-else-if="['created', 'start_from', 'due_by', 'closed'].includes(column.name)">
                {{
                  props.row[column.name] === null
                    ? '-'
                    : $shortDateString(props.row[column.name], $i18n.locale)
                }}
              </template>

              <div v-else-if="column.name === 'assigned_to'" class="row items-center">
                <div v-if="props.row.assigned_to?.length > 0" class="row q-gutter-xs">
                  <BaseUserAvatar
                    :key="props.row.owner_key"
                    :user="getUserByKey(props.row.owner_key)"
                    :size="'24px'"
                    :show_name="false"
                    avatar-color-class="bg-theme-blue"
                    dense
                  />
                </div>

                <template v-if="parseAssignments(props.row).participants.length > 0">
                  <div class="q-mx-sm text-h5 text-low">/</div>
                  <BaseUserAvatar
                    v-for="assignment in parseAssignments(props.row).participants"
                    :key="assignment.user_key"
                    :user="getUserByKey(assignment.user_key)"
                    :size="'24px'"
                    :show_name="false"
                    class="q-mr-xs"
                    dense
                  />
                </template>

              </div>

              <template v-else>
                {{ $capitalizeAll(props.row[column.name] || '-') }}
              </template>
            </q-td>
          </template>
        </q-tr>
      </template>
    </q-table>

    <!-- Bottom drawer for edit actions -->
    <div
      v-if="edit_mode"
      class="full-width surface1 justify-between q-pb-md q-px-md items-center absolute-bottom edit-drawer"
      :class="{ 'drawer-visible': edit_mode }"

    >
      <div class="row items-center justify-between q-my-md">
          <div class="text-subtitle1">
            {{ $t('countInfo.selected', { count: selected_tasks.size }) }}
          </div>
          <div class="row items-center">
            <q-btn
            size="0.75rem"

              flat
              round
              dense
              icon="mdi-close"
              @click="exitEditMode"
            />
          </div>
        </div>

        <div class="row q-col-gutter-md">
          <!-- START FROM DATE -->
          <div class="col-12 col-sm-6 col-md-3">
            <q-input
              v-model="task_start_from"
              filled
              dense
              clearable
              mask="####-##-##"
              :label="$t('start_from')"
              placeholder="YYYY-MM-DD"
              :rules="[validateDate]"
              hide-bottom-space
              :disable="selected_tasks.size === 0"
              @click.stop
            >
              <template #append>
                <q-icon name="mdi-calendar" class="cursor-pointer" @click.stop>
                  <q-popup-proxy cover transition-show="scale" transition-hide="scale" @click.stop>
                    <q-date v-model="task_start_from" minimal mask="YYYY-MM-DD" @click.stop>
                      <div class="row items-center justify-end">
                        <q-btn v-close-popup :label="$t('close')" color="primary" flat @click.stop />
                      </div>
                    </q-date>
                  </q-popup-proxy>
                </q-icon>
              </template>
            </q-input>
          </div>

          <!-- DUE BY DATE -->
          <div class="col-12 col-sm-6 col-md-3">
            <q-input
              v-model="task_due_by"
              filled
              dense
              clearable
              mask="####-##-##"
              :label="$t('due_by')"
              placeholder="YYYY-MM-DD"
              :rules="[validateDate]"
              hide-bottom-space
              :disable="selected_tasks.size === 0"
              @click.stop
            >
              <template #append>
                <q-icon name="mdi-calendar" class="cursor-pointer" @click.stop>
                  <q-popup-proxy cover transition-show="scale" transition-hide="scale" @click.stop>
                    <q-date v-model="task_due_by" minimal mask="YYYY-MM-DD" @click.stop>
                      <div class="row items-center justify-end">
                        <q-btn v-close-popup :label="$t('close')" color="primary" flat @click.stop />
                      </div>
                    </q-date>
                  </q-popup-proxy>
                </q-icon>
              </template>
            </q-input>
          </div>

          <!-- ASSIGNEES -->
          <div class="col-12 col-sm-6 col-md-4">
            <q-select
              :model-value="task_assigned_to"
              :options="user_options"
              option-label="label"
              option-value="value"
              multiple
              filled
              dense
              clearable
              emit-value
              map-options
              use-input
              input-debounce="0"
              :label="$t('assigned_to')"
              :placeholder="task_assigned_to.length === 0 ? $t('operator_select_prompt') : ''"
              :disable="selected_tasks.size === 0"
              @filter="filterUsers"
              @update:model-value="updateTaskAssignees"
              @clear="task_owner_key = null; task_assigned_to = [];"
            >
              <template #option="scope">
                <q-item v-bind="scope.itemProps">
                  <q-item-section side>
                    <q-checkbox :model-value="scope.selected" @update:model-value="scope.toggleOption(scope.opt)" />
                  </q-item-section>
                  <q-item-section avatar>
                    <BaseUserAvatar :user="getUserByKey(scope.opt.value)" :size="'32px'" :show-name="false" />
                  </q-item-section>
                  <q-item-section />
                  <q-item-section side>
                    <q-btn
                      v-if="task_assigned_to.includes(scope.opt.value)"
                      flat
                      round
                      :color="task_owner_key === scope.opt.value ? 'theme-blue' : null"
                      padding="0px"
                      size="18px"
                      :icon="task_owner_key === scope.opt.value ? 'mdi-crown-circle' : 'mdi-circle-outline'"
                      @click.stop="makeOwner(scope.opt.value)"
                    />
                  </q-item-section>
                </q-item>
              </template>

              <template #selected>
                <template v-if="task_assigned_to.length === 1">
                  <BaseUserAvatar :user="getUserByKey(task_assigned_to[0])" :show-avatar="false" dense class="q-mr-xs" />
                </template>
                <template v-else-if="task_assigned_to.length > 1">
                  {{ task_assigned_to.length }}x
                </template>
              </template>
            </q-select>
          </div>

          <!-- STATUS -->
          <div class="col-12 col-sm-6 col-md-2">
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
              :disable="selected_tasks.size === 0"
            >
              <template #option="scope">
                <q-item v-bind="scope.itemProps">
                  <q-item-section side>
                    <q-icon :name="scope.opt.icon" size="18px" :color="scope.opt.color" />
                  </q-item-section>
                  <q-item-section class="capitalize">
                    {{ scope.opt.label }}
                  </q-item-section>
                </q-item>
              </template>
            </q-select>
          </div>
        </div>

        <div class="row q-mt-md q-gutter-sm">
          <q-btn
            v-if="selected_tasks.size && hasEditData"
            color="theme-blue"
            class="q-mr-sm"
            size="0.75rem"
            unelevated
            :label="$t('confirm')"
            :loading="saving"
            @click.stop="updateTasks"
          />
          <q-btn color="theme-grey" unelevated size="0.75rem" :label="$t('cancel_changes')" @click.stop="exitEditMode"/>
        </div>
  </div>

  <!-- TASK DETAIL -->
</div>
</template>

<script setup>
import { useQuasar, date } from 'quasar';
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter, useRoute } from 'vue-router';
import { useStore } from 'vuex';
import BaseUserAvatar from '@/components/BaseUserAvatar.vue';
import { sendEvent } from '@/composables/event.js';
import { useTask } from '@/composables/task.js';
import multiMatch from '@/lib/MultiFieldSearch.js';
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

// UI state
const hoveredTask = ref(null);

// Edit mode state
const edit_mode = ref(false);
const selected_tasks = ref(new Set());
const saving = ref(false);

// task edit fields
const task_start_from = ref(null);
const task_due_by = ref(null);
const task_assigned_to = ref([]);
const task_owner_key = ref(null);
const task_status = ref(null);

// User selection state
const user_options = ref([]);
const all_users = ref([]);

// Computed properties
const task_list = computed(() => taskStore.tasks);

// Task activation methods
function isTaskActive(taskKey) {
  return taskStore.activeTaskKey === taskKey;
}

function activateTask(taskKey) {
  taskStore.activeTaskKey = taskKey
}

function deactivateTask() {
  taskStore.activeTaskKey = null;
}

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

function parseAssignments(task) {
  let owner = task.assigned_to.find(assignment => assignment.role === 'owner');
  let participants = task.assigned_to.filter(assignment => assignment.role === 'participant');
  return { owner, participants };
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
  task_owner_key.value = null;
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
      let chain = Promise.resolve();

      // Non-status updates via TASK_UPDATED
      const updateData = { task_key: taskKey };
      if (task_start_from.value) {
        updateData.start_from = task_start_from.value;
      }
      if (task_due_by.value) {
        updateData.due_by = task_due_by.value;
      }
      if (task_assigned_to.value.length > 0 && task_owner_key.value) {
        const assignments = [
          { user_key: task_owner_key.value, role: 'owner' },
          ...task_assigned_to.value
            .filter(u => u !== task_owner_key.value)
            .map(u => ({ user_key: u, role: 'participant' }))
        ];
        updateData.assigned_to = assignments;
      }
      const hasFieldUpdates = Object.keys(updateData).length > 1; // beyond task_key
      if (hasFieldUpdates) {
        chain = chain.then(() => sendEvent({ event_type: 'TASK_UPDATED', event_data: updateData }));
      }

      // Status updates via dedicated events
      if (task_status.value) {
        if (task_status.value === 'completed') {
          chain = chain.then(() => sendEvent({ event_type: 'TASK_COMPLETED', event_data: { task_key: taskKey } }));
        } else if (task_status.value === 'canceled') {
          chain = chain.then(() => sendEvent({ event_type: 'TASK_CANCELED', event_data: { task_key: taskKey } }));
        } else if (task_status.value === 'open') {
          chain = chain.then(() => sendEvent({ event_type: 'TASK_REOPENED', event_data: { task_key: taskKey } }));
        } else if (task_status.value === 'pending') {
          chain = chain.then(() => sendEvent({ event_type: 'TASK_SUSPENDED', event_data: { task_key: taskKey } }));
        }
      }

      return chain;
    });

    await Promise.all(updatePromises);

    $q.notify({
      message: t('tasks_updated_successfully'),
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

function updateTaskStatus(taskKey, status) {
  selected_tasks.value.add(taskKey);
  task_status.value = status;
  updateTasks();
}

// Date validation function
function validateDate(value) {
  if (!value) {
    return true; // Allow empty values
  }

  return date.isValid(value) || 'Please enter a valid date';
}

// Keep owner consistent with selected users
watch(task_assigned_to, (newVal) => {
  if (task_owner_key.value && !newVal.includes(task_owner_key.value)) {
    task_owner_key.value = null;
  }
  // If no owner yet but we have selected users, set first as owner
  if (!task_owner_key.value && newVal.length > 0) {
    task_owner_key.value = newVal[0];
  }
});

function makeOwner(userKey) {
  console.log('makeOwner', userKey);
  task_owner_key.value = userKey;
}

function updateTaskAssignees(userKeys) {
  task_assigned_to.value = userKeys;
  console.log('updateTaskAssignees', userKeys);
  if (task_owner_key.value === null) { // if no owner yet, set first as owner
    task_owner_key.value = userKeys[0];
  }
  console.log('task_owner_key', task_owner_key.value);
}

// Keyboard shortcuts
function handleKeyPress(event) {
  if (event.key.toLowerCase() === 'a' && !event.ctrlKey && !event.metaKey && !event.altKey) {
    // Prevent default if focused on input elements
    if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA' || event.target.isContentEditable) {
      return;
    }

    event.preventDefault();

    // If in edit mode and tasks are selected, activate first selected task
    if (edit_mode.value && selected_tasks.value.size === 1) {
      const taskKey = Array.from(selected_tasks.value)[0];
      if (isTaskActive(taskKey)) {
        deactivateTask();
      } else {
        activateTask(taskKey);
      }
    }
    // If there's a hovered task, activate it
    else if (hoveredTask.value) {
      if (isTaskActive(hoveredTask.value)) {
        deactivateTask();
      } else {
        activateTask(hoveredTask.value);
      }
    }
  }
}

// Lifecycle
onMounted(async () => {
  await store.dispatch('loadUsers');
  initUserOptions();

  // Add keyboard event listener
  document.addEventListener('keydown', handleKeyPress);
});

onUnmounted(() => {
  // Clean up keyboard event listener
  document.removeEventListener('keydown', handleKeyPress);
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

.edit-drawer
  transform: translateY(100%)
  transition: transform 0.2s ease-out, opacity 0.3s ease-out
  box-shadow: 0 -4px 12px rgba(0, 0, 0, 0.15)
  opacity: 0
  pointer-events: none

  &.drawer-visible
    transform: translateY(0)
    opacity: 1
    pointer-events: auto

// Active task icon styling
.active-task-icon
  color: var(--theme-blue) !important
  animation: pulse-active-icon 2s ease-in-out infinite
  border-radius: 50%
  padding: 2px

// Pulse animation for active task icon
@keyframes pulse-active-icon
  0%
    color: var(--theme-blue)
    background-color: transparent
  50%
    color: white
    background-color: var(--theme-blue)
  100%
    color: var(--theme-blue)
    background-color: transparent
</style>
