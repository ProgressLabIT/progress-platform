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
            :to="{ name: page.name }"
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
    user_is_editing() {
      const edit_modes = this.$store.state.product.edit_modes
      return Object.values(edit_modes).some( v => v === true )
    }
  },

  methods: {
    exit() {
      /** 
       * the delay allows for a nice closing animation of 
       * the modal  before going back to the previous route
       */
      if (this.user_is_editing) {
        window.alert("Salva o annulla le modifiche prima di cambiare pagina")
      }
      else {
        this.show_modal = false
        // setTimeout(() => {
        this.$router.push({ name: this.root })
        // }, 1)
        // return true
      }
    }
  },

  created() {
    let actions = [
      'loadProductDetails',
      'getProcess',
      'getBom',
      'getOperations'
    ]
    
    actions.forEach( a => this.$store.dispatch(a, this.product_key))
  }
}
</script>

<style lang="css" scoped>
</style>