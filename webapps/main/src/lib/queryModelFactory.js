/*
 * The following is a utility function to define computed properties
 * to model and store template data as url query parameters.
 * This is useful to persist data when navigating to/from pages
 * without having to store it in Vuex/Pinia
 *
 * This function is set as a global Vue property and is intended
 * to be used with the spread operator as follows:
 * computed: { ...queryModelFactory(computed_prop_name, query_param_name, default_value) }
 */

export default function queryModelFactory(data_type, query_param_name, default_value) {
  return {

    get() {
      let value = this.$route.query[query_param_name]
      if (data_type == Number) {
        value = parseFloat(value)
      }
      else if (data_type == Boolean) {
        value = value != 'false'
      }
      return value ?? default_value
    },

    set(value) {
      let query = {
        ...this.$route.query,
        [query_param_name]: value
      }

      // Remove query param from url if value is empty, null, undefined or true (for booleans)
      if ([null, undefined, '', true].includes(value)) {
        delete query[query_param_name]
      }

      this.$router.replace({ query })
    }
  }
}
