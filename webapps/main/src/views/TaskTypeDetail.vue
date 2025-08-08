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

      <!-- FORM AND PRINT TEMPLATES -->
      <q-tabs
        v-model="tab"
        align="left"
        dense
        indicator-color="theme-blue"
        active-class="text-high weight-bold"
        class="q-mt-lg text-low col-auto"
      >
        <q-tab
          content-class="weight-bold"
          name="form"
          :label="$t('form_title')"
        />
        <q-tab name="linked_entities" :label="$t('linked_entities')" />
        <q-tab name="prints" :label="$t('print_templates')" />
      </q-tabs>

      <q-card square class="col">
        <q-tab-panels v-model="tab" class="fit">
          <!-- TASK TYPE FORM -->
          <q-tab-panel name="form" class="fit surface2 column">
            <FormTemplateEditor
              v-model="temp_metadata.form_fields"
              :edit-mode="editMode"
            />
          </q-tab-panel>

          <!-- LINKED ENTITIES -->
          <q-tab-panel name="linked_entities" class="surface2 column q-pa-md">
            <div class="text-h6 q-mb-md">
              {{ $t('allowed_linked_entities_title') }}
            </div>
            <div class="text-body2 text-low q-mb-lg">
              {{ $t('allowed_linked_entities_description') }}
            </div>

            <div class="row q-col-gutter-md">
              <div
                v-for="option in linkedEntityOptions"
                :key="option.value"
                class="col-12 col-md-6 col-lg-4"
              >
                <q-checkbox
                  v-model="temp_metadata.allowed_linked_entities"
                  :val="option.value"
                  :disable="!editMode"
                  :label="$capitalize($t(option.labelKey))"
                  class="q-mb-sm"
                />
              </div>
            </div>
          </q-tab-panel>

          <!-- PRINT TEMPLATES -->
          <q-tab-panel name="prints" class="surface2 column">
            <div
              v-if="temp_metadata.print_templates.length === 0"
              class="q-mt-md text-italic"
            >
              {{ $t('print_template_none') }}
            </div>
            <div v-else class="row col q-col-gutter-md scroll">
              <div
                v-for="(template, index) in temp_metadata.print_templates"
                :key="template._key"
                class="col-3"
              >
                <PrintTemplateCard
                  :template="template"
                  :allow-unlink="editMode"
                  @unlink="deleteTemplate(index)"
                  @restore="template.trash = false"
                />
              </div>
            </div>

            <div class="col-auto">
              <BaseAutocompleteTemplate
                v-if="editMode"
                class="q-px-sm q-mt-md"
                :label="$t('print_template_add')"
                :selected="temp_metadata.print_templates"
                @select="addTemplate"
              />
            </div>
          </q-tab-panel>
        </q-tab-panels>
      </q-card>
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
import BaseAutocompleteTemplate from '@/components/BaseAutocompleteTemplate.vue'
import BaseDialog from '@/components/BaseDialog.vue'
import BaseTooltipIcon from '@/components/BaseTooltipIcon.vue'
import FormTemplateEditor from '@/components/FormTemplateEditor.vue'
import IconLibrary from '@/components/IconLibrary.vue'
import NoDataAlert from '@/components/NoDataAlert.vue'
import PrintTemplateCard from '@/components/PrintTemplateCard.vue'
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
const tab = ref('form')

const linkedEntityOptions = [
  { value: 'work_order', labelKey: 'work_order.long' },
  { value: 'serial', labelKey: 'serial' },
  { value: 'task', labelKey: 'task' },
  { value: 'issue', labelKey: 'issue' },
  { value: 'product', labelKey: 'product.label' },
]

const temp_metadata = reactive({
  name: '',
  description: '',
  active: true,
  icon: 'mdi-check-circle',
  form_fields: [],
  print_templates: [],
  allowed_linked_entities: [],
})

const setTempData = () => {
  if (props.taskType) {
    Object.keys(temp_metadata).forEach((key) => {
      if (key in props.taskType) {
        temp_metadata[key] = _cloneDeep(props.taskType[key])
      } else if (key === 'allowed_linked_entities') {
        // Default to empty array if field doesn't exist in taskType yet
        temp_metadata[key] = []
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

const addTemplate = (template) => {
  temp_metadata.print_templates.push({
    ...template,
    temp: true,
  })
}

const deleteTemplate = (template_index) => {
  const template = temp_metadata.print_templates[template_index]
  template.temp
    ? temp_metadata.print_templates.splice(template_index, 1)
    : (template.trash = true)
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
