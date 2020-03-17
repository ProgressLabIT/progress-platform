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
            :color="$theme.whitehigh"
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
          <v-col cols="auto" >
            <v-btn small :color="$theme.blue">crea ordine</v-btn>
          </v-col>
        </v-row>

        <!-- MAIN CONTENT -->
        <div class="scroll flex-grow-1">
          <keep-alive>
            <!-- <v-component
              :is="views[current_view].component" 
              v-bind="{ filters }"
              @showDetails="showWorkOrderScreen($event)"/> -->
            <router-view v-bind="{filters}"></router-view>
          </keep-alive>
        </div>
          
      </v-col>


      <!-- DIVIDER -->
      <v-divider vertical inset></v-divider>

<!-- FILTERS -->
      <v-col cols="3" class="pa-6">
        <h5 class="highlight text-uppercase">filtri</h5>
        
        <!-- Search box: instructions shows on mouse over info icon, in turn shown only on mouse over input -->
        <v-hover v-slot:default="{ hover }">
          <v-text-field
            hide-details
            single-line
            autocomplete="off"
            name="search"
            label="Ricerca"
            value="search"
            v-model="search_string"
            class="mt-6 mb-12 body-2 text-uppercase">
            <template v-slot:append>
              
              <v-tooltip bottom content-class="opaque">
                <template v-slot:activator="{ on }">
                  <v-icon 
                    v-show="hover"
                    :color="$theme.whitelow"
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
        <v-checkbox dense hide-details :color="$theme.blue"
          v-for="(filter, key) in bool_filters" 
          :key="key" 
          :label="filter.label"
          v-model="filter.value">
        </v-checkbox>
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
      search_string: ''
    }
  },

  computed: {
    filters() {
      const search_string = this.search_string || ''
      const bools_map = {}
      for (const [k,v] of Object.entries(this.bool_filters)) {
        bools_map[k] = v.value
      }
      return { search_string, ...bools_map }
    }
  },

  methods: {
    updateHeight() {
      this.content_height = document.documentElement.clientHeight - header_plus_footer_height
    },
  },

  beforeCreate() {
    this.$store.commit("UPDATE_SCREEN_TITLE", "monitoraggio produzione")
  },

  // created() {
     
  //   Resize app content with window: see also another solution at https://www.html5rocks.com/en/tutorials/speed/animations/ 
    
  //   this.updateHeight()
  //   window.addEventListener('resize', this.updateHeight, false)
  // }
}
</script>

<style lang="css" scoped>
</style>