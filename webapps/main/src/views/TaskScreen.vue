<template>
  <BaseModalScreen :show="true" @close="exit">
    <template #header>
      <span v-if="!task" class="q-ml-md display medium highlight weight-medium text-uppercase">
        {{ $t('task') }}: {{ taskKey }}
      </span>
      <div v-else class="col-auto row q-mx-none items-center q-gutter-x-md display medium highlight weight-medium text-uppercase">
        <div
          :class="{ 'hover-underline': hasAdminAccess, 'pointer': hasAdminAccess }"
          @click="hasAdminAccess ? goToTaskType() : null">
        {{ task.task_type_name }}
        </div>
        <div>
          <q-icon :name="task.icon" size="18px" />
        {{ task.code || '-'}}
        </div>
      </div>
      <q-space />
    </template>

    <template #content>
      <q-splitter
        v-model="taskColumnWidth"
        class="fit"
        separator-class="text-disabled"
      >
         <!-- MESSAGES -->
        <template #after>
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
        </template>
        <template #before>
          <q-skeleton v-if="!task" type="text" />

          <div v-else class="q-pa-md full-height column">
            <div class="row items-center text-low q-col-gutter-x-xl">
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

                <div class="col-auto">
                <q-btn
                  flat
                  round
                  icon="mdi-pencil"
                  size="10px"
                  :disabled="!['pending', 'open'].includes(task.status)"
                  @click="showAssignmentDialog = true"
                >
                  <q-tooltip anchor="center right" self="center left" :delay="200">
                    {{ $t('edit_assignments') }}
                  </q-tooltip>
                </q-btn>
                </div>
              </div>

              <div class="col-auto row items-center q-gutter-x-sm">
                <q-chip
                  :color="taskStatusOptions[task.status]?.color || 'theme-grey'"
                  :label="taskStatusOptions[task.status]?.label"
                  :icon="taskStatusOptions[task.status]?.icon || 'mdi-circle-outline'"
                  size="10px"
                  class="highlight text-uppercase"
                  />
                <!-- CLOSE/REOPEN BUTTON -->
                <q-btn
                  v-if="task.status !== 'pending'"
                  :icon="task.status === 'open' ? 'mdi-check' : 'mdi-restore'"
                  size="10px"
                  flat
                  round
                  :loading="togglingStatus"
                  @click="toggleTaskStatus"
                >
                  <q-tooltip anchor="center right" self="center left" :delay="200">
                    {{ task.status === 'open' ? $t('complete_task') : $t('reopen_task') }}
                  </q-tooltip>
                </q-btn>

                <!-- CANCEL BUTTON -->
                <q-btn
                  v-if="['pending', 'open'].includes(task.status)"
                  size="10px"
                  flat
                  icon="mdi-close"
                  round
                  @click="cancelTask"
                >
                  <q-tooltip anchor="center right" self="center left" :delay="200">
                    {{ $t('cancel_task') }}
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

              <div class="col-auto row q-gutter-md">
                <!-- ACTIVATE BUTTON -->
                <q-btn
                  v-if="!editMode && taskStore.activeTaskKey !== taskKey && task.status === 'open'"
                  :label="$t('activate')"
                  icon="mdi-play"
                  color="theme-green"
                  size="10px"
                  :loading="activating"
                  @click="activateTask"
                />

                <q-btn
                  v-if="!editMode"
                  :disabled="task.status !== 'open'"
                  :label="$t('edit')"
                  icon="mdi-pencil"
                  color="theme-blue"
                  size="10px"
                  @click="editMode = true"
                >
                  <q-tooltip v-if="task.status !== 'open'" anchor="center right" self="center left" :delay="200">
                    {{ $t('task_must_be_open_to_edit') }}
                  </q-tooltip>
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

            <q-separator class="q-mt-md" />


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
              <q-tab name="form" :label="$t('form')" class="text-left" />
              <q-tab name="history" :label="$t('history')" />
              <q-tab name="linked_entities" :label="$t('link', 2)" />
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
                            :delay="200"
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
                  <q-list class="col q-pb-lg">
                    <TimelineItem
                      v-for="(e, index) in history"
                      :key="e._key"
                      :event="e"
                      :show-thread="index < history.length - 1"
                      :user-data="getEventUserData(e)"
                    />
                  </q-list>
                </q-tab-panel>

                <!-- LINKED ENTITIES -->
                <q-tab-panel name="linked_entities">
                  <div class="column q-col-gutter-y-sm">
                    <div v-if="allowedEntityTypes.length === 0" class="text-italic">
                      {{ $t('linked_entities.no_linkable_entities') }}
                    </div>
                    <div v-for="type in allowedEntityTypes" :key="type" class="row items-center q-col-gutter-x-sm" style="min-height: 42px;">
                      <div class="text-h5 text-low text-uppercase col-2">
                        {{ $t(`linked_entities.${type}`) }}
                      </div>

                      <div
                        v-if="canAddLink(type)"
                        class="col-auto q-pr-md">
                        <q-btn
                          color="theme-blue"
                          round
                          icon="mdi-plus"
                          size="8px"
                          padding="2px"
                          @click="openLinkDialog(type)"
                        />
                      </div>

                      <div
                        v-for="link in linksByEntityType[type] || []"
                        :key="link.key"
                        class="col-auto">
                        <q-chip
                          clickable
                          square
                          style="border-radius: 4px;"
                          outline
                          size="12px"
                          padding="2px 12px"
                          @click="goToEntity(link)">
                          <div class="text-uppercase" :class="{ 'text-italic': !link?.code }">
                            <template v-if="link?.code">{{ link?.code }}</template>
                            <template v-else>({{ $t('id') }} {{ link?.key || '-' }})</template>
                          </div>
                          <q-icon
                            name="mdi-close"
                            size="14px"
                            class="q-ml-xs cursor-pointer"
                            color="theme-grey"
                            @click.stop="confirmRemoveLink(link)"
                          />
                        </q-chip>
                      </div>
                    </div>
                  </div>
                </q-tab-panel>
              </q-tab-panels>
            </q-card>
          </div>
        </template>
      </q-splitter>
    </template>
  </BaseModalScreen>


  <!-- ASSIGNMENT DIALOG -->
  <TaskAssignmentDialog
    :show="showAssignmentDialog"
    :loading="savingAssignment"
    :assignments="task?.assigned_to"
    @save="saveAssignments"
    @cancel="cancelAssignment"
  />

  <!-- LINK ENTITY DIALOG -->
  <LinkEntityDialog
    :allowed-entity-types="allowedEntityTypes"
    v-model:selected-entity-type="selectedEntityType"
    :show="showLinkDialog"
    :saving="savingLink"
    :existing-links="task?.links"
    @save="saveLink"
    @close="closeLinkDialog"
  />

  <!-- REMOVE LINK CONFIRMATION DIALOG -->
  <BaseConfirmationDialog
    :show="showRemoveConfirmation"
    :confirm-color="'theme-red'"
    :confirm-prompt="$t('remove')"
    @confirm="removeLink"
    @close="cancelRemoveLink"
  >
    <template #default>
      <div class="text-center">
        {{ $t('confirm_remove_link') || 'Are you sure you want to remove this link?' }}
        <div v-if="linkToRemove" class="text-h5 q-mt-sm text-low">
          {{ linkToRemove.code || linkToRemove.key }}
        </div>
      </div>
    </template>
  </BaseConfirmationDialog>
</template>

<script setup>
import { cloneDeep } from 'lodash';
import { Notify, Dialog } from 'quasar';
import { onMounted, ref, computed, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter, useRoute } from 'vue-router';
import { useStore } from 'vuex';
import { api as $api } from '@/boot/axios';
import { useSSE } from '@/composables/useSSE';
import { capitalize } from '@/boot/filters';
import BaseConfirmationDialog from '@/components/BaseConfirmationDialog.vue';
import BaseModalScreen from '@/components/BaseModalScreen.vue';
import BaseUserAvatar from '@/components/BaseUserAvatar.vue';
import FormField from '@/components/FormField.vue';
import LinkEntityDialog from '@/components/LinkEntityDialog.vue';
import MessageThread from '@/components/MessageThread.vue';
import TaskAssignmentDialog from '@/components/TaskAssignmentDialog.vue';
import TimelineItem from '@/components/TimelineItem.vue';
import { sendEvent } from '@/composables/event.js';
import { useTask } from '@/composables/task';
import { formatDateTime } from '@/lib/TimeHandling';
import { useQueryModel } from '@/lib/queryModelFactory';
import { useTaskStore } from '@/stores/task';

const props = defineProps({
  taskKey: {
    type: String,
    required: true,
  },
});

const store = useStore();
const taskStore = useTaskStore();
const router = useRouter();
const route = useRoute();
const { taskStatusOptions } = useTask();
const { t: $t, locale } = useI18n();

const task = ref(null);
const tab = useQueryModel(String, 'tab', 'form');
const taskColumnWidth = ref(70);
const editMode = ref(false);
const saving = ref(false);
const originalTaskData = ref(null);
const history = ref([]);
const { subscribe: subscribeSSE } = useSSE('task');
const messages = ref([]);

// Status management state
const togglingStatus = ref(false);
const activating = ref(false);
const showLinkDialog = ref(false);

// Assignment dialog state
const showAssignmentDialog = ref(false);
const savingAssignment = ref(false);

// Link dialog state
const savingLink = ref(false);
const selectedEntityType = ref(null);

// Remove link confirmation state
const showRemoveConfirmation = ref(false);
const linkToRemove = ref(null);

// Assignee grouping
const ownerAssignment = computed(() => {
  const assignments = task.value?.assigned_to || [];
  return assignments.find((a) => a.role === 'owner') || null;
});

const otherAssignments = computed(() => {
  const assignments = task.value?.assigned_to || [];
  return assignments.filter((a) => a.role !== 'owner');
});

// Admin access check
const hasAdminAccess = computed(() => {
  return store.getters.hasPermission('admin');
});

// Available entity types for linking
const allowedEntityTypes = computed(() => {
  return task.value?.link_settings.filter(setting => setting.enabled).map(setting => setting.type) || [];
});

function canAddLink(type) {
  const taskStatusCheck = ['open', 'pending'].includes(task.value.status)
  const linkTypeSetting = task.value.link_settings.filter(setting => setting.type === type)[0]
  const linkEnabled = linkTypeSetting?.enabled || false
  const linkMultipleAllowed = linkTypeSetting?.allow_multiple || false
  const currentLinksOfType = task.value.links.filter(link => link.type === type).length
  return taskStatusCheck && linkEnabled && (linkMultipleAllowed || currentLinksOfType === 0);
}


function exit() {
  let query = { ...route.query };

  if (route.query.back_to) {
    delete query.back_to;
    const push_route = { name: route.query.back_to, query };
    router.push(push_route);
  } else {
    router.back()
  }
}


async function fetchTaskData() {
  // Close any open dialogs
  showAssignmentDialog.value = false;
  showLinkDialog.value = false;
  selectedEntityType.value = null;

  // Reset edit mode
  editMode.value = false;

  // Fetch new task data
  task.value = await taskStore.getTaskData(props.taskKey);
  originalTaskData.value = cloneDeep(task.value);

  // Reload history
  getTaskHistory();
}

// Watch for taskKey changes to handle navigation to linked tasks
watch(() => props.taskKey, async () => {
  if (props.taskKey && props.taskKey !== task.value._key) {
    fetchTaskData();
  }
}, { immediate: false });

onMounted(async () => {
  await store.dispatch('loadUsers');
  await fetchTaskData();

  subscribeSSE((event) => {
    handleTaskMessage(event);
  });
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

const getFieldUser = (field) => {
  const userKey = history.value.find((e) => e._key === field.last_updated)?.user_key;
  return store.getters.user_data(userKey);
};

const getFieldTimestamp = (field) => {
  const timestamp = history.value.find((e) => e._key === field.last_updated)?.timestamp;
  return getHumanDate(timestamp, {
    year: '2-digit',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

// History-related methods
function getTaskHistory() {
  $api
    .get('event', { params: { task_key: props.taskKey } })
    .then((resp) => (history.value = resp.data))
    .catch((error) => {
      console.error('Error fetching task history:', error);
    });
}

async function handleTaskMessage(message) {
  let event = JSON.parse(message.data);
  if (event?.task_key === props.taskKey) {
    await fetchTaskData();
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
    await fetchTaskData();

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

// Navigate to task type detail page
function goToTaskType() {
  if (!task.value?.task_type_key) {
    console.warn('No task type key available for navigation');
    return;
  }

  try {
    router.push({
      name: 'taskTypeDetail',
      params: { taskTypeKey: task.value.task_type_key }
    });
  } catch (error) {
    console.error('Error navigating to task type:', error);
    Notify.create({
      message: $t('errors.navigation_err') || 'Error navigating to task type',
      color: 'theme-red',
      timeout: 3000,
      position: 'top',
    });
  }
}

// Navigate to entity screen based on entity type
function goToEntity(link) {
  if (!link || !link.type || !link.key) {
    console.warn('Invalid link data:', link);
    return;
  }

  const entityRoutes = {
    work_order: {
      name: 'workOrderScreen',
      params: { wo_key: link.key }
    },
    product: {
      name: 'productHome',
      params: { product_key: link.key }
    },
    issue: {
      name: 'issueDetail',
      params: { issueKey: link.key }
    },
    serial: {
      name: 'serialDetail',
      params: { serialKey: link.key }
    },
    task: {
      name: 'taskScreen',
      params: { taskKey: link.key }
    }
  };

  const targetRoute = entityRoutes[link.type];
  if (!targetRoute) {
    console.warn(`Unknown entity type: ${link.type}`);
    Notify.create({
      message: $t('errors.unknown_entity_type') || 'Unknown entity type',
      color: 'theme-orange',
      timeout: 3000,
      position: 'top',
    });
    return;
  }

  // Check if we should prompt for task activation before navigating
  const shouldPromptActivation =
    task.value &&
    task.value.status === 'open' &&
    taskStore.activeTaskKey !== props.taskKey;

  if (shouldPromptActivation) {
    // Show activation prompt using programmatic dialog
    Dialog.create({
      title: $t('activate_task_before_leaving') || 'Activate Task Before Leaving?',
      message: $t('activate_task_prompt_message') || 'Would you like to activate this task before navigating to the linked entity? This will help maintain task context.',
      cancel: {
        label: $t('navigate_without_activating') || 'No, just navigate',
        color: 'theme-grey',
        flat: true
      },
      ok: {
        label: $t('activate_and_navigate') || 'Yes, activate and navigate',
        color: 'theme-blue'
      },
      persistent: true
    }).onOk(async () => {
      // Activate the task first
      try {
        if (task.value.status === 'open' && taskStore.activeTaskKey !== props.taskKey) {
          taskStore.setActiveTask(props.taskKey);

          Notify.create({
            message: $t('task_activated_successfully') || 'Task activated successfully',
            color: 'theme-green',
            timeout: 2000,
            position: 'top',
          });
        }

        // Then navigate to the entity
        router.push(targetRoute);
      } catch (error) {
        console.error('Error activating task:', error);
        Notify.create({
          message: $t('errors.activation_err') || 'Error activating task',
          color: 'theme-red',
          timeout: 3000,
          position: 'top',
        });
      }
    }).onCancel(() => {
      // Navigate without activating
      router.push(targetRoute);
    });
  } else {
    // Navigate directly
    router.push(targetRoute);
  }
}

async function save() {
  saving.value = true;
  try {
    // Save files first
    await saveFiles(props.taskKey);

    // Prepare form fields data for the event
    const formFields = task.value.form_fields || [];
    const originalFields = originalTaskData.value.form_fields || [];
    const formData = [];

    formFields.forEach(field => {
      if (!field.form_field_key) {
        return;
      }

      // Find the original field value
      const originalField = originalFields.find(f => f.form_field_key === field.form_field_key);
      const originalValue = originalField?.value;

      // Check if the value has changed (including when clearing to undefined/null)
      const valueChanged = field.value !== originalValue;

      // Include field if value has changed (even if new value is undefined/null)
      if (valueChanged) {
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
    await fetchTaskData();

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


// #########################################################
// LINK MANAGEMENT
// #########################################################

// Group links by entity type
const linksByEntityType = computed(() => {
  return task.value.links.reduce((acc, link) => {
    acc[link.type] = [...(acc[link.type] || []), link];
    return acc;
  }, {});
});


// Link dialog functions
function openLinkDialog(entityType) {
  selectedEntityType.value = entityType;
  showLinkDialog.value = true;
}

function closeLinkDialog() {
  showLinkDialog.value = false;
  selectedEntityType.value = null;
}

// Remove link functions
function confirmRemoveLink(link) {
  linkToRemove.value = link;
  showRemoveConfirmation.value = true;
}

function cancelRemoveLink() {
  showRemoveConfirmation.value = false;
  linkToRemove.value = null;
}


async function saveLink(linkData) {
  savingLink.value = true;
  try {
    // TODO: Implement the actual API call to link the entity to the task
    // This would depend on your backend API structure
    await sendEvent({
      event_type: 'TASK_LINKED',
      event_data: {
        task_key: props.taskKey,
        link_type: linkData.entityType,
        link_key: linkData.entity._key || linkData.entity,
      }
    });


    // Refresh task data to get updated links
    await fetchTaskData();

    closeLinkDialog();

    Notify.create({
      message: $t('entity_linked_successfully') || 'Entity linked successfully',
      color: 'theme-green',
      timeout: 2000,
      position: 'top',
    });
  } catch (error) {
    console.error('Error linking entity:', error);
  } finally {
    savingLink.value = false;
  }
}


async function removeLink() {
  if (!linkToRemove.value) {
    return;
  }

  try {
    await sendEvent({
      event_type: 'TASK_UNLINKED',
      event_data: {
        task_key: props.taskKey,
        link_type: linkToRemove.value.type,
        link_key: linkToRemove.value.key,
      }
    });

    // Close confirmation dialog
    showRemoveConfirmation.value = false;
    linkToRemove.value = null;

    // Refresh task data to get updated links
    await fetchTaskData();

    Notify.create({
      message: $t('link_removed_successfully') || 'Link removed successfully',
      color: 'theme-green',
      timeout: 2000,
      position: 'top',
    });
  } catch (error) {
    console.error('Error removing link:', error);
    Notify.create({
      message: $t('errors.unlink_err') || 'Error removing link',
      color: 'theme-red',
      timeout: 3000,
      position: 'top',
    });
  }
}



// Toggle task status between completed and open
async function toggleTaskStatus() {
  togglingStatus.value = true;
  try {
    const success = await taskStore.toggleTaskStatusWithConfirmation(task.value, $t);
    if (success) {
      // Refresh task data to ensure consistency
      await fetchTaskData();
    }
  } finally {
    togglingStatus.value = false;
  }
}

async function cancelTask() {
  await taskStore.cancelTaskWithConfirmation(props.taskKey, $t);
  await fetchTaskData();
}

// Activate task
async function activateTask() {
  if (task.value.status === 'active' || task.value.status === 'completed') {
    Notify.create({
      message: $t('task_already_active_or_completed') || 'Task already active or completed',
      color: 'theme-orange',
      timeout: 2000,
      position: 'top',
    });
    return;
  }
  taskStore.activeTaskKey = props.taskKey;
}
</script>


