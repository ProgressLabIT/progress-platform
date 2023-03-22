export default {
  methods: {
    enrichIssue(i) {
    // Add badge data for visual indication of status
      let badge = !i.open
        ? { color: 'theme-grey', text: this.$t('closed') }
        : i.critical
        ? { color: 'theme-red', text: this.$t('critical') }
        : { color: 'theme-orange', text: this.$t('open') }
      return { ...i, badge }
    }
  }
}
