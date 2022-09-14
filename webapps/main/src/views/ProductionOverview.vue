<template>
  <v-container fluid class="fill py-0 flex-grow-0">
    <v-row class="fill">

      <!-- WORK ORDERS / JOBS LISTS -->      
      <v-col class="fill d-flex flex-column">

        <!-- TAB LINKS -->
        <v-row dense class="flex-grow-0 mb-2">    
          <v-col cols="auto">
          
          <v-tabs
            background-color="transparent"
            v-model="current_view"
            :color="$theme.text_high"
            hide-slider
            class="flex-shrink-1 flex-grow-0">
            <v-tab 
              v-for="(view, index) in views"
              :key="index"
              :to="{ name: view.route_name }"
              class="display">
              {{ $tc(`views.${view.route_name}`) }}
            </v-tab>
          </v-tabs>
          </v-col>

          <v-spacer></v-spacer>
          
          <!-- CREATE NEW WORK ORDER -->
          <template v-if="$route.name == 'workOrderList'">
            <v-col cols="auto" v-if="!editing">
              <v-btn small 
                :color="$theme.blue"
                @click="$router.push({ name: 'newWorkOrder'})">
                {{ $tc('create_order') }}
              </v-btn>
            </v-col>
    
            <template v-else>

              <!-- REORDER WORK ORDER QUEUE -->
              <v-col cols="auto">
                <v-btn small
                  :color="$theme.orange"
                  :loading="saving"
                  @click="updateQueue"
                  class="ml-3">
                  {{ $tc('production.save_new_sequence') }}
                </v-btn>
              </v-col>

              <!-- CANCEL CHANGES -->
              <v-col cols="auto">
                <v-btn small
                  :color="$theme.grey"
                  @click="cancelQueueChanges"
                  class="ml-2">
                  {{ $tc('cancel_changes') }}
                </v-btn>
              </v-col>

            </template>

          </template>

        </v-row>

        <!-- MAIN CONTENT -->
        <div class="scroll flex-grow-1">
          <!-- <keep-alive> -->
            <!-- <v-component
              :is="views[current_view].component" 
              v-bind="{ filters }"
              @showDetails="showWorkOrderScreen($event)"/> -->
            <router-view 
              v-bind="{filters}"
              @lateOnly="showLateOnly"
              @criticalOnly="showCriticalOnly"
              @setSearch="setSearch($event)"
              @itemDblClick="showWorkOrderScreen($event)"
              @editing="editing = true">
            </router-view>

          <!-- </keep-alive> -->
        </div>
          
      </v-col>

      
      <!-- DIVIDER -->
      <v-divider vertical inset></v-divider>

      <!-- FILTERS -->
      <v-col cols="3" class="pa-6 d-flex flex-column">
        <h5 class="highlight text-uppercase">{{ $tc('filter', 2) }}</h5>
        
        <!-- FILTERS SPECIFIC TO JOB LIST  -->
        <template v-if="$route.name == 'jobList'">
          <!-- BY DEPARTMENT -->
          <v-autocomplete
            autocomplete="off"
            v-model="department_key"
            :items="$store.state.org.departments"
            item-value="_key"
            item-text="name"
            single-line hide-details clearable
            :label="$tc('department', 1) | capitalize"
            class="mb-6 flex-grow-0">
            <template v-slot:item="{ item: list_item }">
              {{ list_item.name }}
            </template>
            <template v-slot:selection="{ item: selection }">
              {{ selection.name }}
            </template>
          </v-autocomplete>

          <!-- BY OPERATOR: Adapted from JobRebalanceActionCard  -->
          <v-autocomplete
            ref="operator_autocomplete"
            autocomplete="off"
            :items="$store.getters.operator_list()"
            item-value="_key"
            v-model="operator_key"
            single-line hide-details
            clearable
            :filter="filterOperator"
            :label="$tc('operator') | capitalize"
            class="mb-6 flex-grow-0">
            <template v-slot:item="{ item: list_item }">
              <BaseUserAvatar :user="list_item"/>
            </template>
            <template v-slot:selection="{ item: selection }">
              <BaseUserAvatar :user="selection"/>
            </template>
          </v-autocomplete>
        </template>

        <!-- Search box: instructions shows on mouse over info icon, in turn shown only on mouse over input -->
        <v-hover v-slot:default="{ hover }">
          <v-text-field
            clearable
            hide-details
            single-line
            autocomplete="off"
            name="search"
            :label="$tc('search') | capitalize"
            value="search"
            v-model="search_string"
            class="mb-6 body-2 text-uppercase flex-grow-0">
            <template v-slot:append>
              
              <v-tooltip bottom content-class="opaque">
                <template v-slot:activator="{ on }">
                  <v-icon 
                    v-show="hover"
                    :color="$theme.text_low"
                    small class="mr-2"
                    v-on="on">
                    info
                  </v-icon>
                </template>
                <span>
                  {{ $tc('production.search_explainer') | capitalize }}:
                </span>
                <ul>
                  <li>{{ $tc('product_code') | capitalize }}</li>
                  <li>{{ $tc('work_order.long') | capitalize }}</li>
                  <li>{{ $tc('work_order.wo_line.long') | capitalize }}</li>
                  <li>{{ $tc('phase.long') | capitalize }}</li>
                  <li>{{ $tc('department', 1) | capitalize }}</li>
                  <li>{{ $tc('operator', 1) | capitalize }}</li>
                </ul>
              </v-tooltip>

              <span class="material-icons">search</span>

            </template>
          </v-text-field>
        </v-hover>
        
        <!-- Checkboxes -->
        <v-checkbox dense hide-details 
          :color="$theme.blue"
          v-for="(filter, key) in bool_filters" 
          :key="key" 
          :label="$tc(`production.filters.${key}`) | capitalize"
          v-model="filter.value"
          class="mt-2">
        </v-checkbox>

        <v-spacer></v-spacer>
        <!-- FILTERS RESET -->
        <v-btn :color="$theme.blue"
          v-show="filters_active"
          @click="resetFilters">
          {{ $tc('reset_filters') }}
        </v-btn>

      </v-col>
    </v-row>
  </v-container>
</template>

<script>
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
    BaseUserAvatar
  },

  data () {
    return {
      // content_height: 0,
      views: production_views,
      current_view: 0,
      bool_filters: {
        started: { value: true },
        queued: { value: true },
        on_time: { value: true },
        late: { value: true },
        active: { value: true },
        idle: { value: true },
        critical: { value: true },
        not_critical: { value: true }
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
    this.$store.dispatch("loadDepartments")
    this.$store.dispatch("loadUsers")
    this.$store.dispatch("loadWorkOrders")
    this.$store.dispatch("loadJobAssignments")
  },

  created() {
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
