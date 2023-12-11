<template>TEST</template>

<script>
// import BaseTooltipIcon from '@/components/BaseTooltipIcon.vue'

export default {
  name: 'BaseAvatarListElement',

  props: {
    src: String,
    title: String,
    subtitle: String,
    edit: Boolean,
    icon: {
      type: String,
      default: 'close',
    },
    tooltip: String,
    color: String,
  },

  // components: {BaseTooltipIcon},

  methods: {
    emit() {
      this.$emit('iconClick');
    },
  },
};
</script>

<style lang="css" scoped></style>
