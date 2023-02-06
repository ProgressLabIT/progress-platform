<template>
  <BaseModalScreen :show="show" @close="$emit('close')">

    <template #header>
      <div class="q-ml-md q-py-xs medium highlight">
        {{ media_name }}
      </div>
    </template>

    <template #content>
      <div class="fit flex flex-center" style="background-color: ;">
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

        <q-page-sticky position="top-right" :offset="[35, 0]">
          <div class="column q-gutter-md">
          <q-btn
            round
            padding="sm sm"
            icon="mdi-magnify-plus-outline"
            class="shadow-12"
            color="grey"
            @click="zoomIn">
          </q-btn>
          <q-btn
            round
            padding="sm sm"
            icon="mdi-magnify-minus-outline"
            class="shadow-12"
            color="grey"
            @click="zoomOut">
          </q-btn>
          </div>
        </q-page-sticky>
      </div>
    </template>

  </BaseModalScreen>
</template>

<script>
import VuePdfEmbed from 'vue-pdf-embed'
import BaseModalScreen from '@/components/BaseModalScreen.vue'

export default {

  name: 'MediaViewer',

  components: {
    BaseModalScreen,
    VuePdfEmbed
  },

  props: ['show', 'media_name', 'media_src'],

  data() {
    return {
      image_extensions: ['png', 'jpeg', 'jpg'],
      doc_width: 800,
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
  }
}
</script>

<style lang="css">
.vue-pdf-embed > div {
  margin-bottom: 8px;
  box-shadow: 0 2px 8px 4px rgba(0,0,0,.1);
}
</style>
