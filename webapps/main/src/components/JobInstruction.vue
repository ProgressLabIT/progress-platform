<template>
  <div id="media-container" class="col relative-position">
    <div class="absolute-full row q-pa-none">
      <!-- MEDIA CONTAINER -->
      <div v-if="step_media.length" class="absolute-full scroll">
        <div
          class="q-mx-auto flex flex-center full-width relative-position"
          style="z-index: 0"
        >
          <!-- INVISIBLE NAVIGATION -->
          <div class="row absolute-full justify-between">
            <div class="col-3" style="z-index: 1" @click="show('prev')" />
            <div class="col-3" style="z-index: 1" @click="show('next')" />
          </div>

          <!-- IMAGE CONTENT -->
          <q-img
            v-if="is_image"
            id="step-image"
            class="full-width"
            fit="cover"
            :src="media_src"
          >
          </q-img>

          <!-- PDF CONTENT -->
          <div v-else-if="is_pdf" class="q-py-xl">
            <vue-pdf-embed
              id="pdf"
              ref="pdf"
              class="vue-pdf-embed"
              disable-text-layer
              disable-annotation-layer
              :source="media_src"
              :width="pdf_width"
            />
          </div>

          <!-- VIDEO/AUDIO CONTENT -->
          <div v-else-if="video_mimetype">
            <video-player
              :options="{
                autoplay: false,
                controls: true,
                sources: [
                  {
                    src: media_src,
                    type: video_mimetype,
                  },
                ],
              }"
            />
          </div>

          <!-- UNKNOWN CONTENT -->
          <div v-else>
            <div class="col text-h5 text-uppercase font-weight-medium">
              {{ $t('cannot_render_content') }}
            </div>
            <q-btn
              flat
              square
              class="q-mr-lg"
              :style="darkGlassStyle"
              size="md"
              :download="media_src"
              :href="media_src"
              >{{ $t('download') }}
            </q-btn>
          </div>
        </div>
      </div>

      <!-- INSTRUCTIONS -->
      <div
        v-show="step_media.length ? show_details : true"
        :class="
          step_media.length
            ? 'absolute-top q-pa-md'
            : 'absolute q-pa-md q-ma-xl'
        "
        :style="step_media.length ? 'background-color: #111a' : ''"
      >
        <div class="text-h3 display">{{ step.title }}</div>
        <div style="white-space: pre-line">{{ step.description }}</div>
      </div>

      <q-btn
        v-if="step_media.length"
        round
        color="theme-blue"
        class="absolute-top-right q-mt-md q-mr-md"
        style="z-index: 5"
        :icon="show_details ? 'mdi-close' : 'mdi-information-variant'"
        @click="show_details = !show_details"
      >
      </q-btn>

      <q-btn
        v-if="step_media.length"
        round
        color="theme-grey"
        class="absolute-bottom-right q-mb-md q-mr-md"
        style="z-index: 5"
        icon="mdi-fullscreen"
        @click="show_full_screen = true"
      >
      </q-btn>

      <MediaViewer
        :show="show_full_screen"
        :media_name="media_name"
        :media_src="media_src"
        v-bind="{
          instruction_title: step.title,
          instruction_detail: step.description,
        }"
        @close="show_full_screen = false"
      >
        <template #context-title>
          {{ $t('product.code').toUpperCase() }}: {{ product.code }}
        </template>
      </MediaViewer>
    </div>
  </div>

  <!-- THUMBNAIL NAVIGATION -->
  <div
    v-if="step_media.length > 1"
    class="absolute-bottom row q-mb-sm justify-center q-gutter-md"
    style="z-index: 3"
  >
    <q-img
      v-for="(media, index) in step_media"
      :key="media"
      loading="eager"
      style="height: 50px; width: 70px"
      :style="
        step_media_index === index
          ? 'border-bottom: solid 3px' + $theme.blue
          : ''
      "
      :src="media_base_path + '/' + media"
      class="shadow-6"
      @mouseenter="show(index)"
    >
      <template #error>
        <div class="row fit flex-center surface1">
          <q-icon size="sm" :name="media_icon(media)" class="text-low">
          </q-icon>
        </div>
      </template>
    </q-img>
  </div>
</template>

<script>
import VuePdfEmbed from 'vue-pdf-embed';
import MediaViewer from '@/components/MediaViewer.vue';
import VideoPlayer from '@/components/VideoPlayer.vue';

export default {
  name: 'JobInstruction',

  components: {
    MediaViewer,
    VuePdfEmbed,
    VideoPlayer,
  },

  props: {
    step: {
      type: Object,
      default: () => ({}),
    },
  },

  data() {
    return {
      pdf_width: undefined,
      media_root_path: '/media/step/',
      show_details: true,
      image_extensions: ['png', 'jpeg', 'jpg'],
      show_full_screen: false,
      pdf_extensions: ['pdf'],
      mimetypes_kinds: {
        opus: 'video/ogg',
        ogv: 'video/ogg',
        mp4: 'video/mp4',
        mov: 'video/mp4',
        m4v: 'video/mp4',
        mkv: 'video/x-matroska',
        m4a: 'audio/mp4',
        mp3: 'audio/mpeg',
        aac: 'audio/aac',
        caf: 'audio/x-caf',
        flac: 'audio/flac',
        oga: 'audio/ogg',
        wav: 'audio/wav',
        m3u8: 'application/x-mpegURL',
        mpd: 'application/dash+xml',
        svg: 'image/svg+xml',
        webp: 'image/webp',
      },
    };
  },

  computed: {
    step_media() {
      return this.step.media ?? [];
    },

    step_media_index: {
      get() {
        return this.$store.state.traceability.current_step_media_index;
      },
      set(index) {
        this.$store.state.traceability.current_step_media_index = index;
      },
    },

    media_name() {
      return this.step_media[this.step_media_index] ?? '';
    },

    media_base_path() {
      return this.media_root_path + this.step._key;
    },

    media_src() {
      return this.media_base_path + '/' + this.media_name ?? null;
    },

    is_image() {
      return this.image_extensions.some((e) => this.media_name.endsWith(e));
    },

    is_pdf() {
      return this.check_pdf(this.media_name);
    },

    video_mimetype() {
      return this.get_video_mimetype(this.media_name);
    },
  },

  mounted() {
    if (this.is_image) {
      return;
    }

    const container = document.getElementById('media-container');
    this.pdf_width = container.clientWidth * 0.9;

    this.step_media_index = 0;
  },

  methods: {
    show(which) {
      const len = this.step_media.length;

      if (which == 'next') {
        this.step_media_index == len - 1
          ? (this.step_media_index = 0)
          : this.step_media_index++;
      } else if (which == 'prev') {
        this.step_media_index == 0
          ? (this.step_media_index = len - 1)
          : this.step_media_index--;
      } else {
        this.step_media_index = which;
      }
    },

    check_pdf(media_name) {
      return media_name
        ? this.pdf_extensions.some((e) => media_name.toLowerCase().endsWith(e))
        : null;
    },

    get_video_mimetype(media_name) {
      if (!media_name) {
        return undefined;
      }

      try {
        const ext = media_name
          .split('.')
          .filter(Boolean) // removes empty extensions (e.g. `filename...txt`)
          .slice(1)
          .join('.');
        const mimetype = this.mimetypes_kinds[ext.toLowerCase()];

        return mimetype || undefined;
      } catch {
        return undefined;
      }
    },

    media_icon(media) {
      if (this.check_pdf(media)) {
        return 'mdi-file-document-outline';
      } else if (this.get_video_mimetype(media)) {
        return 'mdi-video-outline';
      } else {
        return 'mdi-download-outline';
      }
    },
  },
};
</script>
