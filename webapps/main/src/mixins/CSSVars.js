export default {
  computed: {
    CSSVars () {
      return {
        '--text-high': this.$q.dark.isActive ? 'rgba(255,255,255,.87)' : 'rgba(0,0,0,.87)',
        '--text-low': this.$q.dark.isActive ? 'rgba(255,255,255,.6)' : 'rgba(0,0,0,.6)',
        '--bg-color': this.$q.dark.isActive ? '#131E21' : '#eee'
      }
    }
  }
}
