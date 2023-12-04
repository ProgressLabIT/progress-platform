import { boot } from 'quasar/wrappers'

export default boot(async ({ store }) => {
  // Make sure custom fields are ready before the app starts
  await store.dispatch('getCustomFields')
})
