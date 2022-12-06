<template>
  <q-page-container class="fit">
    <q-page class="row">

      <div class="column col-9">
        <!-- WORK ORDERS / JOBS LISTS -->
        <div class="row col-auto items-center q-pr-md">

          <!-- TAB LINKS -->
          <q-tabs
            class="transparent text-low"
            active-class="text-high weight-bold"
            align="left"
            shrink
            indicator-color="transparent">
            <q-route-tab
              v-for="(view, index) in views"
              :key="index"
              :to="{ name: view.route_name }"
              class="display">
              {{ $t(`views.${view.route_name}`) }}
            </q-route-tab>
          </q-tabs>

          <q-space />

          <!-- CREATE NEW WORK ORDER -->
          <template v-if="$route.name == 'workOrderList'">
            <div class="col-auto" v-if="!editing">
              <q-btn
                size="0.75rem"
                color="theme-blue"
                @click="$router.push({ name: 'newWorkOrder'})">
                {{ $t('create_order') }}
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

        <!-- DIVIDER -->
        <q-separator vertical inset/>

        <!-- FILTERS -->
        <div class="col column q-px-md">
          <div class="highlight text-uppercase text-h5 q-mt-sm">
            {{ $t('filter', 2) }}
          </div>

          <!-- FILTERS SPECIFIC TO JOB LIST  -->
          <template v-if="$route.name == 'jobList'">

            <!-- BY DEPARTMENT -->
            <q-select
              use-input
              clearable
              input-debounce="500"
              v-model="department_key"
              :options="$store.state.org.departments"
              option-value="_key"
              option-label="name"
              :label="$capitalize($t('department', 1))"
              class="q-mb-md">
            </q-select>
          </template>
        </div>
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
        //critical: { value: true },
        //not_critical: { value: true }
        // with_open_issues_only: { label: 'Solo con segnalazioni aperte', value: true },
      },
      search_string: undefined,
      department_key: undefined,
      operator_key: undefined,
      editing: false,
      saving: false,
      polling_instance: undefined
    }
  },

  computed: {
    filters() {
      const search_string = this.search_string
      const bools_map = {}
      for (const [k,v] of Object.entries(this.bool_filters)) {
        bools_map[k] = v.value
      }
      const department_key = this.department_key
      const operator_key = this.operator_key
      return { search_string, ...bools_map, department_key, operator_key }
    },

    filters_active() {
      return Object.values(this.bool_filters).some(f => f.value === false) 
        || this.search_string != undefined 
        || this.department != undefined
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
      this.search_string = undefined
      this.department = undefined
      this.operat
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

    filterOperator(operator, search_text) {
      return multiMatch(search_text, operator, ['name', 'surname'])
    },
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
      this.$store.dispatch("updateWorkOrdersProgress")
      this.$store.dispatch("loadJobAssignments")
    }, 5000)
  },

  beforeDestroy() {
    clearInterval(this.polling_instance)
  }
}
</script>

<style lang="css" scoped>
</style>
