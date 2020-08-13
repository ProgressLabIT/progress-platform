<template>
  <v-window 
    continuous
    :show-arrows="false"
    v-model="step_image_index">
    <v-window-item 
      v-for="(img, index) in step_media" 
      :key="index" 
      eager
      class="no-transition">
      <v-img eager 
        :src="displayed_image_src" 
        :height="height">
        <template v-slot:placeholder>
          <v-progress-circular size="60" indeterminate></v-progress-circular>
        </template>

        <div class="d-flex flex-column fill">
          <!-- STEP TITLE AND DESCRIPTION -->
          <v-btn absolute right top fab small
            @click="show_details = !show_details"
            :color="show_details ? null : $theme.blue"
            class="mt-12">
            <v-icon>
              {{ show_details ? 'close' : 'mdi-information-variant' }}
            </v-icon>
          </v-btn>
          
          <v-sheet v-show="show_details" color="rgba(0,0,0,.7)">  
            <v-container>
              <v-row justify="space-between" no-gutters>
                <v-col cols="11">
                  <v-card-title class="display highlight px-0 pt-0">
                    {{ step.title }}
                  </v-card-title>
                  <v-card-subtitle 
                    class="px-0 pb-1">
                    {{ step.description }}
                  </v-card-subtitle>
                </v-col>
              </v-row>    
            </v-container>
          </v-sheet>
          
          <!-- INVISIBLE IMAGE SWITCH CONTROLS -->
          <v-row no-gutters
            v-if="step_media.length > 1"
            class="mx-0">
            <v-col cols="6" @click="show('prev')">
            </v-col>
            <v-col cols="6" @click="show('next')">
            </v-col>
            <v-col align-self="end" style="position: absolute">
              <v-row justify="center">
                <v-card tile raised
                  v-for="(media, index) in step_media" 
                  :key="index" 
                  height="50px" 
                  width="70px"
                  class="ma-2"
                  :style="step_image_index == index ? 'border-bottom: solid 3px' + $theme.blue : ''"
                  :img="media_base_path + '/' + media"
                  @mouseenter="step_image_index = index">
                </v-card>
              </v-row>
            </v-col>  
          </v-row>
        </div>
        
      </v-img>


    </v-window-item>
  </v-window>
</template>

<script>
export default {

  name: 'JobInstruction',

  props: {
    step: {
      type: Object,
      default: () => {}
    },
    height: {
      type: Number,
      required: true
    }
  },

  data () {
    return {
      media_root_path: '/media/step/',
      step_image_index: 0,
      show_details: false,
    }
  },

  computed: {
    step_media() {
      if (this.step != undefined) return this.step.media
      else return []
    },

    media_base_path() {
      return this.media_root_path + this.step._key
    },

    displayed_image_src() {
      return this.media_base_path + '/' + this.step_media[this.step_image_index]
    },
  },

  methods: {
    show(which) {
      const len = this.step_media.length

      if (which == 'next') {
        this.step_image_index == len - 1 
        ? this.step_image_index = 0 
        : this.step_image_index++
      }

      else if (which == 'prev') {
        this.step_image_index == 0 
        ? this.step_image_index = len - 1 
        : this.step_image_index--
      }
    }
  },

  watch: {
    step() {
      this.step_image_index = 0
    }
  }
}
</script>

<style lang="css" scoped>
</style>