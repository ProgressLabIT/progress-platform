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
      <v-img eager :src="displayed_image_src" :height="height">

        <template v-slot:placeholder>
          <v-progress-circular size="60" indeterminate></v-progress-circular>
        </template>

        <template v-if="step_media.length > 1">
          <v-row no-gutters
            class="fill mx-0" 
            style="position:absolute">
            <v-col cols="6" @click="show('prev')">
            </v-col>
            <v-col cols="6" @click="show('next')">
            </v-col>
          </v-row>
          <v-row class="fill-height" justify="center" align="end">
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
        </template>
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
      step_image_index: 0
    }
  },

  computed: {
    step_media() {
      if (this.step != undefined) return this.step.media
      else return []
    },

    media_base_path() {
      return this.media_root_path + this.step._id.split('/')[1]
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