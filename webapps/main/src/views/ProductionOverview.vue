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
            indicator-color="theme-blue">
            <q-route-tab
              v-for="(view, index) in views"
              :key="index"
              :to="{ name: view.route_name, query: $route.query }"
              class="display">
              {{ $t(`views.${view.route_name}`) }}
            </q-route-tab>
          </q-tabs>

          <!-- ARCHIVE SEARCH BOX -->
          <template v-if="$route.name == 'workOrderArchive'">
            <q-input
              clearable
              filled
              dense
              hide-bottom-space
              autocomplete="off"
              name="search"
              debounce="300"
              :label="$capitalize($t('search'))"
              v-model="archive_search"
              class="col-3 q-ml-xl">
              <template v-slot:append>
                <q-icon name="mdi-magnify" size="xs"/>
              </template>
            </q-input>
          </template>



          <!-- CREATE NEW WORK ORDER -->
          <template v-if="$route.name == 'workOrderList'">
            <q-space />

            <div class="col-auto" v-if="!editing">
              <q-btn
                size="0.75rem"
                color="theme-blue"
                @click="$router.push({ name: 'newWorkOrder'})">
                {{ $t('add') }}
              </q-btn>
            </div>

            <template v-else>
              <!-- REORDER WORK ORDER QUEUE -->
              <div class="col-auto">
                <q-btn
                  size="0.7rem"
                  color="theme-orange"
                  :loading="saving"
                  @click="updateQueue"
                  class="q-ml-sm">
                  {{ $t('production.save_new_sequence') }}
                </q-btn>
              </div>

              <!-- CANCEL CHANGES -->
              <div class="col-auto">
                <q-btn
                  size="0.7rem"
                  color="theme-grey"
                  @click="cancelQueueChanges"
                  class="q-ml-md">
                  {{ $t('cancel_changes') }}
                </q-btn>
              </div>
            </template>
          </template>
        </div>

        <!-- MAIN CONTENT -->
        <div class="col relative-position">
          <router-view
            v-if="vuex_ready"
            v-bind="{filters}"
            @setSearch="setSearch($event)"
            @itemDblClick="showWorkOrderScreen($event)"
            @editing="editing = true">
          </router-view>
          <NoDataAlert v-else />
        </div>


      </div>

      <template v-if="$route.name != 'workOrderArchive'">

        <!-- DIVIDER -->
        <q-separator vertical inset/>

        <!-- FILTERS -->
        <div class="col-3 column q-px-lg">
          <div class="highlight text-uppercase text-h5 q-mt-sm q-mb-md">
            {{ $t('filter', 2) }}
          </div>

          <!-- FILTERS SPECIFIC TO JOB LIST  -->
          <template v-if="$route.name == 'jobList'">
            <!-- BY DEPARTMENT -->
            <q-select
              ref="department_filter"
              filled
              dense
              use-input
              clearable
              v-model="department_selected"
              :options="filtered_departments"
              option-label="name"
              option-value="_key"
              emit-value
              map-options
              @filter="filterDepartment"
              :label="$capitalize($t('department', 1))"
              class="q-mb-md"
              popup-content-class="surface1">
            </q-select>

            <!-- BY OPERATOR -->
            <BaseAutocompleteOperator
              :placeholder="$capitalize($t('operator'))"
              dense
              class="q-mb-md"
              key_only
              :value="operator_selected"
              @select="(selection) => operator_selected = selection">
            </BaseAutocompleteOperator>
          </template>
          <!-- END OF JOB-SPECIFIC FILTERS -->

          <!-- SEARCH BOX -->
          <div class="row items-baseline q-col-gutter-md">
            <q-input
              filled
              dense
              clearable
              autocomplete="off"
              name="search"
              debounce="300"
              :label="$capitalize($t('search'))"
              v-model="search_string"
              class="q-mb-md col">
              <template v-slot:append>
                <q-icon name="mdi-magnify"/>
              </template>
            </q-input>
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
          </div>

          <!-- BOOLEAN FILTERS -->
          <div class="row">
            <div
              class="col-6"
              v-for="filter in bool_filters"
              :key="filter">
              <q-checkbox
                dense
                color="theme-blue"
                size="sm"
                :label="$capitalize($t(`production.filters.${filter}`))"
                v-model="_this[filter]"
                class="q-mt-md text-body1 low-text">
              </q-checkbox>
            </div>
            <template v-if="$route.name=='jobList'">
              <div
                class="col-6"
                v-for="filter in job_filters"
                :key="filter">
                <q-checkbox
                  dense
                  color="theme-blue"
                  size="sm"
                  :label="$capitalize($t(`production.filters.${filter}`))"
                  v-model="_this[filter]"
                  class="q-mt-md text-body1 low-text">
                </q-checkbox>
              </div>
            </template>
          </div>

          <q-space />

          <q-btn
            color="theme-blue"
            v-show="filters_active"
            class="q-mb-md"
            @click="resetFilters">
            {{ $t('reset_filters') }}
          </q-btn>
        </div>
      </template>
    </q-page>
  </q-page-container>
</template>

<script>
import NoDataAlert from '@/components/NoDataAlert.vue'
import BaseUserAvatar from '@/components/BaseUserAvatar.vue'
import BaseAutocompleteOperator from '@/components/BaseAutocompleteOperator.vue'
import multiMatch from '@/lib/MultiFieldSearch.js'
import queryModel from '@/lib/queryModelFactory.js'

const production_views = [
  { component: 'WorkOrderList', route_name: 'workOrderList' },
  { component: 'JobList', route_name: 'jobList' },
  { component: 'WorkOrderArchive', route_name: 'workOrderArchive' }
]

const header_plus_footer_height = 80

export default {

  name: 'ProductionOverview',

  components: {
    BaseUserAvatar,
    BaseAutocompleteOperator,
    NoDataAlert
  },

  data () {
    return {
      vuex_ready: false,
      // content_height: 0,
      views: production_views,
      current_view: 0,
      bool_filters: ['started','queued','on_time','late','active','idle','ready','not_ready','critical','not_critical'],
      job_filters: ['assigned', 'unassigned'],
        // with_open_issues_only: { label: 'Solo con segnalazioni aperte', value: true },
      department_search_text: undefined,
      editing: false,
      saving: false,
      polling_instance: undefined,
      operator_search_text: undefined
    }
  },

  computed: {
    // Filters
    search_string: queryModel(String, 'search', null),
    archive_search: queryModel(String, 'archive_search', null),

    operator_selected: queryModel(String, 'operator', undefined),
    department_selected: queryModel(String, 'department', undefined),

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

    _this() { return this },

    filters() {
      let bools = {}
      this.bool_filters.forEach(f => bools[f] = this[f])
      this.job_filters.forEach(f => bools[f] = this[f])

      return {
        search_string: this.search_string,
        archive_search: this.archive_search,
        ...bools,
        department_key: this.department_selected,
        operator_key: this.operator_selected
      }
    },

    filters_active() {
      return this.bool_filters.map(f => this[f]).some(f => f === false)
        || this.search_string != null
        || this.department_selected != null
        || this.operator_selected != null
    },

    operator_list () {
      return this.$store.getters.operator_list()
    },

    filtered_operators() {
      return this.operator_list.filter(
        o => multiMatch(this.operator_search_text, o, ['name', 'surname'])
      )
    },

    department_list() {
      return this.$store.state.org.departments
    },

    filtered_departments() {
      return this.department_search_text
        ? this.department_list.filter(d => d.name.toLowerCase().includes(this.department_search_text))
        : this.department_list
    }

  },

  methods: {
    updateHeight() {
      this.content_height = document.documentElement.clientHeight - header_plus_footer_height
    },

    setSearch(text) {
      this.search_string = text
    },

    resetFilters() {
      this.$router.replace({ query: null })
    },

    showWorkOrderScreen({wo_key, back_to_route_name}) {
      const to_route = {
        name: 'workOrderJobs',
        params: {
          wo_key: wo_key,
        },
        query: {
          back_to: back_to_route_name,
          ...this.$route.query
        }
      }
      this.$router.push(to_route)
    },

    async updateQueue() {
      this.saving = true
      await this.$store.dispatch('saveQueueChanges')
      this.saving = false
      this.editing = false
    },

    cancelQueueChanges() {
      this.$store.commit('RESET_TEMP_QUEUE')
      this.editing = false
    },

    async filterDepartment (val, update, abort) {
      update(() => {
        this.department_search_text = val.toLowerCase()
      })
    },

    async filterOperator (val, update, abort) {
      update(() => {
        this.operator_search_text = val.toLowerCase()
      })
    }
  },

  created() {
    Promise.all([
      this.$store.dispatch("loadDepartments"),
      this.$store.dispatch("loadUsers"),
      this.$store.dispatch("loadWorkOrders"),
      this.$store.dispatch("loadJobAssignments")
      ])
    .then(this.vuex_ready = true)

    this.polling_instance = setInterval(() => {
      this.$store.dispatch("updateWorkOrderList")
      this.$store.dispatch("loadJobAssignments")
    }, 10000)
  },

  beforeUnmount() {
    clearInterval(this.polling_instance)
  }
}
</script>

<style lang="css" scoped>
</style>
