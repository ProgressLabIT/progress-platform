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
            <template v-if="!editing">
              <div class="col-auto">
                <q-btn
                  size="0.75rem"
                  color="theme-blue"
                  class="q-ml-sm"
                  :label="$t('new')"
                  @click="$router.push({ name: 'newWorkOrder' })"
                >
                </q-btn>
              </div>
              <div class="col-auto">
                <q-btn
                  size="0.75rem"
                  color="theme-blue"
                  class="q-ml-sm"
                  @click="sortTableByStartDateDueDate"
                >
                  {{ $t('production.sort_by_date') }}
                </q-btn>
              </div>
            </template>
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
              <q-tooltip :delay="Number(300)" class="text-body2">
                <span>
                  {{ $capitalize($t('production.search_explainer')) }}:
                </span>
                <ul>
                  <li>{{ $capitalize($t('project')) }}</li>
                </ul>
              </q-tooltip>
            </q-icon>
          </template>
        </q-input>
      </div>

      <!-- FILTERS SPECIFIC TO JOB LIST -->
      <template v-if="$route.name === 'jobList'">
        <!-- BY CODE -->
        <q-select
          ref="code_filter"
          v-model="code_selected"
          filled
          dense
          use-input
          clearable
          :options="filtered_codes"
          option-label="name"
          option-value="_key"
          emit-value
          map-options
          :label="$capitalize($t('work_order.long', 1))"
          class="q-mb-md"
          popup-content-class="surface1"
          @filter="filterCode"
        >
        </q-select>

        <!-- BY PRODUCT -->
        <q-select
          ref="product_filter"
          v-model="product_selected"
          filled
          dense
          use-input
          clearable
          :options="filtered_products"
          option-label="name"
          option-value="_key"
          emit-value
          map-options
          :label="$capitalize($t('product.label', 1))"
          class="q-mb-md"
          popup-content-class="surface1"
          @filter="filterProduct"
        >
        </q-select>

        <!-- BY PHASE -->
        <q-select
          ref="phase_filter"
          v-model="phase_selected"
          filled
          dense
          use-input
          clearable
          :options="filtered_phases"
          option-label="name"
          option-value="_key"
          emit-value
          map-options
          :label="$capitalize($t('phase.phase', 1))"
          class="q-mb-md"
          popup-content-class="surface1"
          @filter="filterPhase"
        >
        </q-select>

        <!-- BY DEPARTMENT -->
        <!-- <q-select
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
        </q-select> -->

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
import { useSSE } from '@/composables/useSSE';

const production_views = [
  { component: 'WorkOrderList', route_name: 'workOrderList' },
  { component: 'JobList', route_name: 'jobList' },
  { component: 'WorkOrderArchive', route_name: 'workOrderArchive' },
];

const header_plus_footer_height = 80;

export default {
  name: 'ProductionOverview',

  setup() {
    const { subscribe } = useSSE('production');
    return { subscribeSSE: subscribe };
  },

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
      phase_search_text: undefined,
      code_search_text: undefined,
      product_search_text: undefined,
      editing: false,
      saving: false,
      //polling_instance: undefined,
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

    code_selected: queryModel(String, 'wo', undefined),
    product_selected: queryModel(String, 'product', undefined),
    phase_selected: queryModel(String, 'phase_alias', undefined),

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
        wo_key: this.code_selected,
        phase_alias: this.phase_selected,
        product_key: this.product_selected,
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

    product_list() {
      return this.$store.state.org.wo_open_proucts;
    },

    code_list() {
      return this.$store.state.org.wo_open_codes;
    },

    phase_list() {
      return this.$store.state.org.wo_open_phases;
    },

    filtered_departments() {
      return this.department_search_text
        ? this.department_list.filter((d) =>
            d.name.toLowerCase().includes(this.department_search_text),
          )
        : this.department_list;
    },

    filtered_codes() {
      return this.code_search_text
        ? this.code_list.filter((d) =>
            d.name.toLowerCase().includes(this.code_search_text),
          )
        : this.code_list;
    },

    filtered_products() {
      return this.product_search_text
        ? this.product_list.filter((d) =>
            d.name.toLowerCase().includes(this.product_search_text),
          )
        : this.product_list;
    },

    filtered_phases() {
      return this.phase_search_text
        ? this.phase_list.filter((d) =>
            d.name.toLowerCase().includes(this.phase_search_text),
          )
        : this.phase_list;
    },
  },

  created() {
    Promise.all([
      this.$store.dispatch('loadWorkOrders'),
      this.$store.dispatch('loadDepartments'),
      this.$store.dispatch('loadUsers'),
      this.$store.dispatch('loadJobAssignments'),
      this.$store.dispatch('loadWorkOrderSearchOptions'),
    ]).then((this.vuex_ready = true));

    //this.polling_instance = setInterval(() => {
    //  this.$store.dispatch('updateWorkOrderList');
    //  this.$store.dispatch('loadJobAssignments');
    //}, 10000);
  },

  mounted() {
    this.subscribeSSE((event) => {
      this.handleMessage(event);
    });
  },

  methods: {
    handleMessage(message) {
      let event = JSON.parse(message.data);
      const type = event.event_type || event.notification;

      if (type === 'QUEUE_UPDATED') {
        this.$store.dispatch('loadWorkOrders');
        this.$store.dispatch('loadJobAssignments');
        return;
      }

      if (event.wo_data) {
        this.$store.commit('UPDATE_SINGLE_WO', event.wo_data);
        this.debouncedLoadAssignments();
      }
    },

    debouncedLoadAssignments: (() => {
      let timer = null;
      return function () {
        clearTimeout(timer);
        timer = setTimeout(() => {
          this.$store.dispatch('loadJobAssignments');
        }, 5000);
      };
    })(),

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

    async sortTableByStartDateDueDate() {
      this.editing = true;
      this.$store.commit('SORT_TEMP_QUEUE_BY_START_DATE_DUE_DATE');
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

    async filterProduct(val, update) {
      update(() => {
        this.product_search_text = val.toLowerCase();
      });
    },

    async filterPhase(val, update) {
      update(() => {
        this.phase_search_text = val.toLowerCase();
      });
    },

    async filterCode(val, update) {
      update(() => {
        this.code_search_text = val.toLowerCase();
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
