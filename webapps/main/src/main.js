import Vue from "vue";
import App from "./App.vue";
import router from "./router";
import store from "./store";
import vuetify from './plugins/vuetify';

Vue.config.productionTip = false;
Vue.prototype.$theme = {
  background: '#131E21',
  surface1: '#1F2A2D',
  surface2: '#242E31',
  grey: '#707070',
  blue: '#22AED1',
  green: '#0DAB76',
  red: '#E71D36',
  orange: '#FF9F1C',
}

Vue.filter('capitalize', function (value) {
  if (!value) return ''
  value = value.toString()
  return value.charAt(0).toUpperCase() + value.slice(1)
})


new Vue({
  router,
  store,
  vuetify,
  render: h => h(App)
}).$mount("#app");
