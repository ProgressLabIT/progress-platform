<template>
    <div
      v-if="activeTask"
      class="task-line-container"
      @mouseenter="onMouseEnter"
      @mouseleave="onMouseLeave"
    >
      <!-- Thin line that thickens in center -->
      <div class="task-line">
        <!-- Center thick section with task code -->
        <div class="task-line-center">
          <q-icon
            v-if="activeTask?.icon"
            :name="activeTask.icon"
            size="14px"
            class="task-icon"
          />
          <span class="task-code">{{ activeTask?.code || t('task') }}</span>
          <q-btn
            v-if="isOwner"
            icon="mdi-check"
            flat
            round
            padding="2px"
            size="12px"
            class="owner-icon"
            @click="completeTask"
          />
          <q-btn
            icon="mdi-close"
            flat
            round
            padding="2px"
            size="12px"
            class="dismiss-btn"
            @click="dismissTask"
          />
        </div>
      </div>
    </div>
</template>

<script setup>
import { useQuasar } from 'quasar'
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useStore } from 'vuex'
import { useTaskStore } from '@/stores/task.js'


// const props = defineProps({
//   minimal: {
//     type: Boolean,
//     default: false,
//   },
// })


// Stores
const taskStore = useTaskStore()
const store = useStore()
const { t } = useI18n()
const $q = useQuasar()

// Reactive data
const isExpanded = ref(false)

// Computed properties
const activeTask = computed(() => taskStore.getActiveTask)
console.log(activeTask.value)

const currentUser = computed(() => store.state.session.user)

const isOwner = computed(() => {
  return activeTask.value?.owner_key === currentUser.value._key
})


const onMouseEnter = () => {
  if (!isExpanded.value) {
    isExpanded.value = true
  }
}

const onMouseLeave = () => {
  if (isExpanded.value) {
    isExpanded.value = false
  }
}

const dismissTask = () => {
  // Clear the active task
  $q.dialog({
    title: 'Dismiss Task',
    message: 'Are you sure you want to dismiss this task? You will no longer see it in your active tasks.',
    color: 'theme-orange',
    confirm: 'Dismiss',
    cancel: 'Cancel',
  }).onOk(() => {
      taskStore.activeTaskKey = null
  })
}


const completeTask = () => {
  $q.dialog({
    title: 'Complete Task',
    message: 'Are you sure you want to complete this task?',
    color: 'theme-green',
    confirm: 'Complete',
    cancel: 'Cancel',
  }).onOk(() => {
    taskStore.completeTask(activeTask.value._key)
  })
}

// Add body class when TaskBar is mounted
onMounted(() => {
  if (activeTask.value) {
    document.body.classList.add('has-task-bar')
  }
})

// Watch for activeTask changes to manage body class and cleanup
// watch(activeTask, (newTask, oldTask) => {
//   if (newTask && !oldTask) {
//     // TaskBar is being added
//     document.body.classList.add('has-task-bar')
//   } else if (!newTask && oldTask) {
//     // TaskBar is being removed
//     document.body.classList.remove('has-task-bar')
//     document.body.classList.remove('task-bar-expanded')
//     isExpanded.value = false
//   }
// }, { immediate: true })

</script>

<style lang="scss" scoped>
.task-line-container {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  width: 100%;
  height: 40px;
  z-index: 9999;
  pointer-events: none; /* Allow clicks to pass through */
}

.task-line {
  position: relative;
  width: 100%;
  height: 3px;
  background: linear-gradient(to right,
    transparent 0%,
    var(--theme-blue) 20%,
    var(--theme-blue) 80%,
    transparent 100%);

  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 50%;
    transform: translateX(-50%);
    width: 200px;
    height: 3px;
    background: var(--theme-blue);
    border-radius: 0 0 20px 20px;
    z-index: 1;
  }
}

.task-line-center {
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--theme-blue);
  color: white;
  padding: 0px 16px;
  border-radius: 0 0 20px 20px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  z-index: 2;
  pointer-events: auto; /* Re-enable interactions for this section */

  &:hover {
    padding: 10px 20px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
  }
}

.task-code {
  white-space: nowrap;
  min-width: max-content;
}

.task-icon {
  opacity: 0.9;
}

.owner-icon {
  opacity: 0.8;
  color: gold;
}

.dismiss-btn {
  color: white;
  opacity: 0.8;
  transition: opacity 0.2s ease;

  &:hover {
    opacity: 1;
    background-color: rgba(255, 255, 255, 0.1);
  }
}

.task-bar-wrapper {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  width: 100%;
  z-index: 9999;
  pointer-events: auto;
}

.task-bar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  width: 100%;
  z-index: 9999;
  pointer-events: auto;
  transition: all 0.3s ease-out;
}

.task-bar-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: -1;
}

.task-bar-content {
  position: relative;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  transition: all 0.3s ease-out;
}

.compact-view {
  min-height: 48px;
  transition: all 0.3s ease-out;
}

.expanded-view {
  min-height: 200px;
  transition: all 0.3s ease-out;
}

.task-info {
  max-width: 60%;
}

.opacity-90 {
  opacity: 0.9;
}

.opacity-75 {
  opacity: 0.75;
}

// Slide down animation
.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.3s ease-out;
  overflow: hidden;
}

.slide-down-enter-from {
  max-height: 0;
  opacity: 0;
  transform: translateY(-10px);
}

.slide-down-enter-to,
.slide-down-leave-from {
  max-height: 80px; /* Adjusted for q-bar height */
  opacity: 1;
  transform: translateY(0);
}

.slide-down-leave-to {
  max-height: 0;
  opacity: 0;
  transform: translateY(-10px);
}

/* Global styles for body when TaskBar is active */
// :global(body.has-task-bar) {
//   padding-top: 40px !important;
//   transition: padding-top 0.3s ease;
// }

// :global(body.has-task-bar .q-layout) {
//   padding-top: 0 !important;
// }
</style>
