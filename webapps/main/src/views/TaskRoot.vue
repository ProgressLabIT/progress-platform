<template>
  <q-page-container class="absolute-full">
    <q-page class="row full-height">
      <!-- MAIN CONTENT -->
      <div class="column col full-height">
        <div
          class="row col-auto items-center justify-between q-pl-xs q-pr-md q-py-sm"
        >
          <!-- TAB LINKS -->
          <q-tabs
            class="transparent text-low"
            active-class="text-high weight-bold"
            align="left"
            shrink
            dense
            indicator-color="theme-blue"
          >
            <q-route-tab
              v-for="(view, index) in views"
              :key="index"
              :to="{ name: view.route_name, query: $route.query }"
              class="display"
            >
              {{ $t(`views.${view.route_name}`) }}
            </q-route-tab>
          </q-tabs>

          <q-space />

          <!-- NEW TASK BUTTON -->
          <q-btn
            size="0.75rem"
            :label="$t('new')"
            color="theme-blue"
            @click="show_task_form = true"
          >
          </q-btn>

          <!-- CREATE TASK MODAL -->
          <BaseModalForm
            v-if="show_task_form"
            :show="show_task_form"
            :loading="creating"
            :enable-save="isCreateFormValid"
            @submit="handleCreateTask"
            @cancel="cancelCreate"
          >
            <template #title>
              {{ $t('create_task') }}
            </template>

            <template #form>
              <div class="q-gutter-md">
                <BaseAutocompleteTaskType
                  :value="newTask.type"
                  key-only
                  load-data
                  @select="(selection) => newTask.type = selection"
                />

                <q-input
                  v-model="newTask.title"
                  :label="$t('title')"
                  filled
                  :rules="[val => !!val || $t('field_required')]"
                />

                <q-input
                  v-model="newTask.description"
                  :label="$t('description')"
                  autogrow
                  filled
                  rows="3"
                />
              </div>
            </template>
          </BaseModalForm>

          <q-btn
            v-if="!showFilterDrawer && $route.name !== 'workOrderArchive'"
            class="q-ml-sm"
            size="sm"
            round
            :color="filters_active ? 'theme-blue' : 'theme-grey'"
            icon="mdi-filter"
            @click="showFilterDrawer = true"
          >
            <q-badge
              v-if="filters_active"
              floating
              rounded
              color="theme-red"
              :label="filters_active"
              size="4px"
              style="font-family: 'Red Hat Text'; font-size: 8px"
            />
          </q-btn>
        </div>

        <!-- MAIN CONTENT -->
        <div class="col relative-position">
          <router-view/>
        </div>
      </div>
    </q-page>

    <FilterDrawer
      v-model="showFilterDrawer"
      :active-filters="filters_active"
      @reset="resetFilters"
    >
      <div class="q-pa-md text-h5">
        TEST
      </div>
    </FilterDrawer>
  </q-page-container>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import BaseAutocompleteTaskType from '@/components/BaseAutocompleteTaskType.vue';
import BaseModalForm from '@/components/BaseModalForm.vue';
import FilterDrawer from '@/components/FilterDrawer.vue';
import { useTaskStore } from '@/stores/task.js';

const { t: $t } = useI18n();
const taskStore = useTaskStore();

const showFilterDrawer = ref(false);
const filters_active = ref(0);
const views = [{ component: 'TaskOverview', route_name: 'taskOverview' }];

// Task creation state
const show_task_form = ref(false);
const creating = ref(false);
const newTask = ref({
  task_type_key: '',
  title: '',
  description: '',
});

const isCreateFormValid = computed(() => {
  return newTask.value.task_type_key && newTask.value.title;
});

async function handleCreateTask() {
  creating.value = true;
  try {
    await taskStore.createTask(newTask.value);
    show_task_form.value = false;
    resetCreateForm();
  } catch (error) {
    console.error('Error creating task:', error);
  } finally {
    creating.value = false;
  }
}

function cancelCreate() {
  show_task_form.value = false;
  resetCreateForm();
}

function resetCreateForm() {
  newTask.value = {
    type: '',
    title: '',
    description: '',
  };
}

function resetFilters() {
  filters_active.value = 0;
}
</script>
