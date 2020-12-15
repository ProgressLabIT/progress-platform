<template>
  <BaseModalScreen :show="show_modal" @close="exit()" @input="exit()">
    <template v-slot:header>
      <span class="ml-4 display medium highlight weight-medium">ID ORDINE DI PRODUZIONE: {{ wo_key }}</span>

      <v-col cols="auto" class="ml-auto">
        <v-tabs 
          background-color="transparent"
          :color="$theme.white_high"
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
      <v-container v-if="vuex_ready" fluid class="fill" ref="container">
        <v-row no-gutters class="fill-height">
          
          <v-col cols="4" lg="3" class="fill-height pr-9" style="position:fixed">
            <v-row>
              <v-col class="py-0">
                <WorkOrderDataColumn v-if="vuex_ready" v-bind="{ wo_data }">
                </WorkOrderDataColumn>
              </v-col>
              <v-divider vertical ></v-divider>
            </v-row>
          </v-col>    

          <v-col cols="8"  lg="9" offset="4" offset-lg="3" class="py-0 fill-height">
            <keep-alive>
              <router-view v-if="vuex_ready" v-bind="{ wo_data }"></router-view>
            </keep-alive>
          </v-col>

        </v-row>
      </v-container>

      <LoadingSignal v-else></LoadingSignal>

    </template>

  </BaseModalScreen>
</template>

<script>
import axios from 'axios'
import BaseModalScreen from '@/components/BaseModalScreen.vue'
import WorkOrderDataColumn from '@/components/WorkOrderDataColumn.vue'
import LoadingSignal from '@/components/LoadingSignal'

export default {

  name: 'WorkOrderScreen',

  components: {
    BaseModalScreen,
    LoadingSignal,
    WorkOrderDataColumn,
  },

  props: ['wo_key'],

  data () {
    return { 
      show_modal: true,
      links: [
        {
          name: 'workOrderJobs',
          title: 'lavori'
        },
        {
          name: 'workOrderHistory',
          title: 'storico'
        }
      ],
      vuex_ready: false,
      column_height: '80vh',
      polling_instance: undefined
    }
  },

  computed: {
    wo_data() {
      return this.$store.state.workorder.wo_data || { phase_sequence: []}
    }
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
    },
    get_wo_data() {
      axios.all([
        this.$store.dispatch('loadWorkOrderData', this.wo_key),
        this.$store.dispatch('loadUsers')
      ])
      .then(() => this.vuex_ready = true)
    }
  },

  created() {
    this.get_wo_data()
    this.polling_instance = setInterval(this.get_wo_data, 3000)
  },

  beforeDestroy() {
    clearInterval(this.polling_instance)
  }
}
</script>

<style lang="css" scoped>
</style>