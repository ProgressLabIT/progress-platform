<template>
  <BaseConfirmationDialog
    :show="true"
    confirm_color="theme-red"
    :confirm_prompt="$t('delete')"
    @close="$emit('close')"
    @confirm="deleteTaskType"
  >
    <div>
      {{ $capitalize($t('task_type_delete_question') || 'Are you sure you want to delete this task type?') }}
    </div>
    <div class="text-h3 uppercase highlight q-mt-md">
      {{ taskType.name }}
    </div>
  </BaseConfirmationDialog>
</template>

<script setup>
import { ref } from 'vue'
import { useQuasar } from 'quasar'
import BaseConfirmationDialog from '@/components/BaseConfirmationDialog.vue'
import { useTaskTypeStore } from '@/stores/taskType'

const props = defineProps({
  taskType: {
    type: Object,
    required: true,
  },
})

const emit = defineEmits(['close', 'deleted'])

const $q = useQuasar()
const taskTypeStore = useTaskTypeStore()

const deleting = ref(false)

const deleteTaskType = async () => {
  if (deleting.value) {
    return
  }

  deleting.value = true

  try {
    await taskTypeStore.deleteTaskType(props.taskType._key)

    $q.notify({
      message: 'Task type deleted successfully',
      color: 'theme-green',
      timeout: 2000,
      position: 'top',
    })

    emit('deleted')
  } catch (error) {
    console.error('Error deleting task type:', error)

    let errorMessage = 'Error deleting task type'
    if (error.response?.status === 403) {
      errorMessage = 'Task type is in use and cannot be deleted'
    } else if (error.response?.data?.detail) {
      errorMessage = error.response.data.detail
    }

    $q.notify({
      message: errorMessage,
      color: 'theme-red',
      timeout: 3000,
      position: 'top',
    })

    emit('close')
  } finally {
    deleting.value = false
  }
}
</script>
