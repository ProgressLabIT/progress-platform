<template>
  <v-dialog
    :value="show"
    fullscreen
    class="py-0"
    @input="$emit('close')">
      <v-card :color="$theme.black">
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
          <v-card outlined tile class="flex-grow-1 scroll" :style="'background-color:' + $theme.background">
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
