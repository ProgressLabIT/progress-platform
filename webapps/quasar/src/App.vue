<template>
  <div :style="cssVars">
    <router-view />
  </div>
</template>

<script>
import { DateTime as DT } from 'luxon'
import { defineComponent } from 'vue'

export default defineComponent({
  name: 'App',

  computed: {
    cssVars () {
      return {
        '--text-high': this.$q.dark.isActive ? 'rgba(255,255,255,.87)' : 'rgba(0,0,0,.87)',
        '--text-low': this.$q.dark.isActive ? 'rgba(255,255,255,.6)' : 'rgba(0,0,0,.6)',
        '--bg-color': this.$q.dark.isActive ? '#131E21' : '#eee'
      }
    }
  },

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
