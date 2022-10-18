<template>
  <q-footer :color="$theme.footer">
    <div class="row q-px-sm justify-between">
      <div class="display smaller">PROGRESS PLATFORM</div>
      <div class="display smaller">{{ time }}</div>
      <div class="display smaller">{{ date }}</div>
    </div>
  </q-footer>
</template>

<script>
import { DateTime } from 'luxon'

export default {

  name: 'AppFooter',

  data () {
    return {
      now: 0
    }
  },

  computed: {
    time() { return this.now.toLocaleString(DateTime.TIME_SIMPLE) },
    date() { return this.now.setLocale("it").toLocaleString(DateTime.DATE_HUGE) }
  },

  created() {
    this.now = DateTime.local()
    setInterval(() => {
      this.now = this.now.plus({ seconds: 1 })
    }, 1000)
  }
}
</script>

<style lang="css" scoped>
.material-icons.smaller {
  font-size: .9em;
  vertical-align: bottom
}

.footer-text {
  color:  rgba(255,255,255,.6);
}
</style>
