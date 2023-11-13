<template>
  <div class="text-h5 q-mt-xl q-mb-md text-uppercase">
    {{ $t('phase.checklist_title') }}
  </div>

  <div>
    <div
      v-for="(check, index) in stepModel.checks"
      :key="index"
      class="q-py-md"
    >
      <div
        v-if="confirmingDeleteIndex !== index"
        class="row q-col-gutter-lg items-center"
        @mouseenter="hoveredRowIndex = index"
        @mouseleave="hoveredRowIndex = null"
      >
        <div class="col-1 text-center low-text">
          <template v-if="editMode">
            <q-icon
              v-if="index > 0"
              :name="`mdi-arrow-up-circle${onUpIndex !== index ? '-outline' : ''}`"
              :color="onUpIndex == index ? 'theme-blue' : undefined"
              size="xs"
              @click="moveUp(index)"
              @mouseenter="onUpIndex = index"
              @mouseleave="onUpIndex = null"
            >
              <q-tooltip>
                Move up
              </q-tooltip>
            </q-icon>

            <q-icon
              v-if="index < stepModel.checks.length - 1"
              :name="`mdi-arrow-down-circle${onDownIndex !== index ? '-outline' : ''}`"
              :color="onDownIndex === index ? 'theme-blue' : undefined"
              size="xs"
              @click="moveDown(index)"
              @mouseenter="onDownIndex = index"
              @mouseleave="onDownIndex = null"
            >
              <q-tooltip>
                Move down
              </q-tooltip>
            </q-icon>
          </template>
          <q-icon
            v-else
            name="mdi-checkbox-blank-outline"
            size="sm"
          />
        </div>

        <div class="col-10">
          <q-input
            v-if="editMode"
            :model-value="check"
            filled
            @update:model-value="(value) => stepModel.checks[index] = value"
          />
          <div v-else>{{ check }}</div>
        </div>

        <div
          v-if="editMode && confirmingDeleteIndex !== index"
          v-show="hoveredRowIndex === index"
          class="col-1 q-ml-auto"
        >
          <BaseTooltipIcon
            icon="mdi-delete"
            :tooltip="$capitalize($t('phase.delete_check'))"
            :color="$theme.red"
            @iconClick="confirmingDeleteIndex = index"
          />
        </div>
      </div>

      <!-- DELETE CONFIRMATION -->
      <q-card
        v-else
        square
        bordered
        class="background shadow-6 q-pa-md"
      >
        <div class="row items-center text-body2 q-gutter-md">
          <span class="highlight">
            {{ check }}
          </span>

          <q-space />

          <span class="q-mr-md">
            {{ $capitalize($t('confirm_question')) }}
          </span>
          <q-btn
            padding="xs sm"
            icon="mdi-delete"
            color="theme-red"
            size="xs"
            @click.stop="stepModel.checks.splice(index, 1)"
          />
          <q-btn
            padding="xs sm"
            icon="mdi-close"
            color="theme-grey"
            size="xs"
            @click.stop="confirmingDeleteIndex = null"
          />
        </div>
      </q-card>
    </div>
  </div>

  <q-btn
    v-if="editMode"
    color="theme-blue"
    size="12px"
    class="q-mt-md"
    @click="stepModel.checks.push('')"
  >
    + {{ $capitalize($t('phase.add_check')) }}
  </q-btn>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useStore } from 'vuex'

import BaseTooltipIcon from '@/components/BaseTooltipIcon.vue'

// TODO: Use defineModel macro to simplify the model related logic (Vue 3.3+)

const props = defineProps({
  step: {
    type: Object,
    required: true
  },
  editMode: {
    type: Boolean,
    required: true
  }
})
const emit = defineEmits(['update:step'])

const stepModel = computed({
  get: () => props.step,
  set(value) {
    emit('update:step', value)
  }
})

const store = useStore()
const $theme = computed(() => store.getters.theme)

const hoveredRowIndex = ref(null)
const confirmingDeleteIndex = ref(null)
const onUpIndex = ref(null)
const onDownIndex = ref(null)

function move(index, delta) {
  const [moved] = stepModel.value.checks.splice(index, 1)
  stepModel.value.checks.splice(index + delta, 0, moved)
}
const moveUp = (index) => move(index, -1)
const moveDown = (index) => move(index, 1)
</script>
