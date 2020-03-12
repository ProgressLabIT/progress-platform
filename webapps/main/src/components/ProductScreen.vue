<template>
  <ModalScreen :show="show_modal" @close="exit()">

    <template v-slot:header>
      <span class="ml-4 display medium highlight weight-medium">ID PRODOTTO: {{ product_key }}</span>

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

  </ModalScreen>
</template>

<script>
import ModalScreen from '@/components/ModalScreen'
export default {

  name: 'ProductScreen',

  props: ['product_key'],

  components: {
    ModalScreen
  },

  data () {
    return {
      root: "productList",
      show_modal: true,
      links: [
        {
          name: 'productHome',
          title: 'parametri'
        },
        {
          name: 'productionProcess',
          title: 'processo'
        },
        {
          name: 'bom',
          title: 'distinta'
        }
      ]
    }
  },

  computed: {
    edit_modes() {
      return this.$store.state.product.edit_modes
    },
    user_is_editing() {
      return Object.values(this.edit_modes).some( v => v === true )
    }
  },

  methods: {
    exit() {
      if (this.user_is_editing) {
        window.alert(`Salva o annulla le modifiche in tutte le sezioni prima di uscire.`)
      }
      else {
        this.show_modal = false
        this.$router.push({ name: this.$route.query.back_to })
      }
    }
  },

  created() {
    let actions = [
      'getProcess',
      'getBom',
      'loadProductDetails',
      'getOperations'
    ]
    
    actions.forEach( a => this.$store.dispatch(a, this.product_key))
  }
}
</script>

<style lang="css" scoped>
</style>