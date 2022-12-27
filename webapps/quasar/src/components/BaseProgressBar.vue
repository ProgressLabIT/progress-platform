<template>
  <q-linear-progress
    :value="progress"
    :color="color.foreground"
    :track-color="color.background"
    :buffer="1"
    :size="size">
  </q-linear-progress>
</template>

<script>
export default {

  name: 'BaseProgressBar',

  props: {
    data: {
      type: Object,
      required: true
    },
    size: {
      type: String,
      default: '4px'
    }
  },

  computed: {
    progress() {
      return this.data.progress / 100
    },

    color() {
      return this.data.active
        ? { foreground: 'theme-blue', background: 'blue-backdrop' }
        : { foreground: 'theme-grey', background: 'grey-backdrop' }
    }
  }
}
</script>

<style lang="css" scoped>
</style>
