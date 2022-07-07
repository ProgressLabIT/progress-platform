import Vue from "vue";

import Main from "./Main.vue";
import router from "./router";
import store from "./store";
import vuetify from './plugins/vuetify';
import { i18n } from './plugins/i18n.js'
import 'material-design-icons-iconfont/dist/material-design-icons.css' // Ensure you are using css-loader
import './lib/filters.js'



Vue.config.productionTip = false;

Vue.mixin({
  computed: {
    $theme () {
      return this.$store.getters.theme
    }
  }
})

new Vue({
  router,
  store,
  vuetify,
  i18n,
  // flags,
  render: h => h(Main)
}).$mount("#app");
