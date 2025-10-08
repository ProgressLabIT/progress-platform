<template>
    <div
      v-if="activeTask"
      class="task-line-container"
      @mouseenter="onMouseEnter"
      @mouseleave="onMouseLeave"
    >
      <!-- Thin line that thickens in center -->
      <div
        class="task-line"
        :class="{ 'dragging': isDragging }"
        :style="{ left: `${currentLeft}px` }"
      >
        <!-- Center thick section with task code -->
        <div class="task-line-center" @mouseenter="onCenterHover" @mouseleave="onCenterLeave">
          <q-icon
            v-if="activeTask?.icon"
            :name="activeTask.icon"
            size="14px"
            class="task-icon"
          />
          <span
            class="task-code hover-underline"
            @click="router.push({ name: 'taskScreen', params: { taskKey: activeTask?._key } })">
            {{ activeTask?.code || t('task') }}
          </span>
          <!-- Drag handle icon -->
          <q-icon
            v-show="showDragIcon"
            name="mdi-drag"
            size="14px"
            class="drag-icon"
            @mousedown="startDrag"
            @touchstart="startDrag"
          />
          <q-btn
            v-if="showCompleteButton"
            icon="mdi-check"
            flat
            round
            padding="2px"
            size="12px"
            class="owner-icon"
            @click="completeTask"
          />
          <q-btn
            icon="mdi-power"
            flat
            round
            padding="2px"
            size="10px"
            class="dismiss-btn"
            @click="dismissTask"
          />
        </div>
      </div>
    </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { useStore } from 'vuex'
import { useTaskStore } from '@/stores/task.js'

const router = useRouter()


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


// Reactive data
const isExpanded = ref(false)
const showDragIcon = ref(false)

// Drag functionality state
const isDragging = ref(false)
const dragStartX = ref(0)
const dragStartLeft = ref(0)
const currentLeft = ref(0)

// Computed properties
const activeTask = computed(() => taskStore.getActiveTask)
console.log(activeTask.value)

const currentUser = computed(() => store.state.session.user)

const isOwner = computed(() => {
  return activeTask.value?.owner_key === currentUser.value._key
})

const isTaskAdmin = computed(() => {
  return store.getters.hasPermission('task')
})

const showCompleteButton = computed(() => {
  return isTaskAdmin.value || isOwner.value
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

const onCenterHover = () => {
  showDragIcon.value = true
}

const onCenterLeave = () => {
  if (!isDragging.value) {
    showDragIcon.value = false
  }
}

const dismissTask = async () => {
  await taskStore.dismissTaskWithConfirmation(t)
}

const completeTask = async () => {
  if (activeTask.value) {
    await taskStore.completeTaskWithConfirmation(activeTask.value._key, t)
  }
}

// Drag functionality
const startDrag = (event) => {
  // Handle both mouse and touch events
  if (event.type === 'mousedown' && event.button !== 0) {
    return // Only left mouse button
  }

  isDragging.value = true
  const clientX = event.touches ? event.touches[0].clientX : event.clientX
  dragStartX.value = clientX
  dragStartLeft.value = currentLeft.value

  // Add global event listeners for both mouse and touch
  document.addEventListener('mousemove', onDrag)
  document.addEventListener('mouseup', endDrag)
  document.addEventListener('touchmove', onDrag, { passive: false })
  document.addEventListener('touchend', endDrag)

  // Prevent text selection during drag
  event.preventDefault()
}

const onDrag = (event) => {
  if (!isDragging.value) {
    return
  }

  const clientX = event.touches ? event.touches[0].clientX : event.clientX
  const deltaX = clientX - dragStartX.value
  const newLeft = dragStartLeft.value + deltaX

  // Calculate bounds to keep taskbar visible on screen
  const screenWidth = window.innerWidth
  const taskBarWidth = 200 // Approximate width of task bar center
  const minLeft = -screenWidth / 2 + taskBarWidth / 2
  const maxLeft = screenWidth / 2 - taskBarWidth / 2

  // Apply bounds
  currentLeft.value = Math.max(minLeft, Math.min(maxLeft, newLeft))

  // Prevent scrolling on touch devices
  if (event.touches) {
    event.preventDefault()
  }
}

const endDrag = () => {
  isDragging.value = false
  showDragIcon.value = false

  // Save position to localStorage
  localStorage.setItem('taskbar-position', currentLeft.value.toString())

  // Remove global event listeners for both mouse and touch
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', endDrag)
  document.removeEventListener('touchmove', onDrag)
  document.removeEventListener('touchend', endDrag)
}

// Lifecycle hooks
onMounted(() => {
  // Load saved position from localStorage or default to center
  const savedPosition = localStorage.getItem('taskbar-position')
  currentLeft.value = savedPosition ? parseInt(savedPosition) : 0
})

onBeforeUnmount(() => {
  // Clean up event listeners if component unmounts during drag
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', endDrag)
  document.removeEventListener('touchmove', onDrag)
  document.removeEventListener('touchend', endDrag)
})

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
  user-select: none;
  transition: all 0.3s ease;

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

  &.dragging {
    cursor: grabbing;
    transition: none;
    transform: scale(1.01);
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

  .task-line.dragging & {
    transition: none; /* Disable transition during drag for smooth movement */
    box-shadow: 0 6px 16px rgba(0, 0, 0, 0.3);
    transform: translateX(-50%) scale(1.02);
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

.drag-icon {
  color: white;
  opacity: 0.6;
  cursor: grab;
  transition: opacity 0.2s ease;
  padding: 2px;
  border-radius: 4px;

  &:hover {
    opacity: 1;
    background-color: rgba(255, 255, 255, 0.1);
  }

  &:active {
    cursor: grabbing;
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
