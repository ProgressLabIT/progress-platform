<template>
  <q-dialog
    :model-value="show"
    maximized no-backdrop-dismiss no-shake square
    transition-show="scale"
    transition-hide="scale"
    :style="CSSVars">
    <q-card class="column background q-pa-sm">

      <!-- SCREEN HEADER -->
      <div class="row justify-start items-center q-pl-xs text-high">
        <slot name="close">
          <q-icon size="xs" @click="$emit('close')" name="mdi-close" />
        </slot>
        <slot name="header"></slot>
      </div>

      <!-- WINDOW CONTAINER -->
      <q-card color="surface1" class="col shadow-6 q-ma-xs">
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
  mixins: [CSSVars]

};
</script>

<style lang="css" scoped>
</style>
