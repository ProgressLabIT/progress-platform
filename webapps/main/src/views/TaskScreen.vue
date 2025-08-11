<template>
  <q-page-container>
    <q-page class="q-pa-md column full-height">

      <q-skeleton v-if="!task" type="text" />


      <div v-else class="column q-gutter-y-md">
        <!-- CODE AND STATUS -->
        <div class="row items-center text-low">
          <q-icon :name="task.icon" size="28px" />
          <div class="text-h4 weight-bold text-uppercase q-ml-sm">
            {{ task.task_type_name }} #{{ task.code || '-'}}
          </div>
          <q-chip
            :color="taskStatusOptions[task.status]?.color || 'theme-grey'"
            :label="taskStatusOptions[task.status]?.label"
            :icon="taskStatusOptions[task.status]?.icon || 'mdi-circle-outline'"
            size="12px"
            class="text-uppercase highlight q-ml-lg"
          />
        </div>

        <!-- TITLE -->
        <div class="row items-center">
          <div class="text-h2 highlight col">
            {{ task.title }}
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

        <div class="q-mt-md row items-center q-gutter-x-md">
          <!-- CREATED BY -->
          <div class="text-h5 uppercase text-low">{{ $t('created_date') }}</div>
          <div class="text-caption text-low">
            {{ new Date(task.created).toLocaleString() }}
          </div>
          <BaseUserAvatar
            :user="getUserByKey(task.created_by)"
            :size="'24px'"
          />
        </div>

        <!-- DESCRIPTION -->
        <div v-if="task.description" class="q-mt-md text-body1">
          {{ task.description }}
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
          <q-tab name="assignees" :label="$t('assigned_to')" />
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

            <!-- ASSIGNEES -->
            <q-tab-panel name="assignees">
              <template v-if="task.assigned_to && task.assigned_to.length > 0">
                <q-list dense>
                  <q-item v-for="userKey in task.assigned_to" :key="userKey" style="padding-left: 0px; padding-right: 0px;">
                    <BaseUserAvatar
                      :user="getUserByKey(userKey)"
                      :size="'24px'"
                    />
                  </q-item>
                </q-list>
              </template>
              <div v-else class="col-auto text-italic">No assignees</div>
            </q-tab-panel>
          </q-tab-panels>
        </q-card>

        <template v-if="false">

          <q-separator />

          <!-- ASSIGNED TO -->
          <div class="text-h5 uppercase text-low">{{ $t('assigned_to') }}</div>
          <q-list dense>
            <q-item v-for="userKey in task.assigned_to" :key="userKey" style="padding-left: 0px; padding-right: 0px;">
              <BaseUserAvatar
              :user="getUserByKey(userKey)"
              :size="'24px'"
              />
            </q-item>
          </q-list>
        </template>



      </div>
    </q-page>
  </q-page-container>
</template>

<script setup>
import { cloneDeep } from 'lodash';
import { Notify } from 'quasar';
import { onMounted, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useStore } from 'vuex';
import { api as $api } from 'src/boot/axios';
import BaseUserAvatar from 'src/components/BaseUserAvatar.vue';
import FormField from 'src/components/FormField.vue';
import { sendEvent } from 'src/composables/event.js';
import { useTask } from 'src/composables/task';
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
const { t: $t } = useI18n();

const task = ref(null);
const tab = ref('form');
const editMode = ref(false);
const saving = ref(false);
const originalTaskData = ref(null);

onMounted(async () => {
  task.value = await taskStore.getTaskByKey(props.taskKey);
  // Store original data for cancel functionality
  originalTaskData.value = cloneDeep(task.value);
});

function getUserByKey(userKey) {
  return store.getters.getUserByKey(userKey);
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

    // Send TASK_UPDATED event
    await sendEvent({
      event_type: 'TASK_UPDATED',
      event_data: {
        task_key: props.taskKey,
        form_data: formData
      }
    });

    // Update the original data and exit edit mode
    originalTaskData.value = cloneDeep(task.value);
    editMode.value = false;

    // Refresh task data
    task.value = await taskStore.getTaskByKey(props.taskKey);

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


