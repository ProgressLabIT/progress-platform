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
    :style="{ ...CSSVars, '--backdrop-color': background }">
    <template v-if="maximized">
      <div class="fixed-full row flex-center" style="background-color: backdrop_color;">
        <slot></slot>
      </div>
    </template>
    <template v-else>
      <slot></slot>
    </template>
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
    },
    background: {
      type: String,
      default: '#090C0DCC'
    },
  }
}
</script>

<style lang="sass">
.q-dialog__backdrop
  background-color: var(--backdrop-color)
</style>
