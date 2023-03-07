<template>
  <BaseDialog :show="show" @close="$emit('close')" maximized>

    <!-- FILE NAME -->
    <div class="fixed-top-left medium highlight q-ma-lg" style="z-index: 99;">
      <div
        v-if="info==='name'"
        class="q-pa-md"
        :style="darkGlassStyle">
        {{ media_name }}
        <q-btn
          flat
          round
          padding="xs xs"
          icon="mdi-chevron-left"
          size="md"
          @click="info='icon'">
        </q-btn>
      </div>
      <q-btn
        v-if="info==='icon'"
        round flat
        padding="sm sm"
        icon="mdi-information-outline"
        class="q-mt-sm"
        :style="darkGlassStyle"
        @click="info='name'">
      </q-btn>
    </div>

    <!-- CONTROLS -->
    <div class="fixed-top-right q-ma-lg">
      <div class="column q-gutter-md">
        <q-btn
          round flat
          padding="sm sm"
          icon="mdi-close"
          :style="darkGlassStyle"
          @click="$emit('close')">
        </q-btn>
        <q-btn
          round flat
          padding="sm sm"
          icon="mdi-magnify-plus-outline"
          :style="darkGlassStyle"
          @click="zoomIn">
        </q-btn>
        <q-btn
          round flat
          padding="sm sm"
          :style="darkGlassStyle"
          icon="mdi-magnify-minus-outline"
          @click="zoomOut">
        </q-btn>
      </div>
    </div>

    <!-- CONTENT -->
    <div class="fit flex flex-center q-pa-xl" style="z-index: -1;">
      <q-img fit="contain"
        v-if="hasImageExtension()"
        :src="media_src">
      </q-img>
      <vue-pdf-embed
        v-else
        disableTextLayer
        ref="pdf"
        :source="media_src"
        :width="doc_width">
      </vue-pdf-embed>
    </div>

    <!-- WORK SESSION BUTTONS -->
    <div
      v-if="isWorkSession"
      class="fixed-bottom full-width">
      <q-btn
        flat square
        class="q-mr-lg"
        :style="darkGlassStyle"
        :icon="action_drawer ? 'mdi-chevron-down' : 'mdi-chevron-up'"
        size="md"
        @click="action_drawer = !action_drawer">
      </q-btn>
      <q-slide-transition>
        <div v-if="action_drawer">
          <div class="row" style="height: 10vh;">
            <div class="col" style="backdrop-filter: blur(8px);">
              <StartPauseResumeBtn />
            </div>
            <div class="col" style="backdrop-filter: blur(3px);">
              <ProgressBtn />
            </div>
          </div>
        </div>
      </q-slide-transition>
    </div>
  </BaseDialog>
</template>

<script>
import VuePdfEmbed from 'vue-pdf-embed'
import BaseDialog from '@/components/BaseDialog.vue'
import StartPauseResumeBtn from '@/components/StartPauseResumeBtn.vue'
import ProgressBtn from '@/components/ProgressBtn.vue'

export default {

  name: 'MediaViewer',

  components: {
    BaseDialog,
    VuePdfEmbed,
    StartPauseResumeBtn,
    ProgressBtn
  },

  props: ['show', 'media_name', 'media_src'],

  data() {
    return {
      image_extensions: ['png', 'jpeg', 'jpg'],
      doc_width: 800,
      info: "icon",
      action_drawer: false
    }
  },

  computed: {
    isWorkSession() {
      return this.$route.matched.some(r => r.name == 'workSession')
    }
  },

  methods: {
    hasImageExtension() {
      // const ext = typeof this.media_name == "string" 
      //   ? this.media_name.split('.')[this.media_src.length -1]
      //   : null
      // return ext
      return this.media_src
        ? this.image_extensions.some( e => this.media_src.endsWith(e) )
        : null
    },

    zoomIn() {
      this.doc_width = this.doc_width * 1.2
    },

    zoomOut() {
      this.doc_width = this.doc_width / 1.2
    }
  },


  created() {
    this.doc_width = Math.min(this.$q.screen.width * .8, 1200)
    this.darkGlassStyle = `z-index: 99; backdrop-filter: blur(4px); background-color: ${this.$theme.background}aa`
  }
}
</script>

<style lang="css">
.vue-pdf-embed > div {
  margin-bottom: 8px;
  box-shadow: 0 2px 8px 4px rgba(0,0,0,.1);
}
</style>
