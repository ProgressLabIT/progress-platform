<template>
  <div class="row full-height q-py-md">
    <!-- ASIDE - PHASE LIST -->
    <div class="col-3 column full-height" style="min-width: 400px">
      <div class="q-px-lg">
        <div class="text-h1 display highlight">
          {{ productData.code }}
        </div>
        <div class="text-body1">
          {{ productData.description }}
        </div>
      </div>

      <div class="q-px-lg">
        <q-btn color="theme-blue" @click="showNewTaskDialog = true">
          {{ $t('processTasks.new_task') }}
        </q-btn>
      </div>
    </div>

    <BaseDialog :show="showNewTaskDialog" @close.stop="cancelNewTaskDialog">
      <q-card class="surface1 column">
        <q-card-section class="display text-h3 col-auto">
          {{ $t('create_task') }}
        </q-card-section>
        <q-card-section class="column q-gutter-y-md">
         <BaseAutocompleteTaskType
          v-model="newTask.task_type_key"
          :label="$t('task_type')"
          filled
          clearable
         />
          <q-input
            v-model="newTask.name"
            :label="$t('name')"
            filled
            clearable
          />
          <q-input
            v-model="newTask.description"
            :label="$t('description')"
            filled
            clearable
          />
          <q-select
            v-model="newTask.before_phase"
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
          <q-select
            v-model="newTask.after_phase"
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
        </q-card-section>
        <q-card-section>
          <q-btn color="theme-grey" @click="cancelNewTaskDialog">
            {{ $t('cancel') }}
          </q-btn>
          <q-btn color="theme-blue" @click="createTask">
            {{ $t('create_task') }}
          </q-btn>
        </q-card-section>
      </q-card>
    </BaseDialog>
  </div>
</template>

<script setup>
import { useStore } from 'vuex';
// import { useI18n } from 'vue-i18n';
import { computed, ref, reactive } from 'vue';
import BaseDialog from '@/components/BaseDialog.vue';
import BaseAutocompleteTaskType from '@/components/BaseAutocompleteTaskType.vue';

const store = useStore();
// const { t } = useI18n();

const productData = computed(() => store.state.product.saved);
const processPhases = computed(() => store.state.process.saved.map((phase, index) => ({
  index,
  _key: phase._key,
  alias: phase.alias,
})));

const filteredBeforePhases = computed(() => processPhases.value.filter((phase) => {
  let afterPhaseIndex = newTask.after_phase ? processPhases.value.findIndex((p) => p._key === newTask.after_phase) : null;
  return afterPhaseIndex === null || phase.index > afterPhaseIndex;
}));
const filteredAfterPhases = computed(() => processPhases.value.filter((phase) => {
  let beforePhaseIndex = newTask.before_phase ? processPhases.value.findIndex((p) => p._key === newTask.before_phase) : null;
  return beforePhaseIndex === null || phase.index < beforePhaseIndex;
}));

const showNewTaskDialog = ref(false);
const newTask = reactive({
  task_type_key: '',
  name: '',
  description: '',
  before_phase: null,
  after_phase: null,
});


function cancelNewTaskDialog() {
  showNewTaskDialog.value = false;
}

function createTask() {
  console.log(newTask);
}


</script>

<style lang="scss" scoped>

</style>
