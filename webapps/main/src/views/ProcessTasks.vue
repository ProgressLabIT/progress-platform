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
    <div ref="ganttContainer" class="col q-my-lg" :style="{ '--gantt-height': containerHeight, '--column-height': columnHeight }">
      <q-scroll-area :style="{ height: containerHeight }">
        <div class="gantt-wrapper" :style="{ border: '1px solid grey', height: containerHeight }">
        <!-- PHASES HEADER -->
        <div class="gantt-header" :style="ganttGridStyle">
          <div class="spacer-label"></div>
          <template v-for="phase in processPhases" :key="phase._key">
            <div class="phase-label">
              <span class="phase-label__content">
                {{ phase.alias }}
              </span>
            </div>
            <div class="spacer-label"></div>
          </template>
        </div>

        <!-- GANTT GRID -->
        <div class="gantt-grid" :style="ganttGridStyle">
          <!-- Background columns -->
          <div class="spacer-column column-height"></div>
          <template v-for="phase in processPhases" :key="`col-${phase._key}`">
            <div class="phase-column column-height"></div>
            <div class="spacer-column"></div>
          </template>

          <!-- Task items -->
          <div
            v-for="(task, taskIndex) in sortedTasks"
            :key="task._key"
            class="gantt-task"
            :class="{ 'selected': selectedTask && selectedTask._key === task._key }"
            :style="getTaskGridStyle(task, taskIndex)"
            @click="openEditTaskDialog(task)"
          >
            <q-icon :name="getTaskType(task.task_type_key)?.icon" class="task-icon" />
            <span class="task-name">{{ task.task_name }}</span>
          </div>
        </div>
      </div>
      </q-scroll-area>
    </div>

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
import { computed, ref, reactive, onMounted, nextTick } from 'vue';
import { useStore } from 'vuex';
import BaseAutocompleteTaskType from '@/components/BaseAutocompleteTaskType.vue';
import BaseDialog from '@/components/BaseDialog.vue';
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

// Get container height
const ganttContainer = ref(null);
const containerHeight = ref('500px');
const columnHeight = ref('452px');

onMounted(() => {
  nextTick(() => {
    if (ganttContainer.value) {
      const height = ganttContainer.value.clientHeight;
      containerHeight.value = `${height}px`;
      columnHeight.value = `${height - 50}px`;
    }
  });
});

// Computed property for sorted tasks (each on its own row)
const sortedTasks = computed(() => {
  return [...processTasks.value].sort((a, b) => {
    const aStart = getTaskStartColumn(a);
    const bStart = getTaskStartColumn(b);
    if (aStart !== bStart) {
      return aStart - bStart;
    }

    // If same start, sort by end column
    const aEnd = getTaskEndColumn(a);
    const bEnd = getTaskEndColumn(b);
    return aEnd - bEnd;
  });
});

// Grid template columns: phase, spacer, phase, spacer, ..., phase
const ganttGridStyle = computed(() => {
  const numPhases = processPhases.value.length;
  const columns = ['100px'];
  for (let i = 0; i < numPhases; i++) {
    columns.push('50px');
    columns.push('80px'); // Spacer between phases
  }

  return {
    gridTemplateColumns: columns.join(' ')
  };
});


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
function getTaskStartColumn(task) {
  const afterIndex = task.after_phase
    ? processPhases.value.findIndex(p => p._key === task.after_phase)
    : -1;

  if (afterIndex === -1) {
    return 1; // Start at initial spacer column
  }

  // Start at the spacer after the after_phase
  // Spacer after phase at index i is at grid column (2i + 3)
  return afterIndex * 2 + 3;
}

function getTaskEndColumn(task) {
  const beforeIndex = task.before_phase
    ? processPhases.value.findIndex(p => p._key === task.before_phase)
    : -1;

  if (beforeIndex === -1) {
    // No before_phase, end at last spacer
    return processPhases.value.length * 2 + 1;
  }

  // End at the spacer before the before_phase
  // Spacer before phase at index i is at grid column (2i + 1)
  return beforeIndex * 2 + 1;
}

function getTaskGridStyle(task, taskIndex) {
  const startCol = getTaskStartColumn(task);
  const endCol = getTaskEndColumn(task);
  const rowNum = taskIndex + 2; // +2 because row 1 is for background columns

  return {
    gridColumn: `${startCol} / ${endCol + 1}`,
    gridRow: rowNum,
    backgroundColor: getTaskType(task.task_type_key)?.color || 'var(--q-primary)',
    borderRadius: '4px',
    padding: '0 8px',
    height: '40px',
    display: 'flex',
    alignItems: 'center',
    cursor: 'pointer',
    zIndex: 10,
    marginBottom: '8px'
  };
}



</script>

<style lang="scss" scoped>
.ganttHeight {
  height: var(--gantt-height);
}

.column-height {
  height: var(--column-height);
}

.gantt-wrapper {
  position: relative;
}

.gantt-header {
  display: grid;
  border-bottom: 2px solid var(--q-separator-color);
  gap: 0;
  height: 48px;
  position: relative;
  z-index: 2;
  margin-left: 16px;
  margin-right: 16px;
}

.phase-label {
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 8px 0;
  text-align: center;
  font-weight: 600;
  border-right: 1px solid var(--q-separator-color);
  overflow: visible;
}

.phase-label__content {
  display: inline-block;
  padding: 0 16px;
  white-space: nowrap;
}

.spacer-label {
  background: var(--q-separator-color);
  opacity: 0.3;
}

.gantt-grid {
  position: absolute;
  left: 16px;
  right: 16px;
  display: grid;
  height: var(--column-height);
  gap: 0;
  grid-auto-rows: 48px; /* Height for each task row */
  align-items: start;
}

.phase-column {
  grid-row: 1 / -1; /* Span all rows */
  align-self: stretch;
  background: var(--text-high);
  opacity: 0.1;
}

.spacer-column {
  grid-row: 1 / -1; /* Span all rows */
  align-self: stretch;
}

.gantt-task {
  transition: all 0.2s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
    z-index: 10;
  }

  &.selected {
    animation: pulse 2s infinite;
    border: 2px dashed var(--q-accent) !important;
  }

  .task-icon {
    margin-right: 8px;
    opacity: 0.8;
  }

  .task-name {
    font-size: 14px;
    font-weight: 500;
    color: white;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
}

.task-description {
  padding: 12px;
  background: var(--q-surface-color);
  border-radius: 4px;
  border-left: 4px solid var(--q-primary);
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}

// Responsive design
@media (max-width: 768px) {
  .gantt-grid {
    font-size: 12px;
  }

  .gantt-task {
    .task-name {
      font-size: 12px;
    }
  }
}
</style>
