<template>
  <div class="full-height column" :class="editMode ? 'q-pa-lg' : 'q-pa-xl'">
    <NoDataAlert v-if="!taskType" />
    <template v-else>
      <div class="row q-col-gutter-lg col-auto">
        <template v-if="!editMode">
          <div v-if="!editMode" class="col">
            <div class="text-h2 uppercase display highlight q-mb-sm">
              {{ taskType.name }}
            </div>
            <div style="width: 50%">
              {{ taskType.description || '— No Description —' }}
            </div>
          </div>

          <q-space />

          <BaseTooltipIcon
            icon="mdi-pencil"
            :tooltip="$capitalize($t('edit'))"
            :color="$theme.blue"
            @icon-click="editMode = true"
          >
          </BaseTooltipIcon>

          <BaseTooltipIcon
            icon="mdi-delete"
            :tooltip="$capitalize($t('delete'))"
            :color="$theme.red"
            @icon-click="showDeleteDialog = true"
          >
          </BaseTooltipIcon>
        </template>

        <!-- EDIT TASK TYPE METADATA -->
        <template v-else>
          <div class="col-10 row q-col-gutter-lg q-mb-lg">
            <div class="col">
              <q-input
                v-model="temp_metadata.name"
                filled
                dense
                stack-label
                hide-bottom-space
                :label="$capitalize($t('name'))"
              >
              </q-input>
            </div>

            <div class="col-12">
              <q-input
                v-model="temp_metadata.description"
                filled
                dense
                stack-label
                autogrow
                hide-bottom-space
                :label="$capitalize($t('description'))"
              >
              </q-input>
            </div>
          </div>

          <div class="col column q-pl-xl q-gutter-md">
            <q-btn
              size="12px"
              color="theme-blue"
              :loading="saving"
              :label="$t('save')"
              @click="save"
            >
            </q-btn>
            <q-btn
              size="12px"
              color="theme-grey"
              :label="$t('cancel')"
              @click="cancel"
            >
            </q-btn>
          </div>
        </template>
      </div>

      <!-- TASK TYPE OPTIONS -->
      <div class="row q-gutter-lg items-center col-auto">
        <!-- ACTIVE -->
        <q-toggle
          v-model="temp_metadata.active"
          :disable="!editMode"
          :label="$capitalize($t('active'))"
        >
        </q-toggle>

        <!-- TASK TYPE ICON -->
        <div class="q-pl-xl">
          <div class="row items-center q-pl-sm">
            <div class="text-h5 text-uppercase weight-bold text-low q-mr-md">
              {{ $t('icon') }}
            </div>
            <div class="text-low row items-center">
              <q-icon :name="temp_metadata.icon" size="md" class="q-mr-sm" />
              <div class="text-body2 text-italic">{{ temp_metadata.icon }}</div>
            </div>
            <q-btn
              v-if="editMode"
              flat
              :label="$t('change')"
              color="theme-blue"
              class="q-ml-xl"
              @click="show_icon_library = true"
            >
            </q-btn>
          </div>

          <BaseDialog :show="show_icon_library" :no-backdrop-dismiss="false">
            <div class="surface2 q-pa-md">
              <IconLibrary @choice="(value) => pickIcon(value)" />
            </div>
          </BaseDialog>
        </div>
      </div>
    </template>

    <!-- DELETE DIALOG -->
    <TaskTypeDelete
      v-if="showDeleteDialog"
      :task-type="taskType"
      @close="showDeleteDialog = false"
      @deleted="onTaskTypeDeleted"
    />
  </div>
</template>

<script setup>
import { cloneDeep as _cloneDeep } from 'lodash'
import { useQuasar } from 'quasar'
import { ref, reactive, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import BaseDialog from '@/components/BaseDialog.vue'
import BaseTooltipIcon from '@/components/BaseTooltipIcon.vue'
import IconLibrary from '@/components/IconLibrary.vue'
import NoDataAlert from '@/components/NoDataAlert.vue'
import { useTaskTypeStore } from '@/stores/taskType'
import TaskTypeDelete from './TaskTypeDelete.vue'

const props = defineProps({
  taskType: {
    type: Object,
    required: true,
  },
  taskTypeKey: {
    type: [String, Object],
    required: true,
  },
})

const router = useRouter()
const $q = useQuasar()
const taskTypeStore = useTaskTypeStore()

const editMode = ref(false)
const saving = ref(false)
const showDeleteDialog = ref(false)
const show_icon_library = ref(false)

const temp_metadata = reactive({
  name: '',
  description: '',
  active: true,
  icon: 'mdi-check-circle',
})

const setTempData = () => {
  if (props.taskType) {
    Object.keys(temp_metadata).forEach((key) => {
      if (key in props.taskType) {
        temp_metadata[key] = _cloneDeep(props.taskType[key])
      }
    })
  }
}

const pickIcon = (value) => {
  temp_metadata.icon = value
  show_icon_library.value = false
}

const cancel = () => {
  saving.value = false
  editMode.value = false
  setTempData()
  $q.notify({
    message: 'Changes canceled',
    color: 'theme-grey',
    timeout: 1500,
    position: 'top',
  })
}

const save = async () => {
  saving.value = true
  try {
    const data = {
      _key: props.taskType._key,
      ...temp_metadata,
    }
    await taskTypeStore.updateTaskType(data)
    saving.value = false
    editMode.value = false
    $q.notify({
      message: 'Task type updated successfully',
      color: 'theme-green',
      timeout: 1500,
      position: 'top',
    })
  } catch (error) {
    saving.value = false
    $q.notify({
      message: 'Error updating task type',
      color: 'theme-red',
      timeout: 3000,
      position: 'top',
    })
  }
}

const onTaskTypeDeleted = () => {
  showDeleteDialog.value = false
  router.push({ name: 'taskTypeLibrary' })
}

watch(() => editMode.value, setTempData)
watch(() => props.taskTypeKey, setTempData)

onMounted(() => {
  setTempData()
})
</script>
