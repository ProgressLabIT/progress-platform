<template>
  <LoadingSignal v-if="loading" />

  <div v-else class="row full-height">
    <div class="full-height column col-3">
      <q-input
        v-model="search_text"
        dense
        filled
        class="q-px-md q-pt-md"
        :placeholder="$capitalize($t('search'))"
      >
        <template #append>
          <q-icon name="mdi-magnify" />
        </template>
      </q-input>

      <div
        class="row q-mt-md q-px-lg q-py-sm text-h6 text-uppercase weight-bold"
      >
        <div class="col-4">
          {{ $t('name') }}
        </div>
        <div class="col">
          {{ $t('description') }}
        </div>
        <div class="col-2 text-right">
          {{ $t('active') }}
        </div>
      </div>

      <q-separator />

      <!-- TASK TYPE LIST -->
      <div class="scroll col">
        <div
          v-for="(task_type, index) in filtered_task_types"
          :key="index"
          class="row pointer q-px-lg q-py-xs medium full-width"
          :class="{
            'alternate-row': index % 2 === 0,
            'bg-blue-backdrop': task_type._key === selected_task_type_key,
          }"
          style="white-space: nowrap"
          @click="showTaskTypeDetail(task_type._key)"
        >
          <div class="col-4">
            {{ $capitalize(task_type.name || '') }}
          </div>
          <div class="col-6 ellipsis">
            {{ task_type.description || '-' }}
          </div>
          <div class="col-2 text-right">
            <q-icon :name="task_type.active ? 'mdi-check' : 'mdi-close'" />
          </div>
        </div>
      </div>

      <q-separator />

      <!-- TASK TYPE LIST COUNT -->
      <div class="row flex-center smaller q-py-xs">
        {{ filtered_task_types.length }} {{ $t('of') }}
        {{ task_type_list.length }}
      </div>

      <div class="q-pa-md q-mt-auto">
        <q-btn
          class="full-width q-mt-auto"
          color="theme-blue"
          :label="$t('new')"
          @click="showNewDialog = true"
        >
        </q-btn>
      </div>
    </div>

    <q-separator vertical />

    <!-- TASK TYPE DATA -->
    <div v-if="!loading" class="col full-height">
      <router-view v-slot="{ Component }">
        <component :is="Component" :task-type="selected_task_type" />
      </router-view>
    </div>
  </div>

  <!-- NEW TASK TYPE DIALOG -->
  <TaskTypeNew
    v-if="showNewDialog"
    @close="showNewDialog = false"
    @created="onTaskTypeCreated"
  />
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import LoadingSignal from '@/components/LoadingSignal.vue'
import multiMatch from '@/lib/MultiFieldSearch.js'
import { useTaskTypeStore } from '@/stores/taskType'
import TaskTypeNew from './TaskTypeNew.vue'

const route = useRoute()
const router = useRouter()
const taskTypeStore = useTaskTypeStore()

const loading = ref(true)
const search_text = ref('')
const showNewDialog = ref(false)

const task_type_list = computed(() => {
  const task_types = [...taskTypeStore.taskTypes]
  task_types.sort((a, b) =>
    a.name > b.name ? 1 : a.name < b.name ? -1 : 0,
  )
  return task_types
})

const selected_task_type_key = computed(() => {
  return route.params.taskTypeKey
})

const selected_task_type = computed(() => {
  return task_type_list.value.find(
    (tt) => tt._key == selected_task_type_key.value,
  )
})

const filtered_task_types = computed(() => {
  const fields_to_search = ['name', 'description']
  return task_type_list.value.filter((tt) =>
    multiMatch(search_text.value, tt, fields_to_search),
  )
})

const showTaskTypeDetail = (taskTypeKey) => {
  router.push({
    name: 'taskTypeDetail',
    params: { taskTypeKey },
  })
}

const onTaskTypeCreated = (taskType) => {
  showNewDialog.value = false
  router.push({
    name: 'taskTypeDetail',
    params: { taskTypeKey: taskType._key },
  })
}

onMounted(async () => {
  await taskTypeStore.fetchTaskTypes()
  loading.value = false
})
</script>
