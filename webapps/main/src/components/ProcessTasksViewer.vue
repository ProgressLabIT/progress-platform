<template>
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
            :key="task._key || `${task.title}-${taskIndex}`"
            class="gantt-task"
            :class="{ 'selected': selectedTask && selectedTask._key === task._key }"
            :style="getTaskGridStyle(task, taskIndex)"
            @click="$emit('taskClick', task)"
          >
            <q-icon :name="task.task_type_icon" class="task-icon" />
            <span class="task-name">{{ task.title }}</span>
          </div>
        </div>
      </div>
    </q-scroll-area>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, nextTick } from 'vue';

const props = defineProps({
  processPhases: {
    type: Array,
    required: true,
  },
  tasks: {
    type: Array,
    required: true,
  },
  selectedTask: {
    type: Object,
    required: false,
    default: null,
  },
});

defineEmits(['taskClick']);

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

// Sorted tasks (each on its own row)
const sortedTasks = computed(() => {
  return [...props.tasks].sort((a, b) => {
    const aStart = getTaskStartColumn(a);
    const bStart = getTaskStartColumn(b);
    if (aStart !== bStart) {
      return aStart - bStart;
    }

    const aEnd = getTaskEndColumn(a);
    const bEnd = getTaskEndColumn(b);
    return aEnd - bEnd;
  });
});

// Grid template columns: phase, spacer, phase, spacer, ..., phase
const ganttGridStyle = computed(() => {
  const numPhases = props.processPhases.length;
  const columns = ['100px'];
  for (let i = 0; i < numPhases; i++) {
    columns.push('50px');
    columns.push('80px');
  }

  return {
    gridTemplateColumns: columns.join(' ')
  };
});

// Calculate grid column positions for a task
// Grid columns are: initial-spacer, phase0, spacer0, phase1, spacer1, ..., phaseN, spacerN
// Column indices: 1 (initial-spacer), 2 (phase0), 3 (spacer0), 4 (phase1), 5 (spacer1), etc.
function getTaskStartColumn(task) {
  const afterIndex = task.after_phase
    ? props.processPhases.findIndex(p => p._key === task.after_phase)
    : -1;

  if (afterIndex === -1) {
    return 1;
  }

  return afterIndex * 2 + 3;
}

function getTaskEndColumn(task) {
  const beforeIndex = task.before_phase
    ? props.processPhases.findIndex(p => p._key === task.before_phase)
    : -1;

  if (beforeIndex === -1) {
    return props.processPhases.length * 2 + 1;
  }

  return beforeIndex * 2 + 1;
}

function getTaskGridStyle(task, taskIndex) {
  const startCol = getTaskStartColumn(task);
  const endCol = getTaskEndColumn(task);
  const rowNum = taskIndex + 2;

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
  grid-auto-rows: 48px;
  align-items: start;
}

.phase-column {
  grid-row: 1 / -1;
  align-self: stretch;
  background: var(--text-high);
  opacity: 0.1;
}

.spacer-column {
  grid-row: 1 / -1;
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


