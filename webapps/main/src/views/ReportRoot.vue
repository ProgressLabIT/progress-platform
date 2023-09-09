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
      const port = '8501'
      const domain = window.location.hostname
      return `http://${domain}:${port}`
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
