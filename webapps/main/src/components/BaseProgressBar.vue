<template>
  <q-linear-progress
    animation-speed="300"
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
      const background = this.data.active ? (this.data.critical ? 'red-backdrop' : 'blue-backdrop') : 'grey-backdrop'
      const foreground = this.data.critical ? (this.data.active ? 'theme-red' : 'red-backdrop') : (this.data.active ? 'theme-blue' : 'theme-grey')
      return { foreground, background }
    }
  }
}
</script>

<style lang="css" scoped>
</style>
