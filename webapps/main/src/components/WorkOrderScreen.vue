<template>
  <BaseModalScreen :show="show_modal" @close="exit()">
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
      <keep-alive>
        <router-view></router-view>
      </keep-alive>
    </template>

  </BaseModalScreen>
</template>

<script>
import BaseModalScreen from '@/components/BaseModalScreen.vue'

export default {

  name: 'WorkOrderScreen',

  components: {
    BaseModalScreen
  },

  props: ['wo_key'],

  data () {
    return { 
      show_modal: true,
      links: [
        {
          name: 'workOrderHome',
          title: 'panoramica',
        },
        {
          name: 'workOrderJobs',
          title: 'lavori'
        },
        {
          name: 'workOrderHistory',
          title: 'storico'
        }
      ]

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
    }
  }
}
</script>

<style lang="css" scoped>
</style>