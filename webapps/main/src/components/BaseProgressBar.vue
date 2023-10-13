<template>
  <component
    :is="progressComponent"
    animation-speed="300"
    :value="progress"
    :color="color.foreground"
    :track-color="color.background"
    :buffer="1"
    :size="size"
  />
</template>

<script>
import { QCircularProgress, QLinearProgress } from 'quasar'

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
    },
    type: {
      type: String,
      default: 'linear'
    }
  },

  computed: {
    progressComponent() {
      return this.type === 'linear' ? QLinearProgress : QCircularProgress
    },

    progress() {
      return this.type === 'linear' ? this.data.progress / 100 : this.data.progress
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
