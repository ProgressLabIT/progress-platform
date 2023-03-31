<template>
  <q-page-container class="fit">
    <q-page class="row">

      <div class="column col">
        <!-- WORK ORDERS / JOBS LISTS -->
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
              :to="{ name: view.route_name }"
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
              v-model="search_string"
              class="col-3 q-ml-xl">
              <template v-slot:append>
                <q-icon name="mdi-magnify" size="xs"/>
              </template>
            </q-input>
          </template>


          <q-space />

          <!-- CREATE NEW WORK ORDER -->
          <template v-if="$route.name == 'workOrderList'">
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
        <router-view
          v-if="vuex_ready"
          v-bind="{filters}"
          @lateOnly="showLateOnly"
          @criticalOnly="showCriticalOnly"
          @setSearch="setSearch($event)"
          @itemDblClick="showWorkOrderScreen($event)"
          @editing="editing = true">
        </router-view>

        <NoDataAlert v-else />

      </div>

      <template v-if="$route.name != 'workOrderArchive'">
        <!-- DIVIDER -->
        <q-separator vertical inset/>

        <!-- FILTERS -->
        <div class="col-3 column q-px-lg">
          <div class="highlight text-uppercase text-h5 q-mt-sm">
            {{ $t('filter', 2) }}
          </div>

          <!-- FILTERS SPECIFIC TO JOB LIST  -->
          <template v-if="$route.name == 'jobList'">

            <!-- BY DEPARTMENT -->
            <q-select
              ref="department_filter"
              use-input
              clearable
              v-model="department_selected"
              :options="filtered_departments"
              option-label="name"
              @filter="filterDepartment"
              :label="$capitalize($t('department', 1))"
              class="q-mb-md"
              popup-content-class="surface1">
            </q-select>

            <!-- BY OPERATOR -->
            <q-select
              ref="operator_filter"
              use-input
              clearable
              v-model="operator_selected"
              :options="filtered_operators"
              :option-label="(item) => item.name + ' ' + item.surname"
              @filter="filterOperator"
              :label="$capitalize($t('operator'))"
              class="q-mb-md"
              popup-content-class="surface1">
              <template v-slot:option="scope">
                <q-item v-bind="scope.itemProps">
                  <BaseUserAvatar :user="scope.opt"/>
                </q-item>
              </template>
            </q-select>

          </template>
          <!-- END OF JOB-SPECIFIC FILTERS -->

          <!-- SEARCH BOX -->
          <div class="row items-center q-col-gutter-md">
            <q-input
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
          <q-checkbox
            v-for="(filter, key) in bool_filters"
            :key="key"
            dense
            color="theme-blue"
            size="sm"
            :label="$capitalize($t(`production.filters.${key}`))"
            v-model="filter.value"
            class="q-mt-md text-body1 low-text">
          </q-checkbox>

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
import multiMatch from '@/lib/MultiFieldSearch.js'

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
    NoDataAlert
  },

  data () {
    return {
      vuex_ready: false,
      // content_height: 0,
      views: production_views,
      current_view: 0,
      bool_filters: {
        started: { value: true },
        queued: { value: true },
        // on_time: { value: true },
        // late: { value: true },
        active: { value: true },
        idle: { value: true },
        ready: { value: true },
        not_ready: { value: true },
        //critical: { value: true },
        //not_critical: { value: true }
        // with_open_issues_only: { label: 'Solo con segnalazioni aperte', value: true },
      },
      search_string: undefined,
      department_selected: undefined,
      department_search_text: undefined,
      operator_selected: undefined,
      editing: false,
      saving: false,
      polling_instance: undefined,
      operator_search_text: undefined
    }
  },

  computed: {
    filters() {
      const search_string = this.search_string
      const bools_map = {}
      for (const [k,v] of Object.entries(this.bool_filters)) {
        bools_map[k] = v.value
      }
      const department_key = this.department_selected ? this.department_selected._key : undefined
      const operator_key = this.operator_selected ? this.operator_selected._key : undefined
      return { search_string, ...bools_map, department_key, operator_key }
    },

    filters_active() {
      return Object.values(this.bool_filters).some(f => f.value === false) 
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

    showLateOnly() {
      this.bool_filters.on_time.value = false
    },

    showCriticalOnly() {
      this.bool_filters.not_critical.value = false
    },

    setSearch(text) {
      this.search_string = text
    },

    resetFilters() {
      this.search_string = null
      this.operator_selected = null
      this.department_selected = null
      for (let filter of Object.values(this.bool_filters)) {
        filter.value = true
      }
    },

    showWorkOrderScreen({wo_key, back_to_route_name}) {
      const to_route = {
        name: 'workOrderJobs',
        params: {
          wo_key: wo_key,
        },
        query: {
          back_to: back_to_route_name
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

  beforeCreate() {
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
