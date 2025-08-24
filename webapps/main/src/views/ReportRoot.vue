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
      const domain = window.location.hostname;
      const protocol = window.location.protocol;
      return `${protocol}//reporting.${domain}`;
    },
  },

  created() {
    console.log(this.src);
  },
};
</script>

<style lang="sass" scoped>
#iframe
  height: 100%
  width: 100%
</style>
