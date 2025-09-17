import { computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';

// uses `getRoute`/`getRouter` instead of just `router` since `this` is not available in the root level,
// it's only available inside get() and set()
function baseQueryModelFactory(
  data_type,
  query_param_name,
  default_value,
  getRoute,
  getRouter,
) {
  return {
    get() {
      let value = getRoute.call(this).query[query_param_name];
      if (data_type === Number) {
        value = parseFloat(value);
      } else if (data_type === Boolean) {
        value = ['true', 'false'].includes(value) ? value === 'true' : default_value;
      } else if (data_type === Object || data_type === Array) {
        value = value ? JSON.parse(atob(value)) : null;
      }
      return value ?? default_value;
    },
    set(value) {
      const query = {
        ...getRoute.call(this).query,
        [query_param_name]:
          data_type === Object || data_type === Array
            ? btoa(JSON.stringify(value))
            : value,
      };

      // Remove query param from url if value equals default or is empty/null/undefined
      if (
        [null, undefined, ''].includes(value) ||
        value === default_value ||
        (data_type === Object && Object.keys(value).length === 0) ||
        (data_type === Array && value.length === 0)
      ) {
        delete query[query_param_name];
      }

      getRouter.call(this).replace({ query });
    },
  };
}

/**
 * The following is a utility function to define computed properties
 * to model and store template data as url query parameters.
 * This is useful to persist data when navigating to/from pages
 * without having to store it in Vuex/Pinia
 *
 * @example Options API
 * computed: {
 *  some_name: queryModelFactory(computed_prop_name, query_param_name, default_value)
 * }
 *
 * @see {@link useQueryModel} for Composition API
 */
export default function optionsQueryModelFactory(
  data_type,
  query_param_name,
  default_value,
) {
  return baseQueryModelFactory(
    data_type,
    query_param_name,
    default_value,
    // using function() instead of () => to preserve `this` context
    function () {
      return this.$route;
    },
    function () {
      return this.$router;
    },
  );
}

/**
 * @see {@link optionsQueryModelFactory} for Options API
 */
export function useQueryModel(dataType, queryParamName, defaultValue) {
  const route = useRoute();
  const router = useRouter();

  return computed(
    baseQueryModelFactory(
      dataType,
      queryParamName,
      defaultValue,
      () => route,
      () => router,
    ),
  );
}
