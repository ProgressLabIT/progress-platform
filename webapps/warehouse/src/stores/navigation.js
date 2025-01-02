import { defineStore } from "pinia";
import { Loading } from "quasar";
import { ref, watch } from "vue";

export const useNavStore = defineStore('navigation', () => {
  const dynamicBreadcrumb = ref([]);
  const loading = ref(false);

  watch(loading, (newVal) => {
    if (newVal) {
      Loading.show();
    } else {
      Loading.hide();
    }
  })

  return { dynamicBreadcrumb, loading }
})

