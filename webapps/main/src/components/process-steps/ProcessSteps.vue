<template>
  <q-splitter class="full-height q-py-sm" :model-value="30">
    <template #before>
      <!-- STEP LIST -->
      <div class="col-4 column fit">
        <div class="text-h5 text-uppercase q-px-lg q-my-md col-auto">
          {{ $t('step_sequence') }}
        </div>
        <div v-if="hasSteps" class="col-9 scroll">
          <q-list id="steps" dense>
            <q-item
              v-for="(step, index) in stepsModel"
              :key="step._key"
              v-ripple
              clickable
              :class="[
                !editMode ? 'undraggable' : '',
                currentStepIndex === index ? 'highlight' : 'low-text',
              ]"
              @click="handleStepClick(index)"
            >
              <q-item-section avatar class="col-auto">
                <q-avatar
                  size="20px"
                  :color="
                    currentStepIndex === index ? 'theme-blue' : 'theme-grey'
                  "
                  class="smaller text-high q-ml-sm"
                >
                  {{ index + 1 }}
                </q-avatar>
              </q-item-section>

              <q-item-section class="ellipsis">
                <q-item-label>
                  {{ step.title ? step.title : '(nessun titolo)' }}
                </q-item-label>
              </q-item-section>

              <q-item-section side class="q-mr-sm">
                <q-icon
                  :name="stepTypeToIconMap[step.type]"
                  size="sm"
                  class="q-ml-auto"
                  :color="
                    currentStepIndex === index
                      ? $theme.text_high
                      : $theme.text_low
                  "
                />
              </q-item-section>
            </q-item>
          </q-list>
        </div>

        <!-- NO STEPS -->
        <div v-else class="column q-mt-xl items-center">
          <q-icon
            name="mdi-alert-circle-outline"
            class="text-low q-mb-md"
            size="xl"
          />
          <div class="text-h3 uppercase">
            {{ $t('phase.no_procedure') }}
          </div>
          <div class="text-body1">
            {{ $capitalize($t('phase.add_steps')) }}
          </div>
        </div>

        <!-- ADD STEPS -->
        <div v-if="editMode" class="col-auto q-mt-auto q-mb-sm q-pl-sm q-pr-lg">
          <q-btn
            v-for="stepType in stepTypes"
            :key="stepType"
            flat
            style="width: 105%"
            size="12px"
            align="between"
            @click="addStep(stepType)"
          >
            <span
              >+ {{ $t('add') }} {{ $t(`phase.step_types.${stepType}`) }}</span
            >
            <q-icon :name="stepTypeToIconMap[stepType]" />
          </q-btn>
        </div>
      </div>
    </template>

    <!-- STEP DETAILS -->
    <template #after>
      <div v-if="hasSteps" class="q-pa-md q-mx-md">
        <!-- STEP TITLE -->
        <div class="text-h5 uppercase q-mb-md">
          {{ $t('title') }}
        </div>
        <q-input
          v-if="editMode"
          v-model="stepsModel[currentStepIndex].title"
          filled
          dense
          name="step_title"
          :placeholder="$t('title')"
          debounce="200"
        />
        <div v-else class="q-mb-lg q-mt-md">
          {{ stepsModel[currentStepIndex].title }}
        </div>

        <!-- STEP DESCRIPTION -->
        <div class="text-h5 uppercase q-mt-lg q-mb-md">
          {{ $t('description') }}
        </div>
        <q-input
          v-if="editMode"
          v-model="stepsModel[currentStepIndex].description"
          filled
          dense
          type="textarea"
          name="step_desc"
          debounce="200"
          :placeholder="$t('description')"
        />
        <div v-else class="q-mt-md">
          {{ stepsModel[currentStepIndex].description }}
        </div>

        <component
          :is="activeStepComponent"
          v-model:step="stepsModel[currentStepIndex]"
          :edit-mode="editMode"
        />

        <!-- DELETE SECTION -->
        <div v-if="editMode" class="q-mb-md q-mt-xl">
          <template v-if="!isConfirmingDelete">
            <q-btn
              size="12px"
              icon="mdi-delete"
              color="theme-red"
              :label="$t('delete')"
              @click="isConfirmingDelete = true"
            />
          </template>
          <q-card v-else square class="bg-red-backdrop shadow-6 q-pa-md">
            <div class="row q-gutter-md flex-center">
              <span class="display medium highlight weight-bold">
                {{ $t('confirm_question') }}
              </span>

              <q-btn
                fab
                padding="sm"
                color="theme-grey"
                icon="mdi-close"
                @click="isConfirmingDelete = false"
              />

              <q-btn
                fab
                padding="sm"
                color="theme-red"
                icon="mdi-delete"
                @click="deleteStep(currentStepIndex)"
              />
            </div>
          </q-card>
        </div>
        <!-- END OF DELETE SECTION -->
      </div>
    </template>
  </q-splitter>
</template>

<script setup>
import Sortable from 'sortablejs';
import { computed, onMounted, ref, watch } from 'vue';
import { useStore } from 'vuex';

import StepForm from './StepForm.vue';
import StepInstruction from './StepInstruction.vue';

const props = defineProps({
  editMode: {
    type: Boolean,
    required: true,
  },
});

const stepsModel = defineModel({ type: Array });

const store = useStore();
const $theme = computed(() => store.getters.theme);

const stepTypes = ['instruction', 'form'];
const stepTypeToIconMap = {
  instruction: 'mdi-playlist-check',
  form: 'mdi-playlist-edit',
};
const isConfirmingDelete = ref(false);

watch(
  () => props.editMode,
  (editMode) => {
    isConfirmingDelete.value = false;
    if (editMode) {
      initSortable();
    }
  },
);
onMounted(() => {
  initSortable();
});
function initSortable() {
  const container = document.querySelector('#steps');
  if (!container) {
    return;
  }

  Sortable.create(container, {
    ...store.state.drag_options,
    filter: '.undraggable',
    onEnd: ({ newIndex, oldIndex }) => {
      const [moved] = stepsModel.value.splice(oldIndex, 1);
      stepsModel.value.splice(newIndex, 0, moved);

      // Preserve the current step index at the same step
      if (currentStepIndex.value === oldIndex) {
        currentStepIndex.value = newIndex;
      } else if (
        oldIndex < currentStepIndex.value &&
        newIndex >= currentStepIndex.value
      ) {
        currentStepIndex.value--;
      } else if (
        oldIndex > currentStepIndex.value &&
        newIndex <= currentStepIndex.value
      ) {
        currentStepIndex.value++;
      }
    },
  });
}

const hasSteps = computed(
  () => stepsModel.value !== null && stepsModel.value.length > 0,
);
const currentStepIndex = ref(0);
// Make sure the current step index is always within the bounds
watch(stepsModel, (steps) => {
  if (steps.length === 0) {
    currentStepIndex.value = 0;
  } else if (currentStepIndex.value >= steps.length) {
    currentStepIndex.value = steps.length - 1;
  }
});

function handleStepClick(index) {
  currentStepIndex.value = index;
  isConfirmingDelete.value = false;
}

function addStep(type) {
  stepsModel.value.push({
    type,
    title: '',
    description: '',
    media: [],
    form_fields: [],
    print_templates: [],
  });
  currentStepIndex.value = stepsModel.value.length - 1;
}

const stepTypeToComponentMap = {
  instruction: StepInstruction,
  form: StepForm,
};
const activeStepComponent = computed(() => {
  const currentStep = stepsModel.value[currentStepIndex.value];

  return stepTypeToComponentMap[currentStep.type];
});

function deleteStep(stepIndex) {
  // If deleting the last step, move the current step index back by one
  if (stepIndex === stepsModel.value.length - 1) {
    currentStepIndex.value =
      stepsModel.value.length > 1 ? stepsModel.value.length - 2 : 0;
  }

  stepsModel.value.splice(stepIndex, 1);
  isConfirmingDelete.value = false;
}
</script>
