<template>
    <v-dialog 
      :value="show"
      fullscreen
      class="py-0"
      @keydown.esc="$emit('close')"
      transition="scale-transition"
    >
    <v-lazy>
    <v-card :color="$theme.black">
      <v-container fluid class="d-flex flex-column pt-2 px-5" style="height:100vh"> 
        <v-row dense justify="center" align="center" class="my-0 pl-1 flex-grow-0">
          <v-col >
            <v-icon small @click="$emit('close')">close</v-icon>
            <span class="ml-4 medium highlight">{{ media_name }}</span>
          </v-col>
          <v-spacer></v-spacer>
          <!-- <v-slider
            v-model="zoom"
            max="400"
            min="1"
            append-icon="zoom_in"
            prepend-icon="zoom_out"
            @click:append="zoomIn"
            @click:prepend="zoomOut"
          ></v-slider> -->
          <v-col cols="auto" class="ml-auto display medium highlight weight-medium">
            <slot name="context-title"></slot>
          </v-col>
        </v-row>
  
      <v-card outlined tile class="flex-grow-1 scroll" :style="'background-color:' + $theme.background">
        <v-img contain height="100%"
          v-if="type=='img'" 
          :src="media_src">
        </v-img>
        <embed v-else
          :key="media_src"
          :src="media_src"
          width="100%"
          height="100%" />
        </v-card>
      </v-container>
    </v-card>
  </v-lazy>
  </v-dialog>
</template>

<script>
export default {

  name: 'MediaViewer',

  props: ['show', 'media_name', 'media_src', "type"],

  data() {
    return {
      image_extensions: ['png', 'jpeg', 'jpg']
    }
  },

  methods: {
    media_extension() {
      const ext = typeof this.media_name == "string" 
        ? this.media_name.split('.')[this.media_src.length -1]
        : null
      return ext
    },
  }

}
</script>

<style lang="css" scoped>
</style>