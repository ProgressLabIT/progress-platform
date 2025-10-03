<template>
  <div class="column full-height q-pa-md">

    <!-- PRODUCTT CODE AND DESCRIPTION -->
      <div class="text-h1 display highlight">
        {{ productData.code }}
      </div>
      <div class="text-body1">
        {{ productData.description }}
      </div>

    <!-- GANTT CHART -->
    <ProcessTasksViewer
      :process-phases="processPhases"
      :tasks="processTasks"
      :selected-task="selectedTask"
      @task-click="openEditTaskDialog"
    />

    <q-space />

    <!-- ACTION BUTTONS -->
    <div class="row q-gutter-x-md">
      <q-btn v-if="!editMode" color="theme-blue" @click="editMode = true">
        {{ $t('edit') }}
      </q-btn>

      <template v-if="editMode">
      <q-btn color="theme-grey" @click="editMode = false">
        {{ $t('cancel') }}
      </q-btn>
      <q-btn color="theme-blue" @click="saveProcessTasks">
        {{ $t('save') }}
      </q-btn>
      <q-space />
      <q-btn round icon="mdi-plus" color="theme-blue" @click="openCreateTaskDialog" />
      </template>
    </div>
  </div>

  <!-- UNIFIED TASK DIALOG (Create/Edit) -->
  <BaseDialog :show="showTaskDialog" @close="cancelTaskDialog">
    <q-card class="surface1 column q-pa-sm" style="min-width: 500px">
      <q-card-section class="row items-center q-pb-none">
        <q-icon v-if="dialogMode === 'edit'" :name="getTaskType(currentTask.task_type_key)?.icon" class="q-mr-md" />
        <div class="text-h3">
          {{ dialogMode === 'create' ? $t('create_task') : currentTask.name }}
        </div>
        <q-space />
        <q-btn icon="mdi-close" flat round dense @click="cancelTaskDialog" />
      </q-card-section>

      <q-card-section class="column q-gutter-y-md">
        <BaseAutocompleteTaskType
          v-model="currentTask.task_type_key"
          :label="$t('task_type')"
          filled
          clearable
          key-only
        />
        <q-input
          v-model="currentTask.task_name"
          :label="$t('name')"
          filled
          clearable
        />
        <q-input
          v-model="currentTask.task_description"
          :label="$t('description')"
          filled
          clearable
          autogrow
        />

        <!-- Phase selectors only for new tasks -->
        <q-select
          v-model="currentTask.after_phase"
          :label="$t('processTasks.after_phase')"
          :options="filteredAfterPhases"
          :disable="filteredAfterPhases.length === 0"
          option-value="_key"
          option-label="alias"
          filled
          emit-value
          map-options
          clearable
        />
        <q-select
          v-model="currentTask.before_phase"
          :label="$t('processTasks.before_phase')"
          :options="filteredBeforePhases"
          :disable="filteredBeforePhases.length === 0"
          option-value="_key"
          option-label="alias"
          filled
          emit-value
          map-options
          clearable
        />
      </q-card-section>

      <q-card-section class="text-right">
        <q-btn class="q-mr-sm" color="theme-grey" @click="cancelTaskDialog">
          {{ $t('cancel') }}
        </q-btn>
        <q-btn color="theme-blue" @click="updateTask">
          {{ dialogMode === 'create' ? $t('create_task') : $t('save') }}
        </q-btn>
      </q-card-section>
    </q-card>
  </BaseDialog>
</template>

<script setup>
import { useQuasar } from 'quasar';
import { computed, ref, reactive } from 'vue';
import { useStore } from 'vuex';
import BaseAutocompleteTaskType from '@/components/BaseAutocompleteTaskType.vue';
import BaseDialog from '@/components/BaseDialog.vue';
import ProcessTasksViewer from '@/components/ProcessTasksViewer.vue';
import { useProcessTasksStore } from '@/stores/processTasks';
import { useTaskTypeStore } from '@/stores/taskType';

const store = useStore();
const processTasksStore = useProcessTasksStore();
const $q = useQuasar();
const taskTypeStore = useTaskTypeStore();

const productData = computed(() => store.state.product.saved);

processTasksStore.fetchProcessTasks(productData.value._key);
const processPhases = computed(() => store.state.process.saved.map((phase, index) => ({
  index,
  _key: phase._key,
  alias: phase.alias,
})));


const currentTask = reactive({});
const setEmptyTaskData = () => {
  Object.assign(currentTask, {
    task_type_key: null,
    task_name: '',
    task_description: '',
    before_phase: null,
    after_phase: null,
  })
}

setEmptyTaskData();

const showTaskDialog = ref(false);
const dialogMode = ref('create'); // 'create' or 'edit'
const editMode = ref(false);
const selectedTask = ref(null);
const editingTaskIndex = ref(-1);
const processTasks = computed(() => processTasksStore.temp);

// Timeline rendering moved to ProcessTimeline component


const filteredBeforePhases = computed(() => processPhases.value.filter((phase) => {
  let afterPhaseIndex = currentTask.after_phase ? processPhases.value.findIndex((p) => p._key === currentTask.after_phase) : null;
  return afterPhaseIndex === null || phase.index > afterPhaseIndex;
}));
const filteredAfterPhases = computed(() => processPhases.value.filter((phase) => {
  let beforePhaseIndex = currentTask.before_phase ? processPhases.value.findIndex((p) => p._key === currentTask.before_phase) : null;
  return beforePhaseIndex === null || phase.index < beforePhaseIndex;
}));

function getTaskType(task_type_key) {
  return taskTypeStore.getTaskTypeByKey(task_type_key);
}

function openCreateTaskDialog() {
  dialogMode.value = 'create';
  setEmptyTaskData();
  showTaskDialog.value = true;
  editingTaskIndex.value = -1;
}

function openEditTaskDialog(task) {
  dialogMode.value = 'edit';
  selectedTask.value = task;
  editingTaskIndex.value = processTasks.value.indexOf(task);

  // Copy task data to currentTask
  Object.assign(currentTask, {
    task_type_key: task.task_type_key,
    task_name: task.task_name,
    task_description: task.task_description,
    before_phase: task.before_phase,
    after_phase: task.after_phase,
  });

  showTaskDialog.value = true;
}

function cancelTaskDialog() {
  showTaskDialog.value = false;
  selectedTask.value = null;
  editingTaskIndex.value = -1;
  setEmptyTaskData();
}

function updateTask() {
  if (dialogMode.value === 'create') {
    // Add new task
    processTasksStore.temp.push({...currentTask});
  } else {
    // Update existing task
    if (editingTaskIndex.value !== -1) {
      Object.assign(processTasks.value[editingTaskIndex.value], {
        task_type_key: currentTask.task_type_key,
        task_name: currentTask.task_name,
        task_description: currentTask.task_description,
        before_phase: currentTask.before_phase,
        after_phase: currentTask.after_phase,
      });
    }
  }

  cancelTaskDialog();
}

async function saveProcessTasks() {
  $q.loading.show();
  await processTasksStore.saveTempProcessTasks(productData.value._key, processTasksStore.temp)
  $q.loading.hide();
  editMode.value = false;
}

// Calculate grid column positions for a task
// Grid columns are: initial-spacer, phase0, spacer0, phase1, spacer1, ..., phaseN, spacerN
// Column indices: 1 (initial-spacer), 2 (phase0), 3 (spacer0), 4 (phase1), 5 (spacer1), etc.
// Timeline calculations handled by ProcessTimeline



</script>

<style lang="scss" scoped>
/* Timeline styles moved to ProcessTimeline component */
</style>
