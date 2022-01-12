<template>
  <v-dialog
    :value="show"
    fullscreen persistent no-click-animation
    class="py-0"
    @keydown.esc="$emit('close')"
    @input="$emit('close')">
      <v-card :color="$theme.background">
        <v-container fluid class="d-flex flex-column pt-2 px-5" style="height:100vh"> 
          <v-row dense justify="start" align="center" class="pl-1 flex-grow-0">

            <!-- SCREEN HEADER -->
            <slot name="close">
              <v-icon small @click="$emit('close')">close</v-icon>
            </slot>

            <slot name="header">
            </slot>
          </v-row>  

          <!-- WINDOW CONTAINER -->
          <v-card class="flex-grow-1 scroll" :color="$theme.surface1" elevation="6">
            <slot name="content"></slot>
          </v-card>

        </v-container>
      </v-card>
  </v-dialog>
</template>

<script>
export default {

  name: 'BaseModalScreen',
  props: ['show'],

};
</script>

<style lang="css" scoped>
</style>
