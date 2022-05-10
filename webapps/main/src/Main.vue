<template>
  <v-app style="height: 100vh" :style="cssVars">
    <router-view></router-view>
  </v-app>
</template>

<script>
export default {

  name: 'Main',

  computed: {
    cssVars () {
      return {
        '--bg-color': this.$theme.background,
        '--text-high': this.$theme.text_high,
        '--text-low': this.$theme.text_low
      }
    }
  }
}
</script>

<style lang="css">
</style>
