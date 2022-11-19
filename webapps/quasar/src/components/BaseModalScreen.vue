<template>
  <q-dialog
    :model-value="show"
    maximized no-backdrop-dismiss no-shake square
    transition-show="scale"
    transition-hide="scale">
    <q-card class="column background q-pa-sm">

      <!-- SCREEN HEADER -->
      <div class="row justify-start items-center q-pl-xs">
        <slot name="close">
          <q-icon size="sm" @click="$emit('close')" name="mdi-close" />
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
export default {

  name: 'BaseModalScreen',
  props: ['show'],

};
</script>

<style lang="css" scoped>
</style>
