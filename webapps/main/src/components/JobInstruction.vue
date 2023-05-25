<template>
  <div class="col relative-position" id="media-container">
    <div class="absolute-full row q-pa-none">

      <!-- MEDIA CONTAINER -->
      <div class="absolute-full scroll" v-if="step_media.length">
        <div class="q-mx-auto flex flex-center full-width relative-position" style="z-index: 0">

          <!-- INVISIBLE NAVIGATION -->
          <div class="row absolute-full">
            <div class="col-6" @click="show('prev')" style="z-index: 1"/>
            <div class="col-6" @click="show('next')" style="z-index: 1"/>
          </div>

          <!-- IMAGE CONTENT -->
          <q-img
            class="full-width"
            id="step-image"
            v-if="is_image"
            fit="cover"
            :src="media_src">
          </q-img>

          <!-- PDF CONTENT -->
          <div v-else class="q-py-xl">
            <vue-pdf-embed
              class="vue-pdf-embed"
              disableTextLayer
              disableAnnotationLayer
              ref="pdf"
              id="pdf"
              :source="media_src"
              :width="pdf_width">
            </vue-pdf-embed>
          </div>

        </div>
      </div>

      <!-- INSTRUCTIONS -->
      <div
        :class="step_media.length ? 'absolute-top q-pa-md' : 'absolute q-pa-md q-ma-xl'"
        v-show="step_media.length ? show_details : true"
        :style="step_media.length ? 'background-color: #111a' : ''">
        <div class="text-h3 display">{{step.title}}</div>
        <div>{{ step.description }}</div>
      </div>

      <q-btn
        v-if="step_media.length"
        round
        color="theme-blue"
        class="absolute-top-right q-mt-md q-mr-md"
        style="z-index: 5;"
        :icon="show_details ? 'mdi-close' : 'mdi-information-variant'"
        @click="show_details = !show_details">
      </q-btn>

      <q-btn
        v-if="step_media.length"
        round
        color="theme-grey"
        class="absolute-bottom-right q-mb-md q-mr-md"
        style="z-index: 5;"
        icon="mdi-fullscreen"
        @click="show_full_screen = true">
      </q-btn>

      <MediaViewer
        :show="show_full_screen"
        @close="show_full_screen = false"
        v-bind="{ media_name, media_src, instruction_title: step.title, instruction_detail: step.description }">
        <template v-slot:context-title>
         {{ $t('product.code').toUpperCase() }}: {{ product.code }}
        </template>
      </MediaViewer>

    </div>
  </div>

  <!-- THUMBNAIL NAVIGATION -->
  <div
    v-if="step_media.length > 1"
    class="absolute-bottom row q-mb-sm justify-center q-gutter-md"
    style="z-index: 3;">
    <q-img
      loading="eager"
      v-for="(media, index) in step_media"
      :key="media"
      style="height: 50px; width: 70px"
      :style="step_media_index == index ? 'border-bottom: solid 3px' + $theme.blue : ''"
      :src="media_base_path + '/' + media"
      @mouseenter="show(index)"
      class="shadow-6">
      <template #error>
        <div class="row fit flex-center surface1">
          <q-icon
            size="sm"
            :name="media.endsWith('.pdf') ? 'mdi-file-document-outline': 'mdi-error'"
            class="text-low">
          </q-icon>
        </div>
      </template>
    </q-img>
  </div>
</template>

<script>
import MediaViewer from '@/components/MediaViewer.vue'
import VuePdfEmbed from 'vue-pdf-embed'

export default {

  name: 'JobInstruction',

  components: {
    MediaViewer,
    VuePdfEmbed
  },

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
      show_details: false,
      image_extensions: ['png', 'jpeg', 'jpg'],
      show_full_screen: false
    }
  },

  computed: {

    current_step_index() {
      return this.$store.state.traceability.current_step_index
    },

    step_media() {
      return this.step.media ?? []
    },

    step_media_index: {
      get() {
        return this.$store.state.traceability.current_step_media_index
      },
      set(index) {
        this.$store.state.traceability.current_step_media_index = index
      }
    },

    media_name() {
      return this.step_media[this.step_media_index] ?? ''
    },

    media_base_path() {
      return this.media_root_path + this.step._key
    },

    media_src() {
      return this.media_base_path + '/' + this.media_name ?? null
    },

    is_image() {
      return this.image_extensions.some(e => this.media_name.endsWith(e))
    },
  },

  methods: {
    show(which) {
      const len = this.step_media.length

      if (which == 'next') {
        this.step_media_index == len - 1
        ? this.step_media_index = 0
        : this.step_media_index++
      }

      else if (which == 'prev') {
        this.step_media_index == 0
        ? this.step_media_index = len - 1
        : this.step_media_index--
      }

      else {
        this.step_media_index = which
      }
    }
  },

  watch: {
    current_step_index() {
      this.step_media_index = 0
    }
  },

  mounted() {
    const container = document.getElementById('media-container')
    this.pdf_width = !this.is_image ? container.clientWidth * 0.9 : undefined
  }
}
</script>

<style lang="css" scoped>
</style>
