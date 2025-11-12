import { boot } from 'quasar/wrappers';
import store from '../store/index.js';

export default boot(({ app }) => {
  // Register the Vuex store with the app
  app.use(store);
});

export { store };

