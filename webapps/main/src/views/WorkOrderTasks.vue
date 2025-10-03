<template>
  <div class="column full-height q-pa-md">
    <ProcessTasksViewer
      :process-phases="processPhases"
      :tasks="processTasks"
      :selected-task="null"
      @task-click="noop"
    />
  </div>
  </template>

<script setup>
import { computed } from 'vue'
import ProcessTasksViewer from '@/components/ProcessTasksViewer.vue'

const props = defineProps({
  wo_data: {
    type: Object,
    required: true,
  },
})

const processPhases = computed(() => {
  const sequence = props.wo_data.phase_sequence || []
  const phaseMap = new Map()

  ;(props.wo_data.jobs || []).forEach((job) => {
    if (!phaseMap.has(job.phase_key)) {
      phaseMap.set(job.phase_key, { _key: job.phase_key, alias: job.phase_alias })
    }
  })

  if (sequence.length) {
    return sequence
      .filter((pk) => phaseMap.has(pk))
      .map((pk) => phaseMap.get(pk))
  }

  return Array.from(phaseMap.values())
})

const processTasks = computed(() => props.wo_data.tasks || [])

function noop() {}
</script>


