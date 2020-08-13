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
            :color="$theme.white_high"
            hide-slider
            class="flex-shrink-1 flex-grow-0">
            <v-tab 
              v-for="(view, index) in views"
              :key="index"
              :to="{ name: view.route_name }"
              class="display">
              {{ view.name }}
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
                crea ordine
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
                  SALVA NUOVA SEQUENZA
                </v-btn>
              </v-col>

              <!-- CANCEL CHANGES -->
              <v-col cols="auto">
                <v-btn small
                  :color="$theme.grey"
                  @click="cancelQueueChanges"
                  class="ml-2">
                  ANNULLA MODIFICHE
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
        <h5 class="highlight text-uppercase">filtri</h5>
        

        <!-- FILTER JOBS BY DEPARTMENT -->
        <v-autocomplete v-if="$route.name == 'jobList'"
          autocomplete="off"
          v-model="department"
          :items="$store.state.org.departments"
          item-value="_key"
          single-line hide-details clearable
          label="Dipartimento"
          class="mb-6 flex-grow-0">
          <template v-slot:item="{ item: list_item }">
            {{ list_item.name }}
          </template>
          <template v-slot:selection="{ item: selection }">
            {{ selection.name }}
          </template>
        </v-autocomplete>

        <!-- Search box: instructions shows on mouse over info icon, in turn shown only on mouse over input -->
        <v-hover v-slot:default="{ hover }">
          <v-text-field
            clearable
            hide-details
            single-line
            autocomplete="off"
            name="search"
            label="Ricerca"
            value="search"
            v-model="search_string"
            class="mb-6 body-2 text-uppercase flex-grow-0">
            <template v-slot:append>
              
              <v-tooltip bottom content-class="opaque">
                <template v-slot:activator="{ on }">
                  <v-icon 
                    v-show="hover"
                    :color="$theme.white_low"
                    small class="mr-2"
                    v-on="on">
                    info
                  </v-icon>
                </template>
                <span>
                  Ricerca termini in uno o più dei seguenti campi:
                </span>
                <ul>
                  <li>Codice prodotto</li>
                  <li>Ordine di produzione</li>
                  <li>Riga ordine di produzione</li>
                  <li>Nome cliente</li>
                  <li>Numero ordine/PO cliente</li>
                  <li>Fase di lavorazione</li>
                  <li>Dipartimento</li>
                  <li>Nome operatore</li>
                  <li>Nome attrezzatura</li>
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
          :label="filter.label"
          v-model="filter.value"
          class="mt-2">
        </v-checkbox>

        <v-spacer></v-spacer>
        <!-- FILTERS RESET -->
        <v-btn :color="$theme.blue"
          v-show="filters_active"
          @click="resetFilters">
          ELIMINA FILTRI
        </v-btn>

      </v-col>
    </v-row>
  </v-container>
</template>

<script>
// import WorkOrderList from '@/components/WorkOrderList.vue'
// import JobList from '@/components/JobList.vue'


const production_views = [
  { name: 'ordini di produzione', component: 'WorkOrderList', route_name: 'workOrderList' },
  { name: 'lavori', component: 'JobList', route_name: 'jobList' },
]

const header_plus_footer_height = 80

export default {

  name: 'ProductionOverview',

  // components: {
  //   WorkOrderList,
  //   JobList
  // },

  data () {
    return {
      // content_height: 0,
      views: production_views,
      current_view: 0,
      bool_filters: {
        started: { label: 'Iniziato', value: true, },
        queued: { label: 'In coda', value: true, },
        on_time: { label: 'In tempo', value: true, },
        late: { label: 'In ritardo', value: true, },
        active: { label: 'Attivo', value: true, },
        idle: { label: 'Non attivo', value: true},
        critical: { label: 'Critico', value: true, },
        not_critical: { label: 'Non critico', value: true}
        // with_open_issues_only: { label: 'Solo con segnalazioni aperte', value: true },
      },
      search_string: undefined,
      department: undefined,
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
      const department = this.department
      return { search_string, ...bools_map, department }
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
    }
  },

  beforeCreate() {
    this.$store.dispatch("loadDepartments")
    this.$store.dispatch("loadUsers")
    this.$store.dispatch("loadWorkOrders")
  },

  created() {
    this.polling_instance = setInterval(() => {
      this.$store.dispatch("updateWorkOrdersProgress")
      this.$store.dispatch("loadJobAssignments")
    }, 10000)
  },

  beforeDestroy() {
    clearInterval(this.polling_instance)
  }
}
</script>

<style lang="css" scoped>
</style>