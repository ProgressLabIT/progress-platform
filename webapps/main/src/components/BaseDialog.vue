<template>
  <q-dialog
    :ref="getDialogRef()"
    :model-value="show"
    :maximized="maximized"
    :no-backdrop-dismiss="noBackdropDismiss"
    no-route-dismiss
    no-shake
    square
    transition-show="scale"
    transition-hide="scale"
    :style="{ ...CSSVars, '--backdrop-color': background }"
    @escape-key="$emit('close', $event)"
    @hide="$emit('close', $event)"
    @keydown.esc="$emit('close', $event)"
  >
    <template v-if="maximized">
      <div
        class="fixed-full row flex-center"
        :style="`background-color: ${background || default_background};`"
      >
        <slot></slot>
      </div>
    </template>
    <template v-else>
      <slot></slot>
    </template>
  </q-dialog>
</template>

<script>
import CSSVars from '@/mixins/CSSVars.js';

export default {
  name: 'BaseDialog',
  mixins: [CSSVars],
  props: {
    show: {
      type: Boolean,
      required: true,
    },
    maximized: {
      type: Boolean,
      default: false,
    },
    noBackdropDismiss: {
      type: Boolean,
      default: true,
    },
    background: {
      type: String,
      default: null,
    },
    getDialogRef: {
      type: Function,
      default: () => {},
    },
  },
  emits: ['close'],

  created() {
    this.default_background = this.$theme.background;
  },
};
</script>

<style lang="sass">
.q-dialog__backdrop
  background-color: var(--bg-color)
  opacity: .8
</style>
