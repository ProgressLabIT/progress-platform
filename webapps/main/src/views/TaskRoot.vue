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
          <TaskNew
            :show="show_task_form"
            @created="onTaskCreated"
            @close="show_task_form = false"
          />

          <q-btn
            v-if="!showFilterDrawer && $route.name !== 'workOrderArchive'"
            class="q-ml-sm"
            size="sm"
            round
            :color="activeFiltersCount ? 'theme-blue' : 'theme-grey'"
            icon="mdi-filter"
            @click="showFilterDrawer = true"
          >
            <q-badge
              v-if="activeFiltersCount"
              floating
              rounded
              color="theme-red"
              :label="activeFiltersCount"
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
      :active-filters="activeFiltersCount"
      :min-width="400"
      @reset="resetFilters"
    >
      <!-- STATUS CHECKBOXES -->
      <div class="q-mb-md">
        <div class="text-h5 text-low q-mb-sm">{{ $capitalize($t('status')) }}</div>
        <div class="row q-col-gutter-xs capitalize justify-between">
          <div v-for="statusName in Object.keys(statusFilters)" :key="statusName" class="col-6">
            <q-checkbox
              v-model="statusFilters[statusName].value"
              size="sm"
              dense
            >
              {{ taskStatusOptions[statusName].label }}
              <q-icon :name="taskStatusOptions[statusName].icon" :color="taskStatusOptions[statusName].color" />
            </q-checkbox>
          </div>
        </div>
      </div>

      <!-- TASK TYPE -->
      <BaseAutocompleteTaskType
        dense
        key-only
        class="q-mb-md"
        behavior="menu"
        :value="task_type_key"
        @select="(selection) => (task_type_key = selection)"
      />

      <!-- TEXT SEARCH -->
      <q-input
        v-model="text_search"
        clearable
        filled
        dense
        hide-bottom-space
        autocomplete="off"
        name="search"
        debounce="1000"
        :label="$capitalize($t('search'))"
        class="q-mb-md"
      >
        <template #append>
          <q-icon name="mdi-magnify" />
        </template>
      </q-input>

      <!-- START FROM DATE RANGE -->
      <div class="row q-col-gutter-sm q-mb-md">
        <div class="col">
          <q-input
            v-model="start_from_min"
            filled
            dense
            clearable
            debounce="1000"
            mask="####-##-##"
            :label="$capitalize($t('start_from_min'))"
          >
            <template #append>
              <q-icon name="mdi-calendar" size="xs" class="cursor-pointer">
                <q-popup-proxy
                  cover
                  transition-show="scale"
                  transition-hide="scale"
                >
                  <q-date v-model="start_from_min" minimal>
                    <div class="row items-center justify-end">
                      <q-btn v-close-popup label="Close" color="primary" flat />
                    </div>
                  </q-date>
                </q-popup-proxy>
              </q-icon>
            </template>
          </q-input>
        </div>
        <div class="col">
          <q-input
            v-model="start_from_max"
            filled
            dense
            clearable
            mask="####-##-##"
            debounce="1000"
            :label="$capitalize($t('start_from_max'))"
          >
            <template #append>
              <q-icon name="mdi-calendar" size="xs" class="cursor-pointer">
                <q-popup-proxy
                  cover
                  transition-show="scale"
                  transition-hide="scale"
                >
                  <q-date v-model="start_from_max" minimal>
                    <div class="row items-center justify-end">
                      <q-btn v-close-popup label="Close" color="primary" flat />
                    </div>
                  </q-date>
                </q-popup-proxy>
              </q-icon>
            </template>
          </q-input>
        </div>
      </div>

      <!-- DUE BY DATE RANGE -->
      <div class="row q-col-gutter-sm q-mb-md">
        <div class="col">
          <q-input
            v-model="due_by_min"
            filled
            dense
            clearable
            debounce="1000"
            mask="####-##-##"
            :label="$capitalize($t('due_by_min'))"
          >
            <template #append>
              <q-icon name="mdi-calendar" size="xs" class="cursor-pointer">
                <q-popup-proxy
                  cover
                  transition-show="scale"
                  transition-hide="scale"
                >
                  <q-date v-model="due_by_min" minimal>
                    <div class="row items-center justify-end">
                      <q-btn v-close-popup label="Close" color="primary" flat />
                    </div>
                  </q-date>
                </q-popup-proxy>
              </q-icon>
            </template>
          </q-input>
        </div>
        <div class="col">
          <q-input
            v-model="due_by_max"
            filled
            dense
            clearable
            mask="####-##-##"
            debounce="1000"
            :label="$capitalize($t('due_by_max'))"
          >
            <template #append>
              <q-icon name="mdi-calendar" size="xs" class="cursor-pointer">
                <q-popup-proxy
                  cover
                  transition-show="scale"
                  transition-hide="scale"
                >
                  <q-date v-model="due_by_max" minimal>
                    <div class="row items-center justify-end">
                      <q-btn v-close-popup label="Close" color="primary" flat />
                    </div>
                  </q-date>
                </q-popup-proxy>
              </q-icon>
            </template>
          </q-input>
        </div>
      </div>

      <!-- CREATED DATE RANGE -->
      <div class="row q-col-gutter-sm q-mb-md">
        <div class="col">
          <q-input
            v-model="created_min"
            filled
            dense
            clearable
            debounce="1000"
            mask="####-##-##"
            :label="$t('created_min')"
          >
            <template #append>
              <q-icon name="mdi-calendar" size="xs" class="cursor-pointer">
                <q-popup-proxy
                  cover
                  transition-show="scale"
                  transition-hide="scale"
                >
                  <q-date v-model="created_min" minimal>
                    <div class="row items-center justify-end">
                      <q-btn v-close-popup label="Close" color="primary" flat />
                    </div>
                  </q-date>
                </q-popup-proxy>
              </q-icon>
            </template>
          </q-input>
        </div>
        <div class="col">
          <q-input
            v-model="created_max"
            filled
            dense
            clearable
            mask="####-##-##"
            debounce="1000"
            :label="$t('created_max')"
          >
            <template #append>
              <q-icon name="mdi-calendar" size="xs" class="cursor-pointer">
                <q-popup-proxy
                  cover
                  transition-show="scale"
                  transition-hide="scale"
                >
                  <q-date v-model="created_max" minimal>
                    <div class="row items-center justify-end">
                      <q-btn v-close-popup label="Close" color="primary" flat />
                    </div>
                  </q-date>
                </q-popup-proxy>
              </q-icon>
            </template>
          </q-input>
        </div>
      </div>

      <!-- CLOSED DATE RANGE -->
      <div class="row q-col-gutter-sm q-mb-md">
        <div class="col">
          <q-input
            v-model="closed_min"
            filled
            dense
            clearable
            debounce="1000"
            mask="####-##-##"
            :label="$t('closed_min')"
          >
            <template #append>
              <q-icon name="mdi-calendar" size="xs" class="cursor-pointer">
                <q-popup-proxy
                  cover
                  transition-show="scale"
                  transition-hide="scale"
                >
                  <q-date v-model="closed_min" minimal>
                    <div class="row items-center justify-end">
                      <q-btn v-close-popup label="Close" color="primary" flat />
                    </div>
                  </q-date>
                </q-popup-proxy>
              </q-icon>
            </template>
          </q-input>
        </div>
        <div class="col">
          <q-input
            v-model="closed_max"
            filled
            dense
            clearable
            mask="####-##-##"
            debounce="1000"
            :label="$t('closed_max')"
          >
            <template #append>
              <q-icon name="mdi-calendar" size="xs" class="cursor-pointer">
                <q-popup-proxy
                  cover
                  transition-show="scale"
                  transition-hide="scale"
                >
                  <q-date v-model="closed_max" minimal>
                    <div class="row items-center justify-end">
                      <q-btn v-close-popup label="Close" color="primary" flat />
                    </div>
                  </q-date>
                </q-popup-proxy>
              </q-icon>
            </template>
          </q-input>
        </div>
      </div>

      <!-- OWNER -->
      <BaseAutocompleteUser
        :placeholder="$capitalize($t('owner'))"
        dense
        class="q-mb-md"
        behavior="menu"
        key-only
        :label="$capitalize($t('owner'))"
        :operator-only="false"
        :value="owner_key"
        @select="(selection) => (owner_key = selection)"
      />

      <!-- PARTICIPANTS -->
      <BaseAutocompleteUser
        :placeholder="$capitalize($t('participants'))"
        dense
        class="q-mb-md"
        behavior="menu"
        key-only
        :label="$capitalize($t('participants'))"
        :operator-only="false"
        :value="assigned_to"
        @select="(selection) => (assigned_to = selection)"
      />

      <!-- LINK FILTERS -->
      <div class="text-h5 text-low q-mb-sm">{{ $t('links') }}</div>

      <BaseAutocompleteIssue
        dense
        key-only
        class="q-mb-md"
        :label="$t('issue')"
        :value="issue_key"
        @select="(selection) => (issue_key = selection)"
      />

      <BaseAutocompleteWorkOrder
        dense
        key-only
        class="q-mb-md"
        hint=""
        :label="$t('work_order.long')"
        :value="work_order_key"
        @select="(selection) => (work_order_key = selection)"
      />

      <BaseAutocompleteProduct
        :load-data="false"
        dense
        key-only
        class="q-mb-md"
        :label="$t('product.label')"
        :value="product_key"
        @select="(selection) => (product_key = selection)"
      />

      <BaseAutocompleteSerial
        dense
        key-only
        class="q-mb-md"
        :label="$t('serial')"
        :value="serial_key"
        @select="(selection) => (serial_key = selection)"
      />

      <BaseAutocompleteTask
        dense
        key-only
        class="q-mb-md"
        :label="$t('task')"
        :value="linked_task_key"
        @select="(selection) => (linked_task_key = selection)"
      />
    </FilterDrawer>
  </q-page-container>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter, useRoute } from 'vue-router';
import BaseAutocompleteTaskType from '@/components/BaseAutocompleteTaskType.vue';
import BaseAutocompleteIssue from '@/components/BaseAutocompleteIssue.vue';
import BaseAutocompleteWorkOrder from '@/components/BaseAutocompleteWorkOrder.vue';
import BaseAutocompleteProduct from '@/components/BaseAutocompleteProduct.vue';
import BaseAutocompleteSerial from '@/components/BaseAutocompleteSerial.vue';
import BaseAutocompleteTask from '@/components/BaseAutocompleteTask.vue';
import BaseAutocompleteUser from '@/components/BaseAutocompleteUser.vue';
import FilterDrawer from '@/components/FilterDrawer.vue';
import TaskNew from '@/components/TaskNew.vue';
import { useTask } from '@/composables/task.js';
import { useQueryModel } from '@/lib/queryModelFactory.js';
import { useTaskStore } from '@/stores/task.js';

const { t: $t } = useI18n();
const router = useRouter();
const route = useRoute();
const taskStore = useTaskStore();
const { taskStatusOptions } = useTask();

const showFilterDrawer = ref(false);
const views = [{ component: 'TaskOverview', route_name: 'taskOverview' }];

// Task creation state
const show_task_form = ref(false);

// Filter query models

const start_from_min = useQueryModel(String, 'start_from_min', null);
const start_from_max = useQueryModel(String, 'start_from_max', null);
const due_by_min = useQueryModel(String, 'due_by_min', null);
const due_by_max = useQueryModel(String, 'due_by_max', null);
const created_min = useQueryModel(String, 'created_min', null);
const created_max = useQueryModel(String, 'created_max', null);
const closed_min = useQueryModel(String, 'closed_min', null);
const closed_max = useQueryModel(String, 'closed_max', null);
const task_type_key = useQueryModel(String, 'task_type_key', null);
const text_search = useQueryModel(String, 'search', null);
const owner_key = useQueryModel(String, 'owner_key', null);
const assigned_to = useQueryModel(String, 'assigned_to', null);
const issue_key = useQueryModel(String, 'issue_key', null);
const work_order_key = useQueryModel(String, 'work_order_key', null);
const product_key = useQueryModel(String, 'product_key', null);
const serial_key = useQueryModel(String, 'serial_key', null);
const linked_task_key = useQueryModel(String, 'linked_task_key', null);


const statusFilters = {
  pending: useQueryModel(Boolean, 'status_pending', true),
  open: useQueryModel(Boolean, 'status_open', true),
  completed: useQueryModel(Boolean, 'status_completed', true),
  canceled: useQueryModel(Boolean, 'status_canceled', true),
}

const filters = {
  ...statusFilters,
  start_from_min,
  start_from_max,
  due_by_min,
  due_by_max,
  created_min,
  created_max,
  closed_min,
  closed_max,
  task_type_key,
  text_search,
  owner_key,
  assigned_to,
  issue_key,
  work_order_key,
  product_key,
  serial_key,
  linked_task_key,
}
// Computed filters object and active filter count
const activeFiltersCount = computed(() => {
  return Object.values(filters).filter((f) => {
    return [null, undefined, '', true].includes(f.value ?? undefined) ? false : true;
  }).length
})

function onTaskCreated() {
  show_task_form.value = false;
  taskStore.fetchTasks();
}

async function resetFilters() {
  await router.replace({ query: null });
}

// Watch filters and fetch tasks when they change
watch(() => route.query, () => {
  taskStore.fetchTasks(route.query);
}, { deep: true });

// Initial load of tasks
taskStore.fetchTasks(route.query);
</script>
