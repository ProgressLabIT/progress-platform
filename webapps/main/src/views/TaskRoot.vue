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

          <IssueForm
            :show="show_issue_form"
            mode="new"
            with_links
            @cancel="show_issue_form = false"
            @issue-created="getIssues"
          >
          </IssueForm>

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
import { ref } from 'vue';
// import { useStore } from 'vuex';
import FilterDrawer from '@/components/FilterDrawer.vue';
// import queryModel, { useQueryModel } from '@/lib/queryModelFactory.js';

// const store = useStore();

const showFilterDrawer = ref(false);

const filters_active = ref(0);

const views = [{ component: 'TaskOverview', route_name: 'taskOverview' }];

</script>
