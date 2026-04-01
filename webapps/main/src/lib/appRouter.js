/** Vue Router instance for use outside components (e.g. Vuex actions). Set from a Quasar boot file. */
let router = null;

export function setAppRouter(instance) {
  router = instance;
}

export function getAppRouter() {
  return router;
}
