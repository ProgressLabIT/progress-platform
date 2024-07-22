<template>
  <q-page-container class="absolute-full">
    <q-page class="row full-height">
      <div class="column col full-height">
        <div class="row col-auto items-center q-pl-xs q-pr-md q-py-sm">
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

          <!-- CREATE NEW WORK ORDER -->
          <template v-if="$route.name === 'workOrderList'">
            <div v-if="!editing" class="col-auto">
              <q-btn
                size="0.75rem"
                color="theme-blue"
                :label="$t('new')"
                @click="$router.push({ name: 'newWorkOrder' })"
              >
              </q-btn>
            </div>

            <template v-else>
              <!-- REORDER WORK ORDER QUEUE -->
              <div class="col-auto">
                <q-btn
                  size="0.7rem"
                  color="theme-orange"
                  :loading="saving"
                  class="q-ml-sm"
                  @click="updateQueue"
                >
                  {{ $t('production.save_new_sequence') }}
                </q-btn>
              </div>

              <!-- CANCEL CHANGES -->
              <div class="col-auto">
                <q-btn
                  size="0.7rem"
                  color="theme-grey"
                  class="q-ml-md"
                  @click="cancelQueueChanges"
                >
                  {{ $t('cancel_changes') }}
                </q-btn>
              </div>
            </template>
          </template>

          <!-- FILTER BUTTON -->
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
          <router-view
            v-if="vuex_ready"
            v-bind="{ filters }"
            @set-search="setSearch($event)"
            @item-dbl-click="showWorkOrderScreen($event)"
            @editing="editing = true"
          />
          <NoDataAlert v-else />
        </div>
      </div>
    </q-page>

    <FilterDrawer
      v-if="$route.name !== 'workOrderArchive'"
      v-model="showFilterDrawer"
      :active-filters="filters_active"
      @reset="resetFilters"
    >
      <!-- FILTERS SPECIFIC TO JOB LIST -->
      <template v-if="$route.name === 'jobList'">
        <!-- BY DEPARTMENT -->
        <q-select
          ref="department_filter"
          v-model="department_selected"
          filled
          dense
          use-input
          clearable
          :options="filtered_departments"
          option-label="name"
          option-value="_key"
          emit-value
          map-options
          :label="$capitalize($t('department', 1))"
          class="q-mb-md"
          popup-content-class="surface1"
          @filter="filterDepartment"
        >
        </q-select>

        <!-- BY OPERATOR -->
        <BaseAutocompleteUser
          :placeholder="$capitalize($t('operator'))"
          dense
          class="q-mb-md"
          key-only
          :value="operator_selected"
          @select="(selection) => (operator_selected = selection)"
        >
        </BaseAutocompleteUser>
      </template>
      <!-- END OF JOB-SPECIFIC FILTERS -->

      <!-- SEARCH BOX -->
      <div class="row items-baseline q-col-gutter-md">
        <q-input
          v-model="search_string"
          filled
          dense
          clearable
          autocomplete="off"
          name="search"
          debounce="300"
          :label="$capitalize($t('search'))"
          class="q-mb-md col"
        >
          <template #append>
            <q-icon name="mdi-information-outline" class="col-auto" size="sm">
              <q-tooltip :delay="300" class="text-body2">
                <span>
                  {{ $capitalize($t('production.search_explainer')) }}:
                </span>
                <ul>
                  <li>{{ $capitalize($t('product.code')) }}</li>
                  <li>{{ $capitalize($t('work_order.long')) }}</li>
                  <li>{{ $capitalize($t('project')) }}</li>
                  <li>{{ $capitalize($t('phase.long')) }}</li>
                </ul>
              </q-tooltip>
            </q-icon>
          </template>
        </q-input>
      </div>

      <!-- DATE START RANGE -->
      <div class="row q-col-gutter-sm">
        <div class="col">
          <q-input
            v-model="start_from_min"
            filled
            dense
            clearable
            debounce="1000"
            mask="date"
            :label="
              $capitalize($t('work_order.list_headers.start_from')) +
              ' (' +
              $t('min') +
              ')'
            "
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
            mask="date"
            debounce="1000"
            :label="
              $capitalize($t('work_order.list_headers.start_from')) +
              ' (' +
              $t('max') +
              ')'
            "
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

      <!-- DUE BY RANGE -->
      <div class="row q-col-gutter-sm q-mt-sm">
        <div class="col">
          <q-input
            v-model="due_by_min"
            filled
            dense
            clearable
            mask="date"
            debounce="1000"
            :label="
              $capitalize($t('work_order.list_headers.due_by')) +
              ' (' +
              $t('min') +
              ')'
            "
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
            mask="date"
            debounce="1000"
            :label="
              $capitalize($t('work_order.list_headers.due_by')) +
              ' (' +
              $t('max') +
              ')'
            "
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

      <!-- BOOLEAN FILTERS -->
      <div class="row q-mt-sm">
        <div v-for="filter in bool_filters" :key="filter" class="col-6">
          <q-checkbox
            v-model="_this[filter]"
            dense
            color="theme-blue"
            size="sm"
            :label="$capitalize($t(`production.filters.${filter}`))"
            class="q-mt-md text-body1 low-text"
          >
          </q-checkbox>
        </div>
        <template v-if="$route.name === 'jobList'">
          <div v-for="filter in job_filters" :key="filter" class="col-6">
            <q-checkbox
              v-model="_this[filter]"
              dense
              color="theme-blue"
              size="sm"
              :label="$capitalize($t(`production.filters.${filter}`))"
              class="q-mt-md text-body1 low-text"
            >
            </q-checkbox>
          </div>
        </template>
      </div>
    </FilterDrawer>
  </q-page-container>
</template>

<script>
import BaseAutocompleteUser from '@/components/BaseAutocompleteUser.vue';
import FilterDrawer from '@/components/FilterDrawer.vue';
import NoDataAlert from '@/components/NoDataAlert.vue';
import multiMatch from '@/lib/MultiFieldSearch.js';
import queryModel from '@/lib/queryModelFactory.js';

const production_views = [
  { component: 'WorkOrderList', route_name: 'workOrderList' },
  { component: 'JobList', route_name: 'jobList' },
  { component: 'WorkOrderArchive', route_name: 'workOrderArchive' },
];

const header_plus_footer_height = 80;

export default {
  name: 'ProductionOverview',

  components: {
    BaseAutocompleteUser,
    NoDataAlert,
    FilterDrawer,
  },

  data() {
    return {
      vuex_ready: false,
      // content_height: 0,
      views: production_views,
      current_view: 0,
      bool_filters: [
        'started',
        'queued',
        'on_time',
        'late',
        'active',
        'idle',
        'ready',
        'not_ready',
        'critical',
        'not_critical',
      ],
      job_filters: ['assigned', 'unassigned'],
      // with_open_issues_only: { label: 'Solo con segnalazioni aperte', value: true },
      department_search_text: undefined,
      editing: false,
      saving: false,
      polling_instance: undefined,
      operator_search_text: undefined,

      showFilterDrawer: false,
    };
  },

  computed: {
    // Filters
    search_string: queryModel(String, 'search', null),
    archive_search: queryModel(String, 'archive_search', null),

    operator_selected: queryModel(String, 'operator', undefined),
    department_selected: queryModel(String, 'department', undefined),

    start_from_min: queryModel(String, 'min_start_from', null),
    start_from_max: queryModel(String, 'max_start_from', null),
    due_by_min: queryModel(String, 'min_due_by', null),
    due_by_max: queryModel(String, 'max_due_by', null),

    started: queryModel(Boolean, 'started', true),
    queued: queryModel(Boolean, 'queued', true),
    on_time: queryModel(Boolean, 'on_time', true),
    late: queryModel(Boolean, 'late', true),
    active: queryModel(Boolean, 'active', true),
    idle: queryModel(Boolean, 'idle', true),
    ready: queryModel(Boolean, 'ready', true),
    not_ready: queryModel(Boolean, 'not_ready', true),
    critical: queryModel(Boolean, 'critical', true),
    not_critical: queryModel(Boolean, 'not_critical', true),
    assigned: queryModel(Boolean, 'assigned', true),
    unassigned: queryModel(Boolean, 'unassigned', true),

    _this() {
      return this;
    },

    filters() {
      let bools = {};
      this.bool_filters.forEach((f) => (bools[f] = this[f]));
      this.job_filters.forEach((f) => (bools[f] = this[f]));

      return {
        search_string: this.search_string,
        archive_search: this.archive_search,
        ...bools,
        department_key: this.department_selected,
        operator_key: this.operator_selected,
        start_from_min: this.start_from_min,
        start_from_max: this.start_from_max,
        due_by_min: this.due_by_min,
        due_by_max: this.due_by_max,
      };
    },

    filters_active() {
      return Object.entries(this.filters).filter(([name, value]) => {
        return [...this.bool_filters, ...this.job_filters].includes(name)
          ? value === false
          : !!value;
      }).length;
    },

    operator_list() {
      return this.$store.getters.operator_list();
    },

    filtered_operators() {
      return this.operator_list.filter((o) =>
        multiMatch(this.operator_search_text, o, ['name', 'surname']),
      );
    },

    department_list() {
      return this.$store.state.org.departments;
    },

    filtered_departments() {
      return this.department_search_text
        ? this.department_list.filter((d) =>
            d.name.toLowerCase().includes(this.department_search_text),
          )
        : this.department_list;
    },
  },

  created() {
    Promise.all([
      this.$store.dispatch('loadWorkOrders'),
      this.$store.dispatch('loadDepartments'),
      this.$store.dispatch('loadUsers'),
      this.$store.dispatch('loadJobAssignments'),
    ]).then((this.vuex_ready = true));

    this.polling_instance = setInterval(() => {
      this.$store.dispatch('updateWorkOrderList');
      this.$store.dispatch('loadJobAssignments');
    }, 60000);
  },

  beforeUnmount() {
    clearInterval(this.polling_instance);
  },

  methods: {
    updateHeight() {
      this.content_height =
        document.documentElement.clientHeight - header_plus_footer_height;
    },

    setSearch(text) {
      this.search_string = text;
    },

    resetFilters() {
      this.$router.replace({ query: null });
    },

    showWorkOrderScreen({ wo_key, back_to_route_name }) {
      const to_route = {
        name: 'workOrderJobs',
        params: {
          wo_key: wo_key,
        },
        query: {
          back_to: back_to_route_name,
          ...this.$route.query,
        },
      };
      this.$router.push(to_route);
    },

    async updateQueue() {
      this.saving = true;
      await this.$store.dispatch('saveQueueChanges');
      this.saving = false;
      this.editing = false;
    },

    cancelQueueChanges() {
      this.$store.commit('RESET_TEMP_QUEUE');
      this.editing = false;
    },

    async filterDepartment(val, update) {
      update(() => {
        this.department_search_text = val.toLowerCase();
      });
    },

    async filterOperator(val, update) {
      update(() => {
        this.operator_search_text = val.toLowerCase();
      });
    },
  },
};
</script>
