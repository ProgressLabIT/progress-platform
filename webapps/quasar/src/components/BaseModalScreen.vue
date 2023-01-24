<template>
  <q-dialog
    :model-value="show"
    maximized no-backdrop-dismiss no-shake square no-route-dismiss
    transition-show="scale"
    transition-hide="scale"
    @escape-key="$emit('close')"
    @hide="$emit('close')"
    :style="CSSVars">
    <q-card class="background q-pa-sm">

      <!-- SCREEN HEADER -->
      <div class="row justify-start items-center q-pl-xs text-high">
        <slot name="close">
          <q-btn flat dense @click="$emit('close')">
            <q-icon size="xs" name="mdi-close" />
          </q-btn>
        </slot>
        <slot name="header"></slot>
      </div>

      <!-- WINDOW CONTAINER -->
      <q-card class="surface1 shadow-6 q-mx-sm scroll" :style="`height: ${card_height}px`">
        <slot name="content"></slot>
      </q-card>

    </q-card>
  </q-dialog>
</template>

<script>
import CSSVars from '@/mixins/CSSVars.js'

export default {

  name: 'BaseModalScreen',
  props: ['show'],
  mixins: [CSSVars],

  computed: {
    card_height() {
      return this.$q.screen.height - 52
    }
  }
}
</script>

<style lang="css" scoped>
</style>
