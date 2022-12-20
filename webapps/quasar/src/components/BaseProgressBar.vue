<template>
  <q-linear-progress
    :value="progress"
    :color="color"
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
        ? 'theme-blue'
        : 'theme-grey'
    }
  }
}
</script>

<style lang="css" scoped>
</style>
