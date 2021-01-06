<template>
  <BaseModalScreen :show="show_modal" @close="exit()">

    <template v-slot:header>
      <span class="ml-4 display medium highlight weight-medium">
        {{ $tc('product.key') }}: {{ product_key }}
      </span>

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
      <keep-alive>
        <router-view></router-view>
      </keep-alive>
    </template>

  </BaseModalScreen>
</template>

<script>
import BaseModalScreen from '@/components/BaseModalScreen'
export default {

  name: 'ProductScreen',

  props: ['product_key'],

  components: {
    BaseModalScreen
  },

  data () {
    return {
      root: "productList",
      show_modal: true,
      links: [
        {
          name: 'productHome',
          title: this.$tc('product.tabs.home')
        },
        {
          name: 'productionProcess',
          title: this.$tc('product.tabs.process')
        },
        {
          name: 'bom',
          title: this.$tc('product.tabs.bom')
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
        window.alert(this.$tc('product.alerts.save_before_exit'))
        this.show_modal = true
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