<template>
  <q-page-container>
    <q-page class="q-pa-md column full-height">

      <q-skeleton v-if="!task" type="text" />

      <div v-else class="column full-height">
        <div class="row items-center text-low q-col-gutter-x-xl">
          <!-- CODE AND STATUS -->
          <div class="col-auto row q-col-gutter-x-md items-center">
          <q-icon :name="task.icon" size="18px" />
          <div class="text-h5 weight-bold text-uppercase q-ml-sm">
            {{ task.task_type_name }} #{{ task.code || '-'}}
          </div>
          <q-chip
            :color="taskStatusOptions[task.status]?.color || 'theme-grey'"
            :label="taskStatusOptions[task.status]?.label"
            :icon="taskStatusOptions[task.status]?.icon || 'mdi-circle-outline'"
            size="10px"
            class="text-uppercase highlight q-ml-lg"
          />
          </div>

          <!-- CREATED BY -->
          <div class="col-auto row q-gutter-x-md items-center">
            <div class="text-h5 uppercase text-low">{{ $t('created_date') }}</div>
            <div class="text-caption text-low">
              {{ new Date(task.created).toLocaleString() }}
            </div>
            <BaseUserAvatar
              :user="getUserByKey(task.created_by)"
              :size="'24px'"
            />
          </div>

          <!-- ASSIGNED TO -->
          <div class="col-auto row q-col-gutter-x-md items-center">
            <div class="text-h5 uppercase text-low">{{ $t('assigned_to') }}</div>
            <div v-if="task.assigned_to?.length" class="row items-center no-wrap">
              <!-- OWNER FIRST WITH CROWN OVERLAY -->
              <template v-if="ownerAssignment">
                <BaseUserAvatar
                  :user="getUserByKey(ownerAssignment.user_key)"
                  :size="'24px'"
                  :show_name="false"
                  avatar-color-class="bg-theme-blue"
                  dense
                />
              </template>

              <!-- SLASH SEPARATOR IF THERE ARE OTHER ASSIGNEES -->
              <div v-if="ownerAssignment && otherAssignments.length" class="q-mx-sm text-h5 text-low">/</div>

              <!-- OTHER ASSIGNEES -->
              <div v-if="otherAssignments.length" class="row q-col-gutter-x-xs items-center">
                <BaseUserAvatar
                  v-for="assignment in otherAssignments"
                  :key="assignment.user_key"
                  :user="getUserByKey(assignment.user_key)"
                  :size="'24px'"
                  :show_name="false"
                  dense
                />
              </div>
            </div>
            <div v-else class="text-italic">
              {{ $t('unassigned') }}
            </div>
            <!-- EDIT ASSIGNMENT BUTTON -->
            <q-btn
              flat
              round
              icon="mdi-pencil-circle"
              padding="0px"
              class="q-ml-lg"
              @click="showAssignmentDialog = true"
            >
              <q-tooltip anchor="center right" self="center left" delay="200">
                {{ $t('edit_assignments') }}
              </q-tooltip>
            </q-btn>
          </div>
        </div>

        <!-- TITLE -->
        <div class="row items-center q-col-gutter-x-xl q-mt-lg">
          <div class="col">
            <div v-if="!editMode" class="text-h2 highlight">
              {{ task.title }}
            </div>
            <q-input
              v-else
              v-model="task.title"
              outlined
              autogrow
              :placeholder="$t('title') || 'Title'"
              input-style="font-size: 1.5rem; font-weight: bold; line-height: 1.2;"
            />
          </div>
          <q-space />
          <!-- EDIT BUTTON -->
          <q-btn
            v-if="!editMode"
            flat
            round
            icon="mdi-pencil"
            color="theme-blue"
            @click="editMode = true"
          >
            <q-tooltip>{{ $t('edit') }}</q-tooltip>
          </q-btn>
          <!-- SAVE/CANCEL BUTTONS -->
          <div v-else class="row q-gutter-md">
            <q-btn
              size="12px"
              color="theme-blue"
              :loading="saving"
              :label="$t('save')"
              @click="save"
            />
            <q-btn
              size="12px"
              color="theme-grey"
              :label="$t('cancel')"
              @click="cancel"
            />
          </div>
        </div>


        <!-- DESCRIPTION -->
        <div class="q-mt-md">
          <div v-if="!editMode">
            <div v-if="task.description" class="text-body1" style="white-space: pre-wrap;">
              {{ task.description }}
            </div>
          </div>
          <q-input
            v-else
            v-model="task.description"
            type="textarea"
            autogrow
            outlined
            :placeholder="$t('description') || 'Description'"
            class="text-body1"
          />
        </div>

        <!-- TABS -->
        <q-tabs
          v-model="tab"
          dense
          class="q-mt-lg text-low"
          content-class="text-h5"
          indicator-color="theme-blue"
          align="left"
          active-class="text-high weight-bold"
        >
          <q-tab name="form" :label="$t('task_data')" class="text-left" />
          <q-tab name="history" :label="$t('history')" />
          <q-tab name="messages" :label="$t('message', 2)" />
        </q-tabs>

        <q-card square class="col surface2 scroll">
          <q-tab-panels v-model="tab" class="transparent">
                <!-- TASK FORM DATA -->
            <q-tab-panel name="form">
              <template v-if="task?.form_fields?.length > 0">
                <div class="column col scroll q-pt-sm q-gutter-y-md">
                  <div
                    v-for="field in task?.form_fields"
                    :key="field?.form_field_key"
                    class="row q-col-gutter-x-md items-center"
                  >
                    <FormField
                      :field="field"
                      :root-path="`/media/task/${taskKey}/${field?.form_field_key}`"
                      :disable="!editMode"
                      class="col"
                      dense
                      @update="field.value = $event"
                    />
                    <q-icon
                      v-if="field.last_updated"
                      class="col-auto"
                      name="mdi-information-outline"
                      color="theme-grey"
                      size="24px"
                    >
                      <q-tooltip
                        anchor="center left"
                        self="center right"
                        delay="200"
                        class="bg-theme-blue">
                        <div class="column q-gutter-y-xs text-right q-pa-sm" >
                          <div class="text-h5">
                            {{ $t('last_update') }}
                          </div>
                          <BaseUserAvatar
                            :user="getFieldUser(field)"
                            size="24px"
                          />
                          <div class="text-h6 text-low">{{ getFieldTimestamp(field) }}</div>
                        </div>
                      </q-tooltip>
                    </q-icon>
                  </div>
                </div>
              </template>
              <div v-else class="col-auto text-italic">No form data</div>
            </q-tab-panel>



            <!-- HISTORY -->
            <q-tab-panel name="history">
              <q-list class="q-pl-xl col scroll q-pb-lg">
                <q-item
                  v-for="(e, index) in history"
                  :key="e._key"
                  class="q-mt-md relative-position row justify-between full-width items-baseline"
                >
                  <!-- TIMELINE DOT & THREAD -->
                  <div
                    style="
                      position: absolute;
                      left: -30px;
                      top: 13px;
                      height: 100%;
                      width: 32px;
                    "
                  >
                    <div class="column full-height">
                      <div class="dot"></div>
                      <div v-if="index < history.length - 1" class="thread"></div>
                    </div>
                  </div>

                  <!-- TIMESTAMP -->
                  <q-item-section
                    class="text-italic q-pr-sm"
                    style="max-width: 200px"
                  >
                    {{ getHumanDate(e.timestamp) }}
                  </q-item-section>

                  <!-- EVENT TYPE -->
                  <q-item-section class="text-h4 highlight text-uppercase">
                    {{ $t(`events.${e.event_type}`) }}
                  </q-item-section>

                  <!-- EVENT USER -->
                  <q-item-section class="col-auto">
                    <BaseUserAvatar name_first :user="getEventUserData(e)" />
                  </q-item-section>
                </q-item>
              </q-list>
            </q-tab-panel>

            <!-- MESSAGES -->
            <q-tab-panel name="messages">
              <MessageThread
                :messages="messages"
                context="task"
                :context_key="taskKey"
              >
                <template #header>
                  <div class="display low-text text-h5 col-auto q-pb-md">
                    {{ $t('message', 2) }}
                  </div>
                  <q-separator></q-separator>
                </template>
              </MessageThread>
            </q-tab-panel>
          </q-tab-panels>
        </q-card>


        <!-- ASSIGNMENT DIALOG -->
        <TaskAssignmentDialog
          :show="showAssignmentDialog"
          :loading="savingAssignment"
          :assignments="task.assigned_to"
          @save="saveAssignments"
          @cancel="cancelAssignment"
        />

      </div>
    </q-page>
  </q-page-container>
</template>

<script setup>
import { cloneDeep } from 'lodash';
import { Notify } from 'quasar';
import { onMounted, onBeforeUnmount, ref, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { useStore } from 'vuex';
import { api as $api } from 'src/boot/axios';
import { capitalize } from 'src/boot/filters';
import BaseUserAvatar from 'src/components/BaseUserAvatar.vue';
import FormField from 'src/components/FormField.vue';
import MessageThread from 'src/components/MessageThread.vue';
import TaskAssignmentDialog from 'src/components/TaskAssignmentDialog.vue';
import { sendEvent } from 'src/composables/event.js';
import { useTask } from 'src/composables/task';
import { formatDateTime } from 'src/lib/TimeHandling';
import { useTaskStore } from 'src/stores/task';

const props = defineProps({
  taskKey: {
    type: String,
    required: true,
  },
});

const store = useStore();
const taskStore = useTaskStore();
const { taskStatusOptions } = useTask();
const { t: $t, locale } = useI18n();

const task = ref(null);
const tab = ref('form');
const editMode = ref(false);
const saving = ref(false);
const originalTaskData = ref(null);
const history = ref([]);
const events = ref(null);
const messages = ref([]);

// Assignment dialog state
const showAssignmentDialog = ref(false);
const savingAssignment = ref(false);

// Assignee grouping
const ownerAssignment = computed(() => {
  const assignments = task.value?.assigned_to || [];
  return assignments.find((a) => a.role === 'owner') || null;
});

const otherAssignments = computed(() => {
  const assignments = task.value?.assigned_to || [];
  return assignments.filter((a) => a.role !== 'owner');
});

onMounted(async () => {
  await store.dispatch('loadUsers');
  task.value = await taskStore.getTaskData(props.taskKey);
  console.log(task.value);
  // Store original data for cancel functionality
  originalTaskData.value = cloneDeep(task.value);

  // No longer need to initialize assignment dialog state - handled by component

  // Load history
  getTaskHistory();

  // Set up event listener for real-time updates
  let eventURL = $api.defaults.baseURL + '/notification/task-notification';
  events.value = new EventSource(eventURL, {
    withCredentials: false,
  });
  events.value.addEventListener('task-notification', (event) => {
    handleTaskMessage(event);
  });
});

onBeforeUnmount(() => {
  if (events.value) {
    events.value.close();
  }
});

function getUserByKey(userKey) {
  let user = store.getters.getUserByKey(userKey);
  if (!user) {
    user = {
      name_first: 'Unknown',
      name_last: 'User',
    };
  }
  return user;
}

function getFieldUser(_field) {
  // This would need to be implemented based on task history/event tracking
  // For now, return null as tasks may not have field-level user tracking yet
  return null;
}

function getFieldTimestamp(_field) {
  // This would need to be implemented based on task history/event tracking
  // For now, return null as tasks may not have field-level timestamp tracking yet
  return null;
}

// History-related methods
function getTaskHistory() {
  $api
    .get('event', { params: { task_key: props.taskKey } })
    .then((resp) => (history.value = resp.data))
    .catch((error) => {
      console.error('Error fetching task history:', error);
    });
}

function handleTaskMessage(message) {
  let event = JSON.parse(message.data);
  if (event?.task_key === props.taskKey) {
    getTaskHistory();
  }
}

function getEventUserData(event) {
  return store.getters.getUserByKey(event.user_key);
}

function getHumanDate(timestamp) {
  const config = {
    year: '2-digit',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    second: '2-digit',
    weekday: 'short',
  };
  return capitalize(formatDateTime(timestamp, locale.value, config));
}

function getFieldType(field) {
  return store.getters.getCustomFieldByKey(field.custom_field_key)?.type;
}

async function saveFiles(task_key) {
  const formFields = task.value.form_fields || [];

  const promises = formFields
    .filter((field) => getFieldType(field) === 'files')
    .map(async (field) => {
      const to_delete = [];
      const to_add = [];

      field.value?.forEach((file) => {
        if (file.temp) {
          to_add.push(file.content);
        } else if (file.delete) {
          to_delete.push(file.name);
        }
      });

      const target = {
        bucket: 'task',
        object_key: task_key,
        subfolder: field.form_field_key,
      };

      // Upload new files
      if (to_add.length) {
        // Populate form data
        const add_body = new FormData();
        Object.entries(target).forEach(([k, v]) => add_body.append(k, v));
        to_add.forEach((file) => add_body.append('contents', file));
        // Post files
        try {
          await $api.post('/files', add_body);
        } catch (error) {
          console.error(error);
          throw error;
        }
      }

      // Delete files
      if (to_delete.length) {
        try {
          await $api.delete('/files', {
            data: {
              ...target,
              filenames: to_delete,
            },
          });
        } catch (error) {
          console.error(error);
          throw error;
        }
      }
    });

  return Promise.all(promises);
}

function cancel() {
  // Restore original data
  task.value = cloneDeep(originalTaskData.value);
  editMode.value = false;
  saving.value = false;
}

// Assignment dialog functions
function cancelAssignment() {
  showAssignmentDialog.value = false;
}

async function saveAssignments(newAssignments) {
  savingAssignment.value = true;
  try {
    // Send TASK_UPDATED event with new assignment
    await sendEvent({
      event_type: 'TASK_UPDATED',
      event_data: {
        task_key: props.taskKey,
        assigned_to: newAssignments
      }
    });

    // Update local task data
    task.value.assigned_to = [...newAssignments];
    originalTaskData.value.assigned_to = [...newAssignments];

    // Close dialog
    showAssignmentDialog.value = false;

    // Refresh task data to ensure consistency
    task.value = await taskStore.getTaskData(props.taskKey);

    Notify.create({
      message: $t('assignment_updated_successfully') || 'Assignment updated successfully',
      color: 'theme-green',
      timeout: 2000,
      position: 'top',
    });
  } catch (error) {
    console.error('Error updating assignment:', error);
    Notify.create({
      message: $t('errors.save_err') || 'Error updating assignment',
      color: 'theme-red',
      timeout: 3000,
      position: 'top',
    });
  } finally {
    savingAssignment.value = false;
  }
}

async function save() {
  saving.value = true;
  try {
    // Save files first
    await saveFiles(props.taskKey);

    // Prepare form fields data for the event
    const formFields = task.value.form_fields || [];
    const formData = [];

    formFields.forEach(field => {
      if (field.form_field_key && field.value !== undefined) {
        formData.push({
          form_field_key: field.form_field_key,
          custom_field_key: field.custom_field_key,
          label: field.label,
          hint: field.hint,
          mandatory: field.mandatory,
          value: getFieldType(field) === 'files'
            ? field.value
                ?.filter((file) => !file.delete)
                .map(({ size, name }) => ({ size, name }))
            : field.value
        });
      }
    });

    // Prepare changed primitive fields
    const eventData = {
      task_key: props.taskKey,
      form_fields: formData,
    };

    if (task.value.title !== originalTaskData.value.title) {
      eventData.title = task.value.title;
    }
    if (task.value.description !== originalTaskData.value.description) {
      eventData.description = task.value.description;
    }

    // Send TASK_UPDATED event
    await sendEvent({
      event_type: 'TASK_UPDATED',
      event_data: eventData
    });

    // Update the original data and exit edit mode
    originalTaskData.value = cloneDeep(task.value);
    editMode.value = false;

    // Refresh task data
    task.value = await taskStore.getTaskData(props.taskKey);

    Notify.create({
      message: $t('task_updated_successfully'),
      color: 'theme-green',
      timeout: 2000,
      position: 'top',
    });
  } catch (error) {
    console.error('Error updating task:', error);
    Notify.create({
      message: $t('errors.save_err') || 'Error saving task',
      color: 'theme-red',
      timeout: 3000,
      position: 'top',
    });
  } finally {
    saving.value = false;
  }
}
</script>

<style lang="sass" scoped>
.dot
  height: 13px
  width: 13px
  border-radius: 100%
  background-color: #888
  border: 5px solid var(--surface-2)
  box-sizing: content-box
  z-index:99

.thread
  position: absolute
  height: 100%
  left: 11px
  top: 20px
  width: 1px
  background-color: #fff3
</style>


