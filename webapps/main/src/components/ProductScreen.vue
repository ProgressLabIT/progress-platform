<template>
  <BaseModalScreen :show="show_modal" @close="exit()" :no_esc_dismiss="user_is_editing">

    <template #header>
      <span class="q-ml-md display highlight weight-medium">
        {{ $t('product.key') }}: {{ product_key }}
      </span>

      <div class="col-auto q-ml-auto">
        <q-tabs
          class="transparent text-low"
          active-class="text-high weight-bold"
          indicator-color="theme-blue"
          dense>
          <q-route-tab
            v-for="(page, index) in links"
            :key="index"
            :to="{ name: page.name, query: { ...$route.query } }"
            class="display">
            {{ page.title }}
          </q-route-tab>
        </q-tabs>
      </div>
    </template>

    <template #content>
      <router-view v-slot="{ Component }">
        <keep-alive>
          <component
            :is="Component"
            @changes_saved="showSaveConfirmation"
            @changes_canceled="showCancelConfirmation"/>
        </keep-alive>
      </router-view>
    </template>

  </BaseModalScreen>
</template>

<script>
import BaseModalScreen from '@/components/BaseModalScreen.vue'
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
    }
  },

  computed: {

    links() {
      return [
        {
          name: 'productHome',
          title: this.$t('product.tabs.home')
        },
        {
          name: 'productionProcess',
          title: this.$t('product.tabs.process')
        },
        {
          name: 'bom',
          title: this.$t('product.tabs.bom')
        }
      ]
    },

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
        window.alert(this.$t('product.alerts.save_before_exit'))
      }
      else {
        this.show_modal = false
        let query = { ...this.$route.query }
        delete query.back_to
        this.$router.push({ name: this.$route.query.back_to, query })
      }
    },

    showSaveConfirmation() {
      this.$q.notify({
        message: this.$capitalize(this.$t('snackbars.product_updated')),
        color: 'theme-green',
        timeout: 1500,
        position: 'top'
      })
    },

    showCancelConfirmation() {
      this.$q.notify({
        message: this.$capitalize(this.$t('snackbars.changes_canceled')),
        color: 'theme-grey',
        timeout: 1500,
        position: 'top'
      })
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

<style lang="sass">
</style>
