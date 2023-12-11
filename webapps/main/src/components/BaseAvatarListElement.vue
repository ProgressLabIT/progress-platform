<template>
  <!-- TODO: This component is only used within PhaseAssignments.vue which is not used anywhere -->
  TEST
</template>

<script>
// import BaseTooltipIcon from '@/components/BaseTooltipIcon.vue'

export default {
  name: 'BaseAvatarListElement',

  props: {
    src: {
      type: String,
      required: true,
    },
    title: {
      type: String,
      required: true,
    },
    subtitle: {
      type: String,
      default: undefined,
    },
    edit: {
      type: Boolean,
      default: false,
    },
    icon: {
      type: String,
      default: 'close',
    },
    tooltip: {
      type: String,
      default: undefined,
    },
    color: {
      type: String,
      default: undefined,
    },
  },

  emits: ['iconClick'],

  // components: {BaseTooltipIcon},

  methods: {
    emit() {
      this.$emit('iconClick');
    },
  },
};
</script>

<style lang="css" scoped></style>
