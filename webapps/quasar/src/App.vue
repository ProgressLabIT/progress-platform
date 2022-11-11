<template>
  <router-view />
</template>

<script>
import { DateTime as DT } from 'luxon'
import { defineComponent } from 'vue'

export default defineComponent({
  name: 'App',

  created() {
    // Save vuex state in localStorage before refresh or tab close
    window.addEventListener("beforeunload", async (event) => {
      if (this.$route.name != 'login') {
        console.log('Not login')
        localStorage.setItem('TEMP_SESSION', JSON.stringify({
          ...this.$store.state,
          last_interaction: DT.utc().toMillis()
        }))
      }
    })
  }
})
</script>
