import Vue from "vue";
import Main from "./Main.vue";
import router from "./router";
import store from "./store";
import vuetify from './plugins/vuetify';
import theme from './styles/theme.js'
import 'material-design-icons-iconfont/dist/material-design-icons.css' // Ensure you are using css-loader 
import './lib/filters.js'


Vue.config.productionTip = false;

Vue.prototype.$theme = theme


new Vue({
  router,
  store,
  vuetify,
  render: h => h(Main)
}).$mount("#app");