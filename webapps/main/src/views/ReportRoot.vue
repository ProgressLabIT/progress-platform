<template>
  <div class="absolute-full scroll">
    <iframe id="iframe" :src="src" frameborder="0"></iframe>
  </div>
</template>

<script>
export default {
  name: 'ReportRoot',

  computed: {
    src() {
      // return window.location.hostname
      return 'http://91.229.245.119:30002'
    }
  },

  created() {
    console.log(this.src)
  }
}
</script>

<style lang="sass" scoped>
#iframe
  height: 100%
  width: 100%
</style>
