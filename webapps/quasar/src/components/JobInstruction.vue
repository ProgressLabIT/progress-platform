<template>
  <q-carousel infinite keep-alive v-model="step_image_index" class="col">
    <q-carousel-slide
      v-for="(img, index) in step_media"
      :key="img"
      class="absolute-full row q-pa-none"
      :img-src="displayed_image_src"
      :name="index">

      <!-- INVISIBLE NAVIGATION -->
      <div class="col-6" @click="show('prev')" />
      <div class="col-6" @click="show('next')" />

      <!-- CAPTION -->
      <div class="absolute-top q-pa-md"
        v-show="show_details"
        style="background-color: #111a">
        <div class="text-h3 display">{{step.title}}</div>
        <div>{{ step.description }}</div>
      </div>

      <q-btn
        round
        color="theme-blue"
        class="absolute q-mt-md q-mr-md"
        style="right: 0"
        :icon="show_details ? 'mdi-close' : 'mdi-information-variant'"
        @click="show_details = !show_details">
      </q-btn>
    </q-carousel-slide>
  </q-carousel>

  <!-- THUMBNAIL NAVIGATION -->
  <div
    v-if="step_media.length > 1"
    class="absolute-bottom row q-mb-sm justify-center q-gutter-md"
    style="z-index: 9999;">
    <q-img
      loading="eager"
      v-for="(media, index) in step_media"
      :key="media"
      style="height: 50px; width: 70px"
      :style="step_image_index == index ? 'border-bottom: solid 3px' + $theme.blue : ''"
      :src="media_base_path + '/' + media"
      @mouseenter="step_image_index = index"
      class="shadow-6">
    </q-img>
  </div>
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
