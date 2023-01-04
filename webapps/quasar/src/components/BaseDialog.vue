<template>
  <q-dialog
    :model-value="show"
    :maximized="maximized"
    no-backdrop-dismiss
    no-route-dismiss
    no-shake
    square
    transition-show="scale"
    transition-hide="scale"
    @escape-key="$emit('close')"
    @hide="$emit('close')"
    :style="CSSVars">
    <slot></slot>
  </q-dialog>
</template>

<script>
import CSSVars from '@/mixins/CSSVars.js'

export default {

  name: 'BaseDialog',
  mixins: [CSSVars],
  props: {
    show: {
      type: Boolean,
      required: true
    },
    maximized: {
      type: Boolean,
      default: false
    }
  }
}
</script>

<style lang="css" scoped>
</style>
