export default {
  computed: {
    show_drawer: {
      get() {
        return this.$store.state.show_drawer
      },
      set(value) {
        this.$store.commit('SHOW_DRAWER', value)
      }
    }
  }
}
