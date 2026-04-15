<template>
  <BaseModalForm
    :show="props.show"
    :loading="creating"
    :enable-save="isFormValid"
    :handle-close="handleCancel"
    @submit="handleCreateTask"
    @cancel="handleCancel"
  >
    <template #title>
      {{ $t('create_task') }}
    </template>

    <template #form>
      <div class="row q-col-gutter-sm">
        <div class="col-12">
          <BaseAutocompleteTaskType
            :value="newTask.type"
            key-only
            load-data
            mandatory
            @select="(selection) => newTask.type = selection"
          />
        </div>

        <div class="col-12">
          <q-input
            v-model="newTask.title"
            :label="$capitalize($t('title'))"
            label-slot
            filled
            hide-bottom-space
            :rules="[val => !!val || $t('field_required')]"
          >
            <template #label>
              {{ $capitalize($t('title')) }}
              <span class="text-theme-red"> * </span>
            </template>
          </q-input>
        </div>

        <div class="col-12">
          <q-input
            v-model="newTask.description"
            :label="$capitalize($t('description'))"
            autogrow
            filled
            rows="3"
          />
        </div>

        <div class="col-6">
          <BaseDatePicker
            v-model="newTask.start_from"
            :label="$capitalize($t('start_from'))"
          />
        </div>

        <div class="col-6">
          <BaseDatePicker
            v-model="newTask.due_by"
            :label="$capitalize($t('due_by'))"
          />
        </div>
      </div>
    </template>
  </BaseModalForm>
</template>

<script setup>
import { ref, computed, reactive } from 'vue';
import { useI18n } from 'vue-i18n';
import BaseAutocompleteTaskType from '@/components/BaseAutocompleteTaskType.vue';
import BaseModalForm from '@/components/BaseModalForm.vue';
import BaseDatePicker from '@/components/BaseDatePicker.vue';
import { useTaskStore } from '@/stores/task.js';
import { Notify } from 'quasar';
// Props
const props = defineProps({
  show: {
    type: Boolean,
    default: true,
  }
});


const newTask = reactive({
  type: '',
  title: '',
  description: '',
  start_from: null,
  due_by: null,
});

// Emits
const emit = defineEmits(['close']);

// Composables
const { t: $t } = useI18n();
const taskStore = useTaskStore();

// Local reactive state
const creating = ref(false);

// Computed properties
const isFormValid = computed(() => {
  return !!newTask.type && !!newTask.title;
});

// // Watch for show prop to reset form when modal opens
// watch(() => props.show, (newShow) => {
//   if (newShow) {
//     resetForm();
//   }
// });

// Methods
async function handleCreateTask() {
  if (!isFormValid.value) {
    return;
  }

  creating.value = true;
  try {
    await taskStore.createTask({ ...newTask });

    Notify.create({
      message: 'Task created successfully',
      color: 'theme-green',
      position: 'top',
      timeout: 1500,
    });

    // Reset form and close modal
    resetForm();
    emit('created');
  } catch (error) {
    console.error('Error creating task:', error);
    // TODO: Add error notification handling here if needed
    // The error will be visible to the user through the task store or global error handler
  } finally {
    creating.value = false;
  }
}

function handleCancel() {
  // resetForm();
  emit('close');
}

function resetForm() {
  newTask.type = '';
  newTask.title = '';
  newTask.description = '';
  newTask.start_from = null;
  newTask.due_by = null;
}
</script>
