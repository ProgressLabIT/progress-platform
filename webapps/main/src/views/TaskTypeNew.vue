<template>
  <BaseModalForm
    id="new-task-type-form"
    :show="true"
    :loading="saving"
    max-width="700px"
    :enable-save="canSave"
    @submit="submit"
    @cancel="$emit('close')"
  >
    <template #title>
      {{ $t('task_type_new') || 'New Task Type' }}
    </template>

    <template #form>
      <div class="row q-col-gutter-lg items-center" style="min-width: 400px">
        <div class="col-12">
          <q-input
            v-model="new_task_type.name"
            filled
            stack-label
            :label="$capitalize($t('name').toUpperCase())"
            :error="!new_task_type.name && submitted"
            :error-message="!new_task_type.name ? 'Name is required' : ''"
          >
          </q-input>
        </div>

        <div class="col-12">
          <q-input
            v-model="new_task_type.description"
            filled
            stack-label
            autogrow
            clearable
            :label="$t('description').toUpperCase()"
          >
          </q-input>
        </div>

        <div class="col-12">
          <q-toggle
            v-model="new_task_type.active"
            :label="$t('active').toUpperCase()"
          >
          </q-toggle>
        </div>

        <div class="row items-center justify-between full-width">
          <div class="text-h5 text-high text-uppercase">
            {{ $t('icon') }}
          </div>
          <div class="text-low row items-center">
            <q-icon :name="new_task_type.icon" size="lg" class="q-mr-sm" />
            <div class="text-body2 text-italic">{{ new_task_type.icon }}</div>
          </div>
          <q-btn
            flat
            :label="$t('change')"
            color="theme-blue"
            @click="show_icon_library = true"
          >
          </q-btn>
          <BaseDialog :show="show_icon_library">
            <div class="surface2 q-pa-md">
              <IconLibrary @choice="(value) => pickIcon(value)" />
            </div>
          </BaseDialog>
        </div>
      </div>
    </template>
  </BaseModalForm>
</template>

<script setup>
import { useQuasar } from 'quasar'
import { ref, computed } from 'vue'
import BaseDialog from '@/components/BaseDialog.vue'
import BaseModalForm from '@/components/BaseModalForm.vue'
import IconLibrary from '@/components/IconLibrary.vue'
import { useTaskTypeStore } from '@/stores/taskType'

const emit = defineEmits(['close', 'created'])

const $q = useQuasar()
const taskTypeStore = useTaskTypeStore()

const saving = ref(false)
const submitted = ref(false)
const show_icon_library = ref(false)

const new_task_type = ref({
  name: '',
  description: '',
  active: true,
  icon: 'mdi-check-circle',
})

const canSave = computed(() => {
  return new_task_type.value.name && new_task_type.value.name.trim().length > 0
})

const pickIcon = (value) => {
  new_task_type.value.icon = value
  show_icon_library.value = false
}

const submit = async () => {
  submitted.value = true

  if (!canSave.value) {
    $q.notify({
      message: 'Please fill in the required fields',
      color: 'theme-red',
      timeout: 2000,
      position: 'top',
    })
    return
  }

  saving.value = true

  try {
    const createdTaskType = await taskTypeStore.createTaskType(new_task_type.value)

    $q.notify({
      message: 'Task type created successfully',
      color: 'theme-green',
      timeout: 2000,
      position: 'top',
    })

    emit('created', createdTaskType)
  } catch (error) {
    console.error('Error creating task type:', error)

    let errorMessage = 'Error creating task type'
    if (error.response?.status === 409) {
      errorMessage = 'A task type with this name already exists'
    } else if (error.response?.data?.detail) {
      errorMessage = error.response.data.detail
    }

    $q.notify({
      message: errorMessage,
      color: 'theme-red',
      timeout: 3000,
      position: 'top',
    })
  } finally {
    saving.value = false
  }
}
</script>
