<template>
  <BaseDialog :show="show" maximized @close="$emit('close')">
    <!-- FILE NAME -->
    <div class="fixed-top-left medium highlight q-ma-md" style="z-index: 99">
      <div v-if="info === 'name'" class="q-pa-md row" :style="darkGlassStyle">
        <div class="col column justify-center q-pt-sm">
          <div class="q-mb-md">FILE: {{ media_name }}</div>
          <template v-if="isWorkSession">
            <template v-for="field in job_info">
              <div
                v-if="job[field.name] !== undefined"
                :key="field.name"
                class="row items-center q-py-xs"
              >
                <div class="col text-h5 text-uppercase font-weight-medium">
                  {{ field.text }}
                </div>
                <div class="col">
                  <span>{{ $capitalizeAll(job[field.name]) }}</span>
                </div>
              </div>
            </template>
            <div class="row items-center q-py-xs">
              <div class="col text-h5 text-uppercase font-weight-medium">
                {{ $t('quantity.completed_total') }}
              </div>
              <div class="col">
                <span>{{ job.qt_completed }} / {{ job.qt_planned }}</span>
              </div>
            </div>
            <div v-if="instruction_title" class="q-mt-md text-uppercase">
              {{ instruction_title }}
            </div>
            <div v-if="instruction_details" class="q-my-sm text-body2">
              {{ instruction_details }}
            </div>
          </template>
        </div>
        <div class="col-auto q-ml-md">
          <q-btn
            flat
            round
            padding="xs xs"
            icon="mdi-chevron-left"
            size="md"
            @click="info = 'icon'"
          >
          </q-btn>
        </div>
      </div>
      <q-btn
        v-if="info === 'icon'"
        round
        flat
        padding="sm sm"
        icon="mdi-information-outline"
        class="q-mt-sm"
        :style="darkGlassStyle"
        @click="info = 'name'"
      >
      </q-btn>
    </div>

    <!-- CONTROLS -->
    <div class="fixed-top-right q-ma-lg">
      <div class="column q-gutter-md">
        <q-btn
          round
          flat
          padding="sm sm"
          icon="mdi-close"
          :style="darkGlassStyle"
          @click="$emit('close')"
        >
        </q-btn>
        <template v-if="show_view_controls">
          <q-btn
            round
            flat
            padding="sm sm"
            icon="mdi-magnify-plus-outline"
            :style="darkGlassStyle"
            @click="zoomIn"
          >
          </q-btn>
          <q-btn
            round
            flat
            padding="sm sm"
            :style="darkGlassStyle"
            icon="mdi-magnify-minus-outline"
            @click="zoomOut"
          >
          </q-btn>
          <q-btn
            round
            flat
            padding="sm sm"
            :style="darkGlassStyle"
            icon="mdi-rotate-left"
            @click="rotateLeft"
          >
          </q-btn>
          <q-btn
            round
            flat
            padding="sm sm"
            :style="darkGlassStyle"
            icon="mdi-rotate-right"
            @click="rotateRight"
          >
          </q-btn>
        </template>
      </div>
    </div>

    <!-- CONTENT -->
    <div class="absolute-full" style="z-index: -1">
      <div
        class="q-mx-auto flex flex-center full-height"
        :style="`width: ${doc_width}px`"
      >
        <q-img
          v-if="is_image"
          fit="contain"
          :src="media_src"
          :class="rotation_class"
        >
        </q-img>
        <div v-else-if="is_pdf" class="q-py-xl">
          <vue-pdf-embed
            ref="pdf"
            disable-text-layer
            disable-annotation-layer
            :source="media_src"
            :width="doc_width"
            :class="rotation_class"
            @loading-failed="(error) => console.log(error)"
            @rendering-failed="(error) => console.log(error)"
          >
          </vue-pdf-embed>
        </div>
        <div v-else-if="video_mimetype">
          <video-player
            :options="{
              autoplay: true,
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
        <div v-else>
          <div class="col column items-center q-gutter-lg">
            <div class="text-h5 text-uppercase font-weight-medium">
              {{ $t('cannot_render_content') }}
            </div>
            <div class="text-body1">
              {{ media_name }}
            </div>
            <q-btn
              color="theme-blue"
              class="q-mt-xl"
              stack
              :style="darkGlassStyle"
              icon="mdi-download"
              :label="$t('download')"
              :download="media_src"
              :href="media_src"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- WORK SESSION ITEMS -->
    <template v-if="isWorkSession">
      <div class="fixed-top full-width">
        <BaseProgressBar :data="job" size="8px" />
      </div>

      <div class="fixed-bottom full-width">
        <q-btn
          flat
          round
          class="absolute-top-left q-ml-sm"
          style="margin-top: -55px"
          :style="darkGlassStyle"
          :icon="action_drawer ? 'mdi-chevron-down' : 'mdi-chevron-up'"
          size="md"
          @click="action_drawer = !action_drawer"
        />
        <q-slide-transition>
          <div v-if="action_drawer">
            <div class="row" style="height: 10vh; min-height: 75px">
              <div class="col" style="backdrop-filter: blur(8px)">
                <StartPauseResumeBtn />
              </div>
              <div class="col" style="backdrop-filter: blur(3px)">
                <ProgressBtn />
              </div>
            </div>
          </div>
        </q-slide-transition>
      </div>
    </template>
  </BaseDialog>
</template>

<script>
import VuePdfEmbed from 'vue-pdf-embed';
import BaseDialog from '@/components/BaseDialog.vue';
import BaseProgressBar from '@/components/BaseProgressBar.vue';
import ProgressBtn from '@/components/ProgressBtn.vue';
import StartPauseResumeBtn from '@/components/StartPauseResumeBtn.vue';
import VideoPlayer from '@/components/VideoPlayer.vue';

export default {
  name: 'MediaViewer',

  components: {
    BaseDialog,
    VuePdfEmbed,
    StartPauseResumeBtn,
    ProgressBtn,
    BaseProgressBar,
    VideoPlayer,
  },

  props: {
    show: {
      type: Boolean,
      required: true,
    },
    is_pdf_stream: {
      type: Boolean,
      default: false,
    },
    media_name: {
      type: String,
      default: '',
    },
    media_src: {
      type: [Object, String],
      default: undefined,
    },
    instruction_title: {
      type: String,
      default: '',
    },
    instruction_details: {
      type: String,
      default: '',
    },
  },

  emits: ['close'],

  data() {
    return {
      image_extensions: ['png', 'jpeg', 'jpg', 'gif'],
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
      doc_width: 800,
      rotation_class: '',
      info: 'icon',
      action_drawer: true,
    };
  },

  computed: {
    isWorkSession() {
      return this.$route.matched.some((r) => r.name == 'workSession');
    },

    job() {
      return this.$store.state.traceability.working_job_data;
    },

    job_info() {
      return [
        { name: 'wo_code', text: this.$t('work_order.list_headers.wo_code') },
        { name: 'project_code', text: this.$t('project') },
        { name: 'phase_alias', text: this.$t('phase.short') },
        { name: 'active_batch_qt', text: this.$t('quantity.active.medium') },
      ];
    },

    is_image() {
      return this.media_name
        ? this.image_extensions.some((e) =>
            this.media_name.toLowerCase().endsWith(e),
          )
        : null;
    },

    is_pdf() {
      if (this.is_pdf_stream) {
        return true;
      }
      return this.media_name
        ? this.pdf_extensions.some((e) =>
            this.media_name.toLowerCase().endsWith(e),
          )
        : null;
    },

    show_view_controls() {
      // Control zoom and rotate control visibility
      return this.is_image || this.is_pdf;
    },

    video_mimetype() {
      if (!this.media_name) {
        return undefined;
      }

      try {
        const ext = this.media_name
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
  },

  created() {
    this.doc_width = Math.min(this.$q.screen.width * 0.8, 1200);
    this.darkGlassStyle = `z-index: 99; backdrop-filter: blur(4px); background-color: ${this.$theme.background}aa`;
  },

  methods: {
    zoomIn() {
      this.doc_width = this.doc_width * 1.2;
    },

    zoomOut() {
      this.doc_width = this.doc_width / 1.2;
    },

    rotateLeft() {
      switch (this.rotation_class) {
        case '':
          this.rotation_class = 'rotate-270';
          break;
        case 'rotate-270':
          this.rotation_class = 'rotate-180';
          break;
        case 'rotate-180':
          this.rotation_class = 'rotate-90';
          break;
        case 'rotate-90':
          this.rotation_class = '';
          break;
        default:
          this.rotation_class = '';
      }
    },

    rotateRight() {
      switch (this.rotation_class) {
        case '':
          this.rotation_class = 'rotate-90';
          break;
        case 'rotate-90':
          this.rotation_class = 'rotate-180';
          break;
        case 'rotate-180':
          this.rotation_class = 'rotate-270';
          break;
        case 'rotate-270':
          this.rotation_class = '';
          break;
        default:
          this.rotation_class = '';
      }
    },
  },
};
</script>

<style lang="css">
.vue-pdf-embed > div {
  margin-bottom: 8px;
  box-shadow: 0 2px 8px 4px rgba(0, 0, 0, 0.1);
}
</style>
