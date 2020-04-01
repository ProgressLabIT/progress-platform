<template>
  <BaseModalScreen :show="show_modal" @close="exit()" @input="exit()">
    <template v-slot:header>
      <span class="ml-4 display medium highlight weight-medium">ID ORDINE DI PRODUZIONE: {{ wo_key }}</span>

      <v-col cols="auto" class="ml-auto">
        <v-tabs 
          background-color="transparent"
          :color="$theme.whitehigh"
          hide-slider right
          >
          <v-tab 
            v-for="(page, index) in links" 
            :key="index" 
            :to="{ name: page.name, query: { back_to: $route.query.back_to } }"
            class="display" >
            {{ page.title }}
          </v-tab>
        </v-tabs>
      </v-col>  
    </template>

    <template v-slot:content>
      <v-container fluid class="fill">
        <v-row no-gutters class="fill-height">
          <v-col cols="3" class="fill-height">
            <WorkOrderDataColumn v-bind="{ wo_data, job_data }">
            </WorkOrderDataColumn>
          </v-col>    
          <v-col cols="auto" class="px-3 py-0">
            <v-divider vertical ></v-divider>
          </v-col>
          <v-col class="py-0">
            <keep-alive>
              <router-view v-bind="{ wo_data, job_data }"></router-view>
            </keep-alive>
          </v-col>
        </v-row>
      </v-container>
    </template>

  </BaseModalScreen>
</template>

<script>
import BaseModalScreen from '@/components/BaseModalScreen.vue'
import WorkOrderDataColumn from '@/components/WorkOrderDataColumn.vue'
import {api} from '@/lib/apiCall.js'

export default {

  name: 'WorkOrderScreen',

  components: {
    BaseModalScreen,
    WorkOrderDataColumn,
  },

  props: ['wo_key'],

  data () {
    return { 
      show_modal: true,
      links: [
        // {
        //   name: 'workOrderHome',
        //   title: 'panoramica',
        // },
        {
          name: 'workOrderJobs',
          title: 'lavori'
        },
        {
          name: 'workOrderHistory',
          title: 'storico'
        }
      ],
      wo_data: { phase_sequence: [] }

    }
  },

  computed: {
    wo_id() {
      return 'WorkOrder/' + this.wo_key
    },

    job_data() {
      return this.$store.state.job.job_list.filter( job => job.wo_id == this.wo_id)
    },
  },

  methods: {

    exit() {
      // if (this.user_is_editing) {
      //   window.alert(`Salva o annulla le modifiche in tutte le sezioni prima di uscire.`)
      // }
      // else {
        this.show_modal = false
        this.$router.push({ name: this.$route.query.back_to })
      // }
    }
  },

  created() {
    api.get(`/work-order/${this.wo_key}`).then( resp => {
      this.wo_data = resp.data.detail
    })
  }
}
</script>

<style lang="css" scoped>
</style>